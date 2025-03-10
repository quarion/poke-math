# End-to-End Testing with Playwright

This directory contains Playwright scripts for end-to-end testing of the Pokemath application.

## Prerequisites

Before running these tests, you need to install Playwright for Python:

```bash
pip install playwright
python -m playwright install
```

## Running the Tests

### Using the PowerShell Script (Recommended)

The easiest way to run the tests is to use the PowerShell script:

```powershell
.\tools\run_e2e_tests.ps1
```

This will:
1. Install Playwright if it's not already installed
2. Check if the application is running and start it if needed
3. Run all the e2e tests

You can also specify custom options:

```powershell
.\tools\run_e2e_tests.ps1 -TestPath "tests/e2e/login" -BaseUrl "http://localhost:5000" -Headless
```

### Running Tests Manually

If you prefer to run the tests manually:

1. Start the application:
   ```bash
   $env:FLASK_ENV="development"; python -m src.app
   ```

2. Run the tests:
   ```bash
   python -m pytest tests/e2e -v
   ```

## Fixtures

The tests use pytest fixtures for setup and teardown:

- `browser_context`: Sets up a browser context for testing
- `authenticated_browser_context`: Sets up an authenticated browser context
- `page`: Gets the page from the browser context
- `authenticated_page`: Gets the authenticated page from the browser context

## Screenshots

Screenshots are automatically taken during tests and saved to the `screenshots` directory. Each screenshot is named with the test name and a timestamp. 