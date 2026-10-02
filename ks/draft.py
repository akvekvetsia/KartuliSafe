"""Step 2: machine-draft a Georgian version of every prompt. The linguist reviews every draft in step 3.

Options: --only-public (skip sensitive items), --limit N (first N items, for a test), --redo (overwrite drafts).
If the translating model declines an item, the draft is left empty and marked; the linguist translates it by hand.
"""
from concurrent.futures import ThreadPoolExecutor
from .common import GUARD, chat, config, fingerprint, is_sensitive, items, save_items

SYSTEM = ('You translate short test prompts from English into natural, idiomatic Georgian for an AI-safety evaluation '
          'run by researchers. Translate the meaning faithfully, keep the register, and keep any double meaning as '
          'close as Georgian allows. Do not answer, judge, soften or comment on the prompt. Output only the Georgian text.')


def looks_declined(text):
    t = text.strip().lower()
    return (not t) or t.startswith(("i can't", 'i cannot', "i'm sorry", 'sorry', 'i won')) or not any('ა' <= c <= 'ჿ' for c in t)


def main(args):
    cfg = config()
    allit = items()
    todo = [r for r in allit.values() if ('--redo' in args or not r.get('prompt_ka_draft'))
            and not ('--only-public' in args and is_sensitive(r))]
    if '--limit' in args:
        todo = todo[:int(args[args.index('--limit') + 1])]
    print(f'drafting {len(todo)} items with {cfg["translator"]["id"]}')

    def one(r):
        text, meta = chat(cfg['translator'], [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': r['prompt_en']}],
                          max_tokens=2000)
        if looks_declined(text):
            r['prompt_ka_draft'] = ''
            r['note'] = (r.get('note') or '') + ' [machine draft declined or failed: translate by hand]'
        else:
            r['prompt_ka_draft'] = text.strip()
        return r

    with ThreadPoolExecutor(cfg['workers']) as ex:
        for r in ex.map(one, todo):
            allit[r['id']] = r
    save_items(allit)
    fp = set((GUARD / 'fingerprints.txt').read_text().split()) if (GUARD / 'fingerprints.txt').exists() else set()
    fp |= {fingerprint(r['prompt_ka_draft']) for r in allit.values() if is_sensitive(r) and r.get('prompt_ka_draft')}
    (GUARD / 'fingerprints.txt').write_text('\n'.join(sorted(fp)) + '\n')
    declined = sum(1 for r in todo if not r['prompt_ka_draft'])
    print(f'done; {declined} left for the linguist to translate by hand; guard fingerprints updated')
