#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smoke tests for the player progression features.
These tests verify that the core player progression features are working correctly.
"""

import pytest
import json
from playwright.async_api import Page, expect

from tests.e2e.pages import HomePage, ProfilePage
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
async def test_adventure_completion_api_structure(authenticated_page: Page):
    """Test that the adventure completion API returns the expected structure."""
    # Arrange
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    
    # Act - Call the adventure completion API
    # Prepare the payload
    payload = {
        "difficulty": 1,
        "caught_pokemon": ["pikachu"]
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
    
    # Check the response data structure
    assert "success" in response_data, "Response should include success"
    assert "xp_gained" in response_data, "Response should include xp_gained"
    assert "pokemon_counts" in response_data, "Response should include pokemon_counts"
    assert "leveled_up" in response_data, "Response should include leveled_up"
    assert "level_info" in response_data, "Response should include level_info"
    
    # Check level_info structure
    assert "level" in response_data["level_info"], "level_info should include level"
    assert "xp" in response_data["level_info"], "level_info should include xp"
    assert "xp_needed" in response_data["level_info"], "level_info should include xp_needed"


@pytest.mark.asyncio
async def test_xp_calculation(authenticated_page: Page):
    """Test that XP is calculated correctly for different Pokémon tiers and difficulties."""
    # Arrange - Get initial level and XP
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    
    initial_level = await profile_page.get_player_level()
    initial_xp, _ = await profile_page.get_player_xp()
    
    # Act - Call the adventure completion API with different difficulties
    # Test with difficulty 1 (lowest)
    low_difficulty_payload = {
        "difficulty": 1,
        "caught_pokemon": ["pikachu"]  # Tier 2 Pokémon
    }
    
    low_difficulty_response = await authenticated_page.request.post(
        "http://localhost:8080/adventure/complete",
        data=json.dumps(low_difficulty_payload),
        headers={"Content-Type": "application/json"}
    )
    
    low_difficulty_data = await low_difficulty_response.json()
    low_difficulty_xp = low_difficulty_data["xp_gained"]
    
    # Test with difficulty 7 (highest)
    high_difficulty_payload = {
        "difficulty": 7,
        "caught_pokemon": ["pikachu"]  # Same Pokémon for fair comparison
    }
    
    high_difficulty_response = await authenticated_page.request.post(
        "http://localhost:8080/adventure/complete",
        data=json.dumps(high_difficulty_payload),
        headers={"Content-Type": "application/json"}
    )
    
    high_difficulty_data = await high_difficulty_response.json()
    high_difficulty_xp = high_difficulty_data["xp_gained"]
    
    # Assert - Higher difficulty should give more XP
    assert high_difficulty_xp > low_difficulty_xp, "Higher difficulty should give more XP"
    
    # Reload profile page to see final state
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
    assert final_level > initial_level or final_xp > initial_xp, "Player level or XP should increase after adventures"


@pytest.mark.asyncio
async def test_pokemon_tier_xp_rewards(authenticated_page: Page):
    """Test that different Pokémon tiers give different XP rewards."""
    # Arrange - Get initial level and XP
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    
    # Act - Call the adventure completion API with different Pokémon
    # Test with a tier 2 Pokémon (pikachu)
    tier2_payload = {
        "difficulty": 1,
        "caught_pokemon": ["pikachu"]  # Tier 2 Pokémon
    }
    
    tier2_response = await authenticated_page.request.post(
        "http://localhost:8080/adventure/complete",
        data=json.dumps(tier2_payload),
        headers={"Content-Type": "application/json"}
    )
    
    tier2_data = await tier2_response.json()
    tier2_xp = tier2_data["xp_gained"]
    
    # Test with a tier 5 Pokémon (mew)
    tier5_payload = {
        "difficulty": 1,
        "caught_pokemon": ["mew"]  # Tier 5 Pokémon
    }
    
    tier5_response = await authenticated_page.request.post(
        "http://localhost:8080/adventure/complete",
        data=json.dumps(tier5_payload),
        headers={"Content-Type": "application/json"}
    )
    
    tier5_data = await tier5_response.json()
    tier5_xp = tier5_data["xp_gained"]
    
    # Assert - Higher tier should give more XP
    assert tier5_xp > tier2_xp, "Higher tier Pokémon should give more XP"
    
    # Take a screenshot
    await profile_page.goto()
    await authenticated_page.screenshot(
        path=f"tests/e2e/screenshots/{generate_screenshot_name('smoke_pokemon_tier_xp')}.png",
        full_page=True
    ) 