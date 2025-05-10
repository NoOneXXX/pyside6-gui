# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pyside6-mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHeaderView, QMainWindow, QMenu,
    QMenuBar, QSizePolicy, QSplitter, QTableWidget,
    QTableWidgetItem, QToolBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1079, 873)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralLayout = QVBoxLayout(self.centralwidget)
        self.centralLayout.setObjectName(u"centralLayout")
        self.splitter = QSplitter(self.centralwidget)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.leftWidget = QWidget(self.splitter)
        self.leftWidget.setObjectName(u"leftWidget")
        self.verticalLayout = QVBoxLayout(self.leftWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.leftWidget)
        self.rightWidget = QWidget(self.splitter)
        self.rightWidget.setObjectName(u"rightWidget")
        self.rightLayout = QVBoxLayout(self.rightWidget)
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalSplitter = QSplitter(self.rightWidget)
        self.verticalSplitter.setObjectName(u"verticalSplitter")
        self.verticalSplitter.setOrientation(Qt.Vertical)
        self.noteTable = QTableWidget(self.verticalSplitter)
        if (self.noteTable.columnCount() < 3):
            self.noteTable.setColumnCount(3)
        __qtablewidgetitem = QTableWidgetItem()
        self.noteTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.noteTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.noteTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        self.noteTable.setObjectName(u"noteTable")
        self.noteTable.setStyleSheet(u"background-color: #FFFFFF;")
        self.noteTable.setRowCount(0)
        self.noteTable.setColumnCount(3)
        self.verticalSplitter.addWidget(self.noteTable)
        self.noteTable.horizontalHeader().setStretchLastSection(True)
        self.noteContentTable = QTableWidget(self.verticalSplitter)
        if (self.noteContentTable.columnCount() < 1):
            self.noteContentTable.setColumnCount(1)
        if (self.noteContentTable.rowCount() < 1):
            self.noteContentTable.setRowCount(1)
        self.noteContentTable.setObjectName(u"noteContentTable")
        self.noteContentTable.setStyleSheet(u"background-color: #FFFFFF; QTableWidget { border: none; } QTableWidget::item { border: none; }")
        self.noteContentTable.setRowCount(1)
        self.noteContentTable.setColumnCount(1)
        self.noteContentTable.setShowGrid(False)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.noteContentTable.sizePolicy().hasHeightForWidth())
        self.noteContentTable.setSizePolicy(sizePolicy)
        self.verticalSplitter.addWidget(self.noteContentTable)
        self.noteContentTable.horizontalHeader().setVisible(False)
        self.noteContentTable.verticalHeader().setVisible(False)

        self.rightLayout.addWidget(self.verticalSplitter)

        self.splitter.addWidget(self.rightWidget)

        self.centralLayout.addWidget(self.splitter)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1079, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuSearch = QMenu(self.menubar)
        self.menuSearch.setObjectName(u"menuSearch")
        self.menuFormat = QMenu(self.menubar)
        self.menuFormat.setObjectName(u"menuFormat")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuGo = QMenu(self.menubar)
        self.menuGo.setObjectName(u"menuGo")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName(u"menuTools")
        self.menuWindow = QMenu(self.menubar)
        self.menuWindow.setObjectName(u"menuWindow")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuSearch.menuAction())
        self.menubar.addAction(self.menuFormat.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuGo.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menuWindow.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"My Software Notes", None))
        ___qtablewidgetitem = self.noteTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Title", None));
        ___qtablewidgetitem1 = self.noteTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Created time", None));
        ___qtablewidgetitem2 = self.noteTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Modified time", None));

        __sortingEnabled = self.noteContentTable.isSortingEnabled()
        self.noteContentTable.setSortingEnabled(False)
        self.noteContentTable.setSortingEnabled(__sortingEnabled)

        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuSearch.setTitle(QCoreApplication.translate("MainWindow", u"Search", None))
        self.menuFormat.setTitle(QCoreApplication.translate("MainWindow", u"Format", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menuGo.setTitle(QCoreApplication.translate("MainWindow", u"Go", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.menuWindow.setTitle(QCoreApplication.translate("MainWindow", u"Window", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

