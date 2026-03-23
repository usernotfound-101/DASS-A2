# DASS A2 - Run Guide

This repository contains three parts:

1. `blackbox`: QuickCart API black-box tests
2. `integration`: StreetRaceManager integration code + tests
3. `whitebox`: MoneyPoly white-box code + tests

## 1. Prerequisites

- Python 3.10+ (recommended)
- `pip`

From the repository root, install common test dependencies:

```bash
python3 -m pip install pytest requests
```

Optional (recommended) virtual environment setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pytest requests
```

## 2. Integration Part (StreetRaceManager)

### Run the CLI app

```bash
cd integration/code
python main.py
```

You can also run directly:

```bash
cd integration/code
python streetracemanager/system.py
```

### Run integration tests

```bash
cd integration/code
pytest -q streetracemanager/tests
```

Alternative test location:

```bash
cd integration
PYTHONPATH=code pytest -q tests
```

## 3. Whitebox Part (MoneyPoly)

### Run the game

```bash
cd whitebox/code/moneypoly
python main.py
```

### Run white-box tests

```bash
cd whitebox/code/moneypoly
pytest -q tests
```

Alternative test location:

```bash
cd whitebox
PYTHONPATH=code/moneypoly pytest -q tests
```

## 4. Blackbox Part (QuickCart API Tests)

These tests call a running QuickCart API service.

Current test configuration expects:

- Base URL: `http://localhost:8080/api/v1`
- Header `X-Roll-Number`
- Header `X-User-ID` for user endpoints

If your API is running elsewhere, update `BASE_URL` in:

- `blackbox/tests/test_quickcart_blackbox.py`

### Run black-box tests

From repository root:

```bash
pytest -q blackbox/tests/test_quickcart_blackbox.py
```

Or run all tests in the blackbox folder:

```bash
pytest -q blackbox/tests
```

## 5. Run Everything (where applicable)

If your environment and API are set up, you can run all tests with:

```bash
pytest -q
```

Note: This executes all test suites across the workspace and may include failing cases that depend on API seed data or service behavior.
