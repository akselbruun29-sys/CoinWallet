use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::plugin::{Builder as PluginBuilder, TauriPlugin};
use tauri::{Manager, RunEvent};
use url::Url;

struct ApiSidecar(Mutex<Option<Child>>);

fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..")
}

fn python_executable(root: &PathBuf) -> PathBuf {
    if cfg!(windows) {
        let scripts = root.join("venv").join("Scripts");
        let pythonw = scripts.join("pythonw.exe");
        if pythonw.exists() {
            pythonw
        } else {
            scripts.join("python.exe")
        }
    } else {
        root.join("venv").join("bin").join("python")
    }
}

fn configure_hidden_sidecar(cmd: &mut Command) {
    cmd.stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }
}

fn start_api_sidecar(root: &PathBuf) -> Option<Child> {
    let python = python_executable(root);
    if !python.exists() {
        log::warn!(
            "Python venv not found at {} - start the API manually or run setup first",
            python.display()
        );
        return None;
    }

    let mut cmd = Command::new(&python);
    cmd.current_dir(root)
        .env("STRICT_SECRETS", "true")
        .env(
            "COINWALLET_PRODUCTION",
            if cfg!(debug_assertions) {
                "false"
            } else {
                "true"
            },
        )
        .args([
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8002",
        ]);

    if cfg!(not(debug_assertions)) {
        configure_hidden_sidecar(&mut cmd);
    }

    match cmd.spawn()
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

fn allow_navigation(url: &Url) -> bool {
    match url.scheme() {
        "tauri" | "asset" | "data" | "blob" => true,
        "http" | "https" => url
            .host_str()
            .map(|host| {
                host == "localhost"
                    || host == "127.0.0.1"
                    || host.ends_with("blockstream.info")
                    || host.ends_with("xmrchain.net")
            })
            .unwrap_or(false),
        _ => false,
    }
}

fn navigation_guard_plugin<R: tauri::Runtime>() -> TauriPlugin<R> {
    PluginBuilder::new("navigation-guard")
        .on_navigation(|_webview, url| allow_navigation(url))
        .build()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let root = project_root();
    let sidecar_child = start_api_sidecar(&root);

    let app = tauri::Builder::default()
        .plugin(navigation_guard_plugin())
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
