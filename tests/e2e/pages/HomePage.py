#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Home Page Object Model class for the home page functionality.
"""

from playwright.async_api import Page, expect
from .BasePage import BasePage


class HomePage(BasePage):
    """Page object for the home page."""
    
    def __init__(self, page: Page):
        """
        Initialize the home page.
        
        Args:
            page (Page): The Playwright page object
        """
        super().__init__(page)
        self.path = "/"
        
        # Locators
        self.welcome_message_locator = "h2"
        self.profile_link_locator = "a[href='/profile']"
        self.my_missions_link_locator = "a[href='/my-quizzes']"
        self.new_mission_link_locator = "a[href='/new-exercise']"
    
    async def goto(self):
        """Navigate to the home page."""
        await super().goto(self.path)
    
    async def is_welcome_message_visible(self):
        """
        Check if the welcome message is visible.
        
        Returns:
            bool: True if the welcome message is visible, False otherwise
        """
        welcome_message = self.page.locator(self.welcome_message_locator)
        await expect(welcome_message).to_be_visible()
        return await welcome_message.is_visible()
    
    async def get_welcome_message_text(self):
        """
        Get the welcome message text.
        
        Returns:
            str: The welcome message text
        """
        return await self.page.locator(self.welcome_message_locator).inner_text()
    
    async def navigate_to_profile(self):
        """
        Navigate to the profile page.
        
        Returns:
            bool: True if successful, False otherwise
        """
        profile_link = self.page.locator(self.profile_link_locator)
        await expect(profile_link).to_be_visible()
        await profile_link.click()
        
        # Wait for navigation to the profile page
        await self.wait_for_url("/profile")
        return True
    
    async def navigate_to_my_missions(self):
        """
        Navigate to the my missions page.
        
        Returns:
            bool: True if successful, False otherwise
        """
        my_missions_link = self.page.locator(self.my_missions_link_locator)
        await expect(my_missions_link).to_be_visible()
        await my_missions_link.click()
        
        # Wait for navigation to the my missions page
        await self.wait_for_url("/my-quizzes")
        return True
    
    async def navigate_to_new_mission(self):
        """
        Navigate to the new mission page.
        
        Returns:
            bool: True if successful, False otherwise
        """
        new_mission_link = self.page.locator(self.new_mission_link_locator)
        await expect(new_mission_link).to_be_visible()
        await new_mission_link.click()
        
        # Wait for navigation to the new mission page
        await self.wait_for_url("/new-exercise")
        return True 