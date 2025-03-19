#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zarządzający systemem powiadomień w aplikacji.
"""

import os
import logging
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect,
    QGridLayout, QApplication
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QColor, QFont, QIcon

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class NotificationTypes(Enum):
    """Typy powiadomień obsługiwane przez system."""
    INFO = 0
    SUCCESS = 1
    WARNING = 2
    ERROR = 3

class NotificationWidget(QWidget):
    """Widget powiadomienia wyświetlanego w rogu ekranu."""
    
    def __init__(self, message, notification_type, parent=None, duration=5000):
        """
        Inicjalizacja widgetu powiadomienia.
        
        Args:
            message (str): Treść powiadomienia
            notification_type (NotificationTypes): Typ powiadomienia
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
            duration (int, optional): Czas wyświetlania w milisekundach. Domyślnie 5000.
        """
        super().__init__(parent)
        
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        
        # Ustawienie flagi okna narzędziowego bez ramki
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        # Ustawienie przezroczystego tła
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Zapobieganie focusowi
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Timer do zamknięcia powiadomienia
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close_animation)
        self.timer.start(duration)
        
        # Animacja pokazywania
        self.show_animation()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika powiadomienia."""
        # Ustawienie kolorów w zależności od typu powiadomienia
        if self.notification_type == NotificationTypes.INFO:
            background_color = "#3498db"
            icon_path = os.path.join(ICONS_DIR, "info.png")
        elif self.notification_type == NotificationTypes.SUCCESS:
            background_color = "#2ecc71"
            icon_path = os.path.join(ICONS_DIR, "success.png")
        elif self.notification_type == NotificationTypes.WARNING:
            background_color = "#f39c12"
            icon_path = os.path.join(ICONS_DIR, "warning.png")
        elif self.notification_type == NotificationTypes.ERROR:
            background_color = "#e74c3c"
            icon_path = os.path.join(ICONS_DIR, "error.png")
        else:
            background_color = "#2c3e50"
            icon_path = os.path.join(ICONS_DIR, "info.png")
        
        # Ustawienie StyleSheet
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {background_color};
                color: white;
                border-radius: 5px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }}
        """)
        
        # Układy
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        
        # Ikona
        icon_label = QLabel()
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            icon_label.setPixmap(icon.pixmap(24, 24))
        main_layout.addWidget(icon_label)
        
        # Treść
        message_label = QLabel(self.message)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setWordWrap(True)
        main_layout.addWidget(message_label, 1)
        
        # Dodanie efektu cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie maksymalnej szerokości
        self.setMaximumWidth(400)
        self.adjustSize()
    
    def show_animation(self):
        """Animacja pokazywania powiadomienia."""
        # Pozycja początkowa (poza ekranem)
        start_pos = self.pos()
        # Pozycja końcowa (w rogu ekranu)
        end_pos = self.pos()
        
        # Animacja przesunięcia
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setStartValue(QRect(start_pos.x(), start_pos.y() - 50, self.width(), self.height()))
        self.anim.setEndValue(QRect(end_pos.x(), end_pos.y(), self.width(), self.height()))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
    
    def close_animation(self):
        """Animacja zamykania powiadomienia."""
        # Pozycja początkowa (aktualna)
        start_pos = self.pos()
        # Pozycja końcowa (poza ekranem w prawo)
        end_pos = QApplication.instance().desktop().availableGeometry().topRight()
        
        # Animacja przesunięcia
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setStartValue(QRect(start_pos.x(), start_pos.y(), self.width(), self.height()))
        self.anim.setEndValue(QRect(end_pos.x(), start_pos.y(), self.width(), self.height()))
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        self.anim.finished.connect(self.close)
        self.anim.start()

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
        self.positions = []
    
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
            if not self.parent:
                logger.warning("Brak rodzica dla powiadomień")
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
            notification = NotificationWidget(message, notification_type, self.parent, duration)
            
            # Dodanie do listy aktywnych powiadomień
            self.notifications.append(notification)
            
            # Pozycjonowanie powiadomienia
            self.position_notification(notification)
            
            # Wyświetlenie powiadomienia
            notification.show()
            
            # Usunięcie powiadomienia z listy po zamknięciu
            notification.destroyed.connect(lambda: self.remove_notification(notification))
            
        except Exception as e:
            logger.error(f"Błąd podczas wyświetlania powiadomienia: {e}")
    
    def position_notification(self, notification):
        """
        Pozycjonuje powiadomienie na ekranie.
        
        Args:
            notification (NotificationWidget): Widget powiadomienia do pozycjonowania
        """
        # Pobierz dostępną geometrię ekranu
        screen_geometry = QApplication.instance().desktop().availableGeometry()
        
        # Oblicz pozycję początkową (prawy górny róg)
        pos_x = screen_geometry.width() - notification.width() - 20
        pos_y = 20
        
        # Dostosuj pozycję Y, uwzględniając już wyświetlone powiadomienia
        for n in self.notifications:
            if n != notification and n.isVisible():
                # Dodaj odstęp między powiadomieniami
                pos_y += n.height() + 10
        
        # Ustaw pozycję powiadomienia
        notification.move(pos_x, pos_y)
    
    def remove_notification(self, notification):
        """
        Usuwa powiadomienie z listy aktywnych powiadomień.
        
        Args:
            notification (NotificationWidget): Widget powiadomienia do usunięcia
        """
        if notification in self.notifications:
            self.notifications.remove(notification)
            
            # Przeorganizuj pozycje pozostałych powiadomień
            for i, n in enumerate(self.notifications):
                if n.isVisible():
                    screen_geometry = QApplication.instance().desktop().availableGeometry()
                    pos_x = screen_geometry.width() - n.width() - 20
                    pos_y = 20
                    
                    # Uwzględnij wcześniejsze powiadomienia
                    for j in range(i):
                        if self.notifications[j].isVisible():
                            pos_y += self.notifications[j].height() + 10
                    
                    # Animacja przesunięcia
                    anim = QPropertyAnimation(n, b"geometry")
                    anim.setDuration(300)
                    anim.setStartValue(QRect(n.pos().x(), n.pos().y(), n.width(), n.height()))
                    anim.setEndValue(QRect(pos_x, pos_y, n.width(), n.height()))
                    anim.setEasingCurve(QEasingCurve.OutCubic)
                    anim.start()