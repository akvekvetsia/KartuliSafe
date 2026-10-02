#!/bin/sh
# One-time setup on a new computer: Python environment, the leak guard, and the private folder.
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install --quiet -r requirements.txt
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
PRIV=$(.venv/bin/python -c "from ks.common import private_dir; print(private_dir())")
if [ ! -f "$PRIV/keys.env" ]; then
  printf '# API keys for KartuliSafe. This file is outside the repository and must stay there.\nOPENROUTER_API_KEY=\nANTHROPIC_API_KEY=\n' > "$PRIV/keys.env"
  chmod 600 "$PRIV/keys.env"
fi
echo "Ready. Private folder: $PRIV"
echo "Put your API keys in $PRIV/keys.env, then run:  .venv/bin/python -m ks status"
