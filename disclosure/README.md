# Disclosure: telling the developers before publishing

When `ks analyze` has produced the sensitive results, and before anything sensitive is published:

1. For each model developer, send `template.md` filled in with that developer's own numbers only (from
   `<private_dir>/results/tables_sensitive.md`), through their official channel. Find the channel on their own site
   at the time of sending (security or responsible-disclosure page, or the safety contact named there); record it in
   `log.md` with the date. Anthropic's policy: https://www.anthropic.com/responsible-disclosure-policy
   Developers to cover: every model in `config.json` (for the open-weight model, its publisher).
2. Send examples privately if they ask (a few prompts, with their own model's answer). Never send another developer's
   results.
3. Set `disclosure_date` in `config.json` to the date of the last notice. `ks release` will refuse to publish before
   that date plus 30 days (`disclosure_window_days`).
4. If a developer asks for more time with a good reason (a fix in progress), the study lead decides; extend
   `disclosure_window_days` in `config.json` and note it in `log.md`.

Safe and benign results (over-refusal) are not sensitive and can be published at any time.
