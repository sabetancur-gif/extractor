install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && python src/app/app.python

test:
	. .venv/bin/activate && pytest