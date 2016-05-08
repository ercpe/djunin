TARGET?=tests

test_default_python:
	cd src && PYTHONPATH="..:." DJANGO_SETTINGS_MODULE="test_settings" python manage.py test -v1

test_py2:
	@echo Executing test with python2
	cd src && PYTHONPATH="..:." DJANGO_SETTINGS_MODULE="test_settings" python2 manage.py test

test_py3:
	@echo Executing test with python3
	cd src && PYTHONPATH="..:." DJANGO_SETTINGS_MODULE="test_settings" python3 manage.py test -v1

test: test_py2 test_py3

compile:
	@echo Compiling python code
	python -m compileall src/

compile_optimized:
	@echo Compiling python code optimized
	python -O -m compileall src/

coverage:
	coverage erase
	cd src && PYTHONPATH="..:." DJANGO_SETTINGS_MODULE="test_settings" coverage run --source='.' --rcfile ../.coveragerc manage.py test
	cd src && coverage report -m

travis: compile compile_optimized test_default_python coverage
