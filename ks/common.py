"""Shared helpers: configuration, paths, the public/private split, CSV/JSONL I/O and the API client."""
import csv, datetime, hashlib, json, os, re, sys, time, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, RESULTS, GUARD = ROOT / 'data', ROOT / 'results', ROOT / 'guard'
ITEM_FIELDS = ['id', 'set', 'label', 'sensitive', 'category', 'prompt_en', 'prompt_ka_draft', 'prompt_ka', 'adapted', 'note']


def config():
    return json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))


def private_dir():
    """Where everything sensitive lives. It must be OUTSIDE the repository, so git can never see it."""
    p = Path(os.environ.get('KS_PRIVATE') or config()['private_dir']).expanduser().resolve()
    if p == ROOT or ROOT in p.parents:
        sys.exit(f'Refusing to run: the private folder {p} is inside the repository {ROOT}. '
                 'Set private_dir in config.json (or KS_PRIVATE) to a folder outside it.')
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_keys():
    """API keys come from the environment or from <private_dir>/keys.env, never from the repository."""
    f = private_dir() / 'keys.env'
    if f.exists():
        for line in f.read_text().splitlines():
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def slug(model_id):
    return re.sub(r'[^a-z0-9.]+', '-', model_id.lower()).strip('-')


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def read_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def append_jsonl(path, rec):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def items():
    """All items, public and private, keyed by id."""
    rows = read_csv(DATA / 'items_public.csv') if (DATA / 'items_public.csv').exists() else []
    priv = private_dir() / 'items_private.csv'
    if priv.exists():
        rows += read_csv(priv)
    return {r['id']: r for r in rows}


def save_items(all_items):
    """Write items back to the right side of the split."""
    rows = list(all_items.values())
    write_csv(DATA / 'items_public.csv', [r for r in rows if not is_sensitive(r)], ITEM_FIELDS)
    write_csv(private_dir() / 'items_private.csv', [r for r in rows if is_sensitive(r)], ITEM_FIELDS)


def is_sensitive(item):
    return str(item.get('sensitive')) == '1'


def store(item, kind):
    """Folder for a record about this item: public data/<kind>/ or private <private_dir>/<kind>/."""
    return (private_dir() if is_sensitive(item) else DATA) / kind


def normalize(text):
    t = unicodedata.normalize('NFC', str(text)).lower()
    t = re.sub(r'\s+', ' ', t).strip().strip('"\'„“”.,;:!?()[] ')
    return t


def fingerprint(text):
    return hashlib.sha256(normalize(text).encode('utf-8')).hexdigest()


def today():
    return datetime.date.today()


def released():
    """True once release.py has run: the disclosure window is over."""
    return (GUARD / 'RELEASED').exists()


# ---------------- API client ----------------
OPENROUTER = 'https://openrouter.ai/api/v1/chat/completions'
ANTHROPIC = 'https://api.anthropic.com/v1/messages'


def chat(model, messages, max_tokens, temperature=0.0, schema=None, tries=5):
    """One chat call with retries. Returns (text, meta). model is a config entry: {id, via, anthropic_model?}."""
    import requests
    load_keys()
    last = ''
    for attempt in range(tries):
        try:
            if model.get('via') == 'anthropic':
                key = os.environ.get('ANTHROPIC_API_KEY') or sys.exit('ANTHROPIC_API_KEY missing (see README, Keys)')
                system = '\n'.join(m['content'] for m in messages if m['role'] == 'system')
                msgs = [m for m in messages if m['role'] != 'system']
                body = {'model': model.get('anthropic_model') or sys.exit(f"anthropic_model not set for {model['id']}"),
                        'max_tokens': max_tokens, 'temperature': temperature, 'messages': msgs}
                if system:
                    body['system'] = system
                r = requests.post(ANTHROPIC, json=body, timeout=300,
                                  headers={'x-api-key': key, 'anthropic-version': '2023-06-01',
                                           'content-type': 'application/json'})
                if r.status_code in (429, 500, 502, 503, 529):
                    raise RuntimeError(f'{r.status_code}: {r.text[:200]}')
                r.raise_for_status()
                d = r.json()
                text = ''.join(b.get('text', '') for b in d.get('content', []) if b.get('type') == 'text')
                meta = {'model_returned': d.get('model'), 'provider': 'anthropic', 'usage': d.get('usage'),
                        'stop': d.get('stop_reason')}
            else:
                key = os.environ.get('OPENROUTER_API_KEY') or sys.exit('OPENROUTER_API_KEY missing (see README, Keys)')
                body = {'model': model['id'], 'messages': messages, 'max_tokens': max_tokens,
                        'temperature': temperature, 'usage': {'include': True}}
                if schema:
                    body['response_format'] = {'type': 'json_schema',
                                               'json_schema': {'name': 'verdict', 'strict': True, 'schema': schema}}
                r = requests.post(OPENROUTER, json=body, timeout=300,
                                  headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
                                           'X-Title': 'KartuliSafe evaluation'})
                if r.status_code in (408, 429, 500, 502, 503, 504):
                    raise RuntimeError(f'{r.status_code}: {r.text[:200]}')
                r.raise_for_status()
                d = r.json()
                if 'error' in d:
                    raise RuntimeError(str(d['error'])[:200])
                ch = d['choices'][0]
                text = ch['message'].get('content') or ''
                meta = {'model_returned': d.get('model'), 'provider': d.get('provider'), 'usage': d.get('usage'),
                        'stop': ch.get('finish_reason')}
            if not text.strip() and attempt < tries - 1:
                # reasoning models can spend the whole budget thinking: raise the limit and retry
                max_tokens = int(max_tokens * 1.6)
                last = f'empty answer (stop={meta.get("stop")})'
                continue
            return text, meta
        except Exception as e:  # network errors, rate limits, provider outages
            last = str(e)[:300]
            time.sleep(min(60, 4 * 2 ** attempt))
    return '', {'error': last}
