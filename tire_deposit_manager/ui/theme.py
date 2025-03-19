#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zarządzania motywami dla aplikacji.
"""

from PySide6.QtCore import QSettings

# Stałe kolorów dla trybów jasnego i ciemnego
COLORS = {
    "light": {
        "background": "#f5f7fa",
        "card_bg": "#ffffff",
        "text_primary": "#2c3e50",
        "text_secondary": "#7f8c8d",
        "accent_blue": "#3498db",
        "accent_green": "#2ecc71",
        "accent_orange": "#f39c12",
        "accent_red": "#e74c3c",
        "accent_purple": "#9b59b6",
        "border": "#e0e6ed",
        "hover": "#f0f5fa",
        "chart_colors": ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
    },
    "dark": {
        "background": "#1a1d21",
        "card_bg": "#2c3034",
        "text_primary": "#ecf0f1",
        "text_secondary": "#bdc3c7",
        "accent_blue": "#4dabf7",
        "accent_green": "#51cf66",
        "accent_orange": "#ffa94d",
        "accent_red": "#ff6b6b",
        "accent_purple": "#cc5de8",
        "border": "#444444",
        "hover": "#3a3f44",
        "chart_colors": ['#4dabf7', '#51cf66', '#ff6b6b', '#ffa94d', '#cc5de8']
    }
}

class ThemeManager:
    """
    Zarządza motywem aplikacji (jasny/ciemny).
    Implementacja singletonu.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Zwraca singleton instancji ThemeManager.
        
        Returns:
            ThemeManager: Jedyna instancja menedżera motywów
        """
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance
    
    def __init__(self):
        """Inicjalizacja menedżera motywów."""
        self.settings = QSettings()
        self.is_dark_mode = self.settings.value("theme/dark_mode", False, type=bool)
        self.theme_changed_callbacks = []
    
    def get_colors(self):
        """
        Zwraca bieżący zestaw kolorów.
        
        Returns:
            dict: Słownik kolorów dla aktualnego motywu
        """
        return COLORS["dark"] if self.is_dark_mode else COLORS["light"]
    
    def toggle_theme(self):
        """Przełącza między trybem jasnym a ciemnym."""
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue("theme/dark_mode", self.is_dark_mode)
        self.notify_theme_changed()
    
    def register_callback(self, callback):
        """
        Rejestruje funkcję zwrotną do wywołania przy zmianie motywu.
        
        Args:
            callback (callable): Funkcja zwrotna
        """
        if callback not in self.theme_changed_callbacks:
            self.theme_changed_callbacks.append(callback)
    
    def unregister_callback(self, callback):
        """
        Usuwa funkcję zwrotną z listy powiadomień.
        
        Args:
            callback (callable): Funkcja zwrotna do usunięcia
        """
        if callback in self.theme_changed_callbacks:
            self.theme_changed_callbacks.remove(callback)
    
    def notify_theme_changed(self):
        """Powiadamia wszystkie zarejestrowane komponenty o zmianie motywu."""
        for callback in self.theme_changed_callbacks:
            callback()