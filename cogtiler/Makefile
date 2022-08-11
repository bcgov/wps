ifdef VIRTUAL_ENV
POETRY_RUN=
else
POETRY_RUN=poetry run
endif

define run-api
	# function to run api	
	${1} uvicorn cogtiler.main:app --host 0.0.0.0 --reload --port 8090;
endef

run:
	${call run-api,$(POETRY_RUN)}

notebook:
	# Run jupyter notebooks.
	POSTGRES_HOST=localhost PYTHONPATH=$(shell pwd) JUPYTER_PATH=$(shell pwd) poetry run jupyter notebook --ip 0.0.0.0
