import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtWidgets import QListWidget, QScrollBar, QMessageBox
from PyQt5.QtWidgets import QLabel, QLineEdit
from PyQt5.QtWidgets import QToolTip, QStyleFactory
from PyQt5.QtGui import QFont, QColor, QCursor
from PyQt5 import QtCore, QtWidgets
from PyQt5.Qt import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import datetime as dt


# класс функций для работы с базой данных
class DB:
    # конструктор класса
    def __init__(self):
        # соединяемся с файлом базы данных
        self.conn = sqlite3.connect("Database5.db")
        # создаём курсор для виртуального управления базой данных
        self.cur = self.conn.cursor()
        # создаем таблицу
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS buy (id INTEGER PRIMARY KEY, product TEXT, \
            price INT, comment TEXT, date DATE, category TEXT)")
        # сохраняем сделанные изменения в базе
        self.conn.commit()

        # деструктор класса

    # отключаемся от базы при завершении работы
    def disconnect(self):
        self.conn.close()

    # просмотр всех записей
    def view(self):
        # выбираем все записи о покупках
        self.cur.execute("SELECT * FROM buy")
        # собираем все найденные записи в колонку со строками
        rows = self.cur.fetchall()
        # возвращаем сроки с записями расходов
        return rows

    # добавляем новую запись
    def insert(self, product, price, comment, date, category):
        # формируем запрос с добавлением новой записи в БД
        self.cur.execute("INSERT INTO buy VALUES (NULL,?,?,?,?,?)", (product, price, comment, date, category,))
        # сохраняем изменения
        self.conn.commit()

    # обновляем информацию о покупке
    def update(self, id, product, price, date, category, comment):
        # формируем запрос на обновление записи в БД
        self.cur.execute("UPDATE buy SET product=?, price=?, date=?, category=?, comment=? WHERE id=?",
                         (product, price, date, category, comment, id,))
        # сохраняем изменения
        self.conn.commit()

    # удаляем запись
    def delete(self, id):
        # формируем запрос на удаление выделенной записи по внутреннему порядковому номеру
        self.cur.execute("DELETE FROM buy WHERE id=?", (id,))
        # сохраняем изменения
        self.conn.commit()

    # ищем запись по названию покупки
    def search(self, product="", ):
        # формируем запрос на поиск по точному совпадению
        self.cur.execute("SELECT * FROM buy WHERE product=?", (product,))
        # формируем полученные строки и возвращаем их как ответ
        rows = self.cur.fetchall()
        return rows


# создаём экземпляр базы данных на основе класса
db = DB()


# класс для рисования графика
class GraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('График распределния трат по категориям')
        self.setGeometry(100, 100, 500, 500)

        # Создаем виджет для размещения графика
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем объект Figure и FigureCanvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Создаем переменную для хранения подписей категорий
        self.labels = []

    def plot_matplotlib(self, dictionary):
        # Очищаем виджет графика
        self.figure.clear()

        ax = self.figure.add_subplot()
        labels = list(dictionary.keys())
        values = list(dictionary.values())
        self.labels = ax.pie(values, labels=labels, autopct='%1.0f%%')
        ax.set_title('Основные категории расходов')
        self.canvas.draw()


