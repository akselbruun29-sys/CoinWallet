use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};
use tauri::plugin::{Builder as PluginBuilder, TauriPlugin};
use tauri::{AppHandle, Manager, RunEvent};
use url::Url;

mod tor_sidecar;
use tor_sidecar::{apply_tor_env, start_tor_sidecar, stop_tor_sidecar, TorSidecar};

struct ApiSidecar(Mutex<Option<Child>>);

fn app_data_dir() -> PathBuf {
    if let Ok(custom) = std::env::var("COINWALLET_APP_DATA") {
        if !custom.trim().is_empty() {
            return PathBuf::from(custom);
        }
    }

    #[cfg(windows)]
    {
        if let Ok(local) = std::env::var("LOCALAPPDATA") {
            return PathBuf::from(local).join("CoinWallet");
        }
    }

    #[cfg(target_os = "macos")]
    {
        if let Ok(home) = std::env::var("HOME") {
            return PathBuf::from(home)
                .join("Library")
                .join("Application Support")
                .join("CoinWallet");
        }
    }

    if let Ok(home) = std::env::var("HOME") {
        return PathBuf::from(home).join(".coinwallet");
    }

    PathBuf::from(".coinwallet")
}

fn project_root() -> PathBuf {
    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent().map(PathBuf::from);
        for _ in 0..8 {
            let Some(current) = dir else {
                break;
            };
            let venv_marker = if cfg!(windows) {
                current.join("venv").join("Scripts").join("python.exe")
            } else {
                current.join("venv").join("bin").join("python")
            };
            if venv_marker.exists() && current.join("api").join("main.py").exists() {
                return current;
            }
            dir = current.parent().map(PathBuf::from);
        }
    }

    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..")
}

fn python_executable(root: &Path) -> PathBuf {
    if cfg!(windows) {
        root.join("venv").join("Scripts").join("python.exe")
    } else {
        root.join("venv").join("bin").join("python")
    }
}

fn bundled_sidecar_name() -> &'static str {
    #[cfg(all(windows, target_arch = "x86_64"))]
    {
        return "coinwallet-api-x86_64-pc-windows-msvc.exe";
    }
    #[cfg(all(windows, target_arch = "aarch64"))]
    {
        return "coinwallet-api-aarch64-pc-windows-msvc.exe";
    }
    #[cfg(all(target_os = "macos", target_arch = "aarch64"))]
    {
        return "coinwallet-api-aarch64-apple-darwin";
    }
    #[cfg(all(target_os = "macos", target_arch = "x86_64"))]
    {
        return "coinwallet-api-x86_64-apple-darwin";
    }
    #[cfg(all(target_os = "linux", target_arch = "x86_64"))]
    {
        return "coinwallet-api-x86_64-unknown-linux-gnu";
    }
    #[allow(unreachable_code)]
    {
        "coinwallet-api"
    }
}

fn resolve_bundled_sidecar(app: &AppHandle) -> Option<PathBuf> {
    let name = bundled_sidecar_name();

    if let Ok(exe) = std::env::current_exe() {
        if let Some(parent) = exe.parent() {
            let candidate = parent.join(name);
            if candidate.exists() {
                return Some(candidate);
            }
        }
    }

    if let Ok(resource_dir) = app.path().resource_dir() {
        let candidate = resource_dir.join(name);
        if candidate.exists() {
            return Some(candidate);
        }
    }

    None
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

fn apply_sidecar_env(cmd: &mut Command, app_data: &Path, tor_active: bool) {
    cmd.env("COINWALLET_APP_DATA", app_data);
    cmd.env("COINWALLET_API_HOST", "127.0.0.1");
    cmd.env("COINWALLET_API_PORT", "8002");

    if cfg!(debug_assertions) {
        cmd.env("COINWALLET_PRODUCTION", "false");
        cmd.env("STRICT_SECRETS", "false");
    } else {
        cmd.env("COINWALLET_PRODUCTION", "true");
        cmd.env("STRICT_SECRETS", "true");
        cmd.env("COINWALLET_SERVE_UI", "true");
    }

    if tor_active {
        apply_tor_env(cmd);
    }

    if let Ok(remote) = std::env::var("COINWALLET_REMOTE_SERVICES_URL") {
        if !remote.trim().is_empty() {
            cmd.env("COINWALLET_REMOTE_SERVICES_URL", remote.trim());
        }
    } else if cfg!(not(debug_assertions)) {
        cmd.env(
            "COINWALLET_REMOTE_SERVICES_URL",
            "https://coinwallet.pages.dev",
        );
    }
}

fn start_dev_python_sidecar(root: &Path, app_data: &Path, tor_active: bool) -> Option<Child> {
    let python = python_executable(root);
    if !python.exists() {
        log::warn!(
            "Python venv not found at {} — start the API manually or run setup first",
            python.display()
        );
        return None;
    }

    let mut cmd = Command::new(&python);
    cmd.current_dir(root)
        .args([
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8002",
        ]);
    apply_sidecar_env(&mut cmd, app_data, tor_active);

    match cmd.spawn() {
        Ok(child) => {
            log::info!("Started dev wallet API on http://127.0.0.1:8002");
            Some(child)
        }
        Err(err) => {
            log::error!("Failed to start dev wallet API: {err}");
            None
        }
    }
}

fn start_bundled_sidecar(binary: &Path, app_data: &Path, tor_active: bool) -> Option<Child> {
    let mut cmd = Command::new(binary);
    apply_sidecar_env(&mut cmd, app_data, tor_active);
    configure_hidden_sidecar(&mut cmd);

    match cmd.spawn() {
        Ok(child) => {
            log::info!("Started bundled wallet API on http://127.0.0.1:8002");
            Some(child)
        }
        Err(err) => {
            log::error!("Failed to start bundled wallet API: {err}");
            None
        }
    }
}

fn start_api_sidecar(app: &AppHandle, app_data: &Path, tor_active: bool) -> Option<Child> {
    let _ = std::fs::create_dir_all(app_data);

    if cfg!(debug_assertions) {
        return start_dev_python_sidecar(&project_root(), app_data, tor_active);
    }

    if let Some(binary) = resolve_bundled_sidecar(app) {
        return start_bundled_sidecar(&binary, app_data, tor_active);
    }

    log::warn!("Bundled API sidecar not found — falling back to dev venv layout");
    start_dev_python_sidecar(&project_root(), app_data, tor_active)
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
                    || host.ends_with(".workers.dev")
                    || host == "coinwallet.pages.dev"
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

fn wait_for_api_port(host: &str, port: u16, timeout: Duration) -> bool {
    let addr: SocketAddr = format!("{host}:{port}")
        .parse()
        .unwrap_or_else(|_| panic!("invalid API address {host}:{port}"));
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if TcpStream::connect_timeout(&addr, Duration::from_millis(250)).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    false
}

fn show_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_data = app_data_dir();

    let app = tauri::Builder::default()
        .plugin(navigation_guard_plugin())
        .manage(ApiSidecar(Mutex::new(None)))
        .manage(TorSidecar(Mutex::new(None)))
        .setup(move |app| {
            app.handle().plugin(
                tauri_plugin_log::Builder::default()
                    .level(log::LevelFilter::Info)
                    .build(),
            )?;

            let tor_child = start_tor_sidecar(app.handle(), &app_data);
            let tor_active = tor_child.is_some();
            if let Some(state) = app.try_state::<TorSidecar>() {
                if let Ok(mut guard) = state.0.lock() {
                    *guard = tor_child;
                }
            }

            let child = start_api_sidecar(app.handle(), &app_data, tor_active);
            if let Some(state) = app.try_state::<ApiSidecar>() {
                if let Ok(mut guard) = state.0.lock() {
                    *guard = child;
                }
            }

            if cfg!(debug_assertions) {
                show_main_window(app.handle());
            } else {
                let ready = wait_for_api_port("127.0.0.1", 8002, Duration::from_secs(45));
                if !ready {
                    log::warn!("Timed out waiting for wallet API on :8002 — showing window anyway");
                }
                show_main_window(app.handle());
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
            if let Some(tor) = app_handle.try_state::<TorSidecar>() {
                stop_tor_sidecar(tor.inner());
            }
        }
    });
}
