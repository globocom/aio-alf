BUMP := 'patch'

setup:
	@pip install -U -e .\[tests\]


clean:
	@find . -iname '*.pyc' -delete
	@rm -rf *.egg-info dist

test: clean
	@nosetests tests/ --with-coverage --cover-erase --cover-branches --cover-package=aioalf --nocapture
	@flake8 aioalf tests

patch:
	@$(eval BUMP := 'patch')

minor:
	@$(eval BUMP := 'minor')

major:
	@$(eval BUMP := 'major')

bump:
	@bumpversion ${BUMP}
	@git push
	@git push --tags

release: clean
	@read -r -p "PyPI index-server: " PYPI_SERVER; \
		python setup.py -q sdist upload -r "$$PYPI_SERVER"

tox:
	@tox
