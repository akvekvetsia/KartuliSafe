"""Steps 3 and 4: the linguist's review sheets.

  python -m ks review export   -> two CSV sheets in <private_dir>/review/ (open them in Google Sheets or Excel)
  python -m ks review import   -> reads the filled sheets back and fixes the final Georgian text

Sheet columns the linguist fills: prompt_ka (the final Georgian; leave empty to accept the draft as it is),
adapted (y if the prompt was adapted rather than translated, e.g. English wordplay), note (one line why).
Both sheets live in the private folder: the sensitive one must never be uploaded anywhere public.
"""
from .common import GUARD, fingerprint, is_sensitive, items, private_dir, read_csv, save_items, write_csv

COLS = ['id', 'set', 'label', 'category', 'prompt_en', 'prompt_ka_draft', 'prompt_ka', 'adapted', 'note']


def export():
    d = private_dir() / 'review'
    allit = items().values()
    for name, rows in (('review_non_sensitive.csv', [r for r in allit if not is_sensitive(r)]),
                       ('review_SENSITIVE.csv', [r for r in allit if is_sensitive(r)])):
        write_csv(d / name, rows, COLS)
        print(f'{d / name}: {len(rows)} rows')
    print('Give both sheets to the linguist privately (not by a public link). '
          'The SENSITIVE sheet contains the harmful prompts.')


def import_():
    d = private_dir() / 'review'
    allit = items()
    missing, changed = [], 0
    for name in ('review_non_sensitive.csv', 'review_SENSITIVE.csv'):
        for row in read_csv(d / name):
            it = allit.get(row['id'])
            if not it:
                continue
            final = (row.get('prompt_ka') or '').strip() or (row.get('prompt_ka_draft') or '').strip()
            if not final:
                missing.append(row['id'])
                continue
            changed += final != (it.get('prompt_ka_draft') or '').strip()
            it.update({'prompt_ka': final, 'adapted': (row.get('adapted') or '').strip().lower()[:1],
                       'note': (row.get('note') or '').strip()})
    save_items(allit)
    fp = set((GUARD / 'fingerprints.txt').read_text().split())
    fp |= {fingerprint(r['prompt_ka']) for r in allit.values() if is_sensitive(r) and r.get('prompt_ka')}
    (GUARD / 'fingerprints.txt').write_text('\n'.join(sorted(fp)) + '\n')
    print(f'imported; {changed} items changed by the linguist; {len(missing)} still without Georgian: {missing[:20]}')


def main(args):
    {'export': export, 'import': import_}[args[0] if args else 'export']()
