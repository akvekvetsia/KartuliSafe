# KartuliSafe: does AI safety speak Georgian?

Do frontier AI models refuse harmful requests, and answer harmless ones, as reliably in Georgian as in English?
This repository is the whole study: the code, the method, the linguist's materials, the disclosure plan and the
public results. Project page: https://openclaw.ge/en/research/kartulisafe/ (Georgian: https://openclaw.ge/research/kartulisafe/).

*ქართულად: ეს რეპოზიტორია კვლევის სრული ნაკრებია: კოდი, მეთოდი, ლინგვისტის მასალები, გამჟღავნების გეგმა და საჯარო შედეგები.*

## The study in one paragraph

Two public test sets, [XSTest](https://huggingface.co/datasets/Paul/XSTest) (450 prompts: 250 safe, 200 unsafe
contrasts) and [JailbreakBench JBB-Behaviors](https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors)
(100 harmful behaviours, 100 benign twins), are machine-drafted into Georgian and reviewed item by item by a native
Georgian linguist. Five models (four frontier, one open-weight) answer every prompt in English and Georgian. Two
automatic judges from different developers classify every answer, and the linguist labels a sample of 400 Georgian
answers to measure how far the judges can be trusted in Georgian. The result: how often each model refuses harmless
requests or complies with harmful ones, Georgian against English. A [pilot](pilot/README.md) (40 safe prompts,
3 models, 240 answers) found no over-refusal in Georgian.

## What stays private (read this first)

Two kinds of material never enter this public repository before the disclosure window ends, and one never does:

| Material | Where it lives | Public when |
|---|---|---|
| Code, method, safe and benign prompts (EN and KA), their answers and labels, results on them | this repository | from day one |
| Sensitive prompts: XSTest unsafe contrasts and JBB harmful behaviours, in English and Georgian | the private folder | after the disclosure window, via `python -m ks release` |
| Results on sensitive prompts (rates by model and harm category) | the private folder | after the disclosure window, via `release` |
| Model answers to sensitive prompts | the private folder, then deleted (`purge`) | **never** |

The **private folder** is outside the repository (default `~/kartulisafe-private`, set in `config.json`); the code
refuses to run if it is pointed inside the repository. On top of that, a **leak guard** checks every commit and every
push for API keys, for any sensitive prompt (by fingerprint), and for any record about a sensitive item; it blocks the
commit if it finds one. It catches accidents. It cannot stop someone who copies a file by hand or switches it off, so
never do that.

## Setup (once, about 10 minutes)

Needs Python 3.10+ and git.

```
git clone <this repository>
cd kartulisafe
sh setup.sh
```

`setup.sh` creates `.venv`, installs the one dependency, switches on the leak guard, creates the private folder and a
`keys.env` file in it. Put your keys there (never in the repository):

- `OPENROUTER_API_KEY`: one key for every model, from https://openrouter.ai/settings/keys. Make a key just for this
  study and give it a spending limit.
- `ANTHROPIC_API_KEY`: only if Anthropic research credits were granted; then set `"via": "anthropic"` and the
  `anthropic_model` name for the Claude entries in `config.json` (credits only work on Anthropic's own API).

Check: `.venv/bin/python -m ks status`

## Running the study

Every step is one command, resumable: if it stops, run it again and it continues where it was.
Run them from the repository folder; `ks` below means `.venv/bin/python -m ks`.

| Step | Command | What it does | Time / cost (rough) |
|---|---|---|---|
| 0 | edit `config.json` | check the model names on openrouter.ai/models (they change), pick the newest of each family | 10 min |
| 1 | `ks prepare` | downloads both test sets, splits public and sensitive, updates the guard's fingerprints | 1 min, free |
| 2 | `ks draft` | machine-drafts all 650 prompts into Georgian | 20 min, ~$5 |
| 3 | `ks review export` | two sheets for the linguist, in the private folder | 1 min |
| — | linguist works | about 25 hours; see `linguist/` | 2–3 weeks |
| 4 | `ks review import` | reads her sheets back; reports anything still missing | 1 min |
| 5 | `ks run` | every model, every prompt, EN and KA (3 runs for safe and benign, 1 for sensitive) | a few hours, ~$300–450 |
| 6 | `ks judge` | two judges grade every answer | a few hours, ~$100–200 |
| 7 | `ks sample export`, then `ks sample import` | 400 Georgian answers for the linguist to label (c / p / r) | ~8 hours of her time |
| 8 | `ks analyze` | result tables: `results/` (public) and the private folder (sensitive) | 1 min |
| 9 | `ks purge --yes` | deletes the raw answers to sensitive prompts; keeps labels | 1 min |
| — | disclosure | send `disclosure/` notes to each developer; set `disclosure_date` in `config.json` | 1 day |
| 10 | `ks release` | after 30 days: publishes the sensitive prompts and results (never the answers) | 1 min |

Test the whole chain cheaply before the real run, on harmless prompts only:
`ks draft --only-public --limit 6`, `ks run --only-public --limit 3 --use-drafts --model sonnet`,
`ks judge --only-public`, `ks analyze`. Then delete `data/responses/`, `data/labels/` and `results/` and run
`ks prepare --force` to start clean.

After each step that changes `data/` or `results/`, commit and push as usual. The leak guard checks it.

## A note on the AI companies' rules

Sending known harmful requests to a model can trip its provider's safety systems, even for research. Keep the
sensitive run to one pass (already set), use a key made only for this study, and if a provider asks, explain the
study plainly: published benchmarks, a measurement, disclosure to them first, no harmful content published.

## Results format

`results/summary_public.json` and `results/tables_public.md` are what the openclaw.ge pages are built from; see
[RESULTS_FORMAT.md](RESULTS_FORMAT.md). Do not hand-edit them: re-run `ks analyze`.

## Credits and licences

XSTest: Röttger et al., NAACL 2024, CC-BY-4.0. JailbreakBench JBB-Behaviors: Chao et al., 2024, MIT. Code: MIT.
See [DATA_LICENSES.md](DATA_LICENSES.md).
