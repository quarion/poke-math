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
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
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
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
    # Assert - Check that the profile page is displayed correctly
    assert await profile_page.is_title_visible(), "Profile page title should be visible"


@pytest.mark.asyncio
async def test_player_progression_display(authenticated_page: Page):
    """Test that player progression information is displayed correctly."""
    # Arrange
    profile_page = ProfilePage(authenticated_page)
    
    # Act - Navigate to profile page
    await profile_page.goto()
    
    # Take a screenshot
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('player_progression')}.png",
        full_page=True
    )
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
    # Assert - Check that player level and XP are displayed
    assert await profile_page.is_level_section_visible(), "Player level section should be visible"
    
    # Get player level and XP
    level = await profile_page.get_player_level()
    current_xp, xp_needed = await profile_page.get_player_xp()
    
    # Verify level and XP are reasonable values
    assert level >= 1, "Player level should be at least 1"
    assert current_xp >= 0, "Current XP should be non-negative"
    assert xp_needed > 0, "XP needed should be positive"
    assert current_xp < xp_needed, "Current XP should be less than XP needed for next level"


@pytest.mark.asyncio
async def test_pokemon_collection_display(authenticated_page: Page):
    """Test that Pokémon collection is displayed correctly."""
    # Arrange
    profile_page = ProfilePage(authenticated_page)
    
    # Act - Navigate to profile page
    await profile_page.goto()
    
    # Take a screenshot
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('pokemon_collection')}.png",
        full_page=True
    )
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
    # Assert - Check that Pokémon collection is displayed
    assert await profile_page.is_collection_section_visible(), "Pokémon collection section should be visible"
    
    # Get collection stats
    unique_pokemon, total_pokemon = await profile_page.get_collection_stats()
    
    # Verify collection stats are reasonable values
    assert unique_pokemon >= 0, "Unique Pokémon count should be non-negative"
    assert total_pokemon > 0, "Total Pokémon count should be positive"
    assert unique_pokemon <= total_pokemon, "Unique Pokémon count should not exceed total Pokémon count"
    
    # Check that the number of Pokémon cards matches the unique Pokémon count
    pokemon_count = await profile_page.get_pokemon_count()
    assert pokemon_count == unique_pokemon, f"Number of Pokémon cards ({pokemon_count}) should match unique Pokémon count ({unique_pokemon})" 