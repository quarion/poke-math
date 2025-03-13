#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the login functionality.
"""

import pytest
from playwright.async_api import Page, expect

from tests.e2e.pages import HomePage, LoginPage, NamePage
from tests.e2e.utils.test_helpers import generate_screenshot_name


@pytest.mark.asyncio
async def test_login_page_loads(page: Page):
    """Test that the login page loads correctly."""
    # Arrange
    login_page = LoginPage(page)
    
    # Act
    await login_page.goto()
    
    # Assert
    assert await login_page.is_title_visible(), "Login page title should be visible"
    title_text = await login_page.get_title_text()
    assert "Welcome to Pokemath!" in title_text, f"Expected 'Welcome to Pokemath!' in title, got '{title_text}'"
    
    # Take a screenshot
    await page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('login_page_loads')}.png",
        full_page=True
    )


@pytest.mark.asyncio
async def test_guest_login_flow(page: Page):
    """Test the guest login flow."""
    # Arrange
    login_page = LoginPage(page)
    name_page = NamePage(page)
    home_page = HomePage(page)
    trainer_name = "TestTrainer"
    
    # Act - Step 1: Navigate to login page
    await login_page.goto()
    
    # Assert - Step 1
    assert await login_page.is_title_visible(), "Login page title should be visible"
    
    # Take a screenshot - Step 1
    await page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('guest_login_step1')}.png",
        full_page=True
    )
    
    # Act - Step 2: Continue as guest
    await login_page.continue_as_guest()
    
    # Assert - Step 2
    assert await name_page.is_title_visible(), "Name page title should be visible"
    title_text = await name_page.get_title_text()
    assert "Choose Your Trainer Name!" in title_text, f"Expected 'Choose Your Trainer Name!' in title, got '{title_text}'"
    
    # Take a screenshot - Step 2
    await page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('guest_login_step2')}.png",
        full_page=True
    )
    
    # Act - Step 3: Enter trainer name and save
    await name_page.set_trainer_name(trainer_name)
    
    # Assert - Step 3
    assert await home_page.is_welcome_message_visible(), "Home page welcome message should be visible"
    
    # Take a screenshot - Step 3
    await page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('guest_login_step3')}.png",
        full_page=True
    )


@pytest.mark.asyncio
async def test_google_login_button(page: Page):
    """Test that the Google login button is visible and clickable."""
    # Arrange
    login_page = LoginPage(page)
    
    # Act
    await login_page.goto()
    
    # Assert
    google_button = page.locator(login_page.google_button_locator)
    await expect(google_button).to_be_visible()
    
    # Take a screenshot
    await page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('google_login_button')}.png",
        full_page=True
    ) 