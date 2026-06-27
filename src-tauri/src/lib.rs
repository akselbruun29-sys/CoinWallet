use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::{Manager, RunEvent};

struct ApiSidecar(Mutex<Option<Child>>);

fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..")
}

fn python_executable(root: &PathBuf) -> PathBuf {
    if cfg!(windows) {
        root.join("venv").join("Scripts").join("python.exe")
    } else {
        root.join("venv").join("bin").join("python")
    }
}

fn start_api_sidecar(root: &PathBuf) -> Option<Child> {
    let python = python_executable(root);
    if !python.exists() {
        log::warn!(
            "Python venv not found at {} — start the API manually or run setup first",
            python.display()
        );
        return None;
    }

    match Command::new(&python)
        .current_dir(root)
        .env("STRICT_SECRETS", "true")
        .args([
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8002",
        ])
        .spawn()
    {
        Ok(child) => {
            log::info!("Started local wallet API on http://127.0.0.1:8002");
            Some(child)
        }
        Err(err) => {
            log::error!("Failed to start wallet API sidecar: {err}");
            None
        }
    }
}

fn stop_api_sidecar(sidecar: &ApiSidecar) {
    if let Ok(mut guard) = sidecar.0.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            log::info!("Stopped local wallet API sidecar");
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let root = project_root();
    let sidecar_child = start_api_sidecar(&root);

    let app = tauri::Builder::default()
        .manage(ApiSidecar(Mutex::new(sidecar_child)))
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application");

    app.run(|app_handle, event| {
        if matches!(event, RunEvent::Exit) {
            if let Some(sidecar) = app_handle.try_state::<ApiSidecar>() {
                stop_api_sidecar(sidecar.inner());
            }
        }
    });
}
