.PHONY: install run test lint

install:
python -m venv .venv
. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

run:
. .venv/bin/activate && streamlit run app/app.py

test:
. .venv/bin/activate && pytest -q

lint:
. .venv/bin/activate && ruff check .
