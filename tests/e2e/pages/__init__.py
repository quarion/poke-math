#!/usr/bin/env python

"""
Page Object Model classes for end-to-end testing.
"""

from .BasePage import BasePage
from .HomePage import HomePage
from .LoginPage import LoginPage
from .NamePage import NamePage
from .ProfilePage import ProfilePage

__all__ = ["BasePage", "HomePage", "LoginPage", "NamePage", "ProfilePage"]
