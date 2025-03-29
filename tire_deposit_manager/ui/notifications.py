#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zarządzający systemem powiadomień w aplikacji.
Poprawiona wersja z lepszym układaniem powiadomień i bez obramowań.
"""

import os
import logging
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect,
    QApplication, QFrame, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QEvent
from PySide6.QtGui import QColor, QFont, QIcon, QScreen, QPixmap

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class NotificationTypes(Enum):
    """Typy powiadomień obsługiwane przez system."""
    INFO = 0
    SUCCESS = 1
    WARNING = 2
    ERROR = 3

class NotificationWidget(QFrame):
    """Widget powiadomienia wyświetlanego w ramach rodzica."""
    
    def __init__(self, parent, message, notification_type=NotificationTypes.INFO, duration=5000):
        """
        Inicjalizacja widgetu powiadomienia.
        
        Args:
            parent (QWidget): Widget rodzica
            message (str): Treść powiadomienia
            notification_type (NotificationTypes): Typ powiadomienia
            duration (int): Czas wyświetlania w ms
        """
        super().__init__(parent)
        
        # Zapisz parametry
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        self.parent_widget = parent
        
        # Ustawienia widgetu
        self.setFrameShape(QFrame.NoFrame)  # Usunięcie obramowania
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        # Pozycjonowanie na rodzicu
        self.setGeometry(
            parent.width() - 420, 10, 
            400, 80  # Początkowe wymiary
        )
        
        # Inicjalizacja UI
        self.init_ui()
        
        # Timer do zamknięcia
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.animate_out)
        self.close_timer.start(duration)
        
        # Ukryj na początku, pokaż z animacją
        self.hide()
        QTimer.singleShot(100, self.animate_in)
        
        # Rejestruj w menedżerze powiadomień
        NotificationManager.get_instance().register_notification(self)
    
    def init_ui(self):
        """Inicjalizacja UI powiadomienia."""
        # Ustawienie kolorów i ikon w zależności od typu
        if self.notification_type == NotificationTypes.INFO:
            background_color = "#3498db"
            icon_text = "ℹ️"
        elif self.notification_type == NotificationTypes.SUCCESS:
            background_color = "#2ecc71"
            icon_text = "✅"
        elif self.notification_type == NotificationTypes.WARNING:
            background_color = "#f39c12"
            icon_text = "⚠️"
        elif self.notification_type == NotificationTypes.ERROR:
            background_color = "#e74c3c"
            icon_text = "❌"
        else:
            background_color = "#2c3e50"
            icon_text = "ℹ️"
        
        # Ustawienie StyleSheet
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {background_color};
                color: white;
                border-radius: 5px;
                border: none;
            }}
            QLabel {{
                color: white;
                border: none;
                background-color: transparent;
            }}
            QPushButton {{
                border: none;
                background-color: transparent;
                color: white;
            }}
        """)
        
        # Główny układ
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Ikona
        icon_label = QLabel(icon_text)
        icon_label.setFont(QFont("Segoe UI", 16))
        icon_label.setFixedSize(25, 25)
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Treść
        message_label = QLabel(self.message)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setWordWrap(True)
        
        # Przycisk zamknięcia
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setFont(QFont("Segoe UI", 16))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.animate_out)
        
        # Dodanie elementów do layoutu
        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)  # 1 = stretch
        layout.addWidget(close_btn)
        
        # Efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Dostosuj rozmiar
        self.adjustSize()
    
    def animate_in(self):
        """Animacja wejścia."""
        # Pokaż powiadomienie
        self.show()
        self.raise_()
        
        # Początkowa pozycja (poza ekranem z prawej)
        start_x = self.parent_widget.width()
        start_y = self.y()
        
        # Docelowa pozycja (przy prawej krawędzi)
        end_x = self.parent_widget.width() - self.width() - 20
        end_y = self.y()
        
        # Animacja pozycji
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(QPoint(start_x, start_y))
        self.anim.setEndValue(QPoint(end_x, end_y))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
    
    def animate_out(self):
        """Animacja wyjścia i usunięcie."""
        # Zatrzymaj timer jeśli aktywny
        if self.close_timer.isActive():
            self.close_timer.stop()
        
        # Początkowa pozycja
        start_x = self.x()
        start_y = self.y()
        
        # Docelowa pozycja (poza ekranem w prawo)
        end_x = self.parent_widget.width() + 50
        end_y = self.y()
        
        # Animacja pozycji
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(QPoint(start_x, start_y))
        self.anim.setEndValue(QPoint(end_x, end_y))
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        
        # Po zakończeniu animacji usuń widget
        self.anim.finished.connect(self.on_animation_finished)
        self.anim.start()
    
    def on_animation_finished(self):
        """Obsługa zakończenia animacji."""
        # Powiadom menedżera o usunięciu
        NotificationManager.get_instance().remove_notification(self)
        
        # Usuń widget
        self.deleteLater()
    
    def enterEvent(self, event):
        """Zatrzymaj timer gdy kursor nad powiadomieniem."""
        if self.close_timer.isActive():
            self.close_timer.stop()
        return super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Wznów timer gdy kursor opuszcza powiadomienie."""
        # Restart timera
        self.close_timer.start(self.duration)
        return super().leaveEvent(event)
    
    def sizeHint(self):
        """Sugerowany rozmiar dla widgetu."""
        # Zapewnia bardziej precyzyjne wymiary dla lepszego układania
        from PySide6.QtCore import QSize
        
        width = 350  # Stała szerokość
        height = self.layout().sizeHint().height() + 20  # Wysokość + margines
        return QSize(width, height)

class NotificationManager:
    """
    Menedżer powiadomień - Singleton zapewniający jeden punkt dostępu.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Pobiera instancję menedżera powiadomień (Singleton).
        
        Returns:
            NotificationManager: Instancja menedżera powiadomień
        """
        if cls._instance is None:
            cls._instance = NotificationManager()
        return cls._instance
    
    def __init__(self):
        """Inicjalizacja menedżera powiadomień."""
        self.parent = None
        self.notifications = []
        self.y_offset = 10  # Początkowy odstęp od góry
    
    def set_parent(self, parent):
        """
        Ustawia rodzica dla powiadomień.
        
        Args:
            parent (QWidget): Widget rodzica dla powiadomień
        """
        self.parent = parent
    
    def show_notification(self, message, notification_type=NotificationTypes.INFO, duration=5000):
        """
        Wyświetla nowe powiadomienie.
        
        Args:
            message (str): Treść powiadomienia
            notification_type (NotificationTypes, optional): Typ powiadomienia. Domyślnie INFO.
            duration (int, optional): Czas wyświetlania w milisekundach. Domyślnie 5000.
        """
        try:
            # Upewnij się, że mamy rodzica
            if not self.parent:
                logger.warning("Brak rodzica dla powiadomień - powiadomienie nie zostanie wyświetlone")
                return
            
            # Logi na podstawie typu powiadomienia
            if notification_type == NotificationTypes.INFO:
                logger.info(message)
            elif notification_type == NotificationTypes.SUCCESS:
                logger.info(f"SUKCES: {message}")
            elif notification_type == NotificationTypes.WARNING:
                logger.warning(message)
            elif notification_type == NotificationTypes.ERROR:
                logger.error(message)
            
            # Tworzenie widgetu powiadomienia
            notification = NotificationWidget(self.parent, message, notification_type, duration)
            
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania powiadomienia: {e}")
    
    def register_notification(self, notification):
        """
        Rejestruje nowe powiadomienie.
        
        Args:
            notification (NotificationWidget): Widget powiadomienia
        """
        self.notifications.append(notification)
        self.reposition_notifications()
    
    def remove_notification(self, notification):
        """
        Usuwa powiadomienie z listy aktywnych powiadomień.
        
        Args:
            notification (NotificationWidget): Widget powiadomienia do usunięcia
        """
        if notification in self.notifications:
            self.notifications.remove(notification)
            self.reposition_notifications()
    
    def reposition_notifications(self):
        """Repozycjonuje wszystkie aktywne powiadomienia."""
        if not self.notifications:
            return
        
        # Posortuj powiadomienia wg ich aktualnej pozycji Y
        active_notifications = sorted(
            [n for n in self.notifications if n.isVisible()], 
            key=lambda n: n.y()
        )
        
        # Pozycjonuj wszystkie aktywne powiadomienia od góry
        y_offset = 10  # Początkowy odstęp od góry
        
        for notification in active_notifications:
            # Pobierz aktualną pozycję x
            x_pos = notification.parent_widget.width() - notification.width() - 20
            
            # Jeśli pozycja się zmieniła, animuj przesunięcie
            if notification.y() != y_offset:
                anim = QPropertyAnimation(notification, b"pos")
                anim.setDuration(200)
                anim.setStartValue(notification.pos())
                anim.setEndValue(QPoint(x_pos, y_offset))
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start()
            else:
                # Jeśli nie ma potrzeby animacji, ustaw bezpośrednio pozycję
                notification.move(x_pos, y_offset)
            
            # Zwiększ offset dla następnego powiadomienia
            y_offset += notification.height() + 10

class NotificationCenterWidget(QWidget):
    """
    Centrum powiadomień w aplikacji (zachowane dla kompatybilności wstecznej).
    """
    
    def __init__(self, notification_manager, parent=None):
        """
        Inicjalizacja centrum powiadomień.
        
        Args:
            notification_manager (NotificationManager): Menedżer powiadomień
            parent (QWidget, optional): Widget rodzica
        """
        super().__init__(parent)
        self.notification_manager = notification_manager

# Funkcja pomocnicza do tworzenia menedżera powiadomień
def create_notification_manager(parent_widget=None):
    """
    Tworzy i konfiguruje menedżera powiadomień.
    
    Args:
        parent_widget (QWidget, optional): Główny widget rodzica
    
    Returns:
        NotificationManager: Skonfigurowany menedżer powiadomień
    """
    # Utwórz instancję menedżera powiadomień
    notification_manager = NotificationManager.get_instance()
    
    # Ustaw widget rodzica, jeśli podano
    if parent_widget:
        notification_manager.set_parent(parent_widget)
    
    return notification_manager

# Eksport typów powiadomień dla wygody użycia
__all__ = [
    'NotificationTypes', 
    'NotificationManager', 
    'NotificationWidget', 
    'NotificationCenterWidget', 
    'create_notification_manager'
]