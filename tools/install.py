#!/usr/bin/env python3
"""Install only this adapter into a Live User Library; back up existing files."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from MPC_Key_37.profile import load


def default_user_library():
    if sys.platform.startswith("win"):
        return Path.home() / "Documents" / "Ableton" / "User Library"
    return Path.home() / "Music" / "Ableton" / "User Library"


def install(library, replace_profile=False):
    source = ROOT / "MPC_Key_37"
    destination = library / "Remote Scripts" / "MPC_Key_37"
    load(source / "midi_profile.json")
    existing_profile = destination / "midi_profile.json"
    if existing_profile.exists() and not replace_profile:
        load(existing_profile)
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if destination.exists():
        backup_dir = library / "Remote Script Backups"
        backup_dir.mkdir(exist_ok=True)
        backup = backup_dir / ("MPC_Key_37-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".zip")
        with zipfile.ZipFile(backup, "x", zipfile.ZIP_DEFLATED) as archive:
            for path in destination.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(destination.parent))
    # Stage under the same filesystem before replacing the installed directory.
    with tempfile.TemporaryDirectory(prefix="mpc-install-", dir=library) as temp:
        staged = Path(temp) / "MPC_Key_37"
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if existing_profile.exists() and not replace_profile:
            shutil.copy2(existing_profile, staged / "midi_profile.json")
        previous = Path(temp) / "previous"
        if destination.exists():
            destination.rename(previous)
        try:
            staged.rename(destination)
        except Exception:
            if previous.exists():
                previous.rename(destination)
            raise
    return destination, backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-library", type=Path, default=default_user_library())
    parser.add_argument("--replace-profile", action="store_true", help="Install project profile; old profile remains in backup")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load()
    if args.dry_run:
        print("Validated. Destination:", args.user_library / "Remote Scripts/MPC_Key_37")
        return
    destination, backup = install(args.user_library, args.replace_profile)
    print("Installed:", destination)
    if backup:
        print("Backup:", backup)
    print("In Live, select MPC Key 37 as a Control Surface. Restart Live if it is not listed.")


if __name__ == "__main__":
    main()
