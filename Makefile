.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[\.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: check
check: bandit black-check pip-check test ## Run all checks

.PHONY: bandit
bandit: ## Run bandit
	python -m bandit -r rechnung

.PHONY: black-check
black-check: ## Check code formatting
	python -m black --check rechnung

.PHONY: black
black: ## Format code
	python -m black rechnung

.PHONY: test
test: ## Run unittests
	pytest -v rechnung --cov=./ --cov-report term-missing:skip-covered $(PYTEST_ARGS)

.PHONY: pip-check
pip-check: ## Verify that all python package dependencies are met
	python -m pip check

.PHONY: upgrade
upgrade: ## Update all packages as available
	python -m pip install --upgrade-strategy eager --upgrade $$(cat requirements.in | sed -n 's/==.*$$//p')
	python -m pip install --upgrade-strategy eager --upgrade $$(cat requirements-dev.in | sed -n 's/==.*$$//p')

.PHONY: docs
docs:
	rm -f docs/rechnung.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs rechnung
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
