#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Name Page Object Model class for the trainer name input functionality.
"""

from playwright.async_api import Page, expect

from .BasePage import BasePage


class NamePage(BasePage):
    """Page object for the name input page."""
    
    def __init__(self, page: Page):
        """
        Initialize the name page.
        
        Args:
            page (Page): The Playwright page object
        """
        super().__init__(page)
        self.path = "/name"
        
        # Locators
        self.name_input_locator = "input#trainer-name"
        self.save_button_locator = "button.button-blue"
        self.title_locator = "h2"
    
    async def goto(self):
        """Navigate to the name input page."""
        await super().goto(self.path)
    
    async def is_title_visible(self):
        """
        Check if the name page title is visible.
        
        Returns:
            bool: True if the title is visible, False otherwise
        """
        title = self.page.locator(self.title_locator)
        await expect(title).to_be_visible()
        return await title.is_visible()
    
    async def get_title_text(self):
        """
        Get the name page title text.
        
        Returns:
            str: The title text
        """
        return await self.page.locator(self.title_locator).inner_text()
    
    async def enter_name(self, name: str):
        """
        Enter a trainer name.
        
        Args:
            name (str): The trainer name to enter
        
        Returns:
            bool: True if successful, False otherwise
        """
        name_input = self.page.locator(self.name_input_locator)
        await expect(name_input).to_be_visible()
        await name_input.fill(name)
        return True
    
    async def save_name(self):
        """
        Click the 'SAVE NAME' button.
        
        Returns:
            bool: True if successful, False otherwise
        """
        save_button = self.page.locator(self.save_button_locator)
        await expect(save_button).to_be_visible()
        await save_button.click()
        
        # Wait for navigation to the home page
        await self.wait_for_url("/")
        return True
    
    async def set_trainer_name(self, name: str):
        """
        Enter a trainer name and save it.
        
        Args:
            name (str): The trainer name to enter
        
        Returns:
            bool: True if successful, False otherwise
        """
        await self.enter_name(name)
        await self.save_name()
        return True 