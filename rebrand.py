"""Script auto-rebranding: AI Factory Controller -> Decidiq.

Cara pakai:
  python rebrand.py --preview    (lihat preview dulu)
  python rebrand.py --apply      (apply perubahan)
  python rebrand.py --rollback   (batalkan)
"""
import argparse
import shutil
from datetime import datetime
from pathlib import Path

REPLACEMENTS = [
    ("AI Factory Controller", "Decidiq"),
    ("AI FACTORY CONTROLLER", "DECIDIQ"),
    ("ai factory controller", "decidiq"),
    ("ai_factory_controller", "decidiq"),
    ("AI-Factory-Controller", "Decidiq"),
    ("ai-factory-controller", "decidiq"),
    ("AIFactoryController", "Decidiq"),
    ("aiFactoryController", "decidiq"),
    ("Factory Controller", "Decidiq"),
    ("Manufacturing Intelligence Platform", "Decision Intelligence Platform"),
    ("Manufacturing Cost Control & Performance Dashboard", "Decision Intelligence Dashboard"),
]

TARGET_EXTENSIONS = {".py", ".md", ".txt", ".toml", ".cfg", ".ini", ".yaml", ".yml"}
SKIP_FOLDERS = {"__pycache__", ".git", ".venv", "venv", "env", "_rebrand_backup",
                "node_modules", ".streamlit", "data", ".pytest_cache", ".mypy_cache"}
SKIP_FILES = {"rebrand.py"}


def should_skip(path, root):
    parts = set(path.relative_to(root).parts)
    if parts & SKIP_FOLDERS:
        return True
    if path.name in SKIP_FILES:
        return True
    if path.is_file() and path.suffix not in TARGET_EXTENSIONS:
        return True
    return False


def find_files(root):
    files = []
    for path in root.rglob("*"):
        if path.is_file() and not should_skip(path, root):
            files.append(path)
    return files


def count_replacements(content):
    counts = {}
    for old, new in REPLACEMENTS:
        c = content.count(old)
        if c > 0:
            counts[old] = (c, new)
    return counts


def apply_replacements(content):
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    return content


def preview(root):
    print("=" * 70)
    print("PREVIEW - Perubahan yang akan dilakukan")
    print("=" * 70)
    print()
    files = find_files(root)
    total_files = 0
    total_changes = 0
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        counts = count_replacements(content)
        if not counts:
            continue
        total_files += 1
        rel = f.relative_to(root)
        print(f"  {rel}")
        for old, (c, new) in counts.items():
            total_changes += c
            print(f"     '{old}' -> '{new}' ({c}x)")
        print()
    print("=" * 70)
    print(f"Total: {total_files} file, {total_changes} penggantian")
    print("=" * 70)
    print()
    print("Kalau sudah benar, jalankan: python rebrand.py --apply")


def apply(root):
    print("=" * 70)
    print("APPLY - Rebranding dimulai")
    print("=" * 70)
    print()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "_rebrand_backup" / ts
    backup_root.mkdir(parents=True, exist_ok=True)
    print(f"Backup folder: {backup_root}")
    print()

    files = find_files(root)
    total_files = 0
    total_changes = 0

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        counts = count_replacements(content)
        if not counts:
            continue

        rel = f.relative_to(root)
        backup_file = backup_root / rel
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, backup_file)

        new_content = apply_replacements(content)
        f.write_text(new_content, encoding="utf-8")

        changes = sum(c for c, _ in counts.values())
        total_changes += changes
        total_files += 1
        print(f"  OK  {rel} ({changes} perubahan)")

    print()
    print("=" * 70)
    print(f"Rebranding selesai!")
    print(f"   File diubah: {total_files}")
    print(f"   Total penggantian: {total_changes}")
    print(f"   Backup di: {backup_root}")
    print("=" * 70)
    print()
    print("Langkah selanjutnya:")
    print("   1. git add .")
    print("   2. git commit -m 'Rebrand: AI Factory Controller to Decidiq'")
    print("   3. git push")


def rollback(root, backup_path=None):
    backup_base = root / "_rebrand_backup"
    if not backup_base.exists():
        print("Tidak ada folder backup")
        return
    if backup_path:
        backup = Path(backup_path)
    else:
        backups = sorted(backup_base.iterdir(), reverse=True)
        if not backups:
            print("Tidak ada backup")
            return
        backup = backups[0]
    print(f"Rollback dari: {backup}")
    for f in backup.rglob("*"):
        if f.is_file():
            rel = f.relative_to(backup)
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            print(f"  restored: {rel}")
    print()
    print("Rollback selesai")


def main():
    parser = argparse.ArgumentParser(description="Rebranding Decidiq")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", type=str, nargs="?", const="")
    args = parser.parse_args()
    root = Path.cwd()
    if args.preview:
        preview(root)
    elif args.apply:
        apply(root)
    elif args.rollback is not None:
        rollback(root, args.rollback if args.rollback else None)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()