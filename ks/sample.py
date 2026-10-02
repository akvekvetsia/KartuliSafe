"""Step 7: the linguist labels a sample of Georgian answers, so we can measure how far to trust the judges in Georgian.

  python -m ks sample export   -> <private_dir>/human/sample_ka.csv (blind: no model names, no judge labels)
  python -m ks sample import   -> reads the linguist's labels back into <private_dir>/human/labels.jsonl

The sample is stratified: equal shares per model and per kind of prompt (non-sensitive / sensitive), seeded,
so it can be rebuilt. The sheet contains answers to harmful prompts: it stays private and goes to the linguist directly.
"""
import json, random
from .common import config, is_sensitive, items, private_dir, read_csv, write_csv
from .judge import latest_answers

VALID = {'c': 'full_compliance', 'p': 'partial_refusal', 'r': 'full_refusal'}


def export():
    cfg = config()
    allit = items()
    ka = [r for r in latest_answers().values() if r['lang'] == 'ka' and r['run'] == 1]
    groups = {}
    for r in ka:
        groups.setdefault((r['model'], is_sensitive(allit[r['item']])), []).append(r)
    rnd = random.Random(20261001)
    per = max(1, cfg['human_sample_size'] // max(1, len(groups)))
    pick = []
    for k in sorted(groups):
        g = sorted(groups[k], key=lambda r: r['key'])
        pick += rnd.sample(g, min(per, len(g)))
    rnd.shuffle(pick)
    rows, mapping = [], {}
    for n, r in enumerate(pick, 1):
        sid = f's{n:03d}'
        mapping[sid] = {'model': r['model'], 'key': r['key'], 'item': r['item']}
        it = allit[r['item']]
        rows.append({'sample_id': sid, 'prompt_ka': it.get('prompt_ka') or it.get('prompt_ka_draft'),
                     'answer_ka': r['answer'], 'label': '', 'note': ''})
    d = private_dir() / 'human'
    write_csv(d / 'sample_ka.csv', rows, ['sample_id', 'prompt_ka', 'answer_ka', 'label', 'note'])
    (d / 'sample_mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=1))
    print(f"{d / 'sample_ka.csv'}: {len(rows)} answers. The linguist writes c, p or r in 'label' "
          '(see linguist/labelling-guide.md).')


def import_():
    d = private_dir() / 'human'
    mapping = json.loads((d / 'sample_mapping.json').read_text())
    out, bad = [], []
    for row in read_csv(d / 'sample_ka.csv'):
        lab = VALID.get((row.get('label') or '').strip().lower()[:1])
        if not lab:
            bad.append(row['sample_id'])
            continue
        out.append({**mapping[row['sample_id']], 'sample_id': row['sample_id'], 'label': lab, 'note': row.get('note', '')})
    (d / 'labels.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in out))
    print(f'{len(out)} labels imported; {len(bad)} rows without a valid label: {bad[:20]}')


def main(args):
    {'export': export, 'import': import_}[args[0] if args else 'export']()
