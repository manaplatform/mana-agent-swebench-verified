#!/usr/bin/env python3
"""Audit submitted SWE-bench predictions against the *exact* evaluated patch.

Use from the Mana-Agent repo with --readme PATH/README.md. This script does not
rerun the agent or Docker, alter predictions, or read secret configuration.
It only updates the README's results table and environment field when requested.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from importlib import metadata

TOTAL = 500
FIELDS = (
    'Instances with final predictions',
    'Instances with matching official evaluation evidence',
    'Resolved instances',
    'Unresolved instances',
    'Empty patches',
    'Missing or unevaluated instances',
    'Resolved / 500',
)


def valid_rows(path: Path) -> dict[str, dict]:
    rows = {}
    if not path.is_file():
        raise RuntimeError(f'Predictions file not found: {path}')
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            raise RuntimeError(f'Invalid JSON at {path}:{line_no}: {exc}') from exc
        if not isinstance(row, dict) or not isinstance(row.get('instance_id'), str):
            raise RuntimeError(f'Invalid prediction row: {path}:{line_no}')
        iid = row['instance_id']
        if iid in rows and rows[iid] != row:
            raise RuntimeError(f'Conflicting predictions for {iid}; aborting audit')
        if 'model_patch' not in row or not isinstance(row['model_patch'], str):
            raise RuntimeError(f'Invalid model_patch for {iid}; aborting audit')
        rows[iid] = row
    return rows


def relevant_reports(root: Path):
    # Supports both raw local logs/run_evaluation/<run>/<model>/<iid>/ and
    # packaged logs/<iid>/, including mixed/multiple historical run folders.
    seen = set()
    if not root.is_dir():
        return
    for path in root.rglob('report.json'):
        if path in seen:
            continue
        seen.add(path)
        if '__' not in path.parent.name:
            continue
        yield path


def run_version(cmd: list[str]) -> str:
    try:
        ret = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return (ret.stdout or ret.stderr).strip().splitlines()[0] if ret.returncode == 0 else 'unavailable'
    except Exception:
        return 'unavailable'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--predictions', default='predictions.jsonl', type=Path)
    ap.add_argument('--logs', default='logs/run_evaluation', type=Path)
    ap.add_argument('--readme', default='swebench-submission/README.md', type=Path)
    ap.add_argument('--agent-logs', default='.swe-bench/logs', type=Path)
    ap.add_argument('--write', action='store_true', help='Update just the README results table + environment')
    args = ap.parse_args()
    rows = valid_rows(args.predictions)
    valid = defaultdict(list)
    mismatched, missing_output, invalid_reports = set(), set(), []
    scanned = 0
    for report in relevant_reports(args.logs):
        scanned += 1
        iid = report.parent.name
        if iid not in rows:
            continue
        patchfile = report.parent / 'patch.diff'
        if not patchfile.is_file() or patchfile.read_text(encoding='utf-8', errors='replace') != rows[iid]['model_patch']:
            mismatched.add(iid)
            continue
        if not (report.parent / 'test_output.txt').is_file() and not (report.parent / 'test_output.txt.gz').is_file():
            missing_output.add(iid)
            continue
        try:
            val = json.loads(report.read_text(encoding='utf-8'))[iid]['resolved']
            if not isinstance(val, bool):
                raise ValueError('resolved is not boolean')
        except (ValueError, KeyError, TypeError, OSError) as e:
            invalid_reports.append((iid, str(report), str(e)))
            continue
        valid[iid].append((val, str(report)))
    conflicting = {iid for iid, entries in valid.items() if len(set(v for v, _ in entries)) > 1}
    accepted = {iid: entries[0][0] for iid, entries in valid.items() if iid not in conflicting}
    empty = {iid for iid, row in rows.items() if not row['model_patch'].strip()}
    resolved = {iid for iid, v in accepted.items() if v}
    unresolved = {iid for iid, v in accepted.items() if not v}
    not_evaluated = set(rows) - set(accepted)
    missing_instances = max(0, TOTAL - len(rows))
    score = len(resolved) / TOTAL * 100
    values = {
        FIELDS[0]: str(len(rows)),
        FIELDS[1]: str(len(accepted)),
        FIELDS[2]: str(len(resolved)),
        FIELDS[3]: str(len(unresolved)),
        FIELDS[4]: str(len(empty)),
        FIELDS[5]: str(len(not_evaluated) + missing_instances),
        FIELDS[6]: f'{len(resolved)} / {TOTAL} ({score:.2f}%)',
    }
    print(f'Predictions file : {args.predictions}')
    print(f'Log directory    : {args.logs}')
    print(f'Report files seen: {scanned}')
    for key, val in values.items():
        print(f'{key:49} {val}')
    print(f'Historical patch mismatches (may be normal) : {len(mismatched)}')
    print(f'Conflicting same-patch reports (must review) : {len(conflicting)}')
    print(f'Invalid reports                            : {len(invalid_reports)}')
    print(f'Patch-matched logs without test output     : {len(missing_output)}')
    print(f'Extra predictions above expected 500        : {max(0, len(rows)-TOTAL)}')
    print('\nUnmatched predictions (up to 20):')
    for iid in sorted(not_evaluated)[:20]:
        print(f'  {iid}')
    if conflicting:
        print('\nCONFLICTS:', ', '.join(sorted(conflicting)))

    hints = []
    prompt_files = 0
    if args.agent_logs.is_dir():
        for f in args.agent_logs.rglob('prompt.txt'):
            if '__' not in f.parent.name:
                continue
            prompt_files += 1
            if re.search(r'(?m)^Hints:\s*$', f.read_text(encoding='utf-8', errors='replace')):
                hints.append(f.parent.name)
    print('\nHint audit:')
    print(f'  Prompt files scanned: {prompt_files}')
    print(f'  Files containing a Hints section: {len(hints)}')
    for iid in hints[:20]:
        print(f'    {iid}')
    if hints:
        print('  WARNING: These prompts contain hints_text; review eligibility before submission.')
    else:
        print('  Absence of a Hints section is NOT proof of compliance; older attempts may be absent.')

    host = f'{platform.system()} {platform.release()}, {platform.machine()}'
    docker = run_version(['docker', '--version'])
    try:
        swe_version = metadata.version('swebench')
    except metadata.PackageNotFoundError:
        swe_version = 'not installed in active Python environment'
    env_line = (
        f'**Measured local environment (audit run, not necessarily original evaluation):** '
        f'host {host}; Python {platform.python_version()}; Docker {docker}; '
        f'SWE-bench package {swe_version}. '
        f'The original evaluator used per-instance `--max_workers 1` runs; '
        f'confirm original tool versions and hardware from the run records.'
    )
    print('\n' + env_line)
    if args.write:
        if not args.readme.is_file():
            raise RuntimeError(f'README not found: {args.readme}. Use --readme to supply its path.')
        if len(rows) > TOTAL or conflicting:
            raise RuntimeError('Unsafe result set (more than 500 or conflicting verdicts). Refusing to modify README.')
        text = args.readme.read_text(encoding='utf-8')
        for field, value in values.items():
            pattern = re.compile(r'(?m)^(\|\s*' + re.escape(field) + r'\s*\|\s*)[^|]*(\|\s*)$')
            text, matches = pattern.subn(lambda m: m.group(1) + value + ' ' + m.group(2), text)
            if matches != 1:
                raise RuntimeError(f'Cannot locate unique README results row: {field} (found {matches})')
        text = re.sub(r'(?m)^- \*\*Host and software versions:\*\*.*$',
                      '- ' + env_line, text)
        bak = args.readme.with_name(args.readme.name + '.before-audit')
        if not bak.exists():
            bak.write_text(args.readme.read_text(encoding='utf-8'), encoding='utf-8')
        args.readme.write_text(text, encoding='utf-8')
        print(f'\nREADME updated: {args.readme} (backup: {bak})')
        print('NOTE: Inspect counts, hints, and attempts before publication. Not official verification.')

if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        raise SystemExit(2)
