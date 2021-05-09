VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python3

.PHONY: producer clean lint

venv: $(VENV_NAME)/bin/activate

$(VENV_NAME)/bin/activate: requirements-test.txt requirements.txt
	python -m virtualenv -p python3 $(VENV_NAME)
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -r requirements-test.txt -r requirements.txt
	touch $(VENV_NAME)/bin/activate

clean:
	rm -rf ./$(VENV_NAME)
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf ./build
	rm -rf ./dist

lint: venv
	${PYTHON} -m black *.py
	${PYTHON} -m autoflake --in-place --recursive --remove-all-unused-imports *.py
	${PYTHON} -m mypy --ignore-missing-imports *.py
