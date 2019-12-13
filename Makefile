.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[\.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: check
check: bandit black-check pip-check test ## Run all checks

.PHONY: bandit
bandit: ## Run bandit
	python -m bandit -r rechnung

.PHONY: style-check
style-check: ## Check code formatting
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
	python -m black --check .

.PHONY: black
black: ## Format code
	python -m black rechnung

.PHONY: test
test: ## Run unittests
	pytest -v rechnung --cov=./ --cov-report term-missing:skip-covered $(PYTEST_ARGS)

.PHONY: git-flow
git-flow: ## Initialize git-flow
	@if [ $$(git-flow version 2>/dev/null | grep -c AVH) -lt 1 ]; then \
		echo "You need to have gitflow-avh installed" >&2; \
		exit 1; \
	fi
	grep -q '^\[gitflow ' .git/config || git-flow init -d

.PHONY: pip-sync
pip-sync: ## Install all dev dependencies
	python -m pip install "$$(grep '^pip-tools=' requirements-dev.txt)"
	python -m piptools sync requirements-dev.txt

.PHONY: develop
develop: git-flow pip-sync pip-check ## Setup repository for development

.PHONY: pip-check
pip-check: ## Verify that all python package dependencies are met
	python -m pip check

# Sets the annotation content for the files generated by pip-compile
export CUSTOM_COMPILE_COMMAND := make update-requirements

.PHONY: update-requirements
update-requirements: ## Regenerate requirements.txt with newest versions of dependencies
	python -m piptools compile --rebuild --upgrade --quiet requirements.in
	python -m piptools compile --rebuild --upgrade --quiet requirements-dev.in

.PHONY: upgrade
upgrade: ## Update all packages as available
	python -m pip install --upgrade-strategy eager --upgrade $$(cat requirements.in | sed -n 's/==.*$$//p')
	python -m pip install --upgrade-strategy eager --upgrade $$(cat requirements-dev.in | sed -n 's/==.*$$//p')

.PHONY: install
install: ## Install the package
	pip install -e .

.PHONY: uninstall
uninstall: ## Remove the currently installed version of rechnung
	pip uninstall -y rechnung

.PHONY: reinstall
reinstall: uninstall install 

.PHONY: docs
docs:
	rm -f docs/rechnung.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs rechnung
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
