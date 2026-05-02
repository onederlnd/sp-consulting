.PHONY: run test lint security migrate shell install

run:
	flask run

test:
	pytest tests/ --cov=app --cov-report=term-missing

lint:
	flake8 app/ tests/

security:
	bandit -r app/
	safety check -r requirements/base.txt

migrate:
	flask --app wsgi db upgrade

shell:
	flask --app wsgi shell

install:
	pip install -r requirements/dev.txt

seed:
	flask --app wsgi seed

create-user:
	flask --app wsgi create-user
