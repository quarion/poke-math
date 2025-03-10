#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the profile page functionality.
"""

import pytest
from playwright.async_api import Page, expect

from tests.e2e.pages import HomePage, ProfilePage
from tests.e2e.utils.test_helpers import generate_screenshot_name


@pytest.mark.asyncio
async def test_profile_page_navigation(authenticated_page: Page):
    """Test navigation to the profile page from the home page."""
    # Arrange
    home_page = HomePage(authenticated_page)
    
    # Act - Navigate to home page
    await home_page.goto()
    
    # Assert - Home page loaded
    assert await home_page.is_welcome_message_visible(), "Home page welcome message should be visible"
    
    # Take a screenshot - Home page
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('profile_nav_step1')}.png",
        full_page=True
    )
    
    # Act - Navigate to profile page
    await home_page.navigate_to_profile()
    
    # Take a screenshot - Profile page
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('profile_nav_step2')}.png",
        full_page=True
    )
    
    # Assert - Check that the profile page is displayed correctly
    profile_page = ProfilePage(authenticated_page)
    assert await profile_page.is_title_visible(), "Profile page title should be visible"


@pytest.mark.asyncio
async def test_direct_profile_page_access(authenticated_page: Page):
    """Test direct access to the profile page."""
    # Arrange
    profile_page = ProfilePage(authenticated_page)
    
    # Act - Navigate directly to profile page
    await profile_page.goto()
    
    # Take a screenshot
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('direct_profile_access')}.png",
        full_page=True
    )
    
    # Assert - Check that the profile page is displayed correctly
    assert await profile_page.is_title_visible(), "Profile page title should be visible" 