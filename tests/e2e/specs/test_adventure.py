#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the adventure completion functionality.
This file focuses on adventure mechanics rather than player progression.
"""

import pytest
import json
from playwright.async_api import Page, expect

from tests.e2e.pages import HomePage, ProfilePage
from tests.e2e.utils.test_helpers import generate_screenshot_name
from tests.e2e.utils.api_helpers import complete_adventure, verify_adventure_response_structure


@pytest.mark.asyncio
async def test_adventure_completion_api(authenticated_page: Page, player_stats_before_adventure):
    """Test the adventure completion API and its effects."""
    # Arrange - Get initial player stats from fixture
    initial_stats = player_stats_before_adventure
    profile_page = ProfilePage(authenticated_page)
    
    # Take a screenshot - Initial state
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('adventure_completion_initial')}.png",
        full_page=True
    )
    
    # Act - Call the adventure completion API using our helper
    response, response_data = await complete_adventure(
        authenticated_page,
        difficulty=3,
        caught_pokemon=["pikachu", "bulbasaur", "charmander"]
    )
    
    # Assert - Check the response
    assert response.ok, f"Adventure completion API call failed with status {response.status}"
    
    # Verify response structure using our helper
    verify_adventure_response_structure(response_data)
    
    # Check that XP was gained
    assert response_data["xp_gained"] > 0, "XP gained should be positive"
    
    # Check that Pokémon were caught
    for pokemon_id in ["pikachu", "bulbasaur", "charmander"]:
        assert pokemon_id in response_data["pokemon_counts"], f"Pokemon {pokemon_id} should be in pokemon_counts"
        assert response_data["pokemon_counts"][pokemon_id] > 0, f"Pokemon {pokemon_id} count should be positive"
    
    # Reload the profile page to see the changes
    await profile_page.goto()
    
    # Take a screenshot - After adventure
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('adventure_completion_after')}.png",
        full_page=True
    )
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
    # Get updated stats
    updated_level = await profile_page.get_player_level()
    updated_xp, _ = await profile_page.get_player_xp()
    updated_unique_pokemon, _ = await profile_page.get_collection_stats()
    
    # Check that level or XP increased
    assert updated_level > initial_stats["level"] or updated_xp > initial_stats["xp"], "Player level or XP should increase after adventure"
    
    # Check that Pokémon collection increased
    assert updated_unique_pokemon >= initial_stats["unique_pokemon"], "Unique Pokémon count should not decrease after adventure"


@pytest.mark.asyncio
async def test_adventure_difficulty_scaling(authenticated_page: Page):
    """Test that adventure difficulty affects rewards appropriately."""
    # Test with difficulty 1 (lowest)
    low_difficulty_response, low_difficulty_data = await complete_adventure(
        authenticated_page, 
        difficulty=1, 
        caught_pokemon=["pikachu"]
    )
    
    low_difficulty_xp = low_difficulty_data["xp_gained"]
    
    # Test with difficulty 7 (highest)
    high_difficulty_response, high_difficulty_data = await complete_adventure(
        authenticated_page, 
        difficulty=7, 
        caught_pokemon=["pikachu"]
    )
    
    high_difficulty_xp = high_difficulty_data["xp_gained"]
    
    # Assert - Higher difficulty should give more XP
    assert high_difficulty_xp > low_difficulty_xp, "Higher difficulty should give more XP"
    
    # Take a screenshot
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('adventure_difficulty_scaling')}.png",
        full_page=True
    )


@pytest.mark.asyncio
async def test_adventure_pokemon_quantity(authenticated_page: Page):
    """Test that catching more Pokémon in an adventure gives more rewards."""
    # Test with one Pokémon
    single_pokemon_response, single_pokemon_data = await complete_adventure(
        authenticated_page, 
        difficulty=3, 
        caught_pokemon=["pikachu"]
    )
    
    single_pokemon_xp = single_pokemon_data["xp_gained"]
    
    # Test with multiple Pokémon
    multiple_pokemon_response, multiple_pokemon_data = await complete_adventure(
        authenticated_page, 
        difficulty=3, 
        caught_pokemon=["pikachu", "bulbasaur", "charmander"]
    )
    
    multiple_pokemon_xp = multiple_pokemon_data["xp_gained"]
    
    # Assert - More Pokémon should give more XP
    assert multiple_pokemon_xp > single_pokemon_xp, "Catching more Pokémon should give more XP"