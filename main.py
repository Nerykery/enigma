import sys
import os
import platform
import requests
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView, QApplication, QMainWindow, QTableWidget, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon
from datetime import datetime
import pymysql
import time

# site = "127.0.0.1"
# with open('site.txt', 'r') as f:
#     site = f.read().strip()

#from . resources_rc import * !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from modules import *
from widgets import *
os.environ["QT_FONT_DPI"] = "96" 




def get_connection():
    return pymysql.connect(
        host="94.156.115.39",
        user="nerykery",
        password="N3ryK3ry_Strong_P@ss",   #!!!!
        database="enigma",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )




widgets = None
class Logger:
    def __init__(self, user_login):
        self.user_login = user_login

    def log_action(self, action, target):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO logs (user, interact, target, data)
                            VALUES (%s, %s, %s, NOW())""",
                            (self.user_login, action, target))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка записи лога: {str(e)}")

        
class AuthWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация")
        self.setFixedSize(300, 200)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        self.user_data = None
        
        layout = QVBoxLayout()
        
        
        self.label_login = QLabel("Логин:")
        self.edit_login = QLineEdit()
        self.edit_login.setPlaceholderText("Введите логин")
        
        self.label_password = QLabel("Пароль:")
        self.edit_password = QLineEdit()
        self.edit_password.setPlaceholderText("Введите пароль")
        self.edit_password.setEchoMode(QLineEdit.Password)
        
        self.btn_login = QPushButton("Войти")
        self.btn_login.clicked.connect(self.authenticate)
        
        
        layout.addWidget(self.label_login)
        layout.addWidget(self.edit_login)
        layout.addWidget(self.label_password)
        layout.addWidget(self.edit_password)
        layout.addWidget(self.btn_login)
        
        self.setLayout(layout)
    
    def authenticate(self):
        login = self.edit_login.text().strip()
        password = self.edit_password.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return

        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE login=%s", (login,))
                user = cur.fetchone()
            conn.close()

            if user and user["password"] == password:
                self.user_data = {"login": user["login"], "role": user["role"]}
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к БД: {str(e)}")

    
class MainWindow(QMainWindow):
    def __init__(self, user_data=None):
        QMainWindow.__init__(self)

        
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui
        self.user_data = user_data or {}

        
        
        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        
        
        title = "Invent APP"
        description = "Invent APP"
        
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        
        
        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))

        
        
        UIFunctions.uiDefinitions(self)

        
        self.setupTable()

        
        

        
        widgets.invent_create_id.setText(self.generateInventoryId())
        widgets.btn_home.clicked.connect(self.buttonClick)
        widgets.btn_test.clicked.connect(self.buttonClick)
        widgets.btn_curators.clicked.connect(self.buttonClick)
        widgets.btn_logs.clicked.connect(self.buttonClick)
        widgets.btn_add_user.clicked.connect(self.buttonClick)
        widgets.invent_delete_button.clicked.connect(self.deleteEquipment)
        widgets.invent_fillte_type.currentIndexChanged.connect(self.filterTableByType)
        widgets.adduser_button_delete.clicked.connect(self.deleteUser)
        widgets.invent_search_button.clicked.connect(self.searchEquipment)
        widgets.invent_search.returnPressed.connect(self.searchEquipment)
        widgets.adduser_button_create.clicked.connect(self.createUser)
        self.loadData()
        self.init_ui()
        self.logger = Logger(self.user_data.get('login', 'unknown'))
        self.setupLogsTable()
        self.setupCuratorsTable()
        # widgets.btn_logs.clicked.connect(self.loadLogsData)

        self.loadComboBoxData()
        self.setupCreateEquipment()
        self.setupUserTable()
        self.setupCuratorsTable() 

        
        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)
        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        
        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)
        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)

        
        
        self.show()

        
        
        useCustomTheme = False
        themeFile = "themes\py_dracula_light.qss"

        
        if useCustomTheme:
            
            UIFunctions.theme(self, themeFile, True)

            
            AppFunctions.setThemeHack(self)

        
        
        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    def init_ui(self):
        
        if self.user_data.get('role') == 'admin':
            self.ui.btn_add_user.show()
            self.ui.btn_logs.show()
        else:
            self.ui.btn_add_user.hide()
            self.ui.btn_logs.hide()
        
        
        self.setWindowTitle(f"Invent APP - {self.user_data.get('login', 'Гость')} ({self.user_data.get('role', 'user')})")
        
        

        
        
        self.ui.btn_logout.clicked.connect(self.logout)

    def setupTable(self):
        
        table = widgets.invent_table
        
        
        self.model = QStandardItemModel()
        table.setModel(self.model)
        
        
        headers = [
            "Номер",
            "Наименование техники",
            "Тип",
            "Помещение",
            "Состояние",
            "ФИО ответственного",
            "Номер телефона"
        ]
        self.model.setHorizontalHeaderLabels(headers)
        
        
        table.setStyleSheet("""
            QTableView {
                background-color: rgb(33, 37, 43);
                alternate-background-color: rgb(33, 37, 43);
                gridline-color: #dee2e6;
                border: 1px solid #ced4da;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: rgb(33, 37, 43);
                color: white;
                padding: 5px;
                border: 1px solid 
                font-weight: bold;
            }
        """)
        
        
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        table.horizontalHeader().setFont(font)
        table.verticalHeader().setVisible(False)
        
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(30)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectRows)
        table.setSelectionMode(QTableView.SingleSelection)
        table.setSortingEnabled(False)
        
        
        table.setColumnWidth(0, 130)  
        table.setColumnWidth(1, 200)  
        table.setColumnWidth(2, 150)  
        table.setColumnWidth(3, 150)  
        table.setColumnWidth(4, 120)  
        table.setColumnWidth(5, 200)  
        table.setColumnWidth(6, 180)  

    def loadData(self):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM equipment")
                equipment_data = cur.fetchall()
                cur.execute("SELECT * FROM curators")
                curators_data = cur.fetchall()
            conn.close()

            curators_dict = {
                f"{c['fam']} {c['name']} {c['father']}": c['phonenumber']
                for c in curators_data
            }

            self.model.removeRows(0, self.model.rowCount())
            for item in equipment_data:
                phone = curators_dict.get(item["curator"], "Не указан")
                row_items = [
                    QStandardItem(item["id"]),
                    QStandardItem(item["name"]),
                    QStandardItem(item["type"]),
                    QStandardItem(item["room"]),
                    QStandardItem(item["sost"]),
                    QStandardItem(item["curator"]),
                    QStandardItem(phone)
                ]
                for it in row_items:
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setEditable(False)

                if row_items[4].text() == "Работает":
                    row_items[4].setForeground(QColor(0, 128, 0))
                elif row_items[4].text() == "На складе":
                    row_items[4].setForeground(QColor(255, 140, 0))
                elif row_items[4].text() == "Сломан":
                    row_items[4].setForeground(QColor(178, 34, 34))

                self.model.appendRow(row_items)

            widgets.invent_table.resizeRowsToContents()
            self.loadFilterComboBox()
            widgets.invent_search.clear()
            for row in range(self.model.rowCount()):
                widgets.invent_table.setRowHidden(row, False)

        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")


    def createTableItem(self, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    
    
    
    def buttonClick(self):
        
        btn = self.sender()
        btnName = btn.objectName()

        
        if btnName == "btn_home":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            QTimer.singleShot(1, self.loadData)

        if btnName == "btn_test":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        
        if btnName == "btn_curators":
            widgets.stackedWidget.setCurrentWidget(widgets.curators_page)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))


        
        if btnName == "btn_widgets":
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        
        if btnName == "btn_new":
            widgets.stackedWidget.setCurrentWidget(widgets.new_page) 
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 

        if btnName == "btn_logs":
            widgets.stackedWidget.setCurrentWidget(widgets.logs_page) 
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 
            QTimer.singleShot(1, self.loadLogsData)



        if btnName == "btn_save":
            print("Save BTN clicked!")
        
        if btnName == "btn_add_user":
            widgets.stackedWidget.setCurrentWidget(widgets.adduser_page) 
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))
            QTimer.singleShot(10, self.loadUserData)
        
        if btnName == "invent_create_button":
            self.createEquipment()


        
        print(f'Button "{btnName}" pressed!')

    
    
    def resizeEvent(self, event):
        
        UIFunctions.resize_grips(self)

    
    
    def mousePressEvent(self, event):
        
        self.dragPos = event.globalPosition().toPoint()

        
        if event.buttons() == Qt.LeftButton:
            print('Mouse click: LEFT CLICK')
        if event.buttons() == Qt.RightButton:
            print('Mouse click: RIGHT CLICK')


    def loadComboBoxData(self):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                # Загружаем оборудование (для типов и помещений)
                cur.execute("SELECT type, room FROM equipment")
                equipment_data = cur.fetchall()

                # Загружаем кураторов
                cur.execute("SELECT fam, name, father FROM curators")
                curators_data = cur.fetchall()
            conn.close()

            # --- Типы оборудования ---
            types = {item["type"] for item in equipment_data if item["type"]}
            widgets.invent_create_type.clear()
            widgets.invent_create_type.addItem("Тип")
            for item_type in sorted(types):
                widgets.invent_create_type.addItem(item_type)

            # --- Помещения ---
            rooms = {item["room"] for item in equipment_data if item["room"]}
            widgets.invent_create_room.clear()
            widgets.invent_create_room.addItem("Помещение")
            for room in sorted(rooms):
                widgets.invent_create_room.addItem(room)

            # --- Кураторы ---
            widgets.invent_create_curator.clear()
            widgets.invent_create_curator.addItem("Ответственный")
            for curator in curators_data:
                full_name = f"{curator['fam']} {curator['name']} {curator['father'] or ''}".strip()
                widgets.invent_create_curator.addItem(full_name)

        except Exception as e:
            print(f"Ошибка при загрузке данных для комбобоксов: {e}")

    def generateInventoryId(self):
        from datetime import datetime
        year = datetime.now().year
        
        
        max_num = 0
        for row in range(self.model.rowCount()):
            item_id = self.model.item(row, 0).text()
            if item_id.startswith(f"INVENT-{year}-"):
                try:
                    num = int(item_id.split("-")[2])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    continue
        
        
        new_num = max_num + 1
        return f"INVENT-{year}-{new_num:04d}"

    def createEquipment(self):
        try:
            inventory_id = widgets.invent_create_id.text()

            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as cnt FROM equipment WHERE id=%s", (inventory_id,))
                exists = cur.fetchone()["cnt"] > 0

            if exists:
                QMessageBox.warning(self, "Ошибка", f"Инвентарный номер '{inventory_id}' уже существует!")
                return

            data = (
                inventory_id,
                widgets.invent_create_name.text(),
                widgets.invent_create_type.currentText(),
                widgets.invent_create_room.currentText(),
                widgets.invent_create_curator.currentText(),
                widgets.invent_create_sost.currentText()
            )

            if not data[1]:
                QMessageBox.warning(self, "Ошибка", "Не указано название оборудования!")
                return

            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO equipment (id, name, type, room, curator, sost)
                            VALUES (%s, %s, %s, %s, %s, %s)""", data)
                conn.commit()
            conn.close()

            self.logger.log_action("Создание оборудования", f"Инв. № {inventory_id}")
            QMessageBox.information(self, "Успех", "Оборудование успешно добавлено!")
            self.clearCreateForm()
            self.loadData()
            widgets.invent_create_id.setText(self.generateInventoryId())

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении оборудования: {str(e)}")

            
    def isInventoryIdUnique(self, inventory_id):
            """Проверяет уникальность инвентарного номера"""
            
            for row in range(self.model.rowCount()):
                existing_id = self.model.item(row, 0).text()  
                if existing_id == inventory_id:
                    return False
            return True

    def clearCreateForm(self):
        

        widgets.invent_create_name.clear()
        widgets.invent_create_type.setCurrentIndex(0)
        widgets.invent_create_room.setCurrentIndex(0)
        widgets.invent_create_curator.setCurrentIndex(0)
        widgets.invent_create_sost.setCurrentIndex(0)

    def setupCreateEquipment(self):
        
        widgets.invent_create_button.clicked.connect(self.createEquipment)
        
        
        widgets.invent_create_id.setText(self.generateInventoryId())

    def deleteEquipment(self):
        try:
            selected_row = widgets.invent_table.currentIndex().row()
            if selected_row < 0:
                QMessageBox.warning(self, "Ошибка", "Не выбрана строка для удаления!")
                return

            item_id = self.model.item(selected_row, 0).text()
            item_name = self.model.item(selected_row, 1).text()

            msg_box = QMessageBox()
            msg_box.setWindowTitle('Подтверждение удаления')
            msg_box.setText(f'Вы уверены, что хотите удалить оборудование:\n"{item_name}" (ID: {item_id})?')
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.button(QMessageBox.StandardButton.Yes).setText('Да')
            msg_box.button(QMessageBox.StandardButton.No).setText('Нет')
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            reply = msg_box.exec()

            if reply == QMessageBox.Yes:
                conn = get_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM equipment WHERE id=%s", (item_id,))
                    conn.commit()
                conn.close()

                self.logger.log_action("Удаление оборудования", f"Инв. № {item_id}")
                QMessageBox.information(self, "Успех", "Оборудование успешно удалено!")

                self.model.removeRow(selected_row)
                self.loadData()
                self.loadComboBoxData()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении оборудования: {str(e)}")

            
    def filterTableByType(self, index):
        if index == 0:  
            for row in range(self.model.rowCount()):
                widgets.invent_table.setRowHidden(row, False)
        else:
            selected_type = widgets.invent_fillte_type.currentText()
            for row in range(self.model.rowCount()):
                item_type = self.model.item(row, 2).text()  
                widgets.invent_table.setRowHidden(row, item_type != selected_type)


    def loadFilterComboBox(self):
        try:
            
            widgets.invent_fillte_type.clear()
            widgets.invent_fillte_type.addItem("Фильтр по типу")
            
            
            types = set()
            for row in range(self.model.rowCount()):
                item_type = self.model.item(row, 2).text()  
                types.add(item_type)
            
            
            for item_type in sorted(types):
                widgets.invent_fillte_type.addItem(item_type)
                widgets.invent_create_type.addItem(item_type)
                
        except Exception as e:
            print(f"Ошибка при загрузке фильтра: {e}")

    def searchEquipment(self):
        search_text = widgets.invent_search.text().strip().lower()
        
        if not search_text:
            
            for row in range(self.model.rowCount()):
                widgets.invent_table.setRowHidden(row, False)
            return
        
        
        for row in range(self.model.rowCount()):
            match_found = False
            for col in range(self.model.columnCount()):
                item = self.model.item(row, col)
                if item and search_text in item.text().lower():
                    match_found = True
                    break
            
            widgets.invent_table.setRowHidden(row, not match_found)
    
    def setupUserTable(self):
        
        table = widgets.adduser_user_table
        
        
        table.clear()
        
        
        headers = ["Логин", "Роль"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        
        table.setStyleSheet("""
            QTableWidget {
                background-color: rgb(33, 37, 43);
                alternate-background-color: rgb(40, 44, 52);
                gridline-color: rgb(60, 64, 72);
                color: rgb(221, 221, 221);
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: rgb(33, 37, 43);
                color: rgb(221, 221, 221);
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)
        
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        
        
        table.verticalHeader().setStretchLastSection(False)
        
        
        table.verticalHeader().setDefaultSectionSize(30)  
        
        
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        
        self.loadUserData()

    def loadUserData(self):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT login, role FROM users WHERE login != 'root'")
                users = cur.fetchall()
            conn.close()

            table = widgets.adduser_user_table
            table.setRowCount(0)
            table.setRowCount(len(users))

            for row, user in enumerate(users):
                login_item = QTableWidgetItem(user["login"])
                login_item.setTextAlignment(Qt.AlignCenter)

                role_item = QTableWidgetItem(user["role"])
                role_item.setTextAlignment(Qt.AlignCenter)

                if user["role"] == "admin":
                    role_item.setForeground(QColor(255, 165, 0))  # оранжевый
                else:
                    role_item.setForeground(QColor(144, 238, 144))  # зеленый

                table.setItem(row, 0, login_item)
                table.setItem(row, 1, role_item)

        except Exception as e:
            print(f"Ошибка при загрузке пользователей: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пользователей: {e}")


    def logout(self):
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Выход")
        msg_box.setText("Вы уверены, что хотите выйти?")
        
        
        yes_button = msg_box.addButton("Да", QMessageBox.YesRole)
        no_button = msg_box.addButton("Нет", QMessageBox.NoRole)
        msg_box.setIcon(QMessageBox.Question)
        
        
        msg_box.exec()
        
        if msg_box.clickedButton() == yes_button:
            
            self.close()
            
            
            auth_window = AuthWindow()
            if auth_window.exec() == QDialog.Accepted:
                
                window = MainWindow(auth_window.user_data)
                window.show()
            else:
                
                QApplication.quit()
    
    def createUser(self):
        try:
            login = widgets.adduser_login.text().strip()
            password = widgets.adduser_password.text().strip()
            role_text = widgets.adduser_select_role.currentText()

            if not login or not password:
                QMessageBox.warning(self, "Ошибка", "Введите логин и пароль!")
                return

            role = "admin" if role_text == "Администратор" else "user"

            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (login, password, role) VALUES (%s, %s, %s)",
                            (login, password, role))
                conn.commit()
            conn.close()

            self.logger.log_action("Создание пользователя", login)
            QMessageBox.information(self, "Успех", "Пользователь успешно создан!")

            widgets.adduser_login.clear()
            widgets.adduser_password.clear()
            widgets.adduser_select_role.setCurrentIndex(0)

            self.loadUserData()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании пользователя: {str(e)}")

    
    def deleteUser(self):
        try:
            selected_row = widgets.adduser_user_table.currentRow()

            if selected_row < 0:
                QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления!")
                return

            login_item = widgets.adduser_user_table.item(selected_row, 0)
            login = login_item.text()

            msg_box = QMessageBox()
            msg_box.setWindowTitle("Подтверждение удаления")
            msg_box.setText(f"Вы уверены, что хотите удалить пользователя {login}?")
            msg_box.setIcon(QMessageBox.Question)

            yes_button = msg_box.addButton("Да", QMessageBox.YesRole)
            no_button = msg_box.addButton("Нет", QMessageBox.NoRole)
            msg_box.setDefaultButton(no_button)

            msg_box.exec()

            if msg_box.clickedButton() == yes_button:
                conn = get_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM users WHERE login=%s", (login,))
                    conn.commit()
                conn.close()

                self.logger.log_action("Удаление пользователя", login)
                QMessageBox.information(self, "Успех", f"Пользователь {login} успешно удален!")

                self.loadUserData()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

                    
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                            f"Произошла ошибка: {str(e)}")
    def setupLogsTable(self):
        table = widgets.tableView
        
        
        self.logs_model = QStandardItemModel()
        table.setModel(self.logs_model)
        
        
        headers = ["Пользователь", "Действие", "Цель", "Дата и время"]
        self.logs_model.setHorizontalHeaderLabels(headers)

                
        table.setColumnWidth(0, 150)  
        table.setColumnWidth(1, 250)  
        table.setColumnWidth(2, 200)  
        table.setColumnWidth(3, 180)  
        table.verticalHeader().setVisible(False)
        
        
        table.setStyleSheet("""
            QTableView {
                background-color: rgb(33, 37, 43);
                alternate-background-color: rgb(33, 37, 43);
                gridline-color: 
                border: 1px solid 
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: rgb(33, 37, 43);
                color: white;
                padding: 5px;
                border: 1px solid 
                font-weight: bold;
            }
        """)
        
        
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
    
    def loadLogsData(self):
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT user, interact, target, DATE_FORMAT(data, '%d.%m.%Y %H:%i:%s') as data FROM logs ORDER BY data DESC")
                logs_data = cur.fetchall()
            conn.close()

            self.logs_model.removeRows(0, self.logs_model.rowCount())

            for log in logs_data:
                row = [
                    QStandardItem(log.get("user", "N/A")),
                    QStandardItem(log.get("interact", "N/A")),
                    QStandardItem(log.get("target", "N/A")),
                    QStandardItem(log.get("data", "N/A"))
                ]

                for item in row:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)

                self.logs_model.appendRow(row)

        except Exception as e:
            print(f"Ошибка загрузки логов: {str(e)}")
            self.logs_model.appendRow([
                QStandardItem("Ошибка"),
                QStandardItem(str(e)),
                QStandardItem(""),
                QStandardItem("")
            ])

    def setupCuratorsTable(self):
        table = widgets.curators_table

        self.curators_model = QStandardItemModel()
        table.setModel(self.curators_model)

        headers = ["ID", "Фамилия", "Имя", "Отчество", "Телефон"]
        self.curators_model.setHorizontalHeaderLabels(headers)

        # --- стиль ---
        table.setStyleSheet("""
            QTableView {
                background-color: rgb(33, 37, 43);
                alternate-background-color: rgb(33, 37, 43);
                gridline-color: #dee2e6;
                border: 1px solid #ced4da;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: rgb(33, 37, 43);
                color: white;
                padding: 5px;
                border: 1px solid;
                font-weight: bold;
            }
        """)

        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        table.horizontalHeader().setFont(font)
        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setDefaultSectionSize(30)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectRows)
        table.setSelectionMode(QTableView.SingleSelection)
        table.setSortingEnabled(False)

        # --- ширина колонок ---
        table.setColumnWidth(0, 80)   # ID
        table.setColumnWidth(1, 200)  # Фамилия
        table.setColumnWidth(2, 150)  # Имя
        table.setColumnWidth(3, 150)  # Отчество
        table.setColumnWidth(4, 180)  # Телефон

        # Подключаем кнопки
        widgets.curators_create_button.clicked.connect(self.createCurator)
        widgets.curators_delete_button.clicked.connect(self.deleteCurator)

        self.loadCuratorsData()

    def loadCuratorsData(self):
        """Загрузка кураторов из базы"""
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM curators")
                curators = cur.fetchall()
            conn.close()

            self.curators_model.removeRows(0, self.curators_model.rowCount())

            for c in curators:
                row = [
                    QStandardItem(str(c["id"])),
                    QStandardItem(c["fam"]),
                    QStandardItem(c["name"]),
                    QStandardItem(c["father"] or ""),
                    QStandardItem(c["phonenumber"] or ""),
                ]
                for item in row:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                self.curators_model.appendRow(row)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить кураторов: {e}")

    def createCurator(self):
        fam = widgets.curators_surname.text().strip()
        name = widgets.curators_name.text().strip()
        father = widgets.curators_otchestvo.text().strip()
        phone = widgets.curators_phone.text().strip()

        if not fam or not name:
            QMessageBox.warning(self, "Ошибка", "Введите фамилию и имя куратора!")
            return

        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO curators (fam, name, father, phonenumber) VALUES (%s, %s, %s, %s)",
                    (fam, name, father, phone),
                )
                curator_id = cur.lastrowid  # получаем id вставленной записи
                conn.commit()
            conn.close()

            self.logger.log_action("Создание куратора", f"{fam} {name}")
            QMessageBox.information(self, "Успех", "Куратор успешно добавлен!")

            # очищаем поля
            widgets.curators_surname.clear()
            widgets.curators_name.clear()
            widgets.curators_otchestvo.clear()
            widgets.curators_phone.clear()

            # добавляем новую строку в модель без полной перезагрузки
            row = [
                QStandardItem(str(curator_id)),
                QStandardItem(fam),
                QStandardItem(name),
                QStandardItem(father or ""),
                QStandardItem(phone or ""),
            ]
            for item in row:
                item.setTextAlignment(Qt.AlignCenter)
                item.setEditable(False)
            self.curators_model.appendRow(row)

            self.loadComboBoxData()  # обновляем список ответственных

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении куратора: {e}")


    def deleteCurator(self):
        selected_row = widgets.curators_table.currentIndex().row()
        if selected_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите куратора для удаления!")
            return

        curator_id = self.curators_model.item(selected_row, 0).text()
        curator_name = self.curators_model.item(selected_row, 1).text()

        msg_box = QMessageBox()
        msg_box.setWindowTitle("Подтверждение удаления")
        msg_box.setText(f"Удалить куратора {curator_name}?")
        msg_box.setIcon(QMessageBox.Question)
        yes_button = msg_box.addButton("Да", QMessageBox.YesRole)
        no_button = msg_box.addButton("Нет", QMessageBox.NoRole)
        msg_box.setDefaultButton(no_button)
        msg_box.exec()

        if msg_box.clickedButton() == yes_button:
            try:
                conn = get_connection()
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM curators WHERE id=%s", (curator_id,))
                    conn.commit()
                conn.close()

                self.logger.log_action("Удаление куратора", curator_name)
                QMessageBox.information(self, "Успех", "Куратор удалён!")

                # удаляем строку из модели сразу
                self.curators_model.removeRow(selected_row)

                # сбрасываем выделение
                widgets.curators_table.clearSelection()

                self.loadComboBoxData()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {e}")































if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    
    while True:
        auth_window = AuthWindow()
        if auth_window.exec() == QDialog.Accepted:
            window = MainWindow(auth_window.user_data)
            window.show()
            app.exec_()  
            
            
            if not hasattr(app, 'restart'):
                break
            delattr(app, 'restart')  
        else:
            break  
        
    
    sys.exit()