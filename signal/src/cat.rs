//! Computerized Adaptive Testing — EAP ability estimation.
//!
//! Implements the Bayesian Expected A Posteriori update of Bock & Mislevy (1982)
//! over the 2-parameter logistic model (Lord, 1977), with the graded
//! soft-Bernoulli extension `P^c·(1−P)^(1−c)` so a multi-option item can carry a
//! partial response credit `c ∈ [0, 1]`.
//!
//! This mirrors the orchestrator's pure-Python `app/cat/irt.py`, which is the
//! authoritative engine for the live intake. This endpoint is an optional
//! offload / parity surface (consistent with the rest of `moufida-signal` being
//! best-effort) and a convenient place to recompute the 81-point posterior for
//! visualization or batch re-scoring.

use serde::{Deserialize, Serialize};

const GRID_MIN: f64 = -4.0;
const GRID_MAX: f64 = 4.0;
const GRID_N: usize = 81;
const GRID_STEP: f64 = (GRID_MAX - GRID_MIN) / (GRID_N as f64 - 1.0);
const EPS: f64 = 1e-9;

/// θ-boundaries between the 6 maturity stages (must match item_bank.json meta).
const STAGE_BOUNDARIES: [f64; 5] = [-1.75, -0.75, 0.25, 1.25, 2.25];

#[derive(Deserialize)]
pub struct ItemResponse {
    pub a: f64,
    pub b: f64,
    /// Graded response credit in [0, 1] (1.0 == strong/"correct").
    pub credit: f64,
}

#[derive(Deserialize)]
pub struct EapRequest {
    pub responses: Vec<ItemResponse>,
    /// Include the full 81-point posterior in the response (default false).
    #[serde(default)]
    pub include_posterior: bool,
}

#[derive(Serialize)]
pub struct EapResponse {
    pub theta_hat: f64,
    pub se: f64,
    pub stage: u8,
    /// 6 stage-bucket probabilities (Ideation … Growth).
    pub stage_posterior: Vec<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub posterior: Option<Vec<f64>>,
}

fn theta_at(k: usize) -> f64 {
    GRID_MIN + k as f64 * GRID_STEP
}

/// Numerically stable logistic.
fn sigmoid(x: f64) -> f64 {
    if x >= 0.0 {
        1.0 / (1.0 + (-x).exp())
    } else {
        let z = x.exp();
        z / (1.0 + z)
    }
}

fn theta_to_stage(theta: f64) -> u8 {
    for (i, &boundary) in STAGE_BOUNDARIES.iter().enumerate() {
        if theta < boundary {
            return (i + 1) as u8;
        }
    }
    (STAGE_BOUNDARIES.len() + 1) as u8
}

pub fn eap(req: &EapRequest) -> EapResponse {
    // log-weight per grid point = log N(0,1) prior + Σ graded log-likelihood.
    let mut log_w = [0.0_f64; GRID_N];
    let log_2pi = (2.0 * std::f64::consts::PI).ln();
    for (k, lw) in log_w.iter_mut().enumerate() {
        let theta = theta_at(k);
        *lw = -0.5 * theta * theta - 0.5 * log_2pi;
        for r in &req.responses {
            let c = r.credit.clamp(0.0, 1.0);
            let p = sigmoid(r.a * (theta - r.b)).clamp(EPS, 1.0 - EPS);
            *lw += c * p.ln() + (1.0 - c) * (1.0 - p).ln();
        }
    }

    // Log-sum-exp normalization.
    let max_lw = log_w.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let sum_exp: f64 = log_w.iter().map(|&x| (x - max_lw).exp()).sum();
    let log_z = max_lw + sum_exp.ln();
    let weights: Vec<f64> = log_w.iter().map(|&lw| (lw - log_z).exp()).collect();

    // EAP mean + SE.
    let theta_hat: f64 = (0..GRID_N).map(|k| theta_at(k) * weights[k]).sum();
    let variance: f64 = (0..GRID_N)
        .map(|k| (theta_at(k) - theta_hat).powi(2) * weights[k])
        .sum();
    let se = variance.max(0.0).sqrt();

    // Collapse θ-posterior into 6 stage buckets.
    let mut stage_posterior = vec![0.0_f64; STAGE_BOUNDARIES.len() + 1];
    for (k, &w) in weights.iter().enumerate() {
        let s = theta_to_stage(theta_at(k)) as usize - 1;
        stage_posterior[s] += w;
    }

    EapResponse {
        theta_hat: round3(theta_hat),
        se: round3(se),
        stage: theta_to_stage(theta_hat),
        stage_posterior: stage_posterior.iter().map(|&p| round4(p)).collect(),
        posterior: if req.include_posterior {
            Some(weights.iter().map(|&w| round4(w)).collect())
        } else {
            None
        },
    }
}

fn round3(x: f64) -> f64 {
    (x * 1000.0).round() / 1000.0
}
fn round4(x: f64) -> f64 {
    (x * 10_000.0).round() / 10_000.0
}

#[cfg(test)]
mod tests {
    use super::*;

    fn resp(a: f64, b: f64, credit: f64) -> ItemResponse {
        ItemResponse { a, b, credit }
    }

    #[test]
    fn empty_history_returns_prior_mean() {
        let out = eap(&EapRequest {
            responses: vec![],
            include_posterior: false,
        });
        // Posterior == prior N(0,1): mean ~0, SE ~1, mid stage.
        assert!(out.theta_hat.abs() < 0.01, "theta = {}", out.theta_hat);
        assert!((out.se - 1.0).abs() < 0.05, "se = {}", out.se);
        assert_eq!(out.stage, 3);
    }

    #[test]
    fn strong_high_difficulty_answers_push_theta_up() {
        // Founder answers strongly (credit 1.0) on hard items (high b).
        let out = eap(&EapRequest {
            responses: vec![
                resp(2.5, 1.5, 1.0),
                resp(2.5, 1.8, 1.0),
                resp(2.7, 2.2, 1.0),
            ],
            include_posterior: false,
        });
        assert!(out.theta_hat > 1.0, "theta = {}", out.theta_hat);
        assert!(out.stage >= 4, "stage = {}", out.stage);
        // SE shrinks below the prior.
        assert!(out.se < 0.9, "se = {}", out.se);
    }

    #[test]
    fn weak_answers_push_theta_down() {
        let out = eap(&EapRequest {
            responses: vec![
                resp(2.5, -1.4, 0.0),
                resp(2.5, -0.8, 0.0),
                resp(2.4, -0.5, 0.0),
            ],
            include_posterior: false,
        });
        assert!(out.theta_hat < -0.5, "theta = {}", out.theta_hat);
        assert!(out.stage <= 2, "stage = {}", out.stage);
    }

    #[test]
    fn stage_posterior_sums_to_one() {
        let out = eap(&EapRequest {
            responses: vec![resp(2.0, 0.0, 1.0), resp(1.8, 0.5, 0.5)],
            include_posterior: true,
        });
        let total: f64 = out.stage_posterior.iter().sum();
        assert!((total - 1.0).abs() < 1e-3, "sum = {}", total);
        assert_eq!(out.posterior.unwrap().len(), GRID_N);
    }

    #[test]
    fn graded_credit_degrades_to_binary() {
        // credit 1.0 == strong positive on an easy item keeps theta near/above prior.
        let high = eap(&EapRequest {
            responses: vec![resp(2.0, 0.0, 1.0)],
            include_posterior: false,
        });
        let low = eap(&EapRequest {
            responses: vec![resp(2.0, 0.0, 0.0)],
            include_posterior: false,
        });
        assert!(high.theta_hat > low.theta_hat);
    }
}
