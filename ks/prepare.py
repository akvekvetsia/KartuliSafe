"""Step 1: download the two public test sets and split them.

Non-sensitive items (XSTest safe prompts, JailbreakBench benign twins) go to data/items_public.csv.
Sensitive items (XSTest unsafe contrasts, JailbreakBench harmful behaviours) go to <private_dir>/items_private.csv,
and only their ids and fingerprints (hashes) go into the repository, for the leak guard.
"""
import csv, io
from .common import DATA, GUARD, ITEM_FIELDS, fingerprint, private_dir, read_csv, save_items, write_csv

XSTEST = 'https://huggingface.co/datasets/Paul/XSTest/resolve/main/xstest_prompts.csv'
JBB = 'https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/main/data/{}-behaviors.csv'


def fetch(url):
    import requests
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.content.decode('utf-8'))))


def main(args):
    if (DATA / 'items_public.csv').exists() and '--force' not in args:
        print('Already prepared (data/items_public.csv exists). Use --force to rebuild from the sources;'
              ' this keeps no translations, so never use it after step 2.')
        return
    raw = private_dir() / 'raw'
    rows = []
    for r in fetch(XSTEST):
        sens = r['label'].strip() == 'unsafe'
        rows.append({'id': f"xs-{r['id']}", 'set': 'xstest', 'label': r['label'].strip(), 'sensitive': int(sens),
                     'category': r.get('type', ''), 'prompt_en': r['prompt']})
    for kind in ('harmful', 'benign'):
        for r in fetch(JBB.format(kind)):
            rows.append({'id': f"jbb-{kind[0]}-{r['Index']}", 'set': 'jbb', 'label': kind,
                         'sensitive': int(kind == 'harmful'), 'category': r.get('Category', ''), 'prompt_en': r['Goal']})
    for r in rows:
        for k in ITEM_FIELDS:
            r.setdefault(k, '')
    save_items({r['id']: r for r in rows})
    sens = [r for r in rows if r['sensitive'] == 1]
    GUARD.mkdir(exist_ok=True)
    (GUARD / 'sensitive_ids.txt').write_text('\n'.join(r['id'] for r in sens) + '\n')
    (GUARD / 'fingerprints.txt').write_text('\n'.join(sorted({fingerprint(r['prompt_en']) for r in sens})) + '\n')
    pub = len(rows) - len(sens)
    print(f'{len(rows)} items: {pub} public -> data/items_public.csv; {len(sens)} sensitive -> {private_dir()}/items_private.csv')
    print('Guard updated: guard/sensitive_ids.txt and guard/fingerprints.txt (ids and hashes only).')
