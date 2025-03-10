#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base Page Object Model class that all other page objects will inherit from.
"""

import os
from playwright.async_api import Page


class BasePage:
    """Base class for all page objects."""
    
    def __init__(self, page: Page):
        """
        Initialize the base page.
        
        Args:
            page (Page): The Playwright page object
        """
        self.page = page
        self.base_url = os.environ.get("BASE_URL", "http://localhost:8080")
    
    async def goto(self, path: str = ""):
        """
        Navigate to a page.
        
        Args:
            path (str): The path to navigate to, relative to base_url
        """
        full_url = f"{self.base_url}{path}"
        await self.page.goto(full_url)
    
    async def get_title(self) -> str:
        """
        Get the page title.
        
        Returns:
            str: The page title
        """
        return await self.page.title()
    
    async def wait_for_url(self, path: str):
        """
        Wait for the URL to match the expected path.
        
        Args:
            path (str): The expected path, relative to base_url
        """
        full_url = f"{self.base_url}{path}"
        await self.page.wait_for_url(full_url)
    
    async def take_screenshot(self, name: str):
        """
        Take a screenshot of the page.
        
        Args:
            name (str): The name of the screenshot
        
        Returns:
            str: The path to the screenshot
        """
        path = f"tests/e2e/screenshots/{name}.png"
        await self.page.screenshot(path=path, full_page=True)
        return path 