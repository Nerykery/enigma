import sys
import os
import platform
import requests
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView, QApplication, QMainWindow, QTableWidget, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon
from datetime import datetime
# site = "127.0.0.1"
with open('site.txt', 'r') as f:
    site = f.read().strip()



from modules import *
from widgets import *
os.environ["QT_FONT_DPI"] = "96" 



widgets = None
class Logger:
    def __init__(self, user_login):
        self.user_login = user_login
        self.site = site

    def log_action(self, action, target):
        try:
            log_entry = {
                "user": self.user_login,
                "interact": action,
                "target": target,
                "data": datetime.now().strftime('%d.%m.%Y %H:%M:%S')  
            }
            
            requests.post(
                f"http://{self.site}/dsa/hs/api/createlogs",
                json=[log_entry],
                headers={'Content-Type': 'application/json'},
                timeout=3
            )
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
            response = requests.get(f"http://{site}/dsa/hs/api/auth/{login}")
            if response.status_code == 200:
                users = response.json()
                if users and isinstance(users, list) and len(users) > 0:
                    user = users[0]
                    if user.get('password') == password and user.get('login'):
                        self.user_data = {
                            'login': user.get('login'),
                            'role': user.get('role')
                        }
                        self.accept()
                    else:
                        QMessageBox.warning(self, "Ошибка", "Неверный пароль или доступ запрещен")
                else:
                    QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
            else:
                QMessageBox.warning(self, "Ошибка", "Ошибка сервера")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения: {str(e)}")
    
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
        widgets.btn_logs.clicked.connect(self.loadLogsData)

        self.loadComboBoxData()
        self.setupCreateEquipment()
        self.setupUserTable() 

        
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
            
            equipment_response = requests.get(f"http://{site}/dsa/hs/api/equipment")
            equipment_data = equipment_response.json()
            
            
            
            curators_response = requests.get(f"http://{site}/dsa/hs/api/curators")
            curators_data = curators_response.json()
            
            
            curators_dict = {}
            for curator in curators_data:
                full_name = f"{curator['fam']} {curator['name']} {curator['father']}"
                curators_dict[full_name] = curator['phonenumber']
            
            
            self.model.removeRows(0, self.model.rowCount())
            
            
            for i, item in enumerate(equipment_data):
                phone = curators_dict.get(item['curator'], 'Не указан')
                
                
                row_items = [
                    QStandardItem(item['id']),  
                    QStandardItem(item['name']),  
                    QStandardItem(item['type']),  
                    QStandardItem(item['room']),  
                    QStandardItem(item['sost']),  
                    QStandardItem(item['curator']),  
                    QStandardItem(phone)  
                ]
                
                
                for item in row_items:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                
                
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

        if btnName == "btn_save":
            print("Save BTN clicked!")
        
        if btnName == "btn_add_user":
            widgets.stackedWidget.setCurrentWidget(widgets.adduser_page) 
            UIFunctions.resetStyle(self, btnName) 
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet())) 
        
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
            
            equipment_response = requests.get(f"http://{site}/dsa/hs/api/equipment")
            equipment_data = equipment_response.json()
            
            
            curators_response = requests.get(f"http://{site}/dsa/hs/api/curators")
            curators_data = curators_response.json()
            
            
            types = set()
            rooms = set()
            for item in equipment_data:
                types.add(item['type'])
                rooms.add(item['room'])
            
            
            widgets.invent_create_type.clear()
            widgets.invent_create_type.addItem("Тип")

            for item_type in sorted(types):
                widgets.invent_create_type.addItem(item_type)

            
            
            widgets.invent_create_room.clear()
            widgets.invent_create_room.addItem("Помещение")
            for room in sorted(rooms):
                widgets.invent_create_room.addItem(room)
            
            
            widgets.invent_create_curator.clear()
            widgets.invent_create_curator.addItem("Ответственный")
            for curator in curators_data:
                full_name = f"{curator['fam']} {curator['name']} {curator['father']}"
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
            
            if not self.isInventoryIdUnique(inventory_id):
                QMessageBox.warning(self, "Ошибка", 
                                f"Инвентарный номер '{inventory_id}' уже существует!")
                return

            data = [{
                "id": inventory_id,
                "name": widgets.invent_create_name.text(),
                "type": widgets.invent_create_type.currentText(),
                "room": widgets.invent_create_room.currentText(),
                "curator": widgets.invent_create_curator.currentText(),
                "sost": widgets.invent_create_sost.currentText()
            }]

            
            if not data[0]['name']:
                QMessageBox.warning(self, "Ошибка", "Не указано название оборудования!")
                return
            if data[0]['type'] == "Тип":
                QMessageBox.warning(self, "Ошибка", "Не выбран тип оборудования!")
                return
            if data[0]['room'] == "Помещение":
                QMessageBox.warning(self, "Ошибка", "Не указано помещение!")
                return

            response = requests.post(
                f"http://{site}/dsa/hs/api/createequip",
                json=data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                self.logger.log_action(
                    action="Создание оборудования",
                    target=f"Инв. № {inventory_id}"  
                )
                QMessageBox.information(self, "Успех", "Оборудование успешно добавлено!")
                self.clearCreateForm()
                self.loadData()
                widgets.invent_create_id.setText(self.generateInventoryId())
            else:
                QMessageBox.critical(self, "Ошибка", 
                                f"Ошибка при добавлении: {response.text}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                            f"Ошибка при отправке данных: {str(e)}")
            
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
                response = requests.get(f"http://{site}/dsa/hs/api/delequip/{item_id}")
                
                if response.status_code == 200:
                    self.logger.log_action(
                        action="Удаление оборудования",
                        target=f"Инв. № {item_id}"  
                    )
                    QMessageBox.information(self, "Успех", "Оборудование успешно удалено!")
                    self.model.removeRow(selected_row)
                    self.loadData()
                    self.loadComboBoxData()
                else:
                    QMessageBox.critical(self, "Ошибка", 
                                    f"Ошибка при удалении: {response.text}")
                        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                            f"Ошибка при удалении оборудования: {str(e)}")
            
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
            
            response = requests.get(f"http://{site}/dsa/hs/api/users")
            users = response.json()
            
            table = widgets.adduser_user_table
            table.setRowCount(0)  
            
            
            filtered_users = [user for user in users if user['login'] != "root"]
            
            
            table.setRowCount(len(filtered_users))
            
            
            for row, user in enumerate(filtered_users):
                
                login_item = QTableWidgetItem(user['login'])
                login_item.setTextAlignment(Qt.AlignCenter)
                
                
                role_item = QTableWidgetItem(user['role'])
                role_item.setTextAlignment(Qt.AlignCenter)
                
                if user['role'] == "admin":
                    role_item.setForeground(QColor(255, 165, 0))  
                else:
                    role_item.setForeground(QColor(144, 238, 144))  
                
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
                
            
            if role_text == "Администратор":
                role = "admin"
            else:
                role = "user"
            
            
            data = [{
                "login": login,
                "password": password,
                "role": role
            }]
            
            
            response = requests.post(
                f"http://{site}/dsa/hs/api/createuser",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.logger.log_action(
                    action="Создание пользователя",
                    target=login,
                    )
                QMessageBox.information(self, "Успех", "Пользователь успешно создан!")
                
                widgets.adduser_login.clear()
                widgets.adduser_password.clear()
                widgets.adduser_select_role.setCurrentIndex(0)
                
                self.loadUserData()
            else:
                QMessageBox.critical(self, "Ошибка", 
                                f"Ошибка при создании пользователя: {response.text}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", 
                            f"Ошибка при отправке данных: {str(e)}")
    
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
            
            
            msg_box.exec_()
            
            if msg_box.clickedButton() == yes_button:
                
                response = requests.get(f"http://{site}/dsa/hs/api/deluser/{login}")
                
                if response.status_code == 200:
                    self.logger.log_action(
                        action="Удаление",
                        target=login,
                    )
                    QMessageBox.information(self, "Успех", f"Пользователь {login} успешно удален!")
                    
                    self.loadUserData()
                else:
                    QMessageBox.critical(self, "Ошибка", 
                                    f"Ошибка при удалении пользователя: {response.text}")
                    
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
            response = requests.get(f"http://{site}/dsa/hs/api/logs")
            
            if response.status_code == 200:
                logs_data = response.json()
                self.logs_model.removeRows(0, self.logs_model.rowCount())
                
                for log in logs_data:
                    row = [
                        QStandardItem(log.get('user', 'N/A')),
                        QStandardItem(log.get('interact', 'N/A')),
                        QStandardItem(log.get('target', 'N/A')),
                        QStandardItem(log.get('data', 'N/A'))  
                    ]
                    
                    for item in row:
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setEditable(False)
                    
                    self.logs_model.appendRow(row)
                
                
                self.logs_model.sort(3, Qt.DescendingOrder)
                
        except Exception as e:
            print(f"Ошибка загрузки логов: {str(e)}")
            self.logs_model.appendRow([
                QStandardItem("Ошибка"),
                QStandardItem(str(e)),
                QStandardItem(""),
                QStandardItem("")
            ])


























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