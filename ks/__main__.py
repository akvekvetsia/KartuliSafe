"""python -m ks <step> [options]. Steps, in order:

  prepare            1. download the test sets and split public / sensitive
  draft              2. machine-draft the Georgian prompts
  review export      3. sheets for the linguist
  review import      4. read the linguist's sheets back
  run                5. ask every model every prompt, English and Georgian
  judge              6. two judges grade every answer
  sample export      7a. sample of Georgian answers for the linguist to label
  sample import      7b. read the linguist's labels back
  analyze            8. results tables
  purge --yes        9. delete raw answers to sensitive prompts
  release            after the disclosure window: publish the sensitive prompts and results
  status             where the study stands
"""
import importlib, sys


def status(args):
    from .common import DATA, config, is_sensitive, items, private_dir, read_jsonl, slug
    cfg = config()
    it = items()
    n_sens = sum(is_sensitive(r) for r in it.values())
    print(f'private folder: {private_dir()}')
    print(f'items: {len(it)} ({n_sens} sensitive); Georgian drafts: {sum(bool(r.get("prompt_ka_draft")) for r in it.values())}; '
          f'final (linguist): {sum(bool(r.get("prompt_ka")) for r in it.values())}')
    for m in cfg['models']:
        n = sum(1 for base in (DATA, private_dir()) for r in read_jsonl(base / 'responses' / f"{slug(m['id'])}.jsonl") if r.get('answer') or r.get('purged'))
        print(f"answers {m['id']}: {n}")
    for j in cfg['judges']:
        n = sum(1 for base in (DATA, private_dir()) for r in read_jsonl(base / 'labels' / f"{slug(j['id'])}.jsonl") if r['label'] != 'unparsed')
        print(f"labels {j['id']}: {n}")
    print(f"disclosure date: {cfg.get('disclosure_date') or 'not set'}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help', 'help'):
        print(__doc__)
        return
    if args[0] == 'status':
        return status(args[1:])
    mod = importlib.import_module(f'ks.{args[0]}')
    mod.main(args[1:])


if __name__ == '__main__':
    main()
