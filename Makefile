BRANCH=master

clean:
	rm -rf dist/ build/

package:
	pip install wheel
	python setup.py sdist bdist_wheel

publish: package
	test -n "$(shell git branch | grep '* ${BRANCH}')"
	pip install twine
	twine upload dist/*

.PHONY: clean package publish
