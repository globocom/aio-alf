
setup:
	@pip install -U -e .\[tests\]


clean:
	@find . -iname '*.pyc' -delete
	@rm -rf *.egg-info dist

test: clean
	@nosetests tests/ --with-coverage --cover-erase --cover-branches --cover-package=aioalf --nocapture
	@flake8 aioalf tests

version:
	@bin/new-version.sh

upload_release: clean
	@read -r -p "PyPI index-server: " PYPI_SERVER; \
		python setup.py -q sdist upload -r "$$PYPI_SERVER"

release: version upload_release

tox:
	@tox
