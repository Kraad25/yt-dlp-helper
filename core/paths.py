import os, sys
import shutil
from pathlib import Path

APP_NAME = "MediaDownloader"

def install_dir()->Path: #ffmpeg,libs/(things the updater replaces)
    return Path(sys.executable).parent if getattr(sys,"frozen",False)\
        else Path(__file__).resolve().parent.parent

def resource_dir()->Path: #read-only bundled files(themes,icon)
    return Path(getattr(sys, "_MEIPASS", install_dir()))

def user_data_dir()->Path: #DB,config,caches,logs (writable, survives upgrades)
    base = Path(os.environ.get("APPDATA") or Path.home())
    p=base /APP_NAME
    p.mkdir(parents=True,exist_ok=True)
    return p

def ffmpeg_directory() -> Path:
    if getattr(sys, "frozen", False):
        return install_dir() / "_internal" / "ffmpeg"
    return install_dir() / "ffmpeg"

def migrate_legacy_data():
    target = user_data_dir()
    for old_root in {install_dir(), resource_dir()}:
        for name in ("config", "database"):
            src, dst = old_root / name, target / name
            if src.is_dir() and not dst.exists():
                shutil.copytree(src, dst)