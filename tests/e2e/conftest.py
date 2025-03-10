#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pytest fixtures for end-to-end testing.
"""

import os
import pytest
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from tests.e2e.utils.test_helpers import setup_browser, teardown_browser, login_as_guest, ensure_screenshots_dir


# Ensure screenshots directory exists
ensure_screenshots_dir()


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def browser_context():
    """
    Set up a browser context for testing.
    
    Yields:
        tuple: A tuple containing the playwright instance, browser, context, and page
    """
    # Get headless mode from environment variable
    headless_str = os.environ.get("HEADLESS", "false").lower()
    headless = headless_str == "true"
    
    playwright, browser, context, page = await setup_browser(headless=headless)
    yield playwright, browser, context, page
    await teardown_browser(playwright, browser)


@pytest.fixture(scope="function")
async def authenticated_browser_context(browser_context):
    """
    Set up an authenticated browser context for testing.
    
    Args:
        browser_context: The browser context fixture
    
    Yields:
        tuple: A tuple containing the playwright instance, browser, context, and page
    """
    playwright, browser, context, page = browser_context
    
    # Log in as guest
    await login_as_guest(page, trainer_name="TestTrainer")
    
    yield playwright, browser, context, page


@pytest.fixture(scope="function")
async def page(browser_context):
    """
    Get the page from the browser context.
    
    Args:
        browser_context: The browser context fixture
    
    Returns:
        Page: The Playwright page object
    """
    _, _, _, page = browser_context
    return page


@pytest.fixture(scope="function")
async def authenticated_page(authenticated_browser_context):
    """
    Get the authenticated page from the browser context.
    
    Args:
        authenticated_browser_context: The authenticated browser context fixture
    
    Returns:
        Page: The authenticated Playwright page object
    """
    _, _, _, page = authenticated_browser_context
    return page