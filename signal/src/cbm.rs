//! Concept Bottleneck Model scoring layer.
//!
//! Implements the linear bottleneck `g(c) = sigmoid(bias + Σ wᵢ·cᵢ) × 5` from
//! *Concept Bottleneck Models* (Koh et al., ICML 2020) in its Label-Free variant
//! (Oikarinen et al., ICLR 2023): the concept activations `c` are produced by an
//! LLM upstream (the Python `cbm/scorer.py`), and this module owns only the
//! interpretable linear head plus its ridge-regression calibration.
//!
//! Weights live in `assets/cbm_weights.json` (prior weights committed; overwritten
//! per-axis by `/cbm/calibrate` once enough diagnostic history exists).

use std::collections::{BTreeSet, HashMap};
use std::path::PathBuf;

use nalgebra::{DMatrix, DVector};
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AxisWeights {
    pub weights: HashMap<String, f64>,
    pub bias: f64,
}

#[derive(Deserialize)]
pub struct ScoreRequest {
    pub axis: String,
    pub concepts: HashMap<String, f64>,
}

#[derive(Serialize)]
pub struct Bottleneck {
    pub concept_id: String,
    pub current: f64,
    pub weight: f64,
    /// Projected axis score (0–5) if this concept improved to 0.80.
    pub score_if_fixed: f64,
}

#[derive(Serialize)]
pub struct ScoreResponse {
    pub axis: String,
    pub score: f64,
    pub weighted_contributions: HashMap<String, f64>,
    pub bottleneck: Option<Bottleneck>,
    /// Whether axis-specific calibrated weights were used (vs. equal-weight fallback).
    pub calibrated: bool,
}

#[derive(Deserialize)]
pub struct Observation {
    pub concepts: HashMap<String, f64>,
    pub actual_score: f64,
}

#[derive(Deserialize)]
pub struct CalibrateRequest {
    pub axis: String,
    pub observations: Vec<Observation>,
    #[serde(default = "default_lambda")]
    pub lambda: f64,
}

fn default_lambda() -> f64 {
    1.0
}

#[derive(Serialize)]
pub struct CalibrateResponse {
    pub axis: String,
    pub weights: HashMap<String, f64>,
    pub bias: f64,
    pub r_squared: f64,
    pub observations: usize,
}

pub struct CbmStore {
    path: PathBuf,
    axes: RwLock<HashMap<String, AxisWeights>>,
}

impl CbmStore {
    pub fn load(path: PathBuf) -> Self {
        let axes = std::fs::read_to_string(&path)
            .ok()
            .and_then(|s| serde_json::from_str::<HashMap<String, AxisWeights>>(&s).ok())
            .unwrap_or_default();
        if axes.is_empty() {
            tracing::warn!(
                "cbm: no weights loaded from {} — using equal-weight fallback until calibration",
                path.display()
            );
        } else {
            tracing::info!("cbm: loaded weights for {} axes from {}", axes.len(), path.display());
        }
        CbmStore {
            path,
            axes: RwLock::new(axes),
        }
    }

    fn sigmoid_to_5(raw: f64) -> f64 {
        let s = 1.0 / (1.0 + (-raw).exp());
        round2(s * 5.0)
    }

    pub fn score(&self, req: &ScoreRequest) -> ScoreResponse {
        let guard = self.axes.read();
        let (aw, calibrated): (AxisWeights, bool) = match guard.get(&req.axis) {
            Some(a) => (a.clone(), true),
            None => (equal_weights(&req.concepts), false),
        };
        drop(guard);

        let mut raw = aw.bias;
        let mut contributions = HashMap::new();
        // Bottleneck = the positively-weighted concept with the most headroom:
        // maximise wᵢ × (1 − cᵢ).
        let mut best: Option<(String, f64, f64, f64)> = None; // (id, current, weight, potential)

        for (id, &c) in &req.concepts {
            let w = aw.weights.get(id).copied().unwrap_or(0.0);
            let contribution = w * c;
            raw += contribution;
            contributions.insert(id.clone(), round4(contribution));

            if w > 0.0 {
                let potential = w * (1.0 - c);
                if best.as_ref().map(|b| potential > b.3).unwrap_or(true) {
                    best = Some((id.clone(), c, w, potential));
                }
            }
        }

        let score = Self::sigmoid_to_5(raw);

        let bottleneck = best.map(|(id, current, weight, _)| {
            // Project: what would the score be if this concept reached 0.80?
            let delta = weight * (0.80 - current);
            let score_if_fixed = Self::sigmoid_to_5(raw + delta);
            Bottleneck {
                concept_id: id,
                current: round4(current),
                weight: round4(weight),
                score_if_fixed,
            }
        });

        ScoreResponse {
            axis: req.axis.clone(),
            score,
            weighted_contributions: contributions,
            bottleneck,
            calibrated,
        }
    }

