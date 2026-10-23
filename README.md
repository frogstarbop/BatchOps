# Introduction
BatchOps is a batch image processing application.

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
