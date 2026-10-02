"""Step 5: ask every model every prompt, in English and in Georgian.

Resumable: answers already saved are skipped, so the command can simply be run again after a failure.
Answers to non-sensitive prompts go to data/responses/<model>.jsonl (public); answers to sensitive prompts go to
<private_dir>/responses/<model>.jsonl and never enter the repository.

Options: --only-public (skip sensitive items), --limit N (first N items), --model <part of an id>,
--use-drafts (use machine drafts where the linguist has not finished; for tests only, never for the real run).
"""
import datetime, threading
from concurrent.futures import ThreadPoolExecutor
from .common import DATA, append_jsonl, chat, config, is_sensitive, items, private_dir, read_jsonl, slug, store

lock = threading.Lock()


def done_keys(model_id):
    keys = set()
    for base in (DATA, private_dir()):
        keys |= {r['key'] for r in read_jsonl(base / 'responses' / f'{slug(model_id)}.jsonl') if r.get('answer')}
    return keys


def main(args):
    cfg = config()
    allit = list(items().values())  # file order, the same order draft uses
    if '--only-public' in args:
        allit = [r for r in allit if not is_sensitive(r)]
    if '--limit' in args:
        allit = allit[:int(args[args.index('--limit') + 1])]
    models = cfg['models']
    if '--model' in args:
        models = [m for m in models if args[args.index('--model') + 1] in m['id']]
    drafts = '--use-drafts' in args
    for m in models:
        have = done_keys(m['id'])
        jobs = []
        for it in allit:
            ka = it.get('prompt_ka') or (it.get('prompt_ka_draft') if drafts else '')
            runs = cfg['runs_sensitive'] if is_sensitive(it) else cfg['runs_non_sensitive']
            for lang, text in (('en', it['prompt_en']), ('ka', ka)):
                if not text:
                    continue
                for run in range(1, runs + 1):
                    key = f"{it['id']}|{lang}|{run}"
                    if key not in have:
                        jobs.append((it, lang, run, key, text))
        print(f"{m['id']}: {len(jobs)} calls to make ({len(have)} already done)")

        def one(job):
            it, lang, run, key, text = job
            answer, meta = chat(m, [{'role': 'user', 'content': text}], cfg['max_tokens_answer'], cfg['temperature'])
            rec = {'key': key, 'item': it['id'], 'lang': lang, 'run': run, 'model': m['id'],
                   'at': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
                   'prompt_source': 'final' if it.get('prompt_ka') or lang == 'en' else 'draft',
                   'answer': answer, **meta}
            with lock:
                append_jsonl(store(it, 'responses') / f"{slug(m['id'])}.jsonl", rec)
            return bool(answer)

        with ThreadPoolExecutor(cfg['workers']) as ex:
            ok = sum(ex.map(one, jobs))
        print(f"  {ok}/{len(jobs)} answered; failures are retried on the next run")
