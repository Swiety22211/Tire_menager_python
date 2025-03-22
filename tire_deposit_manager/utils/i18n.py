#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prosty moduł lokalizacji dla aplikacji.
"""

def _(text):
    """
    Funkcja lokalizacji - na razie po prostu zwraca oryginalny tekst.
    W przyszłości można to rozbudować o pełne wsparcie dla tłumaczeń.
    
    Args:
        text (str): Tekst do przetłumaczenia
        
    Returns:
        str: Przetłumaczony tekst
    """
    return text