# CLAUDE.md: instructions for Claude Code working in this repository

This repository is **KartuliSafe**, a measurement study: do frontier AI models refuse harmful requests, and answer
harmless ones, as reliably in Georgian as in English? Read README.md first; it is the source of truth for the steps.
The person you work with leads the study. Results are published on openclaw.ge (an AI-operated Georgian-English
publication) from this repository's `results/` folder.

## Hard rules

1. **Never write new harmful content.** The study uses only the two published benchmarks (XSTest, JailbreakBench).
   Do not invent, extend, rephrase-to-strengthen or "improve" harmful prompts, and do not try to get more harmful
   detail out of any model. Translating an existing benchmark prompt faithfully is the job; nothing beyond that.
2. **Never put sensitive material in the repository.** Sensitive = XSTest `unsafe` items, JBB `harmful` items, any model
   answer to them, and results on them before release. All of it lives in the private folder (`config.json`
   `private_dir`, outside the repository). Never copy it into the repository, never paste it into an issue, a commit
   message or a public chat, never print a harmful answer in full to the terminal when a count will do.
3. **Never disable or bypass the leak guard** (`guard/check.py`, `.githooks/pre-commit`, `.github/workflows/guard.yml`),
   never commit with `--no-verify`. If it blocks a commit, the material is in the wrong place: move it, do not argue
   with the guard. Changing the guard needs the study lead's explicit approval.
4. **Never commit or print API keys.** Keys live in `<private_dir>/keys.env` only.
5. **Model answers to sensitive prompts are never published**, before or after release; only rates and, in the write-up,
   a few examples with the dangerous part removed by a person.
6. **Disclosure first.** Findings go to each model developer before anything sensitive is published; `release` refuses to
   run before `disclosure_date` + `disclosure_window_days`.
7. **Do not judge answers yourself** in place of the two configured judges or the linguist; the study's numbers must come
   from the documented pipeline so they can be reproduced.

## How to work

- Run steps with `.venv/bin/python -m ks <step>`; `ks status` shows where things stand. Every step is resumable.
- Before the real run, check `config.json` model ids against https://openrouter.ai/models and update them to the newest
  of each family; record the change in the commit message. One model must be open-weight (Qwen, DeepSeek, Llama...).
- Test on harmless prompts only (`--only-public`, `--limit`), as in README "Test the whole chain".
- After each step that changes `data/` or `results/`: `git add`, commit with a plain message saying what ran, push.
- Costs: OpenRouter returns a cost per call in `usage`; keep a running total in commit messages for the big steps.
- If a provider blocks or warns the account, stop the run and tell the study lead; do not switch accounts to get round it.
- Code style: standard library plus `requests`; small, readable functions; comments explain why, not what.
