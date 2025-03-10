#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Login Page Object Model class for the login functionality.
"""

from playwright.async_api import Page, expect
from .BasePage import BasePage


class LoginPage(BasePage):
    """Page object for the login page."""
    
    def __init__(self, page: Page):
        """
        Initialize the login page.
        
        Args:
            page (Page): The Playwright page object
        """
        super().__init__(page)
        self.path = "/login"
        
        # Locators
        self.guest_button_locator = "button.firebaseui-idp-anonymous"
        self.google_button_locator = "button.firebaseui-idp-google"
        self.title_locator = "h2"
    
    async def goto(self):
        """Navigate to the login page."""
        await super().goto(self.path)
    
    async def is_title_visible(self):
        """
        Check if the login page title is visible.
        
        Returns:
            bool: True if the title is visible, False otherwise
        """
        title = self.page.locator(self.title_locator)
        await expect(title).to_be_visible()
        return await title.is_visible()
    
    async def get_title_text(self):
        """
        Get the login page title text.
        
        Returns:
            str: The title text
        """
        return await self.page.locator(self.title_locator).inner_text()
    
    async def continue_as_guest(self):
        """
        Click the 'Continue as guest' button.
        
        Returns:
            bool: True if successful, False otherwise
        """
        guest_button = self.page.locator(self.guest_button_locator)
        await expect(guest_button).to_be_visible()
        await guest_button.click()
        
        # Wait for navigation to the name input page
        await self.wait_for_url("/name")
        return True
    
    async def sign_in_with_google(self):
        """
        Click the 'Sign in with Google' button.
        
        Returns:
            bool: True if successful, False otherwise
        """
        google_button = self.page.locator(self.google_button_locator)
        await expect(google_button).to_be_visible()
        await google_button.click()
        return True 