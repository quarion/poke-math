#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Page Object Model classes for end-to-end testing.
"""

from .BasePage import BasePage
from .LoginPage import LoginPage
from .NamePage import NamePage
from .HomePage import HomePage
from .ProfilePage import ProfilePage

__all__ = [
    'BasePage',
    'LoginPage',
    'NamePage',
    'HomePage',
    'ProfilePage'
] 