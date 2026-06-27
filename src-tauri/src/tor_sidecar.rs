use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::AppHandle;
use tauri::Manager;

pub struct TorSidecar(pub Mutex<Option<Child>>);

pub fn bundled_tor_sidecar_name() -> &'static str {
    #[cfg(all(windows, target_arch = "x86_64"))]
    {
        return "tor-x86_64-pc-windows-msvc.exe";
    }
    #[cfg(all(windows, target_arch = "aarch64"))]
    {
        return "tor-aarch64-pc-windows-msvc.exe";
    }
    #[cfg(all(target_os = "macos", target_arch = "aarch64"))]
    {
        return "tor-aarch64-apple-darwin";
    }
    #[cfg(all(target_os = "macos", target_arch = "x86_64"))]
    {
        return "tor-x86_64-apple-darwin";
    }
    #[cfg(all(target_os = "linux", target_arch = "x86_64"))]
    {
        return "tor-x86_64-unknown-linux-gnu";
    }
    #[allow(unreachable_code)]
    {
        "tor"
    }
}

fn copy_dir_all(src: &Path, dst: &Path) -> io::Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let file_type = entry.file_type()?;
        let from = entry.path();
        let to = dst.join(entry.file_name());
        if file_type.is_dir() {
            copy_dir_all(&from, &to)?;
        } else {
            fs::copy(&from, &to)?;
        }
    }
    Ok(())
}

fn resolve_bundled_tor_sidecar(app: &AppHandle) -> Option<PathBuf> {
    let name = bundled_tor_sidecar_name();

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

fn tor_executable_name() -> &'static str {
    if cfg!(windows) {
        "tor.exe"
    } else {
        "tor"
    }
}

pub fn materialize_tor_bundle(app: &AppHandle, app_data: &Path) -> Option<PathBuf> {
    let tor_home = app_data.join("tor");
    let tor_exe = tor_home.join(tor_executable_name());
    if tor_exe.exists() {
        return Some(tor_exe);
    }

    if let Ok(resource_dir) = app.path().resource_dir() {
        let bundle = resource_dir.join("tor");
        let bundle_exe = bundle.join(tor_executable_name());
        if bundle_exe.exists() {
            let _ = fs::remove_dir_all(&tor_home);
            if copy_dir_all(&bundle, &tor_home).is_ok() && tor_exe.exists() {
                return Some(tor_exe);
            }
        }
    }

    resolve_bundled_tor_sidecar(app)
}

pub fn write_torrc(app_data: &Path) -> io::Result<PathBuf> {
    let tor_dir = app_data.join("tor");
    fs::create_dir_all(tor_dir.join("data"))?;
    let torrc = tor_dir.join("torrc");
    let data_dir = tor_dir.join("data");
    let log_file = tor_dir.join("tor.log");
    let content = format!(
        "DataDirectory {}\nSocksPort 127.0.0.1:9050\nAvoidDiskWrites 1\nLog notice file {}\n",
        data_dir.display(),
        log_file.display()
    );
    fs::write(&torrc, content)?;
    Ok(torrc)
}

fn configure_hidden(cmd: &mut Command) {
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

pub fn start_tor_sidecar(app: &AppHandle, app_data: &Path) -> Option<Child> {
    let tor_exe = materialize_tor_bundle(app, app_data)?;
    let torrc = write_torrc(app_data).ok()?;
    let tor_dir = app_data.join("tor");

    let mut cmd = Command::new(&tor_exe);
    cmd.arg("-f").arg(&torrc).current_dir(&tor_dir);
    configure_hidden(&mut cmd);

    match cmd.spawn() {
        Ok(child) => {
            log::info!("Started bundled Tor SOCKS proxy on 127.0.0.1:9050");
            Some(child)
        }
        Err(err) => {
            log::error!("Failed to start Tor: {err}");
            None
        }
    }
}

pub fn stop_tor_sidecar(sidecar: &TorSidecar) {
    if let Ok(mut guard) = sidecar.0.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            log::info!("Stopped Tor sidecar");
        }
    }
}

pub fn apply_tor_env(cmd: &mut Command) {
    cmd.env("COINWALLET_TOR_MANAGED", "true");
    cmd.env("TOR_ENABLED", "true");
    cmd.env("HTTP_PROXY", "socks5h://127.0.0.1:9050");
    cmd.env("HTTPS_PROXY", "socks5h://127.0.0.1:9050");
    cmd.env("TOR_SOCKS_PROXY", "socks5h://127.0.0.1:9050");
}
