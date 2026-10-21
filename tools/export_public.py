"""Export only files explicitly listed in public-manifest.json."""
from pathlib import Path
import argparse
import shutil
from check_public import ROOT, check

def export(destination):
    destination = Path(destination).resolve()
    source = ROOT.resolve()
    if destination == source or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('Choose a new directory outside this project')
    if destination.exists():
        raise ValueError('Destination already exists; nothing overwritten')
    paths = check()
    destination.mkdir(parents=True)
    for name in paths:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    check(destination)
    print('Public source exported:', destination)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    try:
        export(parser.parse_args().output)
    except ValueError as exc:
        raise SystemExit(str(exc))
