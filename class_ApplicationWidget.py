#
from pathlib import Path
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QMessageBox, QMainWindow

class AplicationWidget:
    def __init__(self) -> None:

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
        self.path_icon_btn_show = str(Path(Path.cwd(), "Resources", "Icons", "icn72.ico"))
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


    # СОЗДАНИЕ ЭКЗЕМПЛЯРОВ КЛАССОВ QMessageBox, СОЗДАНИЕ ДИАЛОГОВЫХ ОКОН 
        
        # Создаем экзепляр класса QMessageBox(), с помощью которого можно создать диалоговое окно
        self.inf_success = QMessageBox() 
        self.inf_del = QMessageBox()
        self.inf_no_user_del = QMessageBox()
        self.err_request_db = QMessageBox()
        self.inf_dubl_ip_address = QMessageBox()
        self.err_ip_correct = QMessageBox()
        self.inf_del_device = QMessageBox()
        self.inf_del_switch = QMessageBox()
        self.inf_del_join_data = QMessageBox()
        self.inf_del_port = QMessageBox()
        self.inf_no_device_del = QMessageBox()
        self.info_done = QMessageBox()
        self.err_port_correct = QMessageBox()
        self.err_token_bot = QMessageBox()
        self.err_socket_snmp = QMessageBox()
        self.warn_dubl_name = QMessageBox()
        self.err_network_bot = QMessageBox()
        self.inf_exit_app = QMessageBox()
        self.info_stop_bot = QMessageBox()
        self.inf_close_page = QMessageBox()
        self.err_run_snmp = QMessageBox()
        self.warn_no_username_file = QMessageBox()
        self.warn_no_device_file = QMessageBox()
        self.inf_snmp_interval_time = QMessageBox()
        self.inf_interval_time = QMessageBox()
        self.inf_hight_temp = QMessageBox()
        self.inf_low_temp = QMessageBox()
        self.inf_low_volt = QMessageBox()
        self.inf_window_hight_volt = QMessageBox()
        self.inf_temp_hight_ddm = QMessageBox()
        self.inf_signal_low_ddm = QMessageBox()
        self.inf_temp_low_ddm = QMessageBox()
        self.err_value = QMessageBox()
        self.inf_not_select_radioButton = QMessageBox()

        # Вызываем у экземпляра класса QMessageBox() метод setWindowTitle, который задает заголовок диалоговому окну.
        self.inf_del.setWindowTitle('Уведомление')
        self.inf_no_user_del.setWindowTitle('Уведомление')
        self.inf_success.setWindowTitle('Уведомление')
        self.inf_dubl_ip_address.setWindowTitle('Уведомление')
        self.err_ip_correct.setWindowTitle('Ошибка')
        self.inf_del_device.setWindowTitle('Уведомление')
        self.inf_del_switch.setWindowTitle('Уведомление')
        self.inf_del_join_data.setWindowTitle('Уведомление')
        self.inf_del_port.setWindowTitle('Уведомление')
        self.inf_no_device_del.setWindowTitle('Уведомление')
        self.info_done.setWindowTitle('Уведомление')
        self.err_port_correct.setWindowTitle('Ошибка')
        self.err_token_bot.setWindowTitle('Ошибка')
        self.err_socket_snmp.setWindowTitle('Ошибка')
        self.warn_dubl_name.setWindowTitle('Предупреждение')
        self.err_network_bot.setWindowTitle('Ошибка')
        self.inf_exit_app.setWindowTitle('Уведомление')
        self.info_stop_bot.setWindowTitle('Уведомление')
        self.inf_close_page.setWindowTitle('Уведомление')
        self.err_run_snmp.setWindowTitle('Ошибка')
        self.warn_no_username_file.setWindowTitle('Предупреждение')
        self.warn_no_device_file.setWindowTitle('Предупреждение')
        self.err_request_db.setWindowTitle('Ошибка')
        self.inf_snmp_interval_time.setWindowTitle('Уведомление')
        self.inf_interval_time.setWindowTitle('Уведомление')
        self.inf_hight_temp.setWindowTitle('Уведомление')
        self.inf_low_temp.setWindowTitle('Уведомление')
        self.inf_low_volt.setWindowTitle('Уведомление')
        self.inf_window_hight_volt.setWindowTitle('Уведомление')
        self.inf_temp_hight_ddm.setWindowTitle('Уведомление')
        self.inf_signal_low_ddm.setWindowTitle('Уведомление')
        self.inf_temp_low_ddm.setWindowTitle('Уведомление')
        self.err_value.setWindowTitle('Ошибка')
        self.inf_not_select_radioButton.setWindowTitle('Уведомление')

        # Вызываем у экземпляра класса QMessageBox() метод setText, который будет выводить текст уведомления при появлении 
        # диалогового окна
        self.inf_success.setText('Успех!')
        self.err_request_db.setText('Ошибка запроса к БД')
        self.err_ip_correct.setText('ip адрес введен некорректно')
        self.info_done.setText('Выполнено!')
        self.err_port_correct.setText('Введенное значение неверно')
        self.err_token_bot.setText('Ошибка подключения')
        self.err_network_bot.setText('Ошибка сетевого подключения')
        self.err_socket_snmp.setText('Ошибка сетевого подключения')
        self.info_stop_bot.setText('Wait...')
        self.inf_exit_app.setText('Выйти из программы?')
        self.inf_close_page.setText('Закрыть страницу?')
        self.err_run_snmp.setText('SNMP-опрощик не запущен')
        self.warn_no_username_file.setText('В файле "Users" нет данных о именах пользователей.\nДобавьте имя пользователя в файл')
        self.warn_no_device_file.setText('В файле "DataBase" нет данных об устройствах.\nДобавьте устройство в файл')
        self.inf_snmp_interval_time.setText('Недопустимое значение')
        self.inf_interval_time.setText('Недопустимое значение')
        self.inf_hight_temp.setText('Недопустимое значение')
        self.inf_low_temp.setText('Недопустимое значение')
        self.inf_low_volt.setText('Недопустимое значение')
        self.inf_window_hight_volt.setText('Недопустимое значение')
        self.inf_temp_hight_ddm.setText('Недопустимое значение')
        self.inf_signal_low_ddm.setText('Недопустимое значение')
        self.inf_temp_low_ddm.setText('Недопустимое значение')
        self.err_value.setText('Ошибка значения')
        self.inf_not_select_radioButton.setText('Выберете номер окна')

        # Вызываем у экземпляра класса QMessageBox() метод setIcon, который задает иконку, которая будет полявляется вместе 
        # с диалоговым окном.
        self.inf_del.setIcon(QMessageBox.Question)
        self.inf_success.setIcon(QMessageBox.Information)
        self.inf_no_user_del.setIcon(QMessageBox.Information)
        self.inf_dubl_ip_address.setIcon(QMessageBox.Information)
        self.err_ip_correct.setIcon(QMessageBox.Critical)
        self.inf_del_device.setIcon(QMessageBox.Question)
        self.inf_del_switch.setIcon(QMessageBox.Question)
        self.inf_del_join_data.setIcon(QMessageBox.Question)
        self.inf_del_port.setIcon(QMessageBox.Question)
        self.inf_no_device_del.setIcon(QMessageBox.Information)
        self.info_done.setIcon(QMessageBox.Information)
        self.err_port_correct.setIcon(QMessageBox.Critical)
        self.err_token_bot.setIcon(QMessageBox.Critical)
        self.err_socket_snmp.setIcon(QMessageBox.Critical)
        self.warn_dubl_name.setIcon(QMessageBox.Warning)
        self.err_network_bot.setIcon(QMessageBox.Critical)
        self.inf_exit_app.setIcon(QMessageBox.Question)
        self.info_stop_bot.setIcon(QMessageBox.Information)
        self.err_run_snmp.setIcon(QMessageBox.Critical)
        self.warn_no_username_file.setIcon(QMessageBox.Warning)
        self.warn_no_device_file.setIcon(QMessageBox.Warning)
        self.err_request_db.setIcon(QMessageBox.Critical)
        self.inf_snmp_interval_time.setIcon(QMessageBox.Information)
        self.inf_interval_time.setIcon(QMessageBox.Information)
        self.inf_hight_temp.setIcon(QMessageBox.Information)
        self.inf_low_temp.setIcon(QMessageBox.Information)
        self.inf_low_volt.setIcon(QMessageBox.Information)
        self.inf_window_hight_volt.setIcon(QMessageBox.Information)
        self.inf_temp_hight_ddm.setIcon(QMessageBox.Information)
        self.inf_signal_low_ddm.setIcon(QMessageBox.Information)
        self.inf_temp_low_ddm.setIcon(QMessageBox.Information)
        self.err_value.setIcon(QMessageBox.Critical)
        self.inf_not_select_radioButton.setIcon(QMessageBox.Information)

        # Вызываем у экземпляра класса QMessageBox() метод setStandardButtons, который создает кнопки диалоговому окну
        self.inf_del.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_exit_app.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        self.inf_del_device.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_switch.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_join_data.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.inf_del_port.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        self.warn_dubl_name.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        self.inf_close_page.setStandardButtons(QMessageBox.Close|QMessageBox.Cancel)

        # Вызываем у экземпляра класса QMessageBox() метод setInformativeText, который задает дополнительный текст под основным текстом
        #self.inf_del.setInformativeText('Дополнительный текст')
        self.warn_dubl_name.setInformativeText('Добавить пользователя?')

        # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
        # указать дополнительную информацию об ошибке
        self.inf_hight_temp.setDetailedText('Значение порога высокой температуры не может быть меньше 25')
        self.inf_low_temp.setDetailedText('Значение порога низкой температуры не может быть больше 10')
        self.inf_low_volt.setDetailedText('Значение порога низкого напряжения не может быть больше 50В')
        self.inf_window_hight_volt.setDetailedText('Значение порога высокого напряжения не может быть меньше 230В')
        self.inf_temp_hight_ddm.setDetailedText('Значение порога высокой температуры DDM не может быть меньше 40')
        self.inf_temp_low_ddm.setDetailedText('Значение порога низкой температуры DDM не может быть больше 10')
        self.inf_signal_low_ddm.setDetailedText('Значение порога низкого уровня сигнала не может быть больше -20dBm')
        self.inf_interval_time.setDetailedText('Значение должно быть больше 0 и\nменьше или равно интервалу времени SNMP-опросчика')
        #self.inf_snmp_interval_time.setDetailedText('Значение должно быть больше 0')
        # Устанавливаем по умолчанию, что при всплывающем окне будет подсвечиваться кнопка Yes
        self.inf_close_page.setDefaultButton(QMessageBox.Close)


        #self.reply = QtWidgets.QMessageBox.information(self.inf_exit_app, 'Выход', 'Вы точно хотите выйти?',
                                                  #QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

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
        # У экземпляра класса inf_add, класс QMessageBox вызываем метод setWindowIcon, которому мы передаем экземпляр класса icon_inf в которм содержится изображение
        self.inf_success.setWindowIcon(self.icon_inf)
        self.inf_no_user_del.setWindowIcon(self.icon_inf)
        self.inf_del.setWindowIcon(self.icon_quest)
        self.inf_dubl_ip_address.setWindowIcon(self.icon_inf)
        self.err_ip_correct.setWindowIcon(self.icon_err)
        self.inf_del_device.setWindowIcon(self.icon_quest)
        self.inf_del_switch.setWindowIcon(self.icon_quest)
        self.inf_del_join_data.setWindowIcon(self.icon_quest)
        self.inf_del_port.setWindowIcon(self.icon_quest)
        self.inf_no_device_del.setWindowIcon(self.icon_inf)
        self.info_done.setWindowIcon(self.icon_inf)
        self.err_port_correct.setWindowIcon(self.icon_err)
        self.info_stop_bot.setWindowIcon(self.icon_inf)
        self.warn_dubl_name.setWindowIcon(self.icon_warn)
        self.inf_exit_app.setWindowIcon(self.icon_quest)
        self.err_token_bot.setWindowIcon(self.icon_err)
        self.err_socket_snmp.setWindowIcon(self.icon_err)
        self.err_network_bot.setWindowIcon(self.icon_err)
        self.err_run_snmp.setWindowIcon(self.icon_err)
        self.warn_no_username_file.setWindowIcon(self.icon_warn)
        self.warn_no_device_file.setWindowIcon(self.icon_warn)
        self.err_request_db.setWindowIcon(self.icon_err)
        self.inf_not_select_radioButton.setWindowIcon(self.icon_inf)

        # Диалоговые окна для установок значения параметров мониторинга
        self.inf_interval_time.setWindowIcon(self.icon_inf)
        self.inf_snmp_interval_time.setWindowIcon(self.icon_inf)
        self.inf_hight_temp.setWindowIcon(self.icon_inf)
        self.inf_low_temp.setWindowIcon(self.icon_inf)
        self.inf_low_volt.setWindowIcon(self.icon_inf)
        self.inf_window_hight_volt.setWindowIcon(self.icon_inf)
        self.inf_signal_low_ddm.setWindowIcon(self.icon_inf)
        self.inf_temp_hight_ddm.setWindowIcon(self.icon_inf)
        self.inf_temp_low_ddm.setWindowIcon(self.icon_inf)
        self.err_value.setWindowIcon(self.icon_err)

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

        

        