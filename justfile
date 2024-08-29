set shell := ["zsh", "-c"]

VENV_NAME := "venv"
CURDIR := invocation_directory()
VENV_ACTIVATE := CURDIR / VENV_NAME + "/bin/activate"
PYTHON_VERSION := "python3.12"
PYTHON := CURDIR / VENV_NAME + "/bin/" + PYTHON_VERSION
REQUIREMENTS := "requirements.txt"

create_venv:
    test -d {{VENV_NAME}} || virtualenv -p {{PYTHON_VERSION}} {{VENV_NAME}}
    source {{VENV_ACTIVATE}};  pip install -Ur {{REQUIREMENTS}}

ipython:
	{{VENV_NAME}}/bin/ipython
