//! moufida-signal — interpretability microservice (port 8010).
//!
//! Three research capabilities behind one HTTP surface:
//!   • Concept Bottleneck scoring  — POST /cbm/score, POST /cbm/calibrate
//!   • Contrastive Axis Directions — POST /probe/project, POST /probe/reload
//!   • Adaptive Testing (IRT/EAP)  — POST /cat/eap
//!
//! All are best-effort from the callers' perspective: the orchestrator and RAG
//! service degrade gracefully if this service is down or its assets are missing
//! (the adaptive intake runs its own authoritative pure-Python IRT engine).

mod cat;
mod cbm;
mod npy;
mod probe;

use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use serde_json::json;

use cat::EapRequest;
use cbm::{CalibrateRequest, CbmStore, ScoreRequest};
use probe::{AxisProbe, ProbeData, ProjectRequest};

#[derive(Clone)]
struct AppState {
    cbm: Arc<CbmStore>,
    probe: Arc<AxisProbe>,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "moufida_signal=info,tower_http=warn".into()),
        )
        .init();

    let assets = std::env::var("SIGNAL_ASSETS_DIR").unwrap_or_else(|_| "assets".to_string());
    let assets = PathBuf::from(assets);

    let cbm = Arc::new(CbmStore::load(assets.join("cbm_weights.json")));
    let probe = Arc::new(AxisProbe::new(&assets));

    let state = AppState { cbm, probe };

    let app = Router::new()
        .route("/health", get(health))
        .route("/cbm/score", post(cbm_score))
        .route("/cbm/calibrate", post(cbm_calibrate))
        .route("/cat/eap", post(cat_eap))
        .route("/probe/project", post(probe_project))
        .route("/probe/install", post(probe_install))
        .route("/probe/reload", post(probe_reload))
        .with_state(state);

    let port: u16 = std::env::var("SIGNAL_PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8010);
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    tracing::info!("moufida-signal listening on {addr}");

    let listener = tokio::net::TcpListener::bind(addr).await.expect("bind");
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await
        .expect("serve");
}

async fn shutdown_signal() {
    let _ = tokio::signal::ctrl_c().await;
    tracing::info!("shutdown signal received");
}

async fn health(State(s): State<AppState>) -> impl IntoResponse {
    Json(json!({
        "status": "ok",
        "service": "moufida-signal",
        "version": env!("CARGO_PKG_VERSION"),
        "probe_ready": s.probe.is_ready(),
        "probe_axes": s.probe.axis_count(),
    }))
}

async fn cbm_score(State(s): State<AppState>, Json(req): Json<ScoreRequest>) -> impl IntoResponse {
    Json(s.cbm.score(&req)).into_response()
}

async fn cbm_calibrate(
    State(s): State<AppState>,
    Json(req): Json<CalibrateRequest>,
) -> impl IntoResponse {
    match s.cbm.calibrate(&req) {
        Ok(resp) => Json(resp).into_response(),
        Err(e) => (StatusCode::BAD_REQUEST, Json(json!({ "error": e }))).into_response(),
    }
}

async fn cat_eap(Json(req): Json<EapRequest>) -> impl IntoResponse {
    Json(cat::eap(&req))
}

async fn probe_project(
    State(s): State<AppState>,
    Json(req): Json<ProjectRequest>,
) -> impl IntoResponse {
    match s.probe.project(&req.embedding, req.top_k) {
        Some(resp) => Json(resp).into_response(),
        None => (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({ "error": "probe directions not loaded or dimension mismatch" })),
        )
            .into_response(),
    }
}

async fn probe_install(State(s): State<AppState>, Json(data): Json<ProbeData>) -> impl IntoResponse {
    match s.probe.install(data) {
        Ok(n) => Json(json!({ "ok": true, "axes": n })).into_response(),
        Err(e) => (
            StatusCode::BAD_REQUEST,
            Json(json!({ "ok": false, "error": e.to_string() })),
        )
            .into_response(),
    }
}

async fn probe_reload(State(s): State<AppState>) -> impl IntoResponse {
    match s.probe.load() {
        Ok(n) => Json(json!({ "ok": true, "axes": n })).into_response(),
        Err(e) => (
            StatusCode::BAD_REQUEST,
            Json(json!({ "ok": false, "error": e.to_string() })),
        )
            .into_response(),
    }
}
