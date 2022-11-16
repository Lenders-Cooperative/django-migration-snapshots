install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt -r requirements_dev.txt

.PHONY: build ## Build bundle
build:
	python setup.py sdist

deploy:
	twine upload dist/*

lint:
	black --exclude "/migrations/,venv/" migration_snapshots setup.py

.PHONY: docs ## Generate docs
docs: install
	cd docs && make html

.PHONY: docs-live ## Generate docs with live reloading
docs-live: install
	cd docs && make livehtml

test:
	pytest