# класс функций-обработчиков
class Functions(QMainWindow):
    def __init__(self):
        super().__init__()
        self.graph_window = None
        self.graph_data = None

    # обрабатываем закрытие окна
    def closeEvent(self, event):
        # отключаемся от базы данных
        db.disconnect()
        # выводим диалоговое окно с подтверждением закрытия
        reply = QMessageBox.question(self, 'Подтверждение', 'Вы действительно хотите закрыть приложение?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # закрываем текущее окно
            self.close()
            # завершаем приложение
            QApplication.quit()

    # заполняем поля ввода значениями выделенной позиции в общем списке
    def get_selected_row(self, event):
        # получаем список выделенных строк
        selected_items = self.listWidget.selectedItems()
        if selected_items:
            # получаем выделенный элемент
            selected_row = selected_items[0]

            # получаем текст элемента
            selected_text = selected_row.text()

            # преобразуем строку с данными в массив, удаляя ненужные символы
            selected_text = selected_text[1:-1].replace("'", "")
            selected_text = selected_text.replace('"', "")
            selected_text = list(map(str, selected_text.split(', ')))

            selected_text_name = selected_text[1]
            selected_text_cost = selected_text[2]
            selected_text_comment = selected_text[3]
            selected_text_date = selected_text[4]
            selected_text_category = selected_text[5]

            # устанавливаем значения полей ввода
            self.name_input.setText(selected_text_name)
            self.cost_input.setText(selected_text_cost)
            self.comment_input.setText(selected_text_comment)
            self.date_input.setText(selected_text_date)
            self.category_input.setText(selected_text_category)

    # обработчик нажатия на кнопку «Посмотреть всё»
    def view_command(self):
        # Очищаем список QListWidget
        self.listWidget.clear()

        # Получаем все записи из базы данных
        rows = db.view()

        # Добавляем записи на экран
        for row in rows:
            # Создаем QListWidgetItem с текстом записи
            item = QListWidgetItem(str(row))
            # Добавляем QListWidgetItem в QListWidget
            self.listWidget.addItem(item)

    # обработчик нажатия на кнопку «Поиск»
    def search_command(self, event):
        # Очищаем QListWidget
        self.listWidget.clear()

        # Получаем текст поискового запроса
        search_text = self.name_input.text()

        # Находим все записи по названию покупки
        rows = db.search(search_text)

        # Добавляем найденные записи в QListWidget
        for row in rows:
            item = QListWidgetItem(str(row))
            self.listWidget.addItem(item)

    # обработчик нажатия на кнопку «Добавить»
    def add_command(self, event):
        try:
            # Получаем значения из полей ввода
            product = self.name_input.text()
            price = int(self.cost_input.text())
            comment = self.comment_input.text()
            date = self.date_input.text()
            date = dt.datetime.strptime(date, "%Y-%m-%d").date()
            category = self.category_input.text()

            # проверяем корректность введенных данных
            if len(product) == 0 or len(str(price)) == 0 or len(category) == 0:
                raise ValueError("Первая строка должна быть заполнена")

            # Добавляем запись в БД
            db.insert(product, price, comment, date, category)

            # Обновляем список в QListWidget
            self.view_command()
        except ValueError:
            QToolTip.showText(QCursor.pos(), "Неверный формат ввода")

    # обработчик нажатия на кнопку «Удалить»
    def delete_command(self, event):
        # получаем список выделенных строк
        selected_items = self.listWidget.selectedItems()
        if selected_items:
            # получаем выделенный элемент
            selected_row = selected_items[0]

            # получаем текст элемента
            selected_text = selected_row.text()

            # преобразуем строку с данными в массив, удаляя ненужные символы
            selected_text = selected_text[1:-1].replace("'", "")
            selected_text = selected_text.replace('"', "")
            selected_text = list(map(str, selected_text.split(', ')))

            # получаем id
            id = selected_text[0]

            # Удаляем запись из базы данных
            db.delete(id)

            # Обновляем таблицу
            self.view_command()

            # очищаем поля
            self.name_input.clear()
            self.cost_input.clear()
            self.date_input.clear()
            self.category_input.clear()
            self.comment_input.clear()

    # обработчик нажатия на кнопку «Обновить»
    def update_command(self, event):
        # получаем список выделенных строк
        selected_items = self.listWidget.selectedItems()
        if selected_items:
            # получаем выделенный элемент
            selected_row = selected_items[0]

            # получаем текст элемента
            selected_text = selected_row.text()

            # преобразуем строку с данными в массив, удаляя ненужные символы
            selected_text = selected_text[1:-1].replace("'", "")
            selected_text = selected_text.replace('"', "")
            selected_text = list(map(str, selected_text.split(', ')))

            id = selected_text[0]
            try:
                # получаем обновленные значения
                product = self.name_input.text()
                price = int(self.cost_input.text())
                comment = self.comment_input.text()
                date = self.date_input.text()
                date = dt.datetime.strptime(date, "%Y-%m-%d").date()
                category = self.category_input.text()

                # проверяем корректность введенных данных
                if len(product) == 0 or len(str(price)) == 0 or len(category) == 0:
                    raise ValueError("Первая строка должна быть заполнена")

                # Обновляем данные в базе данных о выделенной записи
                db.update(id, product, price, date, category, comment)

                # Обновляем список в QListWidget
                self.view_command()
            except ValueError:
                QToolTip.showText(QCursor.pos(), "Неверный формат ввода")

    # обработчик кнопки "очистить поля"
    def clear_command(self):
        self.name_input.clear()
        self.cost_input.clear()
        self.date_input.clear()
        self.category_input.clear()
        self.comment_input.clear()

    # Обработчик кнопки "График"
    def graph_command(self):
        # Подготавливаем данные для графика
        rows = db.view()
        dictionary = {}
        for row in rows:
            selected_text = str(row)[1:-1].replace("'", "")
            selected_text = selected_text.replace('"', "")
            selected_text = list(map(str, selected_text.split(', ')))
            dictionary[str(selected_text[5])] = dictionary.setdefault(str(selected_text[5]), 0) + int(
                selected_text[2])
        df = []
        for key, value in dictionary.items():
            df.append([value, key])
        df.sort(reverse=True)
        grouped_dictionary = {}
        other = 0
        for i in range(len(df)):
            if i <= 3:
                grouped_dictionary[df[i][1].lower()] = df[i][0]
            else:
                other += df[i][0]
        if len(grouped_dictionary) >= 4:
            grouped_dictionary['другое'] = other

        # Если окно с графиком уже открыто, то обновляем данные и перерисовываем график
        if self.graph_window:
            self.graph_window.plot_matplotlib(grouped_dictionary)
            self.graph_window.show()
        else:
            # Создаем новое окно с графиком
            self.graph_window = GraphWindow()
            self.graph_window.plot_matplotlib(grouped_dictionary)
            self.graph_window.show()

    # Обработчик кнопки закрытия графика
    def close_graph(self):
        if self.graph_window:
            self.graph_window.hide()


# подключаем графический интерфейс
class Budget(Functions):
    # инициализируем
    def __init__(self):
        super().__init__()

        # В метод initUI() будем выносить всю настройку интерфейса
        self.initUI()

    def initUI(self):
        # создаем окно и меняем заголовок
        self.setGeometry(300, 300, 1000, 500)
        self.setWindowTitle('Бюджет')

        # кнопка 'Очистить поля'
        self.btn_clear = QPushButton('Очистить поля', self)
        self.btn_clear.resize(125, 25)
        self.btn_clear.move(800, 100)
        font_clear = QFont()
        font_clear.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_clear.setFont(font_clear)
        self.btn_clear.clicked.connect(self.clear_command)  # прикрепляем функцию

        # кнопка 'Посмотреть все'
        self.btn_check_all = QPushButton('Посмотреть все', self)
        self.btn_check_all.resize(125, 25)
        self.btn_check_all.move(800, 150)
        font_check_all = QFont()
        font_check_all.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_check_all.setFont(font_check_all)
        self.btn_check_all.clicked.connect(self.view_command)  # прикрепляем функцию

        # кнопка 'Поиск'
        self.btn_search = QPushButton('Поиск по названию', self)
        self.btn_search.resize(125, 25)
        self.btn_search.move(800, 200)
        font_search = QFont()
        font_search.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_search.setFont(font_search)
        self.btn_search.clicked.connect(self.search_command)  # прикрепляем функцию

        # кнопка 'Добавить'
        self.btn_add = QPushButton('Добавить', self)
        self.btn_add.resize(125, 25)
        self.btn_add.move(800, 250)
        font_add = QFont()
        font_add.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_add.setFont(font_add)
        self.btn_add.clicked.connect(self.add_command)  # прикрепляем функцию

        # кнопка 'Обновить'
        self.btn_update = QPushButton('Обновить', self)
        self.btn_update.resize(125, 25)
        self.btn_update.move(800, 300)
        font_update = QFont()
        font_update.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_update.setFont(font_update)
        self.btn_update.clicked.connect(self.update_command)  # прикрепляем функцию

        # кнопка 'Удалить'
        self.btn_del = QPushButton('Удалить', self)
        self.btn_del.resize(125, 25)
        self.btn_del.move(800, 350)
        font_del = QFont()
        font_del.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_del.setFont(font_del)
        self.btn_del.clicked.connect(self.delete_command)  # прикрепляем функцию

        # кнопка 'График'
        self.btn_graph = QPushButton('График', self)
        self.btn_graph.resize(125, 25)
        self.btn_graph.move(800, 400)
        font_graph = QFont()
        font_graph.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_graph.setFont(font_graph)
        self.btn_graph.clicked.connect(self.graph_command)  # прикрепляем функцию

        # кнопка 'Закрыть'
        self.btn_close = QPushButton('Закрыть', self)
        self.btn_close.resize(125, 25)
        self.btn_close.move(800, 450)
        font_close = QFont()
        font_close.setPointSize(10)  # устанавливаем размер шрифта
        self.btn_close.setFont(font_close)
        self.btn_close.clicked.connect(self.closeEvent)  # прикрепляем функцию

        # надпись для ввода названия
        self.label_name = QLabel("Название*", self)
        self.label_name.resize(200, 35)
        font_name = QFont()
        font_name.setPointSize(16)  # устанавливаем размер шрифта
        self.label_name.setFont(font_name)
        self.label_name.move(70, 30)

        # поле для ввода названия
        self.name_input = QLineEdit(self)
        self.name_input.resize(150, 25)
        self.name_input.move(190, 34)

        # надпись для ввода стоимости
        self.label_cost = QLabel("Стоимость*", self)
        self.label_cost.resize(200, 35)
        font_cost = QFont()
        font_cost.setPointSize(16)  # устанавливаем размер шрифта
        self.label_cost.setFont(font_cost)
        self.label_cost.move(390, 30)

        # поле для ввода стоимости
        self.cost_input = QLineEdit(self)
        self.cost_input.resize(150, 25)
        self.cost_input.move(520, 34)

        # напишем подсказку для стоимости
        self.cost_input.setPlaceholderText("Введите целое число")
        palette_cost = self.cost_input.palette()
        palette_cost.setColor(self.cost_input.palette().PlaceholderText, QColor(0, 0, 0, 127))
        self.cost_input.setPalette(palette_cost)

        # надпись для ввода даты
        self.label_date = QLabel("Дата*", self)
        self.label_date.resize(200, 35)
        font_date = QFont()
        font_date.setPointSize(16)  # устанавливаем размер шрифта
        self.label_date.setFont(font_date)
        self.label_date.move(720, 30)

        # поле для ввода даты
        self.date_input = QLineEdit(self)
        self.date_input.resize(150, 25)
        self.date_input.move(790, 34)

        # напишем подсказку для даты
        self.date_input.setPlaceholderText("Формат: YYYY-mm-dd")
        palette_date = self.date_input.palette()
        palette_date.setColor(self.date_input.palette().PlaceholderText, QColor(0, 0, 0, 127))
        self.date_input.setPalette(palette_date)

        # надпись для ввода категории
        self.label_category = QLabel("Категория*", self)
        self.label_category.resize(200, 35)
        font_category = QFont()
        font_category.setPointSize(16)  # устанавливаем размер шрифта
        self.label_category.setFont(font_category)
        self.label_category.move(70, 70)

        # поле для ввода категории
        self.category_input = QLineEdit(self)
        self.category_input.resize(150, 25)
        self.category_input.move(190, 74)

        # надпись для ввода комментария
        self.label_comment = QLabel("Комментарий", self)
        self.label_comment.resize(200, 35)
        font_comment = QFont()
        font_comment.setPointSize(16)  # устанавливаем размер шрифта
        self.label_comment.setFont(font_comment)
        self.label_comment.move(389, 70)

        # поле для ввода комментария
        self.comment_input = QLineEdit(self)
        self.comment_input.resize(200, 25)
        self.comment_input.move(555, 74)

        # вспомогательная надпись
        self.label_help = QLabel("* - обязательное поле", self)
        self.label_help.resize(self.label_help.sizeHint())
        font_help = QFont()
        font_help.setPointSize(8)  # устанавливаем размер шрифта
        self.label_help.setFont(font_help)
        self.label_help.move(0, 0)

        # Создаем QListWidget, где появятся наши покупки
        self.listWidget = QListWidget(self)
        self.listWidget.setGeometry(0, 125, 700, 375)

        # Привязываем выбор любого элемента списка к запуску функции выбора
        self.listWidget.itemClicked.connect(self.get_selected_row)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    # учитываем разрешение экрана
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Установка глобального стиля для приложения
    app.setStyle(QStyleFactory.create("Fusion"))

    # Устанавливаем стиль шрифта и цвет для всплывающих подсказок
    QToolTip.setFont(QFont("SansSerif", 10))
    app.setStyleSheet("QToolTip { background-color: red; color: white; }")

    # создаем экземпляр класса Budget
    window = Budget()
    window.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
