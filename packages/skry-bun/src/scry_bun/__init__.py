import os
from pathlib import Path
from urllib.request import urlretrieve
import zipfile


def get_os_name() -> str:
    return os.name


def get_os_platform() -> str:
    return os.sys.platform


def install_bun() -> None:
    if find_bun():
        return

    download_bun()


def find_bun() -> str | None:
    path = Path.cwd() / "bin" / "bun"
    match get_os_platform():
        case "linux" | "darwin":
            exec = path / "bun"
        case "win32":
            exec = path / "bun.exe"
    if exec.exists():
        return str(exec)
    return None


BUN_RESOURCES = {
    "darwin": "https://github.com/oven-sh/bun/releases/latest/download/bun-darwin-aarch64.zip",
    "linux": "",
    "win32": "https://github.com/oven-sh/bun/releases/latest/download/bun-windows-x64.zip",
}


def download_bun() -> None:
    match get_os_platform():
        case "win32":
            url = BUN_RESOURCES["win32"]
            dest = Path.cwd() / "bin"
            file, _ = urlretrieve(url)
            zip = zipfile.ZipFile(file)
            zip.extractall(dest)