    /// Ridge regression: solve min_w ‖Cw − y‖² + λ‖w‖² with a bias column.
    /// Writes the learned weights for `axis` back to the store and to disk.
    pub fn calibrate(&self, req: &CalibrateRequest) -> Result<CalibrateResponse, String> {
        let n = req.observations.len();
        if n < 3 {
            return Err(format!("need >= 3 observations to calibrate, got {n}"));
        }

        // Stable concept ordering: union of all keys across observations.
        let mut ids: Vec<String> = BTreeSet::from_iter(
            req.observations
                .iter()
                .flat_map(|o| o.concepts.keys().cloned()),
        )
        .into_iter()
        .collect();
        if ids.is_empty() {
            return Err("observations contain no concepts".into());
        }
        let k = ids.len();

        // Design matrix C: n × (k+1), last column is the bias (all ones).
        let mut c = DMatrix::<f64>::zeros(n, k + 1);
        let mut y = DVector::<f64>::zeros(n);
        for (row, obs) in req.observations.iter().enumerate() {
            for (col, id) in ids.iter().enumerate() {
                c[(row, col)] = obs.concepts.get(id).copied().unwrap_or(0.0);
            }
            c[(row, k)] = 1.0;
            // Map the 0–5 target into logit space so the linear head matches the
            // sigmoid×5 used at scoring time.
            y[row] = inverse_sigmoid_from_5(obs.actual_score);
        }

        // (CᵀC + λI) w = Cᵀ y  — do not regularise the bias term.
        let ct = c.transpose();
        let mut ctc = &ct * &c;
        for i in 0..k {
            ctc[(i, i)] += req.lambda;
        }
        let cty = &ct * &y;
        let solution = ctc
            .lu()
            .solve(&cty)
            .ok_or_else(|| "ridge system is singular".to_string())?;

        // R² in logit space (the space we actually fit).
        let y_mean = y.mean();
        let preds = &c * &solution;
        let ss_res: f64 = (0..n).map(|i| (y[i] - preds[i]).powi(2)).sum();
        let ss_tot: f64 = (0..n).map(|i| (y[i] - y_mean).powi(2)).sum();
        let r_squared = if ss_tot > 1e-12 {
            round4(1.0 - ss_res / ss_tot)
        } else {
            0.0
        };

        let mut weights = HashMap::new();
        for (col, id) in ids.drain(..).enumerate() {
            weights.insert(id, round4(solution[col]));
        }
        let bias = round4(solution[k]);

        let aw = AxisWeights {
            weights: weights.clone(),
            bias,
        };
        {
            let mut guard = self.axes.write();
            guard.insert(req.axis.clone(), aw);
            if let Err(e) = self.persist(&guard) {
                tracing::warn!("cbm: failed to persist weights: {e}");
            }
        }

        Ok(CalibrateResponse {
            axis: req.axis.clone(),
            weights,
            bias,
            r_squared,
            observations: n,
        })
    }

    fn persist(&self, axes: &HashMap<String, AxisWeights>) -> std::io::Result<()> {
        let json = serde_json::to_string_pretty(axes)?;
        // Best-effort atomic write.
        let tmp = self.path.with_extension("json.tmp");
        std::fs::write(&tmp, json)?;
        std::fs::rename(&tmp, &self.path)
    }
}

/// Equal-weight fallback over the provided concepts (weights sum to 1), with a
/// bias placing all-0.5 activations at the 2.5 midpoint.
fn equal_weights(concepts: &HashMap<String, f64>) -> AxisWeights {
    let k = concepts.len().max(1) as f64;
    let w = 1.0 / k;
    let weights = concepts.keys().map(|id| (id.clone(), w)).collect();
    AxisWeights {
        weights,
        bias: -0.5, // sigmoid(0) = 0.5 → score 2.5 when every concept is 0.5
    }
}

/// Map a 0–5 score to a logit, clamped away from the asymptotes.
fn inverse_sigmoid_from_5(score: f64) -> f64 {
    let p = (score / 5.0).clamp(1e-4, 1.0 - 1e-4);
    (p / (1.0 - p)).ln()
}

fn round2(x: f64) -> f64 {
    (x * 100.0).round() / 100.0
}
fn round4(x: f64) -> f64 {
    (x * 10_000.0).round() / 10_000.0
}

#[cfg(test)]
mod tests {
    use super::*;

    fn store() -> CbmStore {
        CbmStore {
            path: PathBuf::from("/tmp/cbm_test_weights.json"),
            axes: RwLock::new(HashMap::new()),
        }
    }

    #[test]
    fn equal_weight_midpoint_is_neutral() {
        let s = store();
        let mut concepts = HashMap::new();
        concepts.insert("a".into(), 0.5);
        concepts.insert("b".into(), 0.5);
        let resp = s.score(&ScoreRequest {
            axis: "market".into(),
            concepts,
        });
        assert!((resp.score - 2.5).abs() < 0.05, "got {}", resp.score);
        assert!(!resp.calibrated);
    }

    #[test]
    fn bottleneck_is_highest_headroom_concept() {
        let s = store();
        let mut concepts = HashMap::new();
        concepts.insert("strong".into(), 0.9);
        concepts.insert("weak".into(), 0.1);
        let resp = s.score(&ScoreRequest {
            axis: "x".into(),
            concepts,
        });
        let b = resp.bottleneck.unwrap();
        assert_eq!(b.concept_id, "weak");
        assert!(b.score_if_fixed > resp.score);
    }

    #[test]
    fn calibration_recovers_a_linear_relationship() {
        let s = store();
        // Construct data where score depends only on concept "a".
        let mut obs = Vec::new();
        for i in 0..20 {
            let a = (i as f64) / 19.0;
            let mut c = HashMap::new();
            c.insert("a".to_string(), a);
            c.insert("b".to_string(), 0.5);
            obs.push(Observation {
                concepts: c,
                actual_score: (a * 4.0 + 0.5).min(5.0),
            });
        }
        let resp = s
            .calibrate(&CalibrateRequest {
                axis: "market".into(),
                observations: obs,
                lambda: 0.01,
            })
            .unwrap();
        assert!(resp.r_squared > 0.8, "r2 = {}", resp.r_squared);
        // "a" should carry far more weight than "b".
        assert!(resp.weights["a"].abs() > resp.weights["b"].abs());
    }
}
