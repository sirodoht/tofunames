# tofunames

domain names for hackers.

AGPL.

## Development

This is a standard Django application.

Setup and run:

```sh
# setup venv
python3 -m venv .venv
source .venv/bin/activate

# setup env variables
cp .envrc.example .envrc
source .envrc

# install dependencies
pip install -r requirements.txt
```

Run development server:

```sh
python manage.py runserver
```

Format:

```sh
ruff format
```

Lint:

```sh
ruff check --fix
```

## Deploy

Every commit on branch `main` auto-deploys. To deploy manually:

```sh
cd ansible/
ansible-playbook playbook.yaml -v
```