#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Uproszczony moduł obsługi tłumaczeń i lokalizacji.
Część aplikacji Menadżer Serwisu Opon.
"""

import os
import logging
from PySide6.QtCore import QSettings

from utils.paths import CONFIG_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

def initialize_locale():
    """Zaślepka inicjalizacji lokalizacji."""
    logger.info("Inicjalizacja lokalizacji pominięta - tłumaczenia wyłączone")
    pass

def load_translations(language_code):
    """Zaślepka ładowania tłumaczeń."""
    logger.info("Ładowanie tłumaczeń pominięte - tłumaczenia wyłączone")
    pass

def _(text):
    """
    Funkcja tłumacząca - zwraca oryginalny tekst bez tłumaczenia.
    
    Args:
        text (str): Tekst do przetłumaczenia
    
    Returns:
        str: Oryginalny tekst bez zmian
    """
    return text

def get_available_languages():
    """
    Zwraca listę dostępnych języków.
    
    Returns:
        list: Lista dostępnych języków - tylko język polski
    """
    return [('pl', 'Polski')]

def current_locale():
    """
    Zwraca aktualnie wybrany język.
    
    Returns:
        str: Zawsze 'pl'
    """
    return 'pl'