//! Minimal NumPy `.npy` reader — just enough to load a 2-D little-endian
//! float32 array saved by `numpy.save(...)` in C (row-major) order.
//!
//! Format reference: <https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html>
//! The probe matrix is saved by `scripts/compute_axis_directions.py` as
//! `np.save(path, matrix.astype(np.float32))` — shape `(n_axes, embed_dim)`.

use anyhow::{anyhow, bail, Result};

pub struct Npy {
    pub shape: Vec<usize>,
    pub data: Vec<f32>,
}

impl Npy {
    /// Parse raw `.npy` bytes into shape + flat f32 data.
    pub fn parse(bytes: &[u8]) -> Result<Npy> {
        if bytes.len() < 10 || &bytes[0..6] != b"\x93NUMPY" {
            bail!("not a .npy file (bad magic)");
        }
        let major = bytes[6];

        // Header-length field width depends on the format version.
        let (header_len, header_start) = if major == 1 {
            let len = u16::from_le_bytes([bytes[8], bytes[9]]) as usize;
            (len, 10)
        } else {
            // v2.0+ uses a 4-byte little-endian length.
            let len = u32::from_le_bytes([bytes[8], bytes[9], bytes[10], bytes[11]]) as usize;
            (len, 12)
        };

        let header_end = header_start + header_len;
        if header_end > bytes.len() {
            bail!("truncated .npy header");
        }
        let header = std::str::from_utf8(&bytes[header_start..header_end])
            .map_err(|e| anyhow!("non-utf8 header: {e}"))?;

        if !header.contains("'<f4'") && !header.contains("\"<f4\"") {
            bail!("unsupported dtype (expected little-endian float32 '<f4'): {header}");
        }
        if header.contains("'fortran_order': True") {
            bail!("fortran-ordered arrays are not supported; save with C order");
        }

        let shape = parse_shape(header)?;
        let expected: usize = shape.iter().product();

        let raw = &bytes[header_end..];
        if raw.len() < expected * 4 {
            bail!(
                "data shorter than shape implies: have {} bytes, need {}",
                raw.len(),
                expected * 4
            );
        }

        let mut data = Vec::with_capacity(expected);
        for chunk in raw[..expected * 4].chunks_exact(4) {
            data.push(f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]));
        }

        Ok(Npy { shape, data })
    }
}

/// Extract the `shape` tuple from the header dict, e.g. `'shape': (9, 1024), `.
fn parse_shape(header: &str) -> Result<Vec<usize>> {
    let key = "'shape':";
    let idx = header
        .find(key)
        .ok_or_else(|| anyhow!("header missing 'shape'"))?;
    let after = &header[idx + key.len()..];
    let open = after.find('(').ok_or_else(|| anyhow!("malformed shape"))?;
    let close = after.find(')').ok_or_else(|| anyhow!("malformed shape"))?;
    let inner = &after[open + 1..close];

    let mut dims = Vec::new();
    for part in inner.split(',') {
        let p = part.trim();
        if p.is_empty() {
            continue;
        }
        dims.push(p.parse::<usize>().map_err(|e| anyhow!("bad dim '{p}': {e}"))?);
    }
    if dims.is_empty() {
        bail!("empty shape");
    }
    Ok(dims)
}
