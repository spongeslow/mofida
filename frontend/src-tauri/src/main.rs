// Moufida desktop shell — Phase 5: companion window + voice pipeline + tray
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Emitter, Manager, WebviewUrl, WebviewWindowBuilder,
};

fn get_or_create_main_window(app: &tauri::AppHandle) -> tauri::WebviewWindow {
    if let Some(w) = app.get_webview_window("main") {
        return w;
    }
    WebviewWindowBuilder::new(app, "main", WebviewUrl::App("index.html".into()))
        .title("Moufida")
        .inner_size(960.0, 640.0)
        .build()
        .expect("failed to create main window")
}

// ── Commands ──────────────────────────────────────────────────────

#[tauri::command]
async fn show_main_window(app: tauri::AppHandle) -> Result<(), String> {
    let w = get_or_create_main_window(&app);
    w.show().map_err(|e| e.to_string())?;
    w.set_focus().map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn toggle_main_window(app: tauri::AppHandle) -> Result<(), String> {
    let w = get_or_create_main_window(&app);
    if w.is_visible().map_err(|e| e.to_string())? {
        w.hide().map_err(|e| e.to_string())?;
    } else {
        w.show().map_err(|e| e.to_string())?;
        w.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
async fn set_companion_visible(app: tauri::AppHandle, visible: bool) -> Result<(), String> {
    if let Some(w) = app.get_webview_window("companion") {
        if visible {
            w.show().map_err(|e| e.to_string())?;
        } else {
            w.hide().map_err(|e| e.to_string())?;
        }
    }
    Ok(())
}

#[tauri::command]
async fn transcribe(audio_b64: String) -> Result<String, String> {
    use std::io::Write;
    use base64::Engine as _;

    let audio_bytes = base64::engine::general_purpose::STANDARD
        .decode(&audio_b64)
        .map_err(|e| e.to_string())?;

    let tmp = std::env::temp_dir().join("moufida_audio.webm");
    let mut f = std::fs::File::create(&tmp).map_err(|e| e.to_string())?;
    f.write_all(&audio_bytes).map_err(|e| e.to_string())?;
    drop(f);

    let tmp_str = tmp.to_string_lossy().to_string();
    let binary = ["whisper-cli", "whisper", "whispercpp"]
        .iter()
        .find(|b| which_exists(b))
        .copied()
        .unwrap_or("whisper-cli");

    let models_dir = std::env::current_dir().unwrap_or_default().join("models");
    let model_str  = models_dir.join("whisper.bin").to_string_lossy().to_string();

    let out = Command::new(binary)
        .args(["-m", &model_str, "-l", "auto", "-f", &tmp_str, "--no-timestamps", "-otxt"])
        .output()
        .map_err(|e| format!("whisper not found: {e}"))?;
    let _ = std::fs::remove_file(&tmp);

    if !out.status.success() {
        return Err(String::from_utf8_lossy(&out.stderr).to_string());
    }
    Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

#[tauri::command]
async fn speak(text: String, lang: String) -> Result<(), String> {
    let models_dir = std::env::current_dir().unwrap_or_default().join("models");
    if lang == "fr" {
        let model = models_dir.join("piper-fr.onnx").to_string_lossy().to_string();
        let script = format!(
            "echo '{}' | piper --model '{}' --output_raw | aplay -r 22050 -f S16_LE -c 1 -q",
            text.replace('\'', "'\\''"), model
        );
        Command::new("sh").args(["-c", &script]).spawn().map_err(|e| e.to_string())?;
    } else {
        let model = models_dir.join("kokoro/model_quantized.onnx").to_string_lossy().to_string();
        let voice = models_dir.join("kokoro/voices/af_heart.bin").to_string_lossy().to_string();
        let script = format!(
            "kokoro --model '{}' --voice '{}' --text '{}' | aplay -q",
            model, voice, text.replace('\'', "'\\''")
        );
        Command::new("sh").args(["-c", &script]).spawn().map_err(|e| e.to_string())?;
    }
    Ok(())
}

/// A file dropped onto the companion window, read off disk and base64-encoded so
/// the webview can rebuild a `File` and POST it to the ingestion endpoint.
#[derive(serde::Serialize)]
struct DroppedFile {
    name: String,
    mime: String,
    bytes_b64: String,
}

const MAX_DROP_BYTES: u64 = 25 * 1024 * 1024; // 25 MB

#[tauri::command]
async fn read_dropped_file(path: String) -> Result<DroppedFile, String> {
    use base64::Engine as _;

    let p = std::path::Path::new(&path);
    let ext = p
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| e.to_ascii_lowercase())
        .unwrap_or_default();

    let mime = match ext.as_str() {
        "pdf"             => "application/pdf",
        "txt"             => "text/plain",
        "md" | "markdown" => "text/markdown",
        "csv"             => "text/csv",
        _ => return Err(format!("unsupported_type:{ext}")),
    };

    let meta = std::fs::metadata(p).map_err(|e| format!("read_failed:{e}"))?;
    if meta.len() > MAX_DROP_BYTES {
        return Err("too_large".into());
    }

    let bytes = std::fs::read(p).map_err(|e| format!("read_failed:{e}"))?;
    let name = p
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("upload")
        .to_string();

    Ok(DroppedFile {
        name,
        mime: mime.to_string(),
        bytes_b64: base64::engine::general_purpose::STANDARD.encode(&bytes),
    })
}

#[tauri::command]
async fn open_url(url: String) -> Result<(), String> {
    #[cfg(target_os = "linux")]
    Command::new("xdg-open").arg(&url).spawn().map_err(|e| e.to_string())?;
    #[cfg(target_os = "macos")]
    Command::new("open").arg(&url).spawn().map_err(|e| e.to_string())?;
    #[cfg(target_os = "windows")]
    Command::new("cmd").args(["/c", "start", "", &url]).spawn().map_err(|e| e.to_string())?;
    Ok(())
}

fn which_exists(name: &str) -> bool {
    Command::new("which").arg(name).output().map(|o| o.status.success()).unwrap_or(false)
}

// ── Entry point ───────────────────────────────────────────────────

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            show_main_window,
            toggle_main_window,
            set_companion_visible,
            transcribe,
            speak,
            open_url,
            read_dropped_file,
        ])
        .setup(|app| {
            // ── Tray menu ──────────────────────────────────────────
            let new_project = MenuItem::with_id(app, "new", "Nouveau projet", true, None::<&str>)?;
            let diagnose    = MenuItem::with_id(app, "diagnose", "Diagnostiquer un projet existant", true, None::<&str>)?;
            let settings    = MenuItem::with_id(app, "settings", "Paramètres", true, None::<&str>)?;
            let quit        = MenuItem::with_id(app, "quit", "Quitter", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&new_project, &diagnose, &settings, &quit])?;

            TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .tooltip("Moufida")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "new" => {
                        let w = get_or_create_main_window(app);
                        w.show().unwrap_or(()); w.set_focus().unwrap_or(());
                        let _ = w.emit("start_new", ());
                    }
                    "diagnose" => {
                        let w = get_or_create_main_window(app);
                        w.show().unwrap_or(()); w.set_focus().unwrap_or(());
                        let _ = w.emit("start_diagnose", ());
                    }
                    "settings" => {
                        let w = get_or_create_main_window(app);
                        w.show().unwrap_or(()); w.set_focus().unwrap_or(());
                    }
                    "quit" => app.exit(0),
                    _ => {}
                })
                .build(app)?;

            // ── Companion window ───────────────────────────────────
            let (comp_w, comp_h) = (110.0_f64, 200.0_f64);

            // Position bottom-right, above the taskbar (heuristic: -48 logical px)
            let (comp_x, comp_y) = if let Ok(Some(mon)) = app.primary_monitor() {
                let sf = mon.scale_factor();
                let sw = mon.size().width  as f64 / sf;
                let sh = mon.size().height as f64 / sf;
                (sw - comp_w - 24.0, sh - comp_h - 48.0)
            } else {
                (1790.0, 832.0)
            };

            WebviewWindowBuilder::new(
                app,
                "companion",
                WebviewUrl::App("companion.html".into()),
            )
            .title("")
            .inner_size(comp_w, comp_h)
            .position(comp_x, comp_y)
            .transparent(true)
            .decorations(false)
            .always_on_top(true)
            .skip_taskbar(true)
            .resizable(false)
            .build()?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Moufida");
}
