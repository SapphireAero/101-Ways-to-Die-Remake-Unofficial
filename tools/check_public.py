"""Check an explicit public file list; do not infer ownership from extensions."""
from pathlib import Path, PurePosixPath
import argparse
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIRS = {'.git', '__pycache__', 'cache', 'saves'}
GENERATED_FILES = {'log.txt', 'traceback.txt', 'errors.txt', 'lint.txt'}

def manifest(root=ROOT):
    paths = json.loads((root / 'public-manifest.json').read_text(encoding='utf-8'))
    if not isinstance(paths, list) or len(paths) != len(set(paths)):
        raise ValueError('Public manifest must contain unique relative file names')
    for name in paths:
        parts = PurePosixPath(name).parts
        if not parts or '..' in parts or '\\' in name or ':' in name or PurePosixPath(name).is_absolute():
            raise ValueError('Unsafe path in public manifest: ' + str(name))
        if (root / name).is_symlink() or not (root / name).is_file():
            raise ValueError('Missing file or symbolic link: ' + name)
        resolved = (root / name).resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError('Path escapes project: ' + name)
    return set(paths)

def tracked_files(root=ROOT):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True, check=True)
    return set(result.stdout.decode('utf-8').rstrip('\0').split('\0')) - {''}

def working_files(root=ROOT):
    result = set()
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if any(part in GENERATED_DIRS for part in relative.parts):
            continue
        if path.is_file() and path.suffix != '.rpyc' and path.name not in GENERATED_FILES:
            result.add(relative.as_posix())
    return result

def check(root=ROOT, tracked=False):
    approved = manifest(root)
    actual = tracked_files(root) if tracked else working_files(root)
    extra = sorted(actual - approved)
    missing = sorted(approved - actual)
    if extra or missing:
        raise ValueError('Outside public manifest: %s\nMissing public files: %s' % (extra, missing))
    # A manifest edit must not accidentally authorize obvious private material.
    for name in sorted(approved):
        path = PurePosixPath(name)
        if any(part in {'original_script', 'original', 'cg_r18', 'dist', 'saves', 'cache'} for part in path.parts):
            raise ValueError('Private or generated directory: ' + name)
        if path.suffix.lower() in {'.mp3', '.ogg', '.wav', '.mp4', '.mpg', '.webm', '.fob', '.dat', '.rpa', '.rpyc', '.zip', '.exe'}:
            raise ValueError('Private media or compiled artifact: ' + name)
        if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.svg', '.ico'}:
            if not (name.startswith('game/gui/') or name.startswith('game/demo/cg/') or name == 'icon.ico'):
                raise ValueError('Unapproved artwork location: ' + name)
        if (root / name).stat().st_size > 5_000_000:
            raise ValueError('Unexpected large file: ' + name)
    return sorted(approved)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tracked', action='store_true', help='check the actual Git index (including forced additions)')
    args = parser.parse_args()
    try:
        files = check(tracked=args.tracked)
    except (ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
    total = sum((ROOT / name).stat().st_size for name in files)
    print('Public file boundary: OK (%d files, %.2f MiB)' % (len(files), total / 1024 ** 2))
