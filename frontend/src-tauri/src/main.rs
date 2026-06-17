// Moufida desktop shell. Phase 0 scaffold: builds a system-tray icon with the
// context menu (New project / Diagnose existing / Settings / Quit) wired to
// empty handlers. Window management, tray pulse animation, and the voice state
// machine are added in Phase 4.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
    Manager,
};

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let new_project = MenuItem::with_id(app, "new", "Nouveau projet", true, None::<&str>)?;
            let diagnose = MenuItem::with_id(app, "diagnose", "Diagnostiquer un projet existant", true, None::<&str>)?;
            let settings = MenuItem::with_id(app, "settings", "Paramètres", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quitter", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&new_project, &diagnose, &settings, &quit])?;

            TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .tooltip("Moufida")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "new" => { /* TODO Phase 4: start STATE_NEW flow */ }
                    "diagnose" => { /* TODO Phase 4: start STATE_EXISTING flow */ }
                    "settings" => { /* TODO Phase 4: open settings window */ }
                    "quit" => app.exit(0),
                    _ => {}
                })
                .build(app)?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Moufida");
}
