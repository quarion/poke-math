#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper functions for end-to-end testing.
"""

import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from tests.e2e.pages import LoginPage, NamePage


async def setup_browser(headless: bool = None):
    """
    Set up a browser for testing.
    
    Args:
        headless (bool): Whether to run the browser in headless mode
    
    Returns:
        tuple: A tuple containing the playwright instance, browser, context, and page
    """
    # Use the environment variable if headless is not specified
    if headless is None:
        headless_str = os.environ.get("HEADLESS", "false").lower()
        headless = headless_str == "true"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context()
    page = await context.new_page()
    return playwright, browser, context, page


async def teardown_browser(playwright, browser):
    """
    Tear down a browser after testing.
    
    Args:
        playwright: The playwright instance
        browser: The browser instance
    """
    await browser.close()
    await playwright.stop()


async def login_as_guest(page: Page, trainer_name: str = "TestTrainer"):
    """
    Log in as a guest and set a trainer name.
    
    Args:
        page (Page): The Playwright page object
        trainer_name (str): The trainer name to use
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Navigate to the login page
    login_page = LoginPage(page)
    await login_page.goto()
    
    # Continue as guest
    await login_page.continue_as_guest()
    
    # Set trainer name
    name_page = NamePage(page)
    await name_page.set_trainer_name(trainer_name)
    
    return True


def ensure_screenshots_dir():
    """
    Ensure the screenshots directory exists.
    
    Returns:
        str: The path to the screenshots directory
    """
    screenshots_dir = os.path.join("tests", "e2e", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    return screenshots_dir


def generate_screenshot_name(test_name: str):
    """
    Generate a screenshot name based on the test name and current timestamp.
    
    Args:
        test_name (str): The name of the test
    
    Returns:
        str: The screenshot name
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{test_name}_{timestamp}" 