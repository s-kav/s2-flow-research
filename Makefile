.PHONY: install test smoke massive verify-massive lint

install:
	python -m pip install -e .

test:
	python -m pytest

smoke:
	python scripts/reproduce_all.py

massive:
	python scripts/massive_verification.py --output-dir results/massive

verify-massive:
	python scripts/verify_campaign.py results/massive

lint:
	python -m compileall -q src scripts tests
