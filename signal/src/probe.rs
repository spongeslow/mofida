//! Contrastive Axis Direction probe.
//!
//! Implements the *Representation Engineering* reading-vector idea (Zou et al.,
//! arXiv 2310.01405) over retrieval embeddings: each of the nine diagnostic axes
//! has a unit direction in the 1024-d `bge-m3` space, computed offline as the
//! normalised difference of positive vs. negative class means
//! (`scripts/compute_axis_directions.py`). Projecting any chunk embedding onto
//! the nine directions yields a per-axis relevance vector.
//!
//! Directions reach this service two ways:
//!   • `POST /probe/install` — the offline script pushes a JSON payload (no shared
//!     volume needed); the service caches it in memory and persists `probe.json`.
//!   • on-disk assets at startup — `probe.json`, or a NumPy `probe_directions.npy`
//!     plus `probe_stats.json` (so a committed/volume-mounted matrix also works).

use std::collections::HashMap;
use std::path::PathBuf;

use parking_lot::RwLock;
use serde::{Deserialize, Serialize};

use crate::npy::Npy;

#[derive(Clone, Serialize, Deserialize)]
pub struct ProbeData {
    /// Row-major (n_axes × embed_dim) unit direction vectors.
    pub directions: Vec<Vec<f32>>,
    /// Axis names, one per row of `directions`.
    pub axis_names: Vec<String>,
    pub embed_dim: usize,
    /// Per-axis (mean, std) of raw projections over the training corpus, keyed by axis.
    pub stats: HashMap<String, StatEntry>,
}

#[derive(Clone, Serialize, Deserialize)]
pub struct StatEntry {
    pub mean: f32,
    pub std: f32,
}

#[derive(Deserialize)]
pub struct ProjectRequest {
    pub embedding: Vec<f32>,
    #[serde(default = "default_top_k")]
    pub top_k: usize,
}

fn default_top_k() -> usize {
    3
}

#[derive(Serialize)]
pub struct ProjectResponse {
    pub axis_relevance: HashMap<String, f32>,
    pub top_axes: Vec<(String, f32)>,
    pub dominant_axis: String,
}

pub struct AxisProbe {
    json_path: PathBuf,
    npy_path: PathBuf,
    stats_path: PathBuf,
    data: RwLock<Option<ProbeData>>,
}

impl AxisProbe {
    pub fn new(assets: &std::path::Path) -> Self {
        let probe = AxisProbe {
            json_path: assets.join("probe.json"),
            npy_path: assets.join("probe_directions.npy"),
            stats_path: assets.join("probe_stats.json"),
            data: RwLock::new(None),
        };
        match probe.load() {
            Ok(n) => tracing::info!("probe: loaded {n} axis directions"),
            Err(e) => tracing::warn!(
                "probe: directions unavailable ({e}); /probe/project returns 503 until installed"
            ),
        }
        probe
    }

    pub fn is_ready(&self) -> bool {
        self.data.read().is_some()
    }

    pub fn axis_count(&self) -> usize {
        self.data.read().as_ref().map(|d| d.axis_names.len()).unwrap_or(0)
    }

    /// (Re)load directions from disk: prefer `probe.json`, fall back to npy+stats.
    pub fn load(&self) -> anyhow::Result<usize> {
        let data = if self.json_path.exists() {
            serde_json::from_str::<ProbeData>(&std::fs::read_to_string(&self.json_path)?)?
        } else {
            self.load_npy()?
        };
        let n = data.axis_names.len();
        *self.data.write() = Some(data);
        Ok(n)
    }

    fn load_npy(&self) -> anyhow::Result<ProbeData> {
        let bytes = std::fs::read(&self.npy_path)?;
        let npy = Npy::parse(&bytes)?;
        if npy.shape.len() != 2 {
            anyhow::bail!("expected a 2-D direction matrix, got shape {:?}", npy.shape);
        }
        let n_axes = npy.shape[0];
        let embed_dim = npy.shape[1];

        let stats: HashMap<String, StatEntry> =
            serde_json::from_str(&std::fs::read_to_string(&self.stats_path)?)?;
        let mut axis_names: Vec<String> = stats.keys().cloned().collect();
        axis_names.sort();
        if axis_names.len() != n_axes {
            anyhow::bail!("stats axis count {} != matrix rows {}", axis_names.len(), n_axes);
        }

        let mut directions = Vec::with_capacity(n_axes);
        for r in 0..n_axes {
            let start = r * embed_dim;
            directions.push(npy.data[start..start + embed_dim].to_vec());
        }
        Ok(ProbeData {
            directions,
            axis_names,
            embed_dim,
            stats,
        })
    }

    /// Install directions pushed over HTTP; persists `probe.json` for restart.
    pub fn install(&self, data: ProbeData) -> anyhow::Result<usize> {
        if data.directions.len() != data.axis_names.len() {
            anyhow::bail!(
                "directions rows {} != axis_names {}",
                data.directions.len(),
                data.axis_names.len()
            );
        }
        for (i, row) in data.directions.iter().enumerate() {
            if row.len() != data.embed_dim {
                anyhow::bail!("row {i} has dim {} != embed_dim {}", row.len(), data.embed_dim);
            }
        }
        let n = data.axis_names.len();
        if let Err(e) = std::fs::write(&self.json_path, serde_json::to_string(&data)?) {
            tracing::warn!("probe: failed to persist probe.json: {e}");
        }
        *self.data.write() = Some(data);
        Ok(n)
    }

    /// Project one embedding onto every axis direction. `None` if not loaded or
    /// the embedding dimensionality is wrong.
    pub fn project(&self, embedding: &[f32], top_k: usize) -> Option<ProjectResponse> {
        let guard = self.data.read();
        let d = guard.as_ref()?;
        if embedding.len() != d.embed_dim {
            tracing::warn!("probe: embedding dim {} != expected {}", embedding.len(), d.embed_dim);
            return None;
        }

        let mut axis_relevance = HashMap::new();
        let mut ranked: Vec<(String, f32)> = Vec::with_capacity(d.axis_names.len());
        for (i, dir) in d.directions.iter().enumerate() {
            let mut raw = 0.0f32;
            for j in 0..d.embed_dim {
                raw += embedding[j] * dir[j];
            }
            let name = &d.axis_names[i];
            let (mu, sigma) = d
                .stats
                .get(name)
                .map(|s| (s.mean, s.std))
                .unwrap_or((0.0, 1.0));
            let z = (raw - mu) / (sigma + 1e-8);
            let score = 1.0 / (1.0 + (-z).exp());
            let score = (score * 1000.0).round() / 1000.0;
            axis_relevance.insert(name.clone(), score);
            ranked.push((name.clone(), score));
        }

        ranked.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        let dominant_axis = ranked.first().map(|(a, _)| a.clone()).unwrap_or_default();
        ranked.truncate(top_k.max(1));

        Some(ProjectResponse {
            axis_relevance,
            top_axes: ranked,
            dominant_axis,
        })
    }
}
