#!/usr/bin/env python3
"""Leak guard. Blocks a commit (or fails CI) if it would put any of these into the public repository:

1. an API key or access token;
2. any sensitive prompt (harmful request) in English or Georgian, recognised by its fingerprint (a hash), before release;
3. any record about a sensitive item in data/responses/ or data/labels/ (model answers to harmful prompts never go public);
4. files with names that belong in the private folder.

  python3 guard/check.py --staged   # what the pre-commit hook runs (files about to be committed)
  python3 guard/check.py --all      # every tracked file (what CI runs)

Standard library only. It stops accidents; it cannot stop someone who disables it on purpose.
"""
import csv, hashlib, io, json, re, subprocess, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY_PATTERNS = [r'sk-or-v1-[0-9a-f]{20,}', r'sk-ant-[A-Za-z0-9_\-]{20,}', r'sk-proj-[A-Za-z0-9_\-]{20,}',
                r'\bsk-[A-Za-z0-9]{32,}\b', r'AIza[0-9A-Za-z_\-]{35}', r'\bxai-[A-Za-z0-9]{20,}',
                r'github_pat_[A-Za-z0-9_]{30,}', r'\bghp_[A-Za-z0-9]{30,}', r'-----BEGIN [A-Z ]*PRIVATE KEY-----']
BLOCKED_NAMES = re.compile(r'(items_private|review_SENSITIVE|summary_sensitive|tables_sensitive|sample_ka|sample_mapping|keys\.env|\.env$)')
TEXT_SUFFIXES = {'.csv', '.json', '.jsonl', '.md', '.txt', '.py', '.yml', '.yaml', '.html', '.tsv', ''}


def normalize(text):
    t = unicodedata.normalize('NFC', str(text)).lower()
    return re.sub(r'\s+', ' ', t).strip().strip('"\'„“”.,;:!?()[] ')


def fp(text):
    return hashlib.sha256(normalize(text).encode('utf-8')).hexdigest()


def load(name):
    p = ROOT / 'guard' / name
    return set(p.read_text().split()) if p.exists() else set()


def candidates(path, text):
    """Every string in the file that could be a prompt: lines, CSV cells, JSON string values."""
    out = set(text.splitlines())
    if path.suffix in ('.csv', '.tsv'):
        try:
            for row in csv.reader(io.StringIO(text), delimiter='\t' if path.suffix == '.tsv' else ','):
                out.update(row)
        except csv.Error:
            pass
    if path.suffix in ('.json', '.jsonl'):
        def walk(o):
            if isinstance(o, str):
                out.add(o)
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        for chunk in ([text] if path.suffix == '.json' else text.splitlines()):
            try:
                walk(json.loads(chunk))
            except Exception:
                pass
    return {c for c in out if len(c.strip()) >= 12}


def files(mode):
    if mode == '--staged':
        names = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'], cwd=ROOT,
                               capture_output=True, text=True).stdout.split('\n')
    else:
        names = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
    return [ROOT / n for n in names if n.strip()]


def staged_text(path, mode):
    if mode == '--staged':
        r = subprocess.run(['git', 'show', f':{path.relative_to(ROOT).as_posix()}'], cwd=ROOT, capture_output=True)
        return r.stdout.decode('utf-8', 'replace')
    return path.read_text(encoding='utf-8', errors='replace')


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--staged'
    released = (ROOT / 'guard' / 'RELEASED').exists()
    prints, sens_ids = load('fingerprints.txt'), load('sensitive_ids.txt')
    problems = []
    for path in files(mode):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith('guard/'):
            continue  # the guard's own files hold ids and hashes only
        if BLOCKED_NAMES.search(path.name):
            problems.append(f'{rel}: this file belongs in the private folder, not the repository')
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = staged_text(path, mode)
        for pat in KEY_PATTERNS:
            if re.search(pat, text):
                problems.append(f'{rel}: looks like an API key or token ({pat[:14]}...)')
        allowed_prompts = released and rel == 'data/items_sensitive.csv'
        if prints and not allowed_prompts:
            hits = sum(1 for c in candidates(path, text) if fp(c) in prints)
            if hits:
                problems.append(f'{rel}: contains {hits} sensitive prompt(s) (harmful requests are private until release)')
        if rel.startswith(('data/responses/', 'data/labels/')) and sens_ids:
            ids = set(re.findall(r'"item":\s*"([^"]+)"', text))
            bad = ids & sens_ids
            if bad:
                problems.append(f'{rel}: holds records about {len(bad)} sensitive item(s); those stay in the private folder')
    if problems:
        print('LEAK GUARD: commit blocked.\n  ' + '\n  '.join(problems))
        print('Move the material to the private folder (see README, "What stays private") and try again.')
        sys.exit(1)
    print('leak guard: OK')


if __name__ == '__main__':
    main()
