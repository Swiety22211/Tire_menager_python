#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moduł zawierający style CSS dla aplikacji.
"""

# Standardowy jasny motyw
STYLE_SHEET = """
QMainWindow {
    background-color: #f0f0f0;
}

QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

QLabel#headerLabel {
    font-size: 14pt;
    font-weight: bold;
    color: #2c3e50;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 5px 15px;
    border-radius: 3px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #1f618d;
}

QPushButton#actionButton {
    background-color: #2ecc71;
    color: white;
}

QPushButton#actionButton:hover {
    background-color: #27ae60;
}

QPushButton#actionButton:pressed {
    background-color: #1e8449;
}

QPushButton#deleteButton {
    background-color: #e74c3c;
    color: white;
}

QPushButton#deleteButton:hover {
    background-color: #c0392b;
}

QPushButton#deleteButton:pressed {
    background-color: #922b21;
}

QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    border: 1px solid #bdc3c7;
    border-radius: 3px;
    padding: 4px;
    background-color: white;
    selection-background-color: #3498db;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3498db;
}

QLineEdit#searchField {
    padding: 5px 10px;
    border: 1px solid #bdc3c7;
    border-radius: 15px;
    background-color: white;
    background-image: url(resources/icons/search.png);
    background-repeat: no-repeat;
    background-position: right;
    padding-right: 25px;
}

QTabWidget::pane {
    border: 1px solid #bdc3c7;
    background-color: white;
}

QTabBar::tab {
    background-color: #ecf0f1;
    border: 1px solid #bdc3c7;
    padding: 8px 12px;
    margin-right: 1px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom-color: white;
}

QTabBar::tab:hover:!selected {
    background-color: #d6e9f8;
}

QTableView, QTreeView, QListView {
    border: 1px solid #bdc3c7;
    alternate-background-color: #ecf0f1;
    selection-background-color: #3498db;
    selection-color: white;
}

QTableView::item, QTreeView::item, QListView::item {
    padding: 4px;
}

QHeaderView::section {
    background-color: #3498db;
    color: white;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QMenu {
    background-color: white;
    border: 1px solid #bdc3c7;
}

QMenu::item {
    padding: 5px 25px 5px 30px;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

QStatusBar {
    background-color: #ecf0f1;
    color: #2c3e50;
}

QFrame#footer {
    background-color: #ecf0f1;
    border-top: 1px solid #bdc3c7;
    padding: 5px;
}

QCalendarWidget {
    background-color: white;
    border: 1px solid #bdc3c7;
}

QCalendarWidget QToolButton {
    color: #2c3e50;
    background-color: transparent;
    border: none;
    padding: 3px;
    border-radius: 3px;
}

QCalendarWidget QToolButton:hover {
    background-color: #d6e9f8;
}

QCalendarWidget QAbstractItemView {
    selection-background-color: #3498db;
    selection-color: white;
}
"""

# Ciemny motyw
DARK_STYLE_SHEET = """
QMainWindow {
    background-color: #292929;
    color: #ecf0f1;
}

QWidget {
    background-color: #292929;
    color: #ecf0f1;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

QLabel#headerLabel {
    font-size: 14pt;
    font-weight: bold;
    color: #3498db;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 5px 15px;
    border-radius: 3px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #1f618d;
}

QPushButton#actionButton {
    background-color: #2ecc71;
    color: white;
}

QPushButton#actionButton:hover {
    background-color: #27ae60;
}

QPushButton#actionButton:pressed {
    background-color: #1e8449;
}

QPushButton#deleteButton {
    background-color: #e74c3c;
    color: white;
}

QPushButton#deleteButton:hover {
    background-color: #c0392b;
}

QPushButton#deleteButton:pressed {
    background-color: #922b21;
}

QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px;
    background-color: #383838;
    color: #ecf0f1;
    selection-background-color: #3498db;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3498db;
}

QLineEdit#searchField {
    padding: 5px 10px;
    border: 1px solid #555;
    border-radius: 15px;
    background-color: #383838;
    background-image: url(resources/icons/search.png);
    background-repeat: no-repeat;
    background-position: right;
    padding-right: 25px;
}

QTabWidget::pane {
    border: 1px solid #555;
    background-color: #383838;
}

QTabBar::tab {
    background-color: #292929;
    border: 1px solid #555;
    padding: 8px 12px;
    margin-right: 1px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #383838;
    border-bottom-color: #383838;
}

QTabBar::tab:hover:!selected {
    background-color: #333;
}

QTableView, QTreeView, QListView {
    border: 1px solid #555;
    background-color: #383838;
    alternate-background-color: #333;
    selection-background-color: #3498db;
    selection-color: white;
    color: #ecf0f1;
}

QTableView::item, QTreeView::item, QListView::item {
    padding: 4px;
}

QHeaderView::section {
    background-color: #293949;
    color: white;
    padding: 6px;
    border: none;
    font-weight: bold;
}

QMenu {
    background-color: #383838;
    border: 1px solid #555;
}

QMenu::item {
    padding: 5px 25px 5px 30px;
    color: #ecf0f1;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}

QStatusBar {
    background-color: #292929;
    color: #ecf0f1;
}

QFrame#footer {
    background-color: #292929;
    border-top: 1px solid #555;
    padding: 5px;
}

QCalendarWidget {
    background-color: #383838;
    border: 1px solid #555;
    color: #ecf0f1;
}

QCalendarWidget QToolButton {
    color: #ecf0f1;
    background-color: transparent;
    border: none;
    padding: 3px;
    border-radius: 3px;
}

QCalendarWidget QToolButton:hover {
    background-color: #444;
}

QCalendarWidget QAbstractItemView {
    selection-background-color: #3498db;
    selection-color: white;
}
"""