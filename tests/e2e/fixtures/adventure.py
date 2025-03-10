#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fixtures for adventure-related e2e tests.
"""

import pytest
from playwright.async_api import Page

from tests.e2e.utils.api_helpers import complete_adventure
from tests.e2e.pages import ProfilePage


@pytest.fixture
async def completed_adventure(authenticated_page: Page):
    """
    Fixture that completes an adventure and returns the response data.
    
    This fixture completes a standard adventure with medium difficulty
    and a few common Pokémon.
    
    Args:
        authenticated_page: The authenticated Playwright page
        
    Returns:
        dict: The parsed JSON response data from the adventure completion
    """
    response, data = await complete_adventure(
        authenticated_page, 
        difficulty=3, 
        caught_pokemon=["pikachu", "bulbasaur", "charmander"]
    )
    
    assert response.ok, f"Adventure completion API call failed with status {response.status}"
    return data


@pytest.fixture
async def player_stats_before_adventure(authenticated_page: Page):
    """
    Fixture that captures player stats before an adventure.
    
    Args:
        authenticated_page: The authenticated Playwright page
        
    Returns:
        dict: Player stats including level, XP, and collection stats
    """
    profile_page = ProfilePage(authenticated_page)
    await profile_page.goto()
    
    level = await profile_page.get_player_level()
    xp, xp_needed = await profile_page.get_player_xp()
    unique_pokemon, total_pokemon = await profile_page.get_collection_stats()
    
    return {
        "level": level,
        "xp": xp,
        "xp_needed": xp_needed,
        "unique_pokemon": unique_pokemon,
        "total_pokemon": total_pokemon
    } 