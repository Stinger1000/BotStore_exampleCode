import logging
import os
import shutil
from tkinter import Image

import requests
import pysftp
from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.QtCore import QSize, QEvent, QMimeDatabase, Signal
from PySide2.QtGui import QImage, QPixmap, QStandardItemModel, QStandardItem, QCursor, QGuiApplication, QClipboard
from PySide2.QtWidgets import QSizePolicy, QApplication, QLabel, QWidget, QVBoxLayout, QFileDialog, QListView, QToolTip, \
    QAbstractItemView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsView, QMenu, QAction
from mysql.connector import Error
from PySide2.QtWidgets import QApplication, QFileDialog, QListWidget, QDialog, QVBoxLayout, QToolTip, QLabel
from PySide2.QtGui import QPixmap, QCursor
from PySide2.QtCore import Qt, QSize

SIZE_PAGE = 50

DIR_SAVE_IMAGES = 'images/product/'
SFTP_SAVE_IMAGES = '/admin/images/'
TIMEOUT_UPDATE = 5000
header_table = ["Номер", "Название", "Цена", "Кол-во", "Статус наличия", "Описание", "Тэги", "Депозит", "Основное изображение",]
column_id = 0
column_name = 1
column_price = 2
column_count = 3
column_availab = 4
column_spec = 5
#column_avito = 6
#column_additional = 7
column_tags = 6
column_deposit = 7
column_image = 8

#-------------------------GLObAL WIDGET--------------------------------
class ProductWidget(QtWidgets.QWidget):
    def __init__(self, parent, connection, ip, username, password):
        super().__init__(parent)

        try:
            self.parent = parent
            self.connection = connection

            layout = QtWidgets.QGridLayout(self)
            self.table = QtWidgets.QTableWidget(self)
            self.table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

            quitActionUpdate = QtWidgets.QAction("Изменить", self)
            quitActionDelete = QtWidgets.QAction("Удалить", self)
            quitActionViewImage = QtWidgets.QAction("Изменить изображения", self)
            quitActionUpdate.triggered.connect(self.UpdateStatusProduct)
            quitActionDelete.triggered.connect(self.DeleteProduct)
            quitActionViewImage.triggered.connect(self.ViewImage)
            self.table.addAction(quitActionUpdate)
            self.table.addAction(quitActionDelete)
            self.table.addAction(quitActionViewImage)

            layout.addWidget(self.table, 1, 0, 1, 4)

            self.group = QtWidgets.QGroupBox("Управление", self)
            layout_group = QtWidgets.QGridLayout(self)
            self.button = QtWidgets.QPushButton("Добавить новый", self)

            self.button.clicked.connect(self.AddNewProduct)

            layout_group.addWidget(self.button, 0, 0)
            self.group.setLayout(layout_group)
            layout.addWidget(self.group, 2, 0, 1, 4)

            lab_page = QtWidgets.QLabel("Страница", self)
            self.cmb_page = QtWidgets.QComboBox(self)
            self.SetPages()
            self.cmb_page.setCurrentIndex(0)

            self.button_update = QtWidgets.QPushButton("Обновить", self)
            spacer = QtWidgets.QSpacerItem(100, 10, QSizePolicy.Expanding)

            layout.addWidget(lab_page, 0, 0)
            layout.addWidget(self.cmb_page, 0, 1)
            layout.addWidget(self.button_update, 0, 2)
            layout.addItem(spacer, 0, 3)

            #SFTP
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            self.sftp = pysftp.Connection(ip, username=username, password=password, cnopts=cnopts)

            self.setLayout(layout)

            self.table.setColumnCount(len(header_table))
            self.table.setHorizontalHeaderLabels(header_table)

            # self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()

            self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

            # timer = QtCore.QTimer(self)
            # timer.timeout.connect(self.UpdateTable)
            # timer.start(TIMEOUT_UPDATE)

            self.button_update.clicked.connect(self.UpdateTable)

            self.changeImage = {}

            self.UpdateTable()

        except Error as e:
            logging.info(e)
# -----------------------------------------------------------------------

# -------------------------UPDATE GLOBAL TABLE--------------------------------
    def UpdateTable(self):
        try:
            orders = self.GetDataProduct()
            self.SetPages()

            if(orders == None):
                return

            self.table.setRowCount(len(orders))

            row = 0
            for x in orders:
                column = 0
                for y in x:

                    if type(y) is int or type(y) is float:
                        y = str(y)

                    if column == column_image:

                        using_sftp = False
                        get = self.changeImage.get(str(x[column_id]))
                        if (get != y):
                            using_sftp = True
                            self.changeImage[str(x[column_id])] = y

                        path_image = SFTP_SAVE_IMAGES + str(x[column_id]) + '/'

                        if(using_sftp):
                            if(not os.path.isdir(DIR_SAVE_IMAGES + str(x[column_id]))):
                                os.mkdir(DIR_SAVE_IMAGES + str(x[column_id]))
                            else:
                                shutil.rmtree(DIR_SAVE_IMAGES + str(x[column_id]))
                                os.mkdir(DIR_SAVE_IMAGES + str(x[column_id]))

                            if(self.sftp.isdir(path_image)):
                                for i in self.sftp.listdir(path_image):
                                    self.sftp.get(path_image + i, DIR_SAVE_IMAGES + str(x[column_id]) + '/' + i)

                        image = QtGui.QPixmap()
                        if(os.path.exists(DIR_SAVE_IMAGES + str(x[column_id]) + '/0.jpg')):
                            image = QtGui.QPixmap(DIR_SAVE_IMAGES + str(x[column_id]) + '/0.jpg')

                        size = QtCore.QSize(200, 200)
                        image = image.scaled(size, QtCore.Qt.KeepAspectRatio)

                        item = QtWidgets.QTableWidgetItem()
                        item.setData(QtCore.Qt.ItemDataRole.DecorationRole, image)
                        self.table.setItem(row, column, item)
                        self.table.resizeColumnToContents(column_image)

                        # self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
                        self.table.resizeRowsToContents()
                        self.table.horizontalHeader().setStretchLastSection(True)

                        # self.parent.resize(self.table.horizontalHeader().size().width() + self.table.horizontalHeader().offset().w, self.parent.height())

                    elif column == column_availab:
                        if(y == "0"):
                            item = QtWidgets.QTableWidgetItem("На заказ")
                            self.table.setItem(row, column, item)
                        elif(y == "1"):
                            item = QtWidgets.QTableWidgetItem("На складе")
                            self.table.setItem(row, column, item)
                        elif(y == "2"):
                            item = QtWidgets.QTableWidgetItem("Предзаказ")
                            self.table.setItem(row, column, item)


                    else:
                        item = QtWidgets.QTableWidgetItem(y)
                        self.table.setItem(row, column, item)

                    column += 1
                row += 1


        except Error as e:
            logging.info(e)

    # -----------------------------------------------------------------------

    # --------------------------UPDATE STATUS IMAGE----------------------

    def UpdateStatusImage(self, row):
        cursor = self.connection.cursor()

        update = ("UPDATE t_figure SET l_update_image = l_update_image + 1" + " where l_id_figure='" + self.table.item(row, column_id).text() + "'")
        cursor.execute(update)
        cursor.fetchall()

        self.connection.commit()

# -----------------------------------------------------------------------

# --------------------------GET DATA FROM BS TO TABLE----------------------
    def GetDataProduct(self):
        try:
            if not(self.connection.is_connected()):
                return 0

            if(self.cmb_page.currentIndex() < 0):
                self.cmb_page.addItems([""])

            cursor = self.connection.cursor()

            cursor.execute("SELECT t_figure.l_id_figure, t_figure.l_id_name, t_figure.l_id_price, "
                           "t_figure.l_id_count, t_figure.l_status_availability, t_figure.l_specification, t_figure.l_tags, t_deposit.l_dep, t_figure.l_update_image"
                           " FROM t_figure left join t_deposit on t_figure.l_id_figure=t_deposit.l_id_figure order by t_figure.l_status_availability desc, t_figure.l_id_count desc, t_figure.l_id_figure asc limit " + str(self.cmb_page.currentIndex() * SIZE_PAGE) + ", " + str(SIZE_PAGE))

            result = cursor.fetchall()

            return result

        except Error as e:
            logging.info(e)

# -----------------------------------------------------------------------

# ------------------------SET PATH FOR IMAGES-----------------------------
    def setPath(self):


        file_name = QFileDialog()
        file_name.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        file_name.setNameFilter("Images (*.png *.jpg)")
        file_name.exec_()


        for img in file_name.selectedFiles():
            if os.path.splitext(img)[1].lower() == "jpg":
                baseName, extension = os.path.splitext(img)
                new_img = os.path.join(os.path.dirname(img), baseName + ".jpg")
                os.rename(img, new_img)

        return file_name.selectedFiles()

