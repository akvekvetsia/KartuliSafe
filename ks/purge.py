"""Step 9: delete the models' raw answers to sensitive prompts once grading is finished.

Run it after step 6 (both judges) and step 7 (linguist labels) are complete and step 8 has produced the results.
It keeps everything the results need (ids, labels, model versions, usage) and blanks the answer text.
Refuses if any sensitive answer has not been graded by every judge yet. Pass --yes to confirm.
"""
import json
from .common import config, private_dir, read_jsonl, slug


def main(args):
    cfg = config()
    pdir = private_dir()
    graded = []
    for j in cfg['judges']:
        graded.append({r['key'] for r in read_jsonl(pdir / 'labels' / f"{slug(j['id'])}.jsonl") if r['label'] != 'unparsed'})
    files = sorted((pdir / 'responses').glob('*.jsonl')) if (pdir / 'responses').exists() else []
    ungraded = 0
    for f in files:
        for r in read_jsonl(f):
            if r.get('answer') and not all(f"{r['model']}|{r['key']}" in g for g in graded):
                ungraded += 1
    if ungraded:
        print(f'{ungraded} sensitive answers are not graded by every judge yet: run step 6 first. Nothing deleted.')
        return
    if '--yes' not in args:
        print(f'Would blank the answer text in {len(files)} files under {pdir}/responses. Re-run with --yes.')
        return
    for f in files:
        rows = read_jsonl(f)
        for r in rows:
            if r.get('answer'):
                r['answer'] = ''
                r['purged'] = True
        f.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    for name in ('sample_ka.csv',):
        p = pdir / 'human' / name
        if p.exists():
            p.unlink()
    print('Sensitive answer texts deleted; labels and run records kept.')
