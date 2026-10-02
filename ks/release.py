"""After the disclosure window: publish the Georgian versions of the sensitive prompts and the harmful-side results.

Refuses unless config.json has a disclosure_date and today is at least disclosure_window_days after it.
Copies the sensitive items (prompts only: never model answers) to data/items_sensitive.csv and the sensitive
results to results/, then writes guard/RELEASED so the leak guard allows those prompts from now on.
Model answers to sensitive prompts are never released, before or after.
"""
import datetime, shutil
from .common import DATA, GUARD, RESULTS, config, is_sensitive, items, private_dir, today, write_csv


def main(args):
    cfg = config()
    if not cfg.get('disclosure_date'):
        print('config.json has no disclosure_date yet (the day the AI companies were told). Nothing released.')
        return
    opens = datetime.date.fromisoformat(cfg['disclosure_date']) + datetime.timedelta(days=cfg['disclosure_window_days'])
    if today() < opens:
        print(f'The disclosure window is still open until {opens}. Nothing released.')
        return
    sens = [r for r in items().values() if is_sensitive(r)]
    write_csv(DATA / 'items_sensitive.csv', sens, ['id', 'set', 'label', 'category', 'prompt_en', 'prompt_ka', 'adapted', 'note'])
    for f in ('summary_sensitive.json', 'tables_sensitive.md'):
        src = private_dir() / 'results' / f
        if src.exists():
            shutil.copy(src, RESULTS / f)
    (GUARD / 'RELEASED').write_text(f'released {today()} (disclosure {cfg["disclosure_date"]})\n')
    print(f'Released: data/items_sensitive.csv ({len(sens)} prompts) and the sensitive results. '
          'Review, then commit and push as usual. Model answers stay private.')