# -----------------------------------------------------------------------

    def Confirm(self):
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        msg_box.setWindowTitle("Удаление объекта");
        msg_box.setInformativeText("Вы действительно хотите это удалить?");
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
        return msg_box.exec_()

# -----------------------ADD NEW PRODUCT-------------------------------
    def AddNewProduct(self):
        try:
            self.dialog = QtWidgets.QDialog(self)
            self.dialog.setWindowTitle("Добавить новый продукт")
            self.dialog.setWindowIcon(self.windowIcon())

            layout = QtWidgets.QGridLayout()
            label_name = QtWidgets.QLabel("Название: ", self.dialog)
            label_price = QtWidgets.QLabel("Цена: ", self.dialog)
            label_count = QtWidgets.QLabel("Кол-во: ", self.dialog)
            label_status_ava = QtWidgets.QLabel("Статус наличия: ", self.dialog)
            label_spec = QtWidgets.QLabel("Описание: ", self.dialog)
            label_avito = QtWidgets.QLabel("Адрес Авито: ", self.dialog)
            label_additional_address = QtWidgets.QLabel("Доп адрес: ", self.dialog)
            label_tags = QtWidgets.QLabel("Тэги: ", self.dialog)
            label_dep = QtWidgets.QLabel("Депозит: ", self.dialog)
            label_path = QtWidgets.QLabel("Путь к изображению: ", self.dialog)
            #this column for add

            self.line_name = QtWidgets.QLineEdit(self.dialog)
            self.line_price = QtWidgets.QLineEdit(self.dialog)
            self.line_dep = QtWidgets.QLineEdit(self.dialog)
            self.line_count = QtWidgets.QLineEdit(self.dialog)
            self.line_path = QtWidgets.QLineEdit(self.dialog)
            self.line_tags = QtWidgets.QTextEdit(self.dialog)
            self.cbb_status = QtWidgets.QComboBox(self.dialog)
            self.button_path = QtWidgets.QPushButton("Задать путь", self.dialog)
            self.text_spec = QtWidgets.QTextEdit(self.dialog)
            self.line_avito = QtWidgets.QLineEdit(self.dialog)
            self.additional_address = QtWidgets.QLineEdit(self.dialog)
            self.check_box = QtWidgets.QCheckBox("Перерасчет на основе курса", self.dialog)

            self.cbb_status.addItems(["На заказ", "На складе", "Предзаказ"]);

            self.line_price.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]*"), self.line_price))
            self.line_count.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]*"), self.line_count))
            self.line_dep.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9]*"), self.line_count))
            self.line_path.setReadOnly(True)

            def setPathForLine():
                self.selectedImages = self.setPath()
                self.line_path.setText(str(self.selectedImages.__len__()) + " файл(ов).")

            self.button_path.clicked.connect(setPathForLine)

            self.buttonSet = QtWidgets.QPushButton("Добавить", self.dialog)

            def addNewProduct():

                if(((len(self.line_name.text())) == 0) or ((len(self.line_price.text())) == 0)):
                    logging.info('Неправильная длина, проверьте правильность')
                    return

                cursor = self.connection.cursor()

                # status = 'false'
                # if(self.cbb_status.currentIndex() == 0):
                #     status = 'true'
                #
                # first = self.line_path.text().rfind('/')

                try:
                    if(self.line_dep.text() == ""):
                        self.line_dep.setText("0")
                    cursor.callproc('insert_figure', [0, self.line_name.text(),
                                   self.line_price.text(), self.line_count.text(), str(self.cbb_status.currentIndex()), self.text_spec.toPlainText(),
                                         self.line_avito.text(), self.additional_address.text(), self.line_tags.toPlainText(), 0, self.line_dep.text()])

                    for x in cursor.stored_results():
                        result_insert = x.fetchall()

                    cursor.fetchall()

                    if(self.check_box.isChecked()):
                        cursor = self.connection.cursor()
                        data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
                        self.USD_exchange = data['Valute']['CNY']['Value']

                        res = cursor.execute("INSERT INTO t_compile_price values(LAST_INSERT_ID(), " + str(self.USD_exchange) + ");")

                        cursor.fetchall()


                    cursor.close()

                    name_dir = SFTP_SAVE_IMAGES + str(result_insert[0][0]) + '/'

                    if(not self.sftp.isdir(name_dir)):
                        self.sftp.mkdir(name_dir)

                    for i in self.selectedImages:
                        self.sftp.put(i, name_dir + str(self.sftp.listdir(name_dir).__len__()) + '.jpg')

                    for filename in os.listdir("image_from_buf"):
                        file_path = os.path.join("image_from_buf", filename)
                        self.sftp.put(file_path, name_dir + str(self.sftp.listdir(name_dir).__len__()) + '.jpg')

                    self.UpdateTable()
                    self.dialog.close()

                except Error as e:
                    logging.info(e)

            self.buttonSet.clicked.connect(addNewProduct)

            layout.addWidget(label_name, 0, 0, )
            layout.addWidget(label_price, 1, 0,)
            layout.addWidget(label_count, 2, 0,)
            layout.addWidget(label_status_ava, 3, 0, )
            layout.addWidget(label_spec, 4, 0,)
            layout.addWidget(label_avito, 5, 0, )
            layout.addWidget(label_additional_address, 6, 0, )
            layout.addWidget(label_tags, 7, 0, )
            layout.addWidget(label_dep, 8, 0, )
            layout.addWidget(label_path, 9, 0, )

            layout.addWidget(self.line_name, 0, 1)
            layout.addWidget(self.line_price, 1, 1)
            layout.addWidget(self.line_count, 2, 1)
            layout.addWidget(self.cbb_status, 3, 1)
            layout.addWidget(self.text_spec, 4, 1)
            layout.addWidget(self.line_avito, 5, 1)
            layout.addWidget(self.additional_address, 6, 1)
            layout.addWidget(self.line_tags, 7, 1)
            layout.addWidget(self.line_dep, 8, 1)
            layout.addWidget(self.line_path, 9, 1)
            layout.addWidget(self.button_path, 9, 2)
            layout.addWidget(self.check_box, 10, 2)

            layout.addWidget(self.buttonSet, 10, 0, 1, 3)

            self.selectedImages = []

            if not os.path.exists("image_from_buf"):  # если папка не существует
                os.makedirs("image_from_buf")  # создаем папку
            else:
                for filename in os.listdir("image_from_buf"):
                    file_path = os.path.join("image_from_buf", filename)
                    # Если текущий файл является файлом, а не папкой, то удаляем его
                    if os.path.isfile(file_path):
                        os.remove(file_path)


            class MyGraphicsView(QGraphicsView):
                add_item = Signal()
                def __init__(self, parent=None):
                    super(MyGraphicsView, self).__init__(parent)

                    # Установка политики контекстного меню
                    self.setContextMenuPolicy(Qt.CustomContextMenu)

                    # Подключение сигнала customContextMenuRequested к обработчику
                    self.customContextMenuRequested.connect(self.showContextMenu)

                def showContextMenu(self, point):
                    # Создание контекстного меню
                    menu = QMenu(self)

                    # Создание действия
                    action = QAction("Добавить из буфера", self)
                    action.triggered.connect(self.onMyAction)

                    # Добавление действия в контекстное меню
                    menu.addAction(action)

                    # Показ контекстного меню
                    menu.exec_(self.mapToGlobal(point))

                def onMyAction(self):
                    count = len(os.listdir("image_from_buf"))

                    clipboard = QClipboard()
                    pixmap = clipboard.pixmap()
                    pixmap.save("image_from_buf/" + str(count) + ".jpg")

                    self.add_item.emit()


            self.scene = QGraphicsScene(self.dialog)


            def AddImagesFromFolder():
                file_path = ""
                count_elem = 0
                for filename in os.listdir("image_from_buf"):
                    file_path = os.path.join("image_from_buf", filename)
                    pixmap1 = QPixmap(file_path)
                    size_image = QSize(100, 100)
                    pixmap1 = pixmap1.scaled(size_image)
                    item1 = QGraphicsPixmapItem(pixmap1)
                    item1.setPos(count_elem * 100, 0)
                    self.scene.addItem(item1)
                    count_elem+=1

                for i in self.selectedImages:
                    pixmap1 = QPixmap(i)
                    size_image = QSize(100, 100)
                    pixmap1 = pixmap1.scaled(size_image)
                    item1 = QGraphicsPixmapItem(pixmap1)
                    item1.setPos(count_elem * 100, 0)
                    self.scene.addItem(item1)
                    count_elem+=1



            view = MyGraphicsView(self.scene)

            view.add_item.connect(AddImagesFromFolder)

            # view.setSceneRect(0, 0, 450 , 150)
            # view.setFixedSize(500, 200)

            layout.addWidget(view, 11, 0, 1, 3)

            self.dialog.setLayout(layout)
            self.dialog.adjustSize()
            self.dialog.exec_()

        except Error as e:
            logging.info(e)

# -----------------------------------------------------------------------

# ----------------------UPDATE STATUS PRODUCT---------------------------
    def UpdateStatusProduct(self):
        try:
            row = 0
            column = 0

            items = self.table.selectedItems()
            for i in items:
                row = i.row()
                column = i.column()

            self.dialogChange = QtWidgets.QDialog(self)
            self.dialogChange.setWindowTitle("Обновить данные")
            self.dialogChange.setWindowIcon(self.windowIcon())

            self.change = ""
            line_or_cbb = QtWidgets.QLineEdit(self)
            button = QtWidgets.QPushButton("Применить", self)
            label_change = QtWidgets.QLabel(self)

            if(column == column_name):
                self.change = "ИЗМЕНИТЬ НАЗВАНИЕ"
                label_change.setText("Введите новое название:")
            elif column == column_price:
                self.change = "ИЗМЕНИТЬ ЦЕНУ"
                label_change.setText("Введите новую цену:")
            elif column == column_count:
                self.change = "ИЗМЕНИТЬ КОЛИЧЕСТВО"
                label_change.setText("Увеличить/Уменьшить количество на:")
            elif column == column_availab:
                self.change = "ИЗМЕНИТЬ СТАТУС НАЛИЧИЯ"
                label_change.setText("Выберите статус наличия:")
                line_or_cbb = QtWidgets.QComboBox(self)
                line_or_cbb.addItems(["На заказ", "На складе", "Предзаказ"])
            elif column == column_spec:
                self.change = "ИЗМЕНИТЬ ОПИСАНИЕ"
                label_change.setText("Введите описание:")
                line_or_cbb = QtWidgets.QTextEdit(self)
            # elif column == column_avito:
            #     self.change = "ИЗМЕНИТЬ АДРЕС НА АВИТО"
            #     label_change.setText("Введите новый адрес:")
            # elif column == column_additional:
            #     self.change = "ИЗМЕНИТЬ ДОПОЛНИТЕЛЬНЫЙ АДРЕС"
            #     label_change.setText("Введите новый адрес:")
            elif column == column_tags:
                self.change = "ИЗМЕНИТЬ ТЭГИ"
                label_change.setText("Введите новые тэги:")
            elif column == column_deposit:
                self.change = "ИЗМЕНИТЬ ДЕПОЗИТ"
                label_change.setText("Введите новый депозит:")
            # elif column == column_image:
                # self.change = "ИЗМЕНИТЬ ИЗОБРАЖЕНИЕ"
                # label_change.setText("Выберите путь:")
                # line_or_cbb = QtWidgets.QWidget(self)
                #
                # layout = QtWidgets.QGridLayout(line_or_cbb)
                # line = QtWidgets.QLineEdit()
                # but = QtWidgets.QPushButton("Выбрать путь")
                #
                # def selectPath():
                #     self.selectedImages = self.setPath()
                #     line.setText(str(self.setPath().count()) + " файлов.")
                #
                # but.clicked.connect(selectPath)
                #
                # layout.addWidget(line, 0, 0)
                # layout.addWidget(but, 0, 1)
                # line_or_cbb.setLayout(layout)
            else:
                return

            layout = QtWidgets.QGridLayout()
            label = QtWidgets.QLabel(
                                       "Название: " + self.table.item(row, 1).text() + "\n"
                                     + "Цена: " + self.table.item(row, 2).text() + "\n"
                                     + "Количество: " + self.table.item(row, 3).text() + "\n"
                                     + "Статус наличия: " + self.table.item(row, 4).text() + "\n"
                                    + "Депозит: " + self.table.item(row, 5).text())

            label.setStyleSheet('''font-size: 24px''')

            layout.addWidget(label, 0, 0, 1, 2)
            layout.addWidget(label_change, 1, 0)
            layout.addWidget(line_or_cbb, 1, 1)
            layout.addWidget(button, 2, 0, 1, 2)

            self.currentRowSelect = row

            def change():

                cursor = self.connection.cursor()

                lbl = ""

                if self.change == "ИЗМЕНИТЬ НАЗВАНИЕ":
                    lbl = "l_id_name"
                elif self.change == "ИЗМЕНИТЬ ЦЕНУ":
                    lbl = "l_id_price"
                elif self.change == "ИЗМЕНИТЬ КОЛИЧЕСТВО":
                    lbl = "l_id_count"
                elif self.change == "ИЗМЕНИТЬ СТАТУС НАЛИЧИЯ":
                    lbl = "l_status_availability"
                    if(line_or_cbb.currentIndex() == 0):
                        status_is = "0"
                    elif (line_or_cbb.currentIndex() == 1):
                        status_is = "1"
                    else:
                        status_is = "2"
                elif self.change == "ИЗМЕНИТЬ ИЗОБРАЖЕНИЕ":
                    lbl = "l_id_path_image"
                elif self.change == "ИЗМЕНИТЬ ОПИСАНИЕ":
                    lbl = "l_specification"
                elif self.change == "ИЗМЕНИТЬ АДРЕС НА АВИТО":
                    lbl = "l_avito_address"
                elif self.change == "ИЗМЕНИТЬ ДОПОЛНИТЕЛЬНЫЙ АДРЕС":
                    lbl = "l_additional_address"
                elif self.change == "ИЗМЕНИТЬ ТЭГИ":
                    lbl = "l_tags"
                elif self.change == "ИЗМЕНИТЬ ДЕПОЗИТ":
                    lbl = "l_dep"

                if self.change == "ИЗМЕНИТЬ СТАТУС НАЛИЧИЯ":
                    cursor.execute(
                        "UPDATE t_figure SET " + lbl + "="  + status_is + " WHERE l_id_figure=" + self.table.item(
                            self.currentRowSelect, 0).text())

                elif self.change == "ИЗМЕНИТЬ НАЗВАНИЕ" or self.change == "ИЗМЕНИТЬ АДРЕС НА АВИТО" or self.change == "ИЗМЕНИТЬ ДОПОЛНИТЕЛЬНЫЙ АДРЕС" or self.change == "ИЗМЕНИТЬ ТЭГИ":
                    cursor.execute(
                        "UPDATE t_figure SET " + lbl + "=" + "'" + line_or_cbb.text() + "'" + " WHERE l_id_figure=" + self.table.item(
                            self.currentRowSelect, 0).text())

                elif self.change == "ИЗМЕНИТЬ ОПИСАНИЕ":
                    cursor.execute(
                        "UPDATE t_figure SET " + lbl + "=" + "'" + line_or_cbb.toPlainText() + "'" + " WHERE l_id_figure=" + self.table.item(
                            self.currentRowSelect, 0).text())

                elif self.change == "ИЗМЕНИТЬ КОЛИЧЕСТВО":
                    cursor.callproc('change_count_figure',  [self.table.item(
                            self.currentRowSelect, 0).text(), line_or_cbb.text()])

                elif self.change == "ИЗМЕНИТЬ ДЕПОЗИТ":
                    cursor.execute(
                        "UPDATE t_deposit SET " + lbl + "="  + line_or_cbb.text() + " WHERE l_id_figure=" + self.table.item(
                            self.currentRowSelect, 0).text())
                else:
                    cursor.execute(
                        "UPDATE t_figure SET " + lbl + "=" + line_or_cbb.text() + " WHERE l_id_figure=" + self.table.item(
                            self.currentRowSelect, 0).text())

                result = cursor.fetchall()

                logging.info("Обновлен продукт: " + self.change + " ID: " + self.table.item(self.currentRowSelect,
                                                                                                  0).text())

                self.connection.commit()

                cursor.close()

                self.UpdateTable()
                self.dialogChange.close()

            button.clicked.connect(change)

            self.dialogChange.setLayout(layout)
            self.dialogChange.exec_()

        except Error as e:
            logging.info(e)

# -----------------------------------------------------------------------

# ------------------------DELETE PRODUCT-----------------------------------------------
    def DeleteProduct(self):
        row = 0
        column = 0

        items = self.table.selectedItems()

        if(len(items) == 0):
            return

        conf = self.Confirm()
        if (conf == QtWidgets.QMessageBox.StandardButton.Cancel):
            return

        for i in items:
            row = i.row()
            column = i.column()

        self.UpdateStatusImage(row)

        if(self.sftp.exists(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text())):
            reFiles = self.sftp.listdir(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text())
            for i in reFiles:
                self.sftp.remove(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + i)

            self.sftp.rmdir(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text())

        cursor = self.connection.cursor()
        cursor.callproc(
            'delete_figure', [int(self.table.item(row, column_id).text())]
        )

        for x in cursor.stored_results():
            result_f = x.fetchall()

        cursor.fetchall()

        result = cursor.fetchall()
        self.connection.commit()
        cursor.close()

        if(not result):
            logging.info("Удачное удаление ПРОДУКТА. строка: %i", row)
        else:
            logging.error("Не удалось удалить ПРОДУКТ")

        self.UpdateTable()

    def GetCountElem(self):
        try:
            if not(self.connection.is_connected()):
                return 0

            cursor = self.connection.cursor()

            cursor.execute("SELECT count(*) FROM t_figure")

            result = cursor.fetchall()

            return result

        except Error as e:
            logging.info(e)


    def SetPages(self):
        try:
            last_index = self.cmb_page.currentIndex()
            self.cmb_page.clear()

            count_pages = (self.GetCountElem()[0][0] + (SIZE_PAGE-1)) / SIZE_PAGE
            text_pages = []
            for i in range(0, int(count_pages)):
                text_pages.append(str('Страница ' + str(i)))

            self.cmb_page.addItems(text_pages)

            if(self.cmb_page.count() > last_index):
                self.cmb_page.setCurrentIndex(last_index)

        except Error as e:
            logging.info(e)

    def ViewImage(self):
        row = 0
        column = 0

        items = self.table.selectedItems()

        if(len(items) == 0):
            return

        for i in items:
            row = i.row()
            column = i.column()

        desktop = QtWidgets.QApplication.desktop()
        screenRect = desktop.screenGeometry()

        dialogImage = QtWidgets.QDialog(self)
        dialogImage.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        layout = QtWidgets.QGridLayout(dialogImage)
        dialogImage.setLayout(layout)
        dialogImage.setFixedSize(screenRect.width() * 0.8, screenRect.height() * 0.8)

        dialogImage.setWindowTitle(self.table.item(row, column_name).text() + " Image: 0.jpg" )

        labelImage = QtWidgets.QLabel(dialogImage)
        buttonBack = QtWidgets.QPushButton("<------НАЗАД", dialogImage)
        buttonDelete = QtWidgets.QPushButton("Удалить", dialogImage)
        buttonChange = QtWidgets.QPushButton("Заменить", dialogImage)
        buttonAdd = QtWidgets.QPushButton("Добавить", dialogImage)
        buttonAddFromBuf = QtWidgets.QPushButton("Вставить из буфера", dialogImage)
        buttonFront = QtWidgets.QPushButton("ВПЕРЕД------>", dialogImage)

        self.current_image = 0

        def BackImage():
            count_images = len(os.listdir(DIR_SAVE_IMAGES + self.table.item(row, column_id).text()))
            if(count_images == 0):
                labelImage.setPixmap(QtGui.QPixmap())
                return

            if(self.current_image == 0):
                self.current_image = count_images - 1
            else:
                self.current_image = self.current_image - 1

            image = QtGui.QPixmap(DIR_SAVE_IMAGES + self.table.item(row, column_id).text() + '/' + str(self.current_image) + '.jpg')
            dialogImage.setWindowTitle(self.table.item(row, column_id).text() + ' Image: ' + str(self.current_image) + '.jpg')
            image = image.scaled(dialogImage.size(), QtCore.Qt.KeepAspectRatio)
            labelImage.setPixmap(image)
            labelImage.setAlignment(QtCore.Qt.AlignCenter)

        def FrontImage():
            count_images = len(os.listdir(DIR_SAVE_IMAGES + self.table.item(row, column_id).text()))
            if(count_images == 0):
                labelImage.setPixmap(QtGui.QPixmap())
                return

            if (self.current_image == count_images - 1):
                self.current_image = 0
            else:
                self.current_image = self.current_image + 1

            image = QtGui.QPixmap(DIR_SAVE_IMAGES + self.table.item(row, column_id).text() + '/' + str(self.current_image) + '.jpg')
            dialogImage.setWindowTitle(self.table.item(row, column_id).text() + ' Image: ' + str(self.current_image) + '.jpg')
            image = image.scaled(dialogImage.size(), QtCore.Qt.KeepAspectRatio)
            labelImage.setPixmap(image)
            labelImage.setAlignment(QtCore.Qt.AlignCenter)

        def DeleteImage():
            count_images = len(os.listdir(DIR_SAVE_IMAGES + self.table.item(row, column_id).text()))
            if(count_images == 0):
                labelImage.setPixmap(QtGui.QPixmap())
                return

            conf = self.Confirm()

            if(conf == QtWidgets.QMessageBox.StandardButton.Cancel):
                return

            self.UpdateStatusImage(row)
            self.sftp.remove(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(self.current_image) + '.jpg')

            for i in range(count_images - 1, self.current_image, -1):
                self.sftp.rename(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(i) + '.jpg',
                                 SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(i - 1) + '.jpg')

            self.current_image = 1

            self.UpdateTable()
            BackImage()

        def ReplaceImage():
            count_images = len(os.listdir(DIR_SAVE_IMAGES + self.table.item(row, column_id).text()))
            if(count_images == 0):
                labelImage.setPixmap(QtGui.QPixmap())
                return

            new_file = self.setPath()
            if(len(new_file) > 0):
                self.UpdateStatusImage(row)
                self.sftp.remove(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(self.current_image) + '.jpg')
                name_dir = SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + '/'
                self.sftp.put(new_file[0], name_dir + str(self.current_image) + '.jpg')
                self.UpdateTable()
                self.current_image = self.current_image + 1
                BackImage()

        def AddImage():
            new_file = self.setPath()

            if(len(new_file) == 0):
                return

            self.UpdateStatusImage(row)

            name_dir = SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + '/'

            count_images = len(os.listdir(DIR_SAVE_IMAGES + self.table.item(row, column_id).text()))
            if(count_images == 0):
                self.sftp.put(new_file[0], name_dir + '0.jpg')
                self.UpdateTable()
                self.current_image = 1
                BackImage()
                return

            for i in range(count_images - 1, self.current_image, -1):
                self.sftp.rename(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(i) + '.jpg',
                                 SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(i + 1) + '.jpg')

            self.sftp.put(new_file[0], name_dir + str(self.current_image + 1) + '.jpg')
            self.UpdateTable()
            self.current_image = self.current_image + 1
            BackImage()

        def AddImageFromBuffer():
            # Получаем картинку из буфера обмена
            clipboard = QGuiApplication.clipboard()
            image = clipboard.image()
            file_path = "image_from_buffer.jpg"

            # Проверяем, была ли получена картинка из буфера обмена
            if not image.isNull():
                # Преобразуем картинку в QPixmap для сохранения
                pixmap = QPixmap.fromImage(image)

                # Сохраняем картинку в выбранный файл

                pixmap.save(file_path, "jpg")
            else:
                return

            new_file = file_path

            if(len(new_file) == 0):
                return

            self.UpdateStatusImage(row)

            name_dir = SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + '/'

            count_images = len(os.listdir(DIR_SAVE_IMAGES + self.table.item(row, column_id).text()))
            if(count_images == 0):
                self.sftp.put(new_file, name_dir + '0.jpg')
                self.UpdateTable()
                self.current_image = 1
                BackImage()
                return

            for i in range(count_images - 1, self.current_image, -1):
                self.sftp.rename(SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(i) + '.jpg',
                                 SFTP_SAVE_IMAGES + self.table.item(row, column_id).text() + "/" + str(i + 1) + '.jpg')

            self.sftp.put(new_file, name_dir + str(self.current_image + 1) + '.jpg')
            self.UpdateTable()
            self.current_image = self.current_image + 1
            BackImage()

        buttonBack.clicked.connect(BackImage)
        buttonFront.clicked.connect(FrontImage)
        buttonDelete.clicked.connect(DeleteImage)
        buttonChange.clicked.connect(ReplaceImage)
        buttonAdd.clicked.connect(AddImage)
        buttonAddFromBuf.clicked.connect(AddImageFromBuffer)

        layout.addWidget(labelImage, 0, 0, 1, 6)
        layout.addWidget(buttonBack, 1, 0, 1, 1)
        layout.addWidget(buttonDelete, 1, 1, 1, 1)
        layout.addWidget(buttonChange, 1, 2, 1, 1)
        layout.addWidget(buttonAdd, 1, 3, 1, 1)
        layout.addWidget(buttonAddFromBuf, 1, 4, 1, 1)
        layout.addWidget(buttonFront, 1, 5, 1, 1)

        image = QtGui.QPixmap(DIR_SAVE_IMAGES + self.table.item(row, column_id).text() + '/0' + '.jpg')
        image = image.scaled(dialogImage.size(), QtCore.Qt.KeepAspectRatio)
        labelImage.setPixmap(image)
        labelImage.setAlignment(QtCore.Qt.AlignCenter)

        dialogImage.show()
