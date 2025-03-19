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
    QApplication, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
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
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        
        # Ustawienia widgetu
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowModality(Qt.NonModal)
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Timer do zamknięcia powiadomienia
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close_animation)
        self.timer.start(duration)
    
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
            QFrame {{
                background-color: {background_color};
                color: white;
                border-radius: 5px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                padding: 10px;
            }}
        """)
        
        # Układy
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Ikona
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setFixedSize(32, 32)
            icon_label.setAlignment(Qt.AlignCenter)
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
        
        # Ustaw maksymalną szerokość
        self.setMaximumWidth(300)
        self.adjustSize()
    
    def show_animation(self):
        """Animacja pokazywania powiadomienia."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Pozycja końcowa
        pos_x = screen_geometry.width() - self.width() - 20
        pos_y = 20
        
        # Ustaw pozycję początkową poza ekranem
        self.move(pos_x, -self.height())
        
        # Animacja przesunięcia
        self.show()
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setStartValue(QPoint(pos_x, -self.height()))
        anim.setEndValue(QPoint(pos_x, pos_y))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
    
    def close_animation(self):
        """Animacja zamykania powiadomienia."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Pozycja końcowa poza ekranem
        pos_x = screen_geometry.width()
        pos_y = self.pos().y()
        
        # Animacja przesunięcia
        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(300)
        anim.setStartValue(self.pos())
        anim.setEndValue(QPoint(pos_x, pos_y))
        anim.setEasingCurve(QEasingCurve.InCubic)
        anim.finished.connect(self.close)
        anim.start()
    
    def show(self):
        """Przesłonięcie metody show z animacją."""
        super().show()
        self.show_animation()

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
        # Pobierz aktualny ekran
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
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
                    screen = QApplication.primaryScreen()
                    screen_geometry = screen.geometry()
                    
                    pos_x = screen_geometry.width() - n.width() - 20
                    pos_y = 20
                    
                    # Uwzględnij wcześniejsze powiadomienia
                    for j in range(i):
                        if self.notifications[j].isVisible():
                            pos_y += self.notifications[j].height() + 10
                    
                    # Animacja przesunięcia
                    anim = QPropertyAnimation(n, b"pos")
                    anim.setDuration(300)
                    anim.setStartValue(n.pos())
                    anim.setEndValue(QPoint(pos_x, pos_y))
                    anim.setEasingCurve(QEasingCurve.OutCubic)
                    anim.start()