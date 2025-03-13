#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the player progression features.
These tests verify that the core player progression features are working correctly.
"""


import pytest
from playwright.async_api import Page

from tests.e2e.pages import ProfilePage
from tests.e2e.utils.api_helpers import complete_adventure
from tests.e2e.utils.test_helpers import generate_screenshot_name


@pytest.mark.asyncio
async def test_player_level_display(authenticated_page: Page):
    """Test that player level is displayed correctly on the profile page."""
    # Arrange
    profile_page = ProfilePage(authenticated_page)
    
    # Act - Navigate to profile page
    await profile_page.goto()
    
    # Take a screenshot
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('smoke_player_level')}.png",
        full_page=True
    )
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
    # Assert - Check that player level section is visible
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
async def test_pokemon_collection_section(authenticated_page: Page):
    """Test that Pokémon collection section is displayed correctly on the profile page."""
    # Arrange
    profile_page = ProfilePage(authenticated_page)
    
    # Act - Navigate to profile page
    await profile_page.goto()
    
    # Take a screenshot
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('smoke_pokemon_collection')}.png",
        full_page=True
    )
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
    # Assert - Check that Pokémon collection section is visible
    assert await profile_page.is_collection_section_visible(), "Pokémon collection section should be visible"


@pytest.mark.asyncio
async def test_xp_calculation(authenticated_page: Page, player_stats_before_adventure):
    """Test that XP is calculated correctly for different Pokémon tiers and difficulties."""
    # Arrange - Get initial level and XP from fixture
    initial_stats = player_stats_before_adventure
    
    # Act - Call the adventure completion API with different difficulties using our helper
    # Test with difficulty 1 (lowest)
    _, low_difficulty_data = await complete_adventure(
        authenticated_page,
        difficulty=1,
        caught_pokemon=["pikachu"]  # Tier 2 Pokémon
    )
    
    low_difficulty_xp = low_difficulty_data["xp_gained"]
    
    # Test with difficulty 7 (highest)
    _, high_difficulty_data = await complete_adventure(
        authenticated_page,
        difficulty=7,
        caught_pokemon=["pikachu"]  # Same Pokémon for fair comparison
    )
    
    high_difficulty_xp = high_difficulty_data["xp_gained"]
    
    # Assert - Higher difficulty should give more XP
    assert high_difficulty_xp > low_difficulty_xp, "Higher difficulty should give more XP"
    
    # Reload profile page to see final state
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    
    # Take a screenshot
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('smoke_xp_calculation')}.png",
        full_page=True
    )
    
    # Get final level and XP
    final_level = await profile_page.get_player_level()
    final_xp, _ = await profile_page.get_player_xp()
    
    # Check that XP or level increased
    assert final_level > initial_stats["level"] or final_xp > initial_stats["xp"], "Player level or XP should increase after adventures"


@pytest.mark.asyncio
async def test_pokemon_tier_xp_rewards(authenticated_page: Page):
    """Test that different Pokémon tiers give different XP rewards."""
    # Act - Call the adventure completion API with different Pokémon using our helper
    # Test with a tier 2 Pokémon (pikachu)
    _, tier2_data = await complete_adventure(
        authenticated_page,
        difficulty=1,
        caught_pokemon=["pikachu"]  # Tier 2 Pokémon
    )
    
    tier2_xp = tier2_data["xp_gained"]
    
    # Test with a tier 5 Pokémon (mew)
    _, tier5_data = await complete_adventure(
        authenticated_page,
        difficulty=1,
        caught_pokemon=["mew"]  # Tier 5 Pokémon
    )
    
    tier5_xp = tier5_data["xp_gained"]
    
    # Assert - Higher tier should give more XP
    assert tier5_xp > tier2_xp, "Higher tier Pokémon should give more XP"
    
    # Take a screenshot
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('smoke_pokemon_tier_xp')}.png",
        full_page=True
    )


@pytest.mark.asyncio
async def test_level_up_progression(authenticated_page: Page, player_stats_before_adventure):
    """Test that player levels up correctly when gaining enough XP."""
    # Arrange - Get initial level and XP from fixture
    initial_stats = player_stats_before_adventure
    profile_page = ProfilePage(authenticated_page)
    
    # Calculate how much XP is needed to level up
    xp_needed_for_level_up = initial_stats["xp_needed"] - initial_stats["xp"]
    
    # We'll need to complete multiple adventures to gain enough XP to level up
    # Keep track of total XP gained
    total_xp_gained = 0
    
    # Complete adventures until we gain enough XP to level up
    while total_xp_gained < xp_needed_for_level_up:
        # Complete a high-difficulty adventure with high-tier Pokémon for maximum XP
        _, response_data = await complete_adventure(
            authenticated_page,
            difficulty=7,
            caught_pokemon=["mew", "mewtwo", "lugia"]  # High-tier Pokémon
        )
        
        total_xp_gained += response_data["xp_gained"]
        
        # If the API indicates we've leveled up, break out of the loop
        if response_data["leveled_up"]:
            break
    
    # Reload profile page to see final state
    await profile_page.goto()
    
    # Take a screenshot
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('level_up_progression')}.png",
        full_page=True
    )
    
    # Get final level
    final_level = await profile_page.get_player_level()
    
    # Assert - Player should have leveled up
    assert final_level > initial_stats["level"], "Player should level up after gaining enough XP" 