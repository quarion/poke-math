#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Profile Page Object Model class for the profile page functionality.
"""

from playwright.async_api import Page, expect
from .BasePage import BasePage


class ProfilePage(BasePage):
    """Page object for the profile page."""
    
    def __init__(self, page: Page):
        """
        Initialize the profile page.
        
        Args:
            page (Page): The Playwright page object
        """
        super().__init__(page)
        self.path = "/profile"
        
        # Locators
        self.title_locator = "h2"
        self.error_message_locator = "body"
    
    async def goto(self):
        """Navigate to the profile page."""
        await super().goto(self.path)
    
    async def is_title_visible(self):
        """
        Check if the profile page title is visible.
        
        Returns:
            bool: True if the title is visible, False otherwise
        """
        try:
            title = self.page.locator(self.title_locator)
            await expect(title).to_be_visible(timeout=5000)
            return await title.is_visible()
        except:
            return False
    
    async def get_title_text(self):
        """
        Get the profile page title text.
        
        Returns:
            str: The title text
        """
        try:
            return await self.page.locator(self.title_locator).inner_text()
        except:
            return ""
    
    async def has_error(self):
        """
        Check if the profile page has an error.
        
        Returns:
            bool: True if there is an error, False otherwise
        """
        title = await self.get_title()
        return "500" in title or "404" in title or "Error" in title
    
    async def get_error_message(self):
        """
        Get the error message if there is an error.
        
        Returns:
            str: The error message
        """
        if await self.has_error():
            return await self.page.locator(self.error_message_locator).inner_text()
        return "" 