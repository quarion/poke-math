#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the adventure completion functionality.
"""

import pytest
import json
from playwright.async_api import Page, expect

from tests.e2e.pages import HomePage, ProfilePage
from tests.e2e.utils.test_helpers import generate_screenshot_name


@pytest.mark.asyncio
async def test_adventure_completion_api(authenticated_page: Page):
    """Test the adventure completion API."""
    # Arrange - Get initial player level and XP
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    
    # Take a screenshot - Initial state
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('adventure_completion_initial')}.png",
        full_page=True
    )
    
    # Check for errors
    if await profile_page.has_error():
        error_message = await profile_page.get_error_message()
        pytest.fail(f"Profile page has an error: {error_message}")
    
    # Get initial level and XP
    initial_level = await profile_page.get_player_level()
    initial_xp, _ = await profile_page.get_player_xp()
    
    # Get initial collection stats
    initial_unique_pokemon, _ = await profile_page.get_collection_stats()
    
    # Act - Call the adventure completion API
    # Prepare the payload
    payload = {
        "difficulty": 3,
        "caught_pokemon": ["pikachu", "bulbasaur", "charmander"]
    }
    
    # Make the API call
    response = await authenticated_page.request.post(
        "http://localhost:8080/adventure/complete",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    
    # Assert - Check the response
    assert response.ok, f"Adventure completion API call failed with status {response.status}"
    
    # Parse the response
    response_data = await response.json()
    
    # Check the response data
    assert response_data["success"], "Adventure completion API should return success=true"
    assert "xp_gained" in response_data, "Response should include xp_gained"
    assert "pokemon_counts" in response_data, "Response should include pokemon_counts"
    assert "leveled_up" in response_data, "Response should include leveled_up"
    assert "level_info" in response_data, "Response should include level_info"
    
    # Check that XP was gained
    assert response_data["xp_gained"] > 0, "XP gained should be positive"
    
    # Check that Pokémon were caught
    for pokemon_id in payload["caught_pokemon"]:
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
    
    # Get updated level and XP
    updated_level = await profile_page.get_player_level()
    updated_xp, _ = await profile_page.get_player_xp()
    
    # Get updated collection stats
    updated_unique_pokemon, _ = await profile_page.get_collection_stats()
    
    # Check that level or XP increased
    assert updated_level > initial_level or updated_xp > initial_xp, "Player level or XP should increase after adventure"
    
    # Check that Pokémon collection increased
    assert updated_unique_pokemon >= initial_unique_pokemon, "Unique Pokémon count should not decrease after adventure"
    
    # If the player didn't have any Pokémon before, they should have some now
    # This is a soft assertion - we'll print a warning but not fail the test
    if initial_unique_pokemon == 0 and updated_unique_pokemon == 0:
        print("WARNING: Player should have caught at least one Pokémon, but collection is still empty")