import logging
from PySide2 import QtWidgets, QtCore, QtGui

#pyinstaller --noconsole --onefile --icon ico_test.ico main.py

class AccessWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QtWidgets.QGridLayout(self)

        self.setWindowIcon(QtGui.QIcon("images/auth.png"))
        self.setWindowTitle("Аутентификация")

        class EnableButSigClass(QtCore.QObject):
            enableBut = QtCore.Signal(str, str, str)

        self.enableBut = EnableButSigClass()

        lblIpServer = QtWidgets.QLabel("IP адрес сервера: ", self)
        lblUsername = QtWidgets.QLabel("Имя пользователя: ", self)
        lblPassword = QtWidgets.QLabel("Пароль: ", self)

        self.linIpServer = QtWidgets.QLineEdit(self)
        self.linUsername = QtWidgets.QLineEdit(self)
        self.linPassword = QtWidgets.QLineEdit(self)

        self.btnAccept = QtWidgets.QPushButton("Войти в систему",self)

        settings = QtCore.QSettings("MySoft", "BotStore")
        self.linIpServer.setText(settings.value("AUTH/ip_adr", type=str))
        self.linUsername.setText(settings.value("AUTH/username", type=str))
        self.linPassword.setText(settings.value("AUTH/password", type=str))

        self.linPassword.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addWidget(lblIpServer, 0, 0, 1, 1)
        layout.addWidget(lblUsername, 1, 0, 1, 1)
        layout.addWidget(lblPassword, 2, 0, 1, 1)
        layout.addWidget(self.linIpServer, 0, 1, 1, 1)
        layout.addWidget(self.linUsername, 1, 1, 1, 1)
        layout.addWidget(self.linPassword, 2, 1, 1, 1)
        layout.addWidget(self.btnAccept, 3, 0, 1, 2)

        self.btnAccept.clicked.connect(self.pushBut)

        self.setLayout(layout)
        self.setMinimumWidth(parent.window().width()/2)

    def pushBut(self):

        settings = QtCore.QSettings("MySoft", "BotStore")
        settings.setValue("AUTH/ip_adr", self.linIpServer.text())
        settings.setValue("AUTH/username", self.linUsername.text())
        settings.setValue("AUTH/password", self.linPassword.text())

        self.enableBut.enableBut.emit(self.linIpServer.text(), self.linUsername.text(), self.linPassword.text())