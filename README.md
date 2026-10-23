# Introduction
BatchOps is a batch image processing application.
# Application

## Running by generating the Installer
You can only generate the installer if you have the [Inno Setup Application](https://jrsoftware.org/isdl.php).

Open the BatchOps.iss file in the Inno Setup Application, then press F9 to generate the installer. From there, the installer will open itself and you can use the wizard to install the application

This will be present when we convert the project to an Open Source application upon completion, however file size limits on GitLab mean that we cannot include the installer itself.



## Running directly using python 

Running in a venv, you need to install requirements.txt

```py
pip install -r requirements.txt
```

From there, the entry point of the application is `widget.py`, so you can execute with

```
python widget.py
```

While in the project directory

The imports will load first, which may take a small amount of time. There will be a loading window throughout this process, so just wait and the home page will show with time. 


# Tests
This project uses python builtin `unittest` library for writing tests.<br>
Test scripts and test related related scripts are stored in the `tests/` directory.<br>

## Running tests
### 1. Open the tests directory

```bash
cd tests
```
### 2. Run the tests

Tests can be run per process-step or all at once.

#### 2.1. All the tests

```bash
python3 -m unittest discover
```

#### 2.2. One specific test file

For example, compression tests:
```bash
python3 test_compression.py
```

