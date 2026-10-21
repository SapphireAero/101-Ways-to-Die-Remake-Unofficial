"""Run the public demo in a temporary project with the supplied Ren'Py SDK."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from check_public import ROOT, check

def run(sdk):
    sdk = Path(sdk).resolve()
    entry = sdk / 'renpy.py'
    candidates = [sdk / 'lib/py3-windows-x86_64/python.exe',
                  sdk / 'lib/py3-linux-x86_64/python',
                  sdk / 'lib/py3-mac-universal/python']
    python = next((path for path in candidates if path.is_file()), None)
    if not entry.is_file() or python is None:
        raise ValueError('A supported Ren\'Py SDK with bundled Python is required')
    paths = check()
    with tempfile.TemporaryDirectory(prefix='101-public-engine-') as temporary:
        project = Path(temporary) / 'project'
        project.mkdir()
        for name in paths:
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   RENPY_RENDERER='sw', APPDATA=str(Path(temporary) / 'appdata'),
                   RENPY_PATH_TO_SAVES=str(Path(temporary) / 'saves'))
        lint = subprocess.run([str(python), str(entry), str(project), 'lint'], env=env,
                              cwd=project, capture_output=True, timeout=60)
        if lint.returncode:
            raise ValueError('RenPy lint failed:\n' + (lint.stdout + lint.stderr).decode('utf-8-sig', 'replace'))
        print('RenPy lint: OK')
        shutil.copyfile(ROOT / 'tests/engine_probe.rpy', project / 'game/zz_public_probe.rpy')
        result = subprocess.run([str(python), str(entry), str(project)], env=env,
                                cwd=project, capture_output=True, timeout=60)
        report_path = project / 'probe-report.json'
        if not report_path.is_file():
            raise ValueError('Engine probe did not finish:\n' + (result.stdout + result.stderr).decode('utf-8-sig', 'replace'))
        report = json.loads(report_path.read_text(encoding='utf-8'))
        if result.returncode or not report.get('ok'):
            raise ValueError(report.get('error', 'Engine probe failed'))
        print('Engine smoke: OK (%d screen renders, %d routes, %d SVGs)' %
              (len(report['screens']), len(report['routes']), report['cg_rendered']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', required=True, help='RenPy SDK directory containing renpy.py')
    try:
        run(parser.parse_args().sdk)
    except (ValueError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(str(exc))
