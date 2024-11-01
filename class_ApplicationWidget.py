#
from pathlib import Path
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QMessageBox, QMainWindow

class AplicationWidget:

    def __init__(self) -> None:
        super().__init__()

    # ПЕРЕМЕННЫЕ PATH

        # Создаем переменные в которые записываем расположение иконки с изображением.
        self.path_icon_main = str(Path(Path.cwd(), "Resources", "Icons", "icn61.ico"))
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_quest = str(Path(Path.cwd(), "Resources", "Icons", "icn28.ico"))
        self.path_icon_err = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        self.path_icon_btn_add = str(Path(Path.cwd(), "Resources", "Icons", "icn37.ico"))
        self.path_icon_btn_run = str(Path(Path.cwd(), "Resources", "Icons", "icn66.ico"))
        self.path_icon_btn_del = str(Path(Path.cwd(), "Resources", "Icons", "icn41.ico"))
        self.path_icon_btn_stop = str(Path(Path.cwd(), "Resources", "Icons", "icn65.ico"))
        self.path_icon_btn_clear = str(Path(Path.cwd(), "Resources", "Icons", "icn41.ico"))
        self.path_icon_btn_show = str(Path(Path.cwd(), "Resources", "Icons", "icn79.ico"))
        self.path_icon_btn_find = str(Path(Path.cwd(), "Resources", "Icons", "icn68.ico"))
        self.path_icon_menu_save = str(Path(Path.cwd(), "Resources", "Icons", "icn46.ico"))
        self.path_icon_menu_open = str(Path(Path.cwd(), "Resources", "Icons", "icn73.ico"))
        self.path_icon_menu_exit = str(Path(Path.cwd(), "Resources", "Icons", "icn75.ico"))
        self.path_icon_close_page = str(Path(Path.cwd(), "Resources", "Icons", "icn20.ico"))
        self.path_icon_btn_set = str(Path(Path.cwd(), "Resources", "Icons", "icn38.ico"))
        self.path_icon_btn_open_window = str(Path(Path.cwd(), "Resources", "Icons", "icn47.ico"))
        self.path_icon_done = str(Path(Path.cwd(), "Resources", "Icons", "icn15.ico"))
        self.path_icon_progress = str(Path(Path.cwd(), "Resources", "Icons", "icn16.ico"))
        self.path_icon_not_runn = str(Path(Path.cwd(), "Resources", "Icons", "icn14.ico"))
        self.path_icon_sound_stop = str(Path(Path.cwd(), "Resources", "Icons", "icn65.ico"))
        self.path_icon_sound_play_btn = str(Path(Path.cwd(), "Resources", "Icons", "icn78.ico"))

        # СОЗДАНИЕ ЭКЗЕМПЛЯРА КЛАССА QLable, ДЛЯ СОЗДАНИЯ ОКНА УВЕДОМЛЕНИЯ
        
        # Создаем экзепляр класса QLabel(), с помощью которого можно создать окно уведомления 
        self.info_wait = QLabel()
        # Устанавливаем заголовок окну уведомления
        self.info_wait.setWindowTitle('Уведомление')
        # Устанавливаем текс окна уведомления
        self.info_wait.setText(f"Please wait...\nProcess is in progress")
        # Автоматически подбирает размер окна и расположение его в зависимости от текста 
        self.info_wait.adjustSize()
        #
        self.info_wait.setFont(QtGui.QFont("Times", 9, QtGui.QFont.Normal))
        # Выравнивание текста по центру
        self.info_wait.setAlignment(QtCore.Qt.AlignCenter)
        # Установка фиксированного значения ширины окна уведомления
        self.info_wait.setFixedWidth(200)
        # Установка фиксированного значения высоты окна уведомления
        self.info_wait.setFixedHeight(80)
        # Установка переноса текста на следующую строку
        self.info_wait.setWordWrap(False)
        # Отступ текста в пикселях
        self.info_wait.setIndent(50)

    # СТАТУС БАР

        # Создаем экземпляр класса  QLable Выводим сообщение в статус бар со статусом загрузки 
        self.lbl = QLabel()
        # Добавляем стиль к экземпляру класса
        self.lbl.setStyleSheet("font-size: 12px;")
        # Выравнивание по левому краю
        self.lbl.setAlignment(QtCore.Qt.AlignLeft)
        # Добавляем в экземпляр класса lbl текст и изображение ввиде html кода
        self.lbl.setText('<img src="{}">  Готово'.format(self.path_icon_done))

        # Создаем экземпляр класса  QLable Выводим сообщение в статус бар со статусом загрузки SNMP
        self.bot_lbl = QLabel()
        # Добавляем стиль к экземпляру класса
        self.bot_lbl.setStyleSheet("font-size: 12px;")
        # Выравнивание по левому краю
        self.bot_lbl.setAlignment(QtCore.Qt.AlignRight)
        # Добавляем в экземпляр класса lbl текст и изображение ввиде html кода
        self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))

        # Создаем экземпляр класса  QLable Выводим сообщение в статус бар со статусом загрузки TelegramBot
        self.snmp_lbl = QLabel()
        # Добавляем стиль к экземпляру класса
        self.snmp_lbl.setStyleSheet("font-size: 12px;")
        # Выравнивание по левому краю
        self.snmp_lbl.setAlignment(QtCore.Qt.AlignRight)
        # Добавляем в экземпляр класса lbl текст и изображение ввиде html кода
        self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_not_runn))

        # Создаем экземпляр класса  QLable Выводим сообщение в статус бар со статусом загрузки AlarmMonitoring
        self.alarm_lbl = QLabel()
        # Добавляем стиль к экземпляру класса
        self.alarm_lbl.setStyleSheet("font-size: 12px;")
        # Выравнивание по левому краю
        self.alarm_lbl.setAlignment(QtCore.Qt.AlignRight)
        # Добавляем в экземпляр класса lbl текст и изображение ввиде html кода
        self.alarm_lbl.setText('<img src="{}">  AlarmMonitoring'.format(self.path_icon_not_runn))

        # СОЗДАЕМ ЭКЗЕМПЛЯР КЛАССА QIcon, ДОБАВЛЕНИЕ ИЗОБРАЖЕНИЯ ДЛЯ ДИАЛОГОВОГО ОКНА

        # Создаем экземпляр класса icon_main_window, класс QIcon - отвечает за добавления иконки с изображением для основного окна программы
        self.icon_main_window = QtGui.QIcon()
        # Вызываем у экземпляра класса icon_main_window метод addFile, у казываем путь где находится изображение
        self.icon_main_window.addFile(self.path_icon_main)
        # Создаем экземпляр класса icon_inf, класс QIcon - отвечает за добавления иконки с изображением для диалогового окна
        self.icon_inf = QtGui.QIcon()
        # Вызываем у экземпляра класса icon_inf метод addFile, у казываем путь где находится изображение "Уведомление"
        self.icon_inf.addFile(self.path_icon_inf)
        # Создаем экземпляр класса icon_warn, класс QIcon - отвечает за добавления иконки с изображением для диалогового окна
        self.icon_warn = QtGui.QIcon()
        # Вызываем у экземпляра класса icon_warn метод addFile, у казываем путь где находится изображение "Предупреждение"
        self.icon_warn.addFile(self.path_icon_warn)
        # Создаем экземпляр класса icon_quest, класс QIcon - отвечает за добавления иконки с изображением для диалогового окна
        self.icon_quest = QtGui.QIcon()
        # Вызываем у экземпляра класса icon_quest метод addFile, у казываем путь где находится изображение "Вопрос"
        self.icon_quest.addFile(self.path_icon_quest)
        # Создаем экземпляр класса, класс QIcon - отвечает за добавления иконки с изображением для диалогового окна
        self.icon_err = QtGui.QIcon()
        # Вызываем у экземпляра класса self.icon_err метод addFile, у казываем путь где находится изображение "Ошибка"
        self.icon_err.addFile(self.path_icon_err)
        # У экземпляра класса info_wait, класс QLable вызываем метод, который добавляет изображение
        self.info_wait.setWindowIcon(self.icon_inf)
        # Добавление иконки для остановки мелодии для она SecondWindow
        self.icon_sound_stop = QtGui.QIcon()
        self.icon_sound_stop.addFile(self.path_icon_sound_stop)

        # У QMainWindow вызываем метод setWindowIcon, которому передаем экземпляр класса нашего приложения app(self) и экземпляр класса icon_main_window в котором содержится изображение
        QMainWindow.setWindowIcon(self, self.icon_main_window)

    # СОЗДАНИЕ ЭКЗЕМПЛЯРОВ КЛАССОВ QMessageBox, СОЗДАНИЕ ДИАЛОГОВЫХ ОКОН 
        
        # Диалоговое окно с запросом на удаление ИБЭП
        self.inf_del_device = QMessageBox()#
        self.inf_del_device.setWindowTitle('Уведомление')
        self.inf_del_device.setIcon(QMessageBox.Question)
        self.inf_del_device.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_device.setWindowIcon(self.icon_quest)
        # Диалоговое окно с запросом на удаление коммутатора
        self.inf_del_switch = QMessageBox() #
        self.inf_del_switch.setWindowTitle('Уведомление')
        self.inf_del_switch.setIcon(QMessageBox.Question)
        self.inf_del_switch.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_switch.setWindowIcon(self.icon_quest)
        # Диалоговое окно с запросом на удаление коммутатора и портов
        self.inf_del_join_data = QMessageBox() #
        self.inf_del_join_data.setWindowTitle('Уведомление')
        self.inf_del_join_data.setIcon(QMessageBox.Question)
        self.inf_del_join_data.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_join_data.setWindowIcon(self.icon_quest)
        # Диалоговое окно с запросом на удаление пользователя
        self.inf_del = QMessageBox() #
        self.inf_del.setWindowTitle('Уведомление')
        self.inf_del.setIcon(QMessageBox.Question)
        self.inf_del.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del.setWindowIcon(self.icon_quest)
        # Диалоговое окно с запросом на удаление порта коммутатора
        self.inf_del_port = QMessageBox()
        self.inf_del_port.setWindowTitle('Уведомление')
        self.inf_del_port.setIcon(QMessageBox.Question)
        self.inf_del_port.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_port.setWindowIcon(self.icon_quest)
        # Диалоговое окно с запросом на удаление sla коммутатора
        self.inf_del_sla = QMessageBox()
        self.inf_del_sla.setWindowTitle('Уведомление')
        self.inf_del_sla.setIcon(QMessageBox.Question)
        self.inf_del_sla.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_sla.setWindowIcon(self.icon_quest)
        # Диалоговое окно с запросом на выход из приложения
        self.inf_exit_app = QMessageBox()
        self.inf_exit_app.setWindowTitle('Уведомление')
        self.inf_exit_app.setText('Выйти из программы?')
        self.inf_exit_app.setIcon(QMessageBox.Question)
        self.inf_exit_app.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        self.inf_exit_app.setWindowIcon(self.icon_quest)
        # Диалоговое окно с уведомлением о результате действия  
        self.inf_success = QMessageBox()
        self.inf_success.setWindowTitle('Уведомление')
        self.inf_success.setText('Успех!')
        self.inf_success.setIcon(QMessageBox.Information)
        self.inf_success.setWindowIcon(self.icon_inf)
        # Диалоговое окно с уведомлением об отсутствии значений
        self.inf_empty = QMessageBox()
        self.inf_empty.setWindowTitle('Уведомление')
        self.inf_empty.setIcon(QMessageBox.Information)
        self.inf_empty.setWindowIcon(self.icon_inf)
        # Диалоговое окно с уведомлением об недопустимом значении
        self.inf_value_invalid = QMessageBox()
        self.inf_value_invalid.setText('Недопустимое значение')
        self.inf_value_invalid.setWindowTitle('Уведомление')
        self.inf_value_invalid.setIcon(QMessageBox.Information)
        self.inf_value_invalid.setWindowIcon(self.icon_inf)
        #
        self.inf_value_error = QMessageBox()
        self.inf_value_error.setText('Ошибка значения')
        self.inf_value_error.setWindowTitle('Уведомление')
        self.inf_value_error.setIcon(QMessageBox.Information)
        self.inf_value_error.setWindowIcon(self.icon_inf)
       # Ошибка выполнения 
        self.runtime_error = QMessageBox()
        self.runtime_error.setWindowTitle('Ошибка')
        self.runtime_error.setIcon(QMessageBox.Critical)
        self.runtime_error.setWindowIcon(self.icon_err)
        # Диалоговое окно на запрос закрытия страницы
        self.inf_close_page = QMessageBox()
        self.inf_close_page.setWindowTitle('Уведомление')
        self.inf_close_page.setText('Закрыть страницу?')
        self.inf_close_page.setStandardButtons(QMessageBox.Close|QMessageBox.Cancel)
        self.inf_close_page.setDefaultButton(QMessageBox.Close)
        # Диалоговое окно на запрос остановить работу Telegram Bot
        self.req_stop_bot = QMessageBox()
        self.req_stop_bot.setWindowTitle('Уведомление')
        self.req_stop_bot.setText('Конфликт запущенных экземпляров Telegram Бот\n Остановить работу Telegram Бота?')
        self.req_stop_bot.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.req_stop_bot.setDefaultButton(QMessageBox.Ok)
        self.req_stop_bot.setWindowIcon(self.icon_quest)

    # СОЗДАЕМ ЭКЗЕМПЛЯР КЛАССА QIcon, ДОБАВЛЕНИЕ ИЗОБРАЖЕНИЯ ДЛЯ КНОПОК ПРИЛОЖЕНИЯ

        # Создаем экземпляр класса icon_btn_add, класс QIcon - отвечает за добавления иконки с изображением для кнопки приложения
        self.icon_btn_add = QtGui.QIcon()
        self.icon_btn_del = QtGui.QIcon()
        self.icon_btn_run = QtGui.QIcon()
        self.icon_btn_stop = QtGui.QIcon()
        self.icon_btn_show = QtGui.QIcon()
        self.icon_btn_clear = QtGui.QIcon()
        self.icon_btn_find = QtGui.QIcon()
        self.icon_btn_set = QtGui.QIcon()
        self.icon_btn_open_second_window = QtGui.QIcon()
        self.icon_btn_play_sound = QtGui.QIcon() 
        # Вызываем у экземпляра класса icon_btn_add метод addFile, передав ему в качестве аргумента путь, где находится изображение
        self.icon_btn_add.addFile(self.path_icon_btn_add)
        self.icon_btn_del.addFile(self.path_icon_btn_del)
        self.icon_btn_run.addFile(self.path_icon_btn_run)
        self.icon_btn_stop.addFile(self.path_icon_btn_stop)
        self.icon_btn_clear.addFile(self.path_icon_btn_clear)
        self.icon_btn_show.addFile(self.path_icon_btn_show)
        self.icon_btn_find.addFile(self.path_icon_btn_find)
        self.icon_btn_set.addFile(self.path_icon_btn_set)
        self.icon_btn_open_second_window.addFile(self.path_icon_btn_open_window)
        self.icon_btn_play_sound.addFile(self.path_icon_sound_play_btn)
        
    # СОЗДАНИЕ ЭКЗЕМПЛЯРОВ КЛАССА QIcon, ДОБАВЛЕНИЕ ИЗОБРАЖЕНИЯ ДЛЯ МЕНЮ ВКЛАДОК

        # Создаем экземпляр класса QIcon - отвечает за добавления иконки с изображением для вкладки меню
        self.icon_menu_save = QtGui.QIcon()
        self.icon_menu_open = QtGui.QIcon()
        self.icon_menu_exit = QtGui.QIcon()
        self.icon_close_page = QtGui.QIcon()

        # Вызываем у экземпляра класса icon_menu_save метод addFile, передав ему в качестве аргумента путь, где находится изображение
        self.icon_menu_save.addFile(self.path_icon_menu_save)
        self.icon_menu_open.addFile(self.path_icon_menu_open)
        self.icon_menu_exit.addFile(self.path_icon_menu_exit)
        self.icon_close_page.addFile(self.path_icon_close_page)

        # Окно для тестов
        self.test_font_size = QMessageBox()
        self.test_font_size.setWindowTitle('Авария')
        self.test_font_size.setText('Авария')
        self.test_font_size.setIcon(QMessageBox.Critical)
        self.test_font_size.setWindowIcon(self.icon_err)


if __name__ == "__main__":
    show = AplicationWidget()
    show.show()

        

        