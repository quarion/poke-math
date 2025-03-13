#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper functions for API calls in e2e tests.
"""

import json

from playwright.async_api import Page


async def complete_adventure(page: Page, difficulty: int, caught_pokemon: list[str]):
    """
    Helper to call the adventure completion API.
    
    Args:
        page: The Playwright page object
        difficulty: The difficulty level of the adventure (1-7)
        caught_pokemon: List of Pokémon IDs that were caught
        
    Returns:
        tuple: (response, response_data) - The raw response and parsed JSON data
    """
    payload = {
        "difficulty": difficulty,
        "caught_pokemon": caught_pokemon
    }
    
    response = await page.request.post(
        "http://localhost:8080/adventure/complete",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    
    return response, await response.json()


async def verify_adventure_response_structure(response_data: dict):
    """
    Verify that the adventure completion API response has the expected structure.
    
    Args:
        response_data: The parsed JSON response data
        
    Returns:
        bool: True if the structure is valid, raises AssertionError otherwise
    """
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
    
    return True 