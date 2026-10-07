"""Script update terminology Decidiq.

Hanya ganti string yang MUNCUL DI UI (dalam quote),
bukan nama variabel/fungsi internal.

Cara pakai:
  python terminology.py --preview    (lihat preview)
  python terminology.py --apply      (apply)
  python terminology.py --rollback   (batalkan)
"""
import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

# Format: (istilah_lama, istilah_baru)
# Hanya ganti kalau ada dalam quote string
TERMINOLOGY = [
    ("Hemat Tahunan", "Cost Saving Tahunan"),
    ("Perbandingan Periode", "Month-over-Month (MoM)"),
    ("Peringatan Aktif", "Cost Alert Aktif"),
    ("Impact Rp", "Financial Impact"),
    ("Rekomendasi Aksi Prioritas", "Priority Actions"),
    ("Rekomendasi Aksi", "Action Plan"),
    ("Controller Score", "Cost Control Score"),
    ("Anomali Scrap", "Outlier Detection"),
    ("Tren Keputusan", "Performance Trend"),
    ("Kualitas Data", "Data Quality Report"),
]

TARGET_EXTENSIONS = {".py"}
SKIP_FOLDERS = {"__pycache__", ".git", ".venv", "venv", "env",
                "_rebrand_backup", "_terminology_backup",
                "node_modules", ".streamlit", "data",
                ".pytest_cache", ".mypy_cache"}
SKIP_FILES = {"rebrand.py", "terminology.py"}


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
    return [p for p in root.rglob("*") if p.is_file() and not should_skip(p, root)]


def count_in_strings(content, old):
    """Cari 'old' hanya kalau ada dalam quote (single/double/triple).

    Pattern: sesuatu yang mengapit 'old' adalah quote.
    """
    # Pattern untuk string literal: "..." atau '...' atau f"..." atau f'...'
    # Kita cari kemunculan old yang diapit oleh karakter kutip
    patterns = [
        rf'"[^"]*{re.escape(old)}[^"]*"',   # dalam double quotes
        rf"'[^']*{re.escape(old)}[^']*'",   # dalam single quotes
    ]
    count = 0
    for pat in patterns:
        count += len(re.findall(pat, content))
    return count


def replace_in_strings(content, old, new):
    """Ganti 'old' jadi 'new' hanya di dalam string literal."""
    # Ganti dalam double quotes
    def repl_double(match):
        return match.group(0).replace(old, new)
    content = re.sub(rf'"[^"]*{re.escape(old)}[^"]*"', repl_double, content)
    # Ganti dalam single quotes
    content = re.sub(rf"'[^']*{re.escape(old)}[^']*'", repl_double, content)
    return content


def preview(root):
    print("=" * 70)
    print("PREVIEW - Terminology Update")
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

        found = {}
        for old, new in TERMINOLOGY:
            c = count_in_strings(content, old)
            if c > 0:
                found[old] = (c, new)

        if not found:
            continue

        total_files += 1
        rel = f.relative_to(root)
        print(f"  {rel}")
        for old, (c, new) in found.items():
            total_changes += c
            print(f"     '{old}' -> '{new}' ({c}x)")
        print()

    print("=" * 70)
    print(f"Total: {total_files} file, {total_changes} penggantian")
    print("=" * 70)
    print()
    print("Kalau sudah benar, jalankan: python terminology.py --apply")


def apply(root):
    print("=" * 70)
    print("APPLY - Terminology Update")
    print("=" * 70)
    print()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "_terminology_backup" / ts
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

        new_content = content
        changes = 0
        for old, new in TERMINOLOGY:
            c = count_in_strings(new_content, old)
            if c > 0:
                new_content = replace_in_strings(new_content, old, new)
                changes += c

        if changes == 0:
            continue

        rel = f.relative_to(root)
        backup_file = backup_root / rel
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, backup_file)

        f.write_text(new_content, encoding="utf-8")

        total_files += 1
        total_changes += changes
        print(f"  OK  {rel} ({changes} perubahan)")

    print()
    print("=" * 70)
    print(f"Terminology update selesai!")
    print(f"   File diubah: {total_files}")
    print(f"   Total penggantian: {total_changes}")
    print(f"   Backup di: {backup_root}")
    print("=" * 70)
    print()
    print("Langkah selanjutnya:")
    print("   git add .")
    print("   git commit -m 'Update terminology to professional terms'")
    print("   git push")


def rollback(root, backup_path=None):
    backup_base = root / "_terminology_backup"
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
    parser = argparse.ArgumentParser(description="Update terminology Decidiq")
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