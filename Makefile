TARGET?=tests

test_default_python:
	PYTHONPATH="." DJANGO_SETTINGS_MODULE="test_settings" python manage.py test -v1

test_py2:
	@echo Executing test with python2
	PYTHONPATH="." DJANGO_SETTINGS_MODULE="test_settings" python2 manage.py test

test_py3:
	@echo Executing test with python3
	PYTHONPATH="." DJANGO_SETTINGS_MODULE="test_settings" python3 manage.py test -v1

test: test_py2 test_py3

compile:
	@echo Compiling python code
	python -m compileall djunin

compile_optimized:
	@echo Compiling python code optimized
	python -O -m compileall djunin

clean:
	find -name "*.py?" -delete
	rm -f coverage.xml .coverage testresults.xml
	rm -fr htmlcov dist amavisvt.egg-info cache .cache

coverage:
	coverage erase
	DJANGO_SETTINGS_MODULE="test_settings" coverage run --source='djunin' --rcfile .coveragerc manage.py test
	coverage xml -i
	coverage report -m

sonar:
#	/usr/local/bin/sonar-scanner/bin/sonar-scanner -Dsonar.projectVersion=$(VERSION)
	/usr/local/bin/sonar-scanner/bin/sonar-scanner

travis: compile compile_optimized test_default_python coverage
jenkins: travis sonar
