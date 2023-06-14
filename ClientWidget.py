import logging

from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtWidgets import QSizePolicy
from mysql.connector import Error

class ClientWidget(QtWidgets.QWidget):
    def __init__(self, parent, connection):
        super().__init__(parent)
        layout = QtWidgets.QGridLayout(self)
        self.table = QtWidgets.QTableWidget(self)
        layout.addWidget(self.table, 1, 0, 1, 2)

        self.connection = connection

        self.setLayout(layout)

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Кол-во покупок","Адрес", "Реальное имя", "Статус блокировки", "Индекс"])

        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        quitActionBlock = QtWidgets.QAction("Заблокировать пользователя", self)
        quitActionBlock.triggered.connect(self.BlockUser)
        self.table.addAction(quitActionBlock)

        quitActionUnblock = QtWidgets.QAction("Разблокировать пользователя", self)
        quitActionUnblock.triggered.connect(self.UnblockUser)
        self.table.addAction(quitActionUnblock)

        # timer = QtCore.QTimer(self)
        # timer.timeout.connect(self.UpdateTable)
        # timer.start(5000)

        self.button_update = QtWidgets.QPushButton("Обновить", self)
        spacer = QtWidgets.QSpacerItem(100, 10, QSizePolicy.Expanding)
        layout.addWidget(self.button_update, 0, 0)
        layout.addItem(spacer, 0, 1)
        self.button_update.clicked.connect(self.UpdateTable)


        self.table.cellDoubleClicked.connect(self.UpdateTable)

        self.UpdateTable()

    def UpdateTable(self):
        try:
            clients = self.GetClients()

            if(clients == None):
                return

            self.table.setRowCount(len(clients))

            row = 0
            for x in clients:
                column = 0
                for y in x:

                    if type(y) is int or type(y) is float:
                        y = str(y)

                    if(column == 5):
                        if(y == '0'):
                            y = "Не заблокирован"
                        else:
                            y = "Заблокирован"

                    item = QtWidgets.QTableWidgetItem(y)
                    self.table.setItem(row, column, item)

                    column += 1
                row += 1

        except Error as e:
            logging.info(e)

    def GetClients(self):
        try:
            if not(self.connection.is_connected()):
                return 0

            cursor = self.connection.cursor()

            cursor.execute("SELECT * FROM t_client")

            result = cursor.fetchall()

            return result

        except Error as e:
            logging.info(e)


    def BlockUnblockDB(self, status_block):

        row = 0
        column = 0

        items = self.table.selectedItems()
        for i in items:
            row = i.row()
            column = i.column()

        cursor = self.connection.cursor()

        cursor.execute("UPDATE t_client SET l_status_block=" + str(status_block) +" WHERE l_id_client=" + self.table.item(row, 0).text())

        result = cursor.fetchall()

        if(status_block):
            logging.info("Заблокирован пользователь: " + self.table.item(row, 1).text() + " ID: " + str(id))
        else:
            logging.info("Разблокирован пользователь: " + self.table.item(row, 1).text() + " ID: " + str(id))

        self.connection.commit()

        cursor.close()

    def BlockUser(self):
        try:

            self.BlockUnblockDB(True)

        except Error as e:
            logging.info(e)

    def UnblockUser(self):
        try:

            self.BlockUnblockDB(False)

        except Error as e:
            logging.info(e)
