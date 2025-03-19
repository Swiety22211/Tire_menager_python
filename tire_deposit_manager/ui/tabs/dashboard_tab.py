#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zakładka pulpitu - główny ekran aplikacji z podsumowaniem kluczowych informacji.
Zmodernizowana wersja z rozbudowaną funkcjonalnością i ulepszonym interfejsem.
"""

import os
import logging
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QSpacerItem, QGraphicsDropShadowEffect, QScrollArea, QCalendarWidget,
    QComboBox, QStackedWidget, QLineEdit, QToolButton, QMenu, QAction,
    QDialog, QTextEdit, QDialogButtonBox, QTabWidget
)
from PySide6.QtCore import (
    Qt, QSize, QDate, Signal, QTimer, QPropertyAnimation, 
    QEasingCurve, Property, QRect, QPoint
)
from PySide6.QtGui import (
    QIcon, QColor, QFont, QPainter, QPixmap, QPalette, QBrush, 
    QLinearGradient, QPen, QCursor
)
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from utils.paths import ICONS_DIR

# Logger
logger = logging.getLogger("TireDepositManager")

class AnimatedDashboardWidget(QFrame):
    """Widget do wyświetlania statystyk na pulpicie z animacją."""
    
    clicked = Signal()  # Sygnał emitowany przy kliknięciu w widget
    
    def __init__(self, title, value, icon_path=None, color="#3498db", parent=None):
        """
        Inicjalizacja widgetu statystyk z animacją.
        
        Args:
            title (str): Tytuł widgetu
            value (str): Wartość do wyświetlenia
            icon_path (str, optional): Ścieżka do ikony. Domyślnie None.
            color (str, optional): Kolor tła w formacie HEX. Domyślnie niebieski.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("dashboardWidget")
        self.setStyleSheet(f"""
            QFrame#dashboardWidget {{
                background-color: {color};
                border-radius: 12px;
                color: white;
                padding: 18px;
            }}
            
            QFrame#dashboardWidget:hover {{
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self._lighten_color(color, 20)}
                );
                border: 1px solid white;
            }}
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnej wysokości
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Nagłówek (ikona + tytuł)
        header_layout = QHBoxLayout()
        
        # Ikona jeśli podano
        self.icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        header_layout.addWidget(self.icon_label)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)
        
        layout.addLayout(header_layout)
        
        # Wartość
        self._current_value = 0
        self._target_value = int(value)
        self.value_label = QLabel("0")
        self.value_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.value_label.setStyleSheet("color: white; margin-top: 5px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Dodatkowy tekst informacyjny
        self.info_label = QLabel("Kliknij, aby zobaczyć szczegóły")
        self.info_label.setFont(QFont("Segoe UI", 9))
        self.info_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Ustawienie wskazówki
        self.setToolTip(f"Kliknij, aby zobaczyć szczegółowe informacje o {title.lower()}")
        
        # Animacja licznika
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_counter)
        self.timer.start(30)
        
        # Podłączenie zdarzenia kliknięcia
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def _update_counter(self):
        """Aktualizuje animowany licznik."""
        if self._current_value < self._target_value:
            # Przyrost wartości (szybciej na początku, wolniej przy końcu)
            increment = max(1, int((self._target_value - self._current_value) / 10))
            self._current_value += increment
            if self._current_value > self._target_value:
                self._current_value = self._target_value
            
            # Aktualizacja wyświetlanej wartości
            self.value_label.setText(str(self._current_value))
        else:
            self.timer.stop()
            
    def set_value(self, new_value):
        """Ustawia nową wartość z animacją."""
        self._target_value = int(new_value)
        # Zresetuj timer jeśli został zatrzymany
        if not self.timer.isActive():
            self.timer.start(30)
            
    def set_trend(self, percentage_change):
        """Ustawia informację o trendzie zmian."""
        if percentage_change > 0:
            trend_text = f"↑ +{percentage_change:.1f}% wzrost"
            trend_color = "rgba(46, 204, 113, 0.8)"
        elif percentage_change < 0:
            trend_text = f"↓ {percentage_change:.1f}% spadek"
            trend_color = "rgba(231, 76, 60, 0.8)"
        else:
            trend_text = "→ Bez zmian"
            trend_color = "rgba(255, 255, 255, 0.7)"
            
        self.info_label.setText(trend_text)
        self.info_label.setStyleSheet(f"color: {trend_color};")
        
    def _lighten_color(self, color, amount=20):
        """Rozjaśnia kolor HEX o podaną wartość."""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def mousePressEvent(self, event):
        """Obsługa kliknięcia w widget."""
        super().mousePressEvent(event)
        # Emitujemy sygnał kliknięcia
        self.clicked.emit()

class NotificationWidget(QFrame):
    """Widget powiadomień z możliwością rozwijania szczegółów."""
    
    def __init__(self, title, message, date, icon_path=None, priority="normal", parent=None):
        """
        Inicjalizacja widgetu powiadomień.
        
        Args:
            title (str): Tytuł powiadomienia
            message (str): Treść powiadomienia
            date (str): Data powiadomienia
            icon_path (str, optional): Ścieżka do ikony. Domyślnie None.
            priority (str, optional): Priorytet ("high", "normal", "low"). Domyślnie "normal".
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("notificationWidget")
        
        # Mapowanie priorytetów na kolory
        priority_colors = {
            "high": "#e74c3c",
            "normal": "#3498db",
            "low": "#2ecc71"
        }
        
        border_color = priority_colors.get(priority, "#3498db")
        
        self.setStyleSheet(f"""
            QFrame#notificationWidget {{
                background-color: white;
                border-left: 5px solid {border_color};
                border-radius: 5px;
                padding: 8px;
                margin: 3px;
            }}
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Główny układ
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Nagłówek (tytuł + data)
        header_layout = QHBoxLayout()
        
        # Ikona
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            header_layout.addWidget(icon_label)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title_label, 1)
        
        # Data
        date_label = QLabel(date)
        date_label.setFont(QFont("Segoe UI", 8))
        date_label.setStyleSheet("color: #7f8c8d;")
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(date_label)
        
        layout.addLayout(header_layout)
        
        # Treść powiadomienia
        message_label = QLabel(message)
        message_label.setFont(QFont("Segoe UI", 9))
        message_label.setStyleSheet("color: #34495e;")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Przyciski akcji
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 5, 0, 0)
        
        # Przycisk szczegółów
        details_button = QPushButton("Szczegóły")
        details_button.setFont(QFont("Segoe UI", 8))
        details_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3498db;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                color: #2980b9;
                text-decoration: underline;
            }
        """)
        details_button.setCursor(QCursor(Qt.PointingHandCursor))
        action_layout.addWidget(details_button)
        
        # Przycisk oznaczenia jako przeczytane
        mark_read_button = QPushButton("Oznacz jako przeczytane")
        mark_read_button.setFont(QFont("Segoe UI", 8))
        mark_read_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8c8d;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                color: #34495e;
                text-decoration: underline;
            }
        """)
        mark_read_button.setCursor(QCursor(Qt.PointingHandCursor))
        action_layout.addWidget(mark_read_button, alignment=Qt.AlignRight)
        
        layout.addLayout(action_layout)
        
        # Podłączenie zdarzeń
        details_button.clicked.connect(self._show_details)
        mark_read_button.clicked.connect(self._mark_as_read)
        
        # Zachowanie treści do wyświetlenia szczegółów
        self._title = title
        self._message = message
        self._date = date
        
    def _show_details(self):
        """Pokazuje dialog ze szczegółami powiadomienia."""
        dialog = QDialog(self.parent())
        dialog.setWindowTitle("Szczegóły powiadomienia")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Tytuł
        title_label = QLabel(self._title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Data
        date_label = QLabel(f"Data: {self._date}")
        date_label.setFont(QFont("Segoe UI", 9))
        date_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(date_label)
        
        # Treść
        message_edit = QTextEdit()
        message_edit.setFont(QFont("Segoe UI", 10))
        message_edit.setText(self._message)
        message_edit.setReadOnly(True)
        layout.addWidget(message_edit)
        
        # Przyciski
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.exec_()
        
    def _mark_as_read(self):
        """Oznacza powiadomienie jako przeczytane (ukrywa je)."""
        self.hide()
        # W prawdziwej aplikacji dodalibyśmy kod do aktualizacji bazy danych

class ActionButtonWidget(QFrame):
    """Widget z przyciskiem szybkiej akcji."""
    
    clicked = Signal()  # Sygnał emitowany przy kliknięciu w widget
    
    def __init__(self, title, icon_path, color="#3498db", parent=None):
        """
        Inicjalizacja widgetu przycisku akcji.
        
        Args:
            title (str): Tytuł przycisku
            icon_path (str): Ścieżka do ikony
            color (str, optional): Kolor tła w formacie HEX. Domyślnie niebieski.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("actionButtonWidget")
        self.setStyleSheet(f"""
            QFrame#actionButtonWidget {{
                background-color: {color};
                border-radius: 10px;
                color: white;
                padding: 10px;
            }}
            
            QFrame#actionButtonWidget:hover {{
                background-color: {self._lighten_color(color)};
                border: 1px solid white;
            }}
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnych wymiarów
        self.setMinimumSize(120, 120)
        self.setMaximumSize(120, 120)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Ikona
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        # Ustawienie wskazówki
        self.setToolTip(f"Kliknij, aby {title.lower()}")
        
        # Podłączenie zdarzenia kliknięcia
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def _lighten_color(self, color, amount=20):
        """Rozjaśnia kolor HEX o podaną wartość."""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def mousePressEvent(self, event):
        """Obsługa kliknięcia w widget."""
        super().mousePressEvent(event)
        # Emitujemy sygnał kliknięcia
        self.clicked.emit()

class PieChartWidget(QFrame):
    """Widget wykresu kołowego."""
    
    def __init__(self, title, data, colors=None, parent=None):
        """
        Inicjalizacja widgetu wykresu kołowego.
        
        Args:
            title (str): Tytuł wykresu
            data (dict): Dane w formacie {etykieta: wartość}
            colors (list, optional): Lista kolorów dla wykresów. Domyślnie None.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("chartWidget")
        self.setStyleSheet("""
            QFrame#chartWidget {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnych wymiarów
        self.setMinimumHeight(250)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Wykres kołowy
        self.chart = QChart()
        self.chart.setTitle("")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        # Seria danych
        series = QPieSeries()
        
        # Domyślne kolory
        if colors is None:
            colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22']
        
        # Dodaj elementy
        for i, (label, value) in enumerate(data.items()):
            slice = series.append(label, value)
            slice.setLabelVisible(True)
            slice.setLabel(f"{label}: {value} ({value / sum(data.values()) * 100:.1f}%)")
            slice.setBrush(QColor(colors[i % len(colors)]))
        
        self.chart.addSeries(series)
        
        # Widok wykresu
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(chart_view)

class BarChartWidget(QFrame):
    """Widget wykresu słupkowego."""
    
    def __init__(self, title, data, categories, color="#3498db", parent=None):
        """
        Inicjalizacja widgetu wykresu słupkowego.
        
        Args:
            title (str): Tytuł wykresu
            data (list): Lista wartości dla słupków
            categories (list): Lista kategorii (etykiet) dla słupków
            color (str, optional): Kolor słupków. Domyślnie niebieski.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("chartWidget")
        self.setStyleSheet("""
            QFrame#chartWidget {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnych wymiarów
        self.setMinimumHeight(250)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Wykres słupkowy
        self.chart = QChart()
        self.chart.setTitle("")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Seria danych
        bar_set = QBarSet("Wartość")
        bar_set.setColor(QColor(color))
        
        # Dodaj elementy
        for value in data:
            bar_set.append(value)
        
        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)
        
        # Osie
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(data) * 1.1)  # Dodaj 10% na górze
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Legenda
        self.chart.legend().setVisible(False)
        
        # Widok wykresu
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(chart_view)

class SearchBarWidget(QFrame):
    """Widget paska wyszukiwania."""
    
    search_requested = Signal(str)  # Sygnał emitowany przy wyszukiwaniu
    
    def __init__(self, parent=None):
        """Inicjalizacja widgetu paska wyszukiwania."""
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("searchBarWidget")
        self.setStyleSheet("""
            QFrame#searchBarWidget {
                background-color: white;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Układ widgetu
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Ikona wyszukiwania
        icon_label = QLabel()
        icon_path = os.path.join(ICONS_DIR, "search.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)
        
        # Pole wyszukiwania
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj klientów, opon, depozytów...")
        self.search_edit.setFont(QFont("Segoe UI", 10))
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 5px;
            }
        """)
        layout.addWidget(self.search_edit)
        
        # Przycisk filtrowania
        filter_button = QToolButton()
        filter_button.setIcon(QIcon(os.path.join(ICONS_DIR, "filter.png")))
        filter_button.setToolTip("Filtry wyszukiwania")
        filter_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        layout.addWidget(filter_button)
        
        # Menu filtrów
        filter_menu = QMenu(filter_button)
        filter_menu.addAction("Klienci")
        filter_menu.addAction("Depozyty")
        filter_menu.addAction("Wizyty")
        filter_menu.addAction("Opony")
        filter_button.setMenu(filter_menu)
        filter_button.setPopupMode(QToolButton.InstantPopup)
        
        # Podłączenie sygnałów
        self.search_edit.returnPressed.connect(self._search)
        
    def _search(self):
        """Wyszukuje podany tekst."""
        search_text = self.search_edit.text()
        if search_text:
            # Emitujemy sygnał z tekstem wyszukiwania
            self.search_requested.emit(search_text)

class WeatherWidget(QFrame):
    """Widget do wyświetlania prognozy pogody."""
    
    def __init__(self, parent=None):
        """Inicjalizacja widgetu prognozy pogody."""
        super().__init__(parent)
        
class ActionButtonWidget(QFrame):
    """Widget z przyciskiem szybkiej akcji."""
    
    clicked = Signal()  # Sygnał emitowany przy kliknięciu w widget
    
    def __init__(self, title, icon_path, color="#3498db", parent=None):
        """
        Inicjalizacja widgetu przycisku akcji.
        
        Args:
            title (str): Tytuł przycisku
            icon_path (str): Ścieżka do ikony
            color (str, optional): Kolor tła w formacie HEX. Domyślnie niebieski.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("actionButtonWidget")
        self.setStyleSheet(f"""
            QFrame#actionButtonWidget {{
                background-color: {color};
                border-radius: 10px;
                color: white;
                padding: 10px;
            }}
            
            QFrame#actionButtonWidget:hover {{
                background-color: {self._lighten_color(color)};
                border: 1px solid white;
            }}
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnych wymiarów
        self.setMinimumSize(120, 120)
        self.setMaximumSize(120, 120)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Ikona
        icon_label = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        # Ustawienie wskazówki
        self.setToolTip(f"Kliknij, aby {title.lower()}")
        
        # Podłączenie zdarzenia kliknięcia
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def _lighten_color(self, color, amount=20):
        """Rozjaśnia kolor HEX o podaną wartość."""
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def mousePressEvent(self, event):
        """Obsługa kliknięcia w widget."""
        super().mousePressEvent(event)
        # Emitujemy sygnał kliknięcia
        self.clicked.emit()

class PieChartWidget(QFrame):
    """Widget wykresu kołowego."""
    
    def __init__(self, title, data, colors=None, parent=None):
        """
        Inicjalizacja widgetu wykresu kołowego.
        
        Args:
            title (str): Tytuł wykresu
            data (dict): Dane w formacie {etykieta: wartość}
            colors (list, optional): Lista kolorów dla wykresów. Domyślnie None.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("chartWidget")
        self.setStyleSheet("""
            QFrame#chartWidget {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnych wymiarów
        self.setMinimumHeight(250)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Wykres kołowy
        self.chart = QChart()
        self.chart.setTitle("")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        
        # Seria danych
        series = QPieSeries()
        
        # Domyślne kolory
        if colors is None:
            colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22']
        
        # Dodaj elementy
        for i, (label, value) in enumerate(data.items()):
            slice = series.append(label, value)
            slice.setLabelVisible(True)
            slice.setLabel(f"{label}: {value} ({value / sum(data.values()) * 100:.1f}%)")
            slice.setBrush(QColor(colors[i % len(colors)]))
        
        self.chart.addSeries(series)
        
        # Widok wykresu
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(chart_view)

class BarChartWidget(QFrame):
    """Widget wykresu słupkowego."""
    
    def __init__(self, title, data, categories, color="#3498db", parent=None):
        """
        Inicjalizacja widgetu wykresu słupkowego.
        
        Args:
            title (str): Tytuł wykresu
            data (list): Lista wartości dla słupków
            categories (list): Lista kategorii (etykiet) dla słupków
            color (str, optional): Kolor słupków. Domyślnie niebieski.
            parent (QWidget, optional): Widget rodzica. Domyślnie None.
        """
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("chartWidget")
        self.setStyleSheet("""
            QFrame#chartWidget {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Ustawienie minimalnych wymiarów
        self.setMinimumHeight(250)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Tytuł
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Wykres słupkowy
        self.chart = QChart()
        self.chart.setTitle("")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Seria danych
        bar_set = QBarSet("Wartość")
        bar_set.setColor(QColor(color))
        
        # Dodaj elementy
        for value in data:
            bar_set.append(value)
        
        series = QBarSeries()
        series.append(bar_set)
        self.chart.addSeries(series)
        
        # Osie
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(data) * 1.1)  # Dodaj 10% na górze
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Legenda
        self.chart.legend().setVisible(False)
        
        # Widok wykresu
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(chart_view)

class SearchBarWidget(QFrame):
    """Widget paska wyszukiwania."""
    
    search_requested = Signal(str)  # Sygnał emitowany przy wyszukiwaniu
    
    def __init__(self, parent=None):
        """Inicjalizacja widgetu paska wyszukiwania."""
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("searchBarWidget")
        self.setStyleSheet("""
            QFrame#searchBarWidget {
                background-color: white;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Układ widgetu
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Ikona wyszukiwania
        icon_label = QLabel()
        icon_path = os.path.join(ICONS_DIR, "search.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        layout.addWidget(icon_label)
        
        # Pole wyszukiwania
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Szukaj klientów, opon, depozytów...")
        self.search_edit.setFont(QFont("Segoe UI", 10))
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 5px;
            }
        """)
        layout.addWidget(self.search_edit)
        
        # Przycisk filtrowania
        filter_button = QToolButton()
        filter_button.setIcon(QIcon(os.path.join(ICONS_DIR, "filter.png")))
        filter_button.setToolTip("Filtry wyszukiwania")
        filter_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        layout.addWidget(filter_button)
        
        # Menu filtrów
        filter_menu = QMenu(filter_button)
        filter_menu.addAction("Klienci")
        filter_menu.addAction("Depozyty")
        filter_menu.addAction("Wizyty")
        filter_menu.addAction("Opony")
        filter_button.setMenu(filter_menu)
        filter_button.setPopupMode(QToolButton.InstantPopup)
        
        # Podłączenie sygnałów
        self.search_edit.returnPressed.connect(self._search)
        
    def _search(self):
        """Wyszukuje podany tekst."""
        search_text = self.search_edit.text()
        if search_text:
            # Emitujemy sygnał z tekstem wyszukiwania
            self.search_requested.emit(search_text)

class WeatherWidget(QFrame):
    """Widget do wyświetlania prognozy pogody."""
    
    def __init__(self, parent=None):
        """Inicjalizacja widgetu prognozy pogody."""
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("weatherWidget")
        self.setStyleSheet("""
            QFrame#weatherWidget {
                background-color: #3498db;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Nagłówek z lokalizacją
        location_layout = QHBoxLayout()
        
        location_label = QLabel("Warszawa")
        location_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        location_label.setStyleSheet("color: white;")
        location_layout.addWidget(location_label)
        
        # Przycisk odświeżania
        refresh_button = QToolButton()
        refresh_button.setIcon(QIcon(os.path.join(ICONS_DIR, "refresh.png")))
        refresh_button.setStyleSheet("""
            QToolButton {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        refresh_button.setFixedSize(30, 30)
        location_layout.addWidget(refresh_button, alignment=Qt.AlignRight)
        
        layout.addLayout(location_layout)
        
        # Informacje o aktualnej pogodzie
        current_weather_layout = QHBoxLayout()
        
        # Ikona pogody
        weather_icon_label = QLabel()
        weather_icon_path = os.path.join(ICONS_DIR, "sun.png")  # Przykładowa ikona
        if os.path.exists(weather_icon_path):
            pixmap = QPixmap(weather_icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            weather_icon_label.setPixmap(pixmap)
        current_weather_layout.addWidget(weather_icon_label)
        
        # Temperatura i opis
        temp_layout = QVBoxLayout()
        
        temp_label = QLabel("12°C")
        temp_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        temp_label.setStyleSheet("color: white;")
        temp_layout.addWidget(temp_label)
        
        desc_label = QLabel("Słonecznie")
        desc_label.setFont(QFont("Segoe UI", 12))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        temp_layout.addWidget(desc_label)
        
        current_weather_layout.addLayout(temp_layout)
        
        layout.addLayout(current_weather_layout)
        
        # Dodatkowe informacje
        details_frame = QFrame()
        details_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px;
            }
        """)
        details_layout = QGridLayout(details_frame)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(10)
        
        # Wiersz 1
        details_layout.addWidget(QLabel("Wilgotność:"), 0, 0)
        details_layout.addWidget(QLabel("45%"), 0, 1)
        details_layout.addWidget(QLabel("Wiatr:"), 0, 2)
        details_layout.addWidget(QLabel("10 km/h"), 0, 3)
        
        # Wiersz 2
        details_layout.addWidget(QLabel("Ciśnienie:"), 1, 0)
        details_layout.addWidget(QLabel("1013 hPa"), 1, 1)
        details_layout.addWidget(QLabel("Widoczność:"), 1, 2)
        details_layout.addWidget(QLabel("10 km"), 1, 3)
        
        # Ustawienie stylu etykiet
        for i in range(details_layout.count()):
            widget = details_layout.itemAt(i).widget()
            if widget:
                widget.setFont(QFont("Segoe UI", 9))
                widget.setStyleSheet("color: white;")
        
        layout.addWidget(details_frame)
        
        # Podłączenie sygnałów
        refresh_button.clicked.connect(self._refresh_weather)
        
    def _refresh_weather(self):
        """Odświeża dane pogodowe."""
        # W rzeczywistej aplikacji, tutaj pobieralibyśmy dane z API pogodowego
        # Na potrzeby przykładu, symulujemy odświeżanie
        self.setDisabled(True)
        QTimer.singleShot(1000, lambda: self.setDisabled(False))

class UpcomingAppointmentsWidget(QFrame):
    """Widget do wyświetlania nadchodzących wizyt."""
    
    view_all_requested = Signal()
    date_selected = Signal(QDate)
    
    def __init__(self, parent=None):
        """Inicjalizacja widgetu nadchodzących wizyt."""
        super().__init__(parent)
        
        # Ustawienie stylu
        self.setObjectName("upcomingAppointmentsWidget")
        self.setStyleSheet("""
            QFrame#upcomingAppointmentsWidget {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Układ widgetu
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Nagłówek
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Najbliższe wizyty")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title_label)
        
        view_all_button = QPushButton("Zobacz wszystkie")
        view_all_button.setFont(QFont("Segoe UI", 9))
        view_all_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3498db;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                color: #2980b9;
                text-decoration: underline;
            }
        """)
        view_all_button.setCursor(QCursor(Qt.PointingHandCursor))
        header_layout.addWidget(view_all_button, alignment=Qt.AlignRight)
        
        layout.addLayout(header_layout)
        
        # Widok kalendarza i listy
        appointments_tabs = QTabWidget()
        appointments_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabBar::tab {
                background: #f2f2f2;
                border: 1px solid #ddd;
                padding: 6px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
        """)
        
        # Zakładka kalendarza
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar.setStyleSheet("""
            QCalendarWidget QWidget {
                alternate-background-color: #f7f7f7;
            }
            QCalendarWidget QAbstractItemView:enabled {
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        calendar_layout.addWidget(calendar)
        
        appointments_tabs.addTab(calendar_widget, "Kalendarz")
        
        # Zakładka listy
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        # Przykładowe dane wizyt
        appointments = [
            {"client": "Jan Kowalski", "service": "Zmiana opon", "date": "Dzisiaj, 14:30", "status": "Potwierdzona"},
            {"client": "Anna Nowak", "service": "Odbiór depozytu", "date": "Jutro, 10:00", "status": "Oczekująca"},
            {"client": "Marcin Wiśniewski", "service": "Badanie stanu opon", "date": "22.03.2025, 12:15", "status": "Potwierdzona"}
        ]
        
        for appointment in appointments:
            appointment_frame = QFrame()
            appointment_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 8px;
                    margin-bottom: 5px;
                }
            """)
            
            appointment_layout = QVBoxLayout(appointment_frame)
            appointment_layout.setContentsMargins(10, 10, 10, 10)
            appointment_layout.setSpacing(5)
            
            # Dane wizyty
            client_label = QLabel(appointment["client"])
            client_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            appointment_layout.addWidget(client_label)
            
            service_label = QLabel(appointment["service"])
            service_label.setFont(QFont("Segoe UI", 9))
            appointment_layout.addWidget(service_label)
            
            # Data i status
            details_layout = QHBoxLayout()
            
            date_label = QLabel(appointment["date"])
            date_label.setFont(QFont("Segoe UI", 9))
            date_label.setStyleSheet("color: #7f8c8d;")
            details_layout.addWidget(date_label)
            
            status_label = QLabel(appointment["status"])
            status_label.setFont(QFont("Segoe UI", 9))
            
            if appointment["status"] == "Potwierdzona":
                status_label.setStyleSheet("color: #2ecc71;")
            elif appointment["status"] == "Oczekująca":
                status_label.setStyleSheet("color: #f39c12;")
            else:
                status_label.setStyleSheet("color: #e74c3c;")
            
            details_layout.addWidget(status_label, alignment=Qt.AlignRight)
            
            appointment_layout.addLayout(details_layout)
            
            # Przycisk szczegółów
            details_button = QPushButton("Zarządzaj")
            details_button.setFont(QFont("Segoe UI", 8))
            details_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            appointment_layout.addWidget(details_button, alignment=Qt.AlignRight)
            
            list_layout.addWidget(appointment_frame)
        
        list_layout.addStretch(1)
        
        appointments_tabs.addTab(list_widget, "Lista")
        
        layout.addWidget(appointments_tabs)
        
        # Podłączenie sygnałów
        view_all_button.clicked.connect(self._view_all_appointments)
        calendar.clicked.connect(self._date_selected)
        
    def _view_all_appointments(self):
        """Pokazuje wszystkie wizyty."""
        # Emitujemy sygnał, który powinien przełączyć widok na zakładkę wizyt
        self.view_all_requested.emit()
        
    def _date_selected(self, date):
        """Obsługuje wybranie daty w kalendarzu."""
        # Emitujemy sygnał z wybraną datą
        self.date_selected.emit(date)

class RecentActivitiesWidget(QTableWidget):
    """Tabela ostatnich działań z rozbudowaną funkcjonalnością."""
    
    details_requested = Signal(str, str, str, str)
    refresh_requested = Signal()
    
    def __init__(self, parent=None):
        """Inicjalizacja rozbudowanej tabeli ostatnich działań."""
        super().__init__(parent)
        
        # Ustawienie stylów
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 10px;
                padding: 5px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #3498db;
                font-weight: bold;
                color: #2c3e50;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)
        
        # Dodaj efekt cienia
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Konfiguracja tabeli
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Data", "Typ", "Opis", "Status", "Akcje"
        ])
        
        # Ustawienie rozciągania kolumn
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Data
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Typ
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Opis
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Akcje
        
        # Ukryj nagłówki wierszy
        self.verticalHeader().setVisible(False)
        
        # Włącz sortowanie
        self.setSortingEnabled(True)
        
        # Ustaw domyślne sortowanie według daty (malejąco)
        self.sortItems(0, Qt.DescendingOrder)
        
        # Ustaw wysokość wierszy
        self.verticalHeader().setDefaultSectionSize(50)
        
        # Wyłącz edycję komórek
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Włącz zaznaczanie całych wierszy
        self.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Kontekstowe menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def add_action(self, date, type_action, description, status):
        """
        Dodaje akcję do tabeli.
        
        Args:
            date (str): Data w formacie string
            type_action (str): Typ akcji
            description (str): Opis akcji
            status (str): Status akcji
        """
        row = self.rowCount()
        self.insertRow(row)
        
        # Dodaj dane do tabeli
        self.setItem(row, 0, QTableWidgetItem(date))
        self.setItem(row, 1, QTableWidgetItem(type_action))
        self.setItem(row, 2, QTableWidgetItem(description))
        
        # Status z odpowiednim kolorem tła
        status_item = QTableWidgetItem(status)
        
        if status == "Zakończona" or status == "Aktywny":
            status_item.setBackground(QColor("#e6f7ed"))  # Jasny zielony
            status_item.setForeground(QColor("#2ecc71"))  # Zielony
        elif status == "W trakcie":
            status_item.setBackground(QColor("#fff8e6"))  # Jasny pomarańczowy
            status_item.setForeground(QColor("#f39c12"))  # Pomarańczowy
        elif status == "Anulowana" or status == "Przeterminowany":
            status_item.setBackground(QColor("#fde9e9"))  # Jasny czerwony
            status_item.setForeground(QColor("#e74c3c"))  # Czerwony
        
        self.setItem(row, 3, status_item)
        
        # Przycisk akcji
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 0, 5, 0)
        actions_layout.setSpacing(5)
        
        details_button = QPushButton()
        details_button.setIcon(QIcon(os.path.join(ICONS_DIR, "details.png")))
        details_button.setToolTip("Szczegóły")
        details_button.setFixedSize(30, 30)
        details_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border-radius: 15px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Tagujemy przyciski z numerem wiersza
        details_button.setProperty("row", row)
        details_button.clicked.connect(lambda: self._show_details(self.sender().property("row")))
        
        actions_layout.addWidget(details_button)
        
        self.setCellWidget(row, 4, actions_widget)
    
    def _show_details(self, row):
        """
        Pokazuje szczegóły akcji z wybranego wiersza.
        
        Args:
            row (int): Numer wiersza
        """
        if row is None:
            return
            
        date = self.item(row, 0).text()
        type_action = self.item(row, 1).text()
        description = self.item(row, 2).text()
        status = self.item(row, 3).text()
        
        # Emitujemy sygnał ze szczegółami
        self.details_requested.emit(date, type_action, description, status)
    
    def _show_context_menu(self, position):
        """
        Pokazuje menu kontekstowe.
        
        Args:
            position (QPoint): Pozycja kursora
        """
        menu = QMenu(self)
        
        details_action = QAction("Szczegóły", self)
        export_action = QAction("Eksportuj", self)
        refresh_action = QAction("Odśwież", self)
        
        menu.addAction(details_action)
        menu.addAction(export_action)
        menu.addSeparator()
        menu.addAction(refresh_action)
        
        # Podłącz akcje
        selected_row = self.currentRow()
        if selected_row >= 0:
            details_action.triggered.connect(lambda: self._show_details(selected_row))
        else:
            details_action.setEnabled(False)
            
        export_action.triggered.connect(self._export_data)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        
        # Pokaż menu
        menu.exec_(self.mapToGlobal(position))
    
    def _export_data(self):
        """Eksport danych z tabeli."""
        # W rzeczywistej aplikacji dodalibyśmy kod do eksportu
        print("Eksport danych...")

class DashboardTab(QWidget):
    """
    Rozbudowana zakładka pulpitu wyświetlająca podsumowanie kluczowych informacji.
    """
    
    tab_change_requested = Signal(str)  # Sygnał do zmiany zakładki
    action_requested = Signal(str)      # Sygnał do wykonania akcji
    
    def __init__(self, db_connection):
        """
        Inicjalizacja zakładki pulpitu.
        
        Args:
            db_connection: Połączenie z bazą danych SQLite
        """
        super().__init__()
        
        self.conn = db_connection
        
        # Inicjalizacja interfejsu użytkownika
        self.init_ui()
        
        # Odświeżenie danych
        self.refresh_data()
    
    def init_ui(self):
        """Inicjalizacja interfejsu użytkownika zakładki."""
        # Główny układ
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Górny pasek (powitanie, wyszukiwarka, data)
        top_bar_layout = QHBoxLayout()
        
        # Powitanie
        welcome_frame = QFrame()
        welcome_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        welcome_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        shadow = QGraphicsDropShadowEffect(welcome_frame)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        welcome_frame.setGraphicsEffect(shadow)
        
        welcome_layout = QHBoxLayout(welcome_frame)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(ICONS_DIR, "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        welcome_layout.addWidget(logo_label)
        
        # Tekst powitania
        greeting_layout = QVBoxLayout()
        
        welcome_label = QLabel("Witaj w Menadżerze Depozytów Opon!")
        welcome_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        welcome_label.setStyleSheet("color: #2c3e50;")
        greeting_layout.addWidget(welcome_label)
        
        sub_welcome_label = QLabel("Twój serwis opon działa sprawnie")
        sub_welcome_label.setFont(QFont("Segoe UI", 10))
        sub_welcome_label.setStyleSheet("color: #7f8c8d;")
        greeting_layout.addWidget(sub_welcome_label)
        
        welcome_layout.addLayout(greeting_layout)
        
        top_bar_layout.addWidget(welcome_frame)
        
        # Wyszukiwarka
        search_bar = SearchBarWidget()
        search_bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        search_bar.setFixedWidth(300)
        top_bar_layout.addWidget(search_bar)
        
        # Data
        date_frame = QFrame()
        date_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        date_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        shadow = QGraphicsDropShadowEffect(date_frame)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        date_frame.setGraphicsEffect(shadow)
        
        date_layout = QVBoxLayout(date_frame)
        date_layout.setAlignment(Qt.AlignCenter)
        
        day_label = QLabel(datetime.now().strftime("%d"))
        day_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        day_label.setStyleSheet("color: #e74c3c;")
        day_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(day_label)
        
        month_year_label = QLabel(datetime.now().strftime("%b %Y"))
        month_year_label.setFont(QFont("Segoe UI", 12))
        month_year_label.setStyleSheet("color: #7f8c8d;")
        month_year_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(month_year_label)
        
        top_bar_layout.addWidget(date_frame)
        
        main_layout.addLayout(top_bar_layout)
        
        # Środkowa sekcja (karty statystyk i przyciski szybkich akcji)
        mid_section_layout = QHBoxLayout()
        
        # Widgety statystyk
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        # Widgets do statystyk z animacją
        self.clients_widget = AnimatedDashboardWidget(
            "Klienci", "0", 
            os.path.join(ICONS_DIR, "client.png"), 
            "#3498db"
        )
        stats_layout.addWidget(self.clients_widget, 0, 0)
        
        self.deposits_widget = AnimatedDashboardWidget(
            "Depozyty", "0", 
            os.path.join(ICONS_DIR, "tire.png"), 
            "#2ecc71"
        )
        stats_layout.addWidget(self.deposits_widget, 0, 1)
        
        self.inventory_widget = AnimatedDashboardWidget(
            "Opony na stanie", "0", 
            os.path.join(ICONS_DIR, "inventory.png"), 
            "#f39c12"
        )
        stats_layout.addWidget(self.inventory_widget, 1, 0)
        
        self.appointments_widget = AnimatedDashboardWidget(
            "Najbliższe wizyty", "0", 
            os.path.join(ICONS_DIR, "calendar.png"), 
            "#e74c3c"
        )
        stats_layout.addWidget(self.appointments_widget, 1, 1)
        
        mid_section_layout.addLayout(stats_layout, 2)
        
        # Przyciski szybkich akcji i pogoda
        quick_actions_layout = QVBoxLayout()
        quick_actions_layout.setSpacing(15)
        
        # Pogoda
        weather_widget = WeatherWidget()
        quick_actions_layout.addWidget(weather_widget)
        
        # Przyciski szybkich akcji
        quick_actions_frame = QFrame()
        quick_actions_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(quick_actions_frame)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        quick_actions_frame.setGraphicsEffect(shadow)
        
        quick_buttons_layout = QVBoxLayout(quick_actions_frame)
        
        # Tytuł
        quick_actions_title = QLabel("Szybkie akcje")
        quick_actions_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        quick_actions_title.setStyleSheet("color: #2c3e50;")
        quick_buttons_layout.addWidget(quick_actions_title)
        
        # Przyciski
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(10)
        
        add_client_button = ActionButtonWidget(
            "Dodaj klienta", os.path.join(ICONS_DIR, "add_client.png"), "#3498db"
        )
        buttons_grid.addWidget(add_client_button, 0, 0)
        
        add_deposit_button = ActionButtonWidget(
            "Nowy depozyt", os.path.join(ICONS_DIR, "add_deposit.png"), "#2ecc71"
        )
        buttons_grid.addWidget(add_deposit_button, 0, 1)
        
        add_appointment_button = ActionButtonWidget(
            "Zaplanuj wizytę", os.path.join(ICONS_DIR, "add_appointment.png"), "#e74c3c"
        )
        buttons_grid.addWidget(add_appointment_button, 1, 0)
        
        generate_report_button = ActionButtonWidget(
            "Generuj raport", os.path.join(ICONS_DIR, "report.png"), "#9b59b6"
        )
        buttons_grid.addWidget(generate_report_button, 1, 1)
        
        quick_buttons_layout.addLayout(buttons_grid)
        
        quick_actions_layout.addWidget(quick_actions_frame)
        
        mid_section_layout.addLayout(quick_actions_layout, 1)
        
        main_layout.addLayout(mid_section_layout)
        
        # Dolna sekcja
        bottom_section_layout = QHBoxLayout()
        
        # Nadchodzące wizyty
        upcoming_appointments = UpcomingAppointmentsWidget()
        bottom_section_layout.addWidget(upcoming_appointments, 1)
        
        # Aktywności
        activities_layout = QVBoxLayout()
        
        activities_header = QHBoxLayout()
        
        activities_label = QLabel("Ostatnie działania")
        activities_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        activities_label.setStyleSheet("color: #2c3e50;")
        activities_header.addWidget(activities_label)
        
        filter_combo = QComboBox()
        filter_combo.addItems(["Wszystkie", "Klienci", "Depozyty", "Wizyty"])
        filter_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ddd;
            }
        """)
        activities_header.addWidget(filter_combo, alignment=Qt.AlignRight)
        
        activities_layout.addLayout(activities_header)
        
        # Tabela ostatnich działań
        self.recent_actions_table = RecentActivitiesWidget()
        activities_layout.addWidget(self.recent_actions_table)
        
        bottom_section_layout.addLayout(activities_layout, 2)
        
        main_layout.addLayout(bottom_section_layout)
        
        # Połączenie zdarzeń
        self.clients_widget.clicked.connect(lambda: self._show_tab("clients"))
        self.deposits_widget.clicked.connect(lambda: self._show_tab("deposits"))
        self.inventory_widget.clicked.connect(lambda: self._show_tab("inventory"))
        self.appointments_widget.clicked.connect(lambda: self._show_tab("appointments"))
        
        add_client_button.clicked.connect(self._add_client)
        add_deposit_button.clicked.connect(self._add_deposit)
        add_appointment_button.clicked.connect(self._add_appointment)
        generate_report_button.clicked.connect(self._generate_report)
        
        upcoming_appointments.view_all_requested.connect(lambda: self._show_tab("appointments"))
        
        self.recent_actions_table.details_requested.connect(self._show_action_details)
        self.recent_actions_table.refresh_requested.connect(self.refresh_data)
        
        search_bar.search_requested.connect(self._search)
        filter_combo.currentTextChanged.connect(self._filter_activities)
    
    def refresh_data(self):
        """Odświeża dane na pulpicie."""
        try:
            cursor = self.conn.cursor()
            
            # Aktualizacja liczby klientów
            cursor.execute("SELECT COUNT(*) FROM clients")
            clients_count = cursor.fetchone()[0]
            self.clients_widget.set_value(str(clients_count))
            
            # Dodaj informację o trendzie (przykładowo +5.2% wzrost)
            self.clients_widget.set_trend(5.2)
            
            # Aktualizacja liczby depozytów
            cursor.execute("SELECT COUNT(*) FROM deposits WHERE status = 'Aktywny'")
            deposits_count = cursor.fetchone()[0]
            self.deposits_widget.set_value(str(deposits_count))
            self.deposits_widget.set_trend(2.8)
            
            # Aktualizacja liczby opon na stanie
            cursor.execute("SELECT COUNT(*) FROM inventory")
            inventory_count = cursor.fetchone()[0]
            self.inventory_widget.set_value(str(inventory_count))
            self.inventory_widget.set_trend(-1.5)
            
            # Aktualizacja liczby najbliższych wizyt
            today = datetime.now().date()
            cursor.execute("""
                SELECT COUNT(*) FROM appointments 
                WHERE appointment_date >= ? AND status != 'Anulowana'
            """, (today.strftime("%Y-%m-%d"),))
            appointments_count = cursor.fetchone()[0]
            self.appointments_widget.set_value(str(appointments_count))
            self.appointments_widget.set_trend(10.0)
            
            # Ładowanie ostatnich działań
            self.load_recent_actions()
            
        except Exception as e:
            logger.error(f"Błąd podczas odświeżania danych pulpitu: {e}")
    
    def load_recent_actions(self):
        """Ładuje listę ostatnich działań z różnych tabel."""
        try:
            cursor = self.conn.cursor()
            
            # Pobierz ostatnie działania z różnych tabel
            cursor.execute("""
                SELECT 'Klient' as type, name as description, 'Dodano' as status, 
                       created_at as date
                FROM clients 
                ORDER BY created_at DESC 
                LIMIT 5
                
                UNION ALL
                
                SELECT 'Wizyta', service_type, status, appointment_date
                FROM appointments 
                ORDER BY appointment_date DESC 
                LIMIT 5
                
                UNION ALL
                
                SELECT 'Depozyt', tire_brand || ' ' || tire_size, status, deposit_date
                FROM deposits 
                ORDER BY deposit_date DESC 
                LIMIT 5
                
                ORDER BY date DESC
                LIMIT 10
            """)
            
            actions = cursor.fetchall()
            
            # Czyszczenie tabeli
            self.recent_actions_table.setRowCount(0)
            
            # Wypełnienie tabeli
            for type_action, description, status, date in actions:
                # Formatowanie daty
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d.%m.%Y")
                except (ValueError, TypeError):
                    formatted_date = date
                
                # Dodaj dane do tabeli
                self.recent_actions_table.add_action(
                    formatted_date,
                    type_action,
                    description,
                    status
                )
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania ostatnich działań: {e}")
    
    def _show_tab(self, tab_name):
        """
        Przełącza do wybranej zakładki.
        
        Args:
            tab_name (str): Nazwa zakładki do pokazania
        """
        # Emitujemy sygnał ze zmianą zakładki
        # Ten sygnał powinien być obsłużony przez główne okno aplikacji
        self.tab_change_requested.emit(tab_name)
        
    def _add_client(self):
        """Obsługuje dodawanie nowego klienta."""
        self.action_requested.emit("add_client")
        
    def _add_deposit(self):
        """Obsługuje dodawanie nowego depozytu."""
        self.action_requested.emit("add_deposit")
        
    def _add_appointment(self):
        """Obsługuje dodawanie nowej wizyty."""
        self.action_requested.emit("add_appointment")
        
    def _generate_report(self):
        """Obsługuje generowanie raportu."""
        self.action_requested.emit("generate_report")
        
    def _show_action_details(self, date, type_action, description, status):
        """
        Pokazuje szczegóły wybranej akcji.
        
        Args:
            date (str): Data akcji
            type_action (str): Typ akcji
            description (str): Opis akcji
            status (str): Status akcji
        """
        # W rzeczywistej aplikacji, ta metoda wyświetlałaby dialog ze szczegółami
        # lub przełączała do odpowiedniej zakładki z wybranym elementem
        
        # Przykładowa implementacja - wygenerowanie prostego dialogu ze szczegółami
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{type_action} - Szczegóły")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Tytuł
        title_label = QLabel(description)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Informacje
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("Typ:"), 0, 0)
        info_layout.addWidget(QLabel(type_action), 0, 1)
        
        info_layout.addWidget(QLabel("Data:"), 1, 0)
        info_layout.addWidget(QLabel(date), 1, 1)
        
        info_layout.addWidget(QLabel("Status:"), 2, 0)
        
        status_label = QLabel(status)
        if status == "Zakończona" or status == "Aktywny":
            status_label.setStyleSheet("color: #2ecc71;")
        elif status == "W trakcie":
            status_label.setStyleSheet("color: #f39c12;")
        elif status == "Anulowana" or status == "Przeterminowany":
            status_label.setStyleSheet("color: #e74c3c;")
            
        info_layout.addWidget(status_label, 2, 1)
        
        layout.addLayout(info_layout)
        
        # Przykładowe szczegóły w zależności od typu
        if type_action == "Klient":
            client_info = QTextEdit()
            client_info.setReadOnly(True)
            client_info.setText("Informacje o kliencie:\n\n"
                               f"Imię i nazwisko: {description}\n"
                               "Telefon: +48 123 456 789\n"
                               "Email: przykład@email.com\n"
                               "Adres: ul. Przykładowa 123, 00-000 Miasto")
            layout.addWidget(client_info)
        elif type_action == "Depozyt":
            deposit_info = QTextEdit()
            deposit_info.setReadOnly(True)
            deposit_info.setText("Informacje o depozycie:\n\n"
                                f"Opony: {description}\n"
                                "Liczba opon: 4\n"
                                "Stan: Dobry\n"
                                "Przebieg: 25000 km\n"
                                "Klient: Jan Kowalski")
            layout.addWidget(deposit_info)
        elif type_action == "Wizyta":
            visit_info = QTextEdit()
            visit_info.setReadOnly(True)
            visit_info.setText("Informacje o wizycie:\n\n"
                              f"Usługa: {description}\n"
                              f"Data: {date}\n"
                              "Klient: Anna Nowak\n"
                              "Samochód: Toyota Corolla\n"
                              "Numer rejestracyjny: WA12345")
            layout.addWidget(visit_info)
        
        # Przyciski
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.exec_()
        
    def _search(self, query):
        """
        Obsługuje wyszukiwanie.
        
        Args:
            query (str): Zapytanie wyszukiwania
        """
        # W rzeczywistej aplikacji, ta metoda przeprowadzałaby wyszukiwanie w bazie danych
        # lub przełączała do widoku wyszukiwania z podanym zapytaniem
        print(f"Wyszukiwanie: {query}")
        
    def _filter_activities(self, filter_text):
        """
        Filtruje aktywności według wybranego typu.
        
        Args:
            filter_text (str): Tekst filtrowania
        """
        # W rzeczywistej aplikacji, ta metoda filtrowałaby dane w tabeli
        # Na potrzeby przykładu, symulujemy odświeżanie
        
        # Jeśli wybrano "Wszystkie", pokaż wszystkie typy
        if filter_text == "Wszystkie":
            for row in range(self.recent_actions_table.rowCount()):
                self.recent_actions_table.setRowHidden(row, False)
        else:
            # W przeciwnym razie, pokaż tylko wybraną kategorię
            for row in range(self.recent_actions_table.rowCount()):
                item = self.recent_actions_table.item(row, 1)
                if item:
                    item_type = item.text()
                    self.recent_actions_table.setRowHidden(
                        row, 
                        not (filter_text == item_type or 
                            (filter_text == "Klienci" and item_type == "Klient") or
                            (filter_text == "Wizyty" and item_type == "Wizyta"))
                    )