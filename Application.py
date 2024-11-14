#
from __future__ import annotations
from typing import Optional, Any
from telegram.utils import request
import sqlite3
import time
import sys
import ipaddress
import multiprocessing
from telegram import error
from class_ThreadSNMPAsc import ThreadSNMPAsk
from class_ThreadSNMPSwitch import ThreadSNMPSwitch
from PyQt5 import QtWidgets, QtCore
from PlaineAccessui import Ui_MainWindow
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox
from queue import Queue, Empty
from class_ThreadMonitorAlarmsQT_new import ThreadMonitorAlarms
#from class_ThreadTelegramBot import ThreadTelegramBot
from class_TelegramBot import TelegramBot
from class_ApplicationWidget import AplicationWidget
from class_SecondWindowBrowser import SecondWindowBrowser
from class_SqlLiteMain import ConnectSqlDB
from psutil import Process, NoSuchProcess
from class_ThreadCheckModelDevice import ThreadCheckModelDevice

class Application(Ui_MainWindow, QtWidgets.QMainWindow, AplicationWidget): # type: ignore[misc]

    def __init__(self) -> None:
        # Т.к. могут быть ситуации, когда у дочернего и родительского классов есть метод который называется также, для 
        # этого используется функция super, которая вызвает такой же метод __init__ но у родительского класса.
        super().__init__()
        # Вызываем метод setupUi, в котором настроены все наши виджеты (кнопки, поля и т.д.)
        self.setupUi(self)
        # Определяем номер запущенного процесса, вызвав метод current_process() 
        self.proc_pid = multiprocessing.current_process().pid
        
    # КЛАСС QTimer
        # Создаем экземпляр класса QTimer(), это updater, который многократно через указанный промежуток времени вызывает метод 
        # прикрепленный к нему 
        self.timer = QtCore.QTimer(self)
        # Задаем интервал запуска timer(обновления)
        self.timer.setInterval(1000)
        # Вызываем у экземпляра timer метод timeout(сигнал) и с помощью connect прикрепляем наш метод update_textEdit, который будет
        # вызываться при каждом срабатывании сигналя(timeout) через указанный промежуток времени
        self.timer.timeout.connect(self.update_textEdit)
        # Запускаем экземпляр класса timer, вызвав у него метод start
        self.timer.start()
        
    # СОЗДАЕМ ЭКЗЕМПЛЯРЫ КЛАССОВ 
        # Создаем экземпляр класса Queue(очередь)
        #self.line: Queue[Tuple[type, Union[Unauthorized, InvalidToken, NetworkError, TimedOut], Any]] = Queue()
        # Создаем экземпляр класса ThreadSNMPASwitch
        self.snmp_switch = ThreadSNMPSwitch()
        # Создаем экземпляр класса ThreadSNMPAsk
        self.snmp_ask = ThreadSNMPAsk()
        # Создаем экземпляр класса ThreadMonitorAlarms
        self.monitoring_alarms = ThreadMonitorAlarms()
        # Создаем экземпляр класса SecondWindowBrowser
        self.window_second = SecondWindowBrowser()
        #
        self.check_model = ThreadCheckModelDevice()

    # PyQt СИГНАЛЫ
        ''' В модуле telegram.utils.requests создали класс помошник QtSignalHelper для работы с сигналами PyQt.
        '''
        # Создаем экземпляр класса helper передаем ему наш экземпляр класса Application
        self.helper = request.QtSignalHelper(self)
        # Подключаем сигнал signal_conflict к Слоту(метод handler_signal_bot_conflict)
        self.helper.signal_conflict.connect(self.handler_signal_bot_conflict)
        # Подключаем сигнал signal_network_error к Слоту(метод show_dialog_box_network_err)
        self.helper.signal_network_error.connect(self.show_dialog_box_network_err)
        # Подключаем сигнал signal_network_connect к Слоту(метод handler_signal_bot_connect)
        self.helper.signal_network_connect.connect(self.close_dialog_box_network_err)
        
        ''' В модуле class_ClientModbus создали сигнал signa_network_error, который будет испускаться при отсутствии
        подключения к сети '''
        # У экземпляра класса snmp_ask вызываем сигнал к которому монтируем метод, который будет вызываться при испускании сигнала
        self.snmp_ask.signa_network_error.connect(self.show_dialog_box_network_err)

        '''
        В модуле class_CheckModelDevice создаем сигнал signal_snmp_request_done, который будет испускаться
        при завершении snmp запроса и будет передавать результат запроса
        '''
        # Вызываем сигнал к которому монтируем метод, который будет вызываться при испускании сигнала и выводить результат
        self.check_model.signal_snmp_request_done.connect(self.outpu_result)

    # ПЕРЕМЕННАЯ КООРДИНАТА
        # Создаем переменные координаты X, Y, значение которых будет задавть сдвиг диалогового окна относительно основного окна приложения
        self.X = 100
        self.Y = 150

    # ПЕРЕМЕННАЯ ФЛАГ СТИЛЬ SecondWindow
        # Флаги определяют какой из стилей выбран
        self.isStyle_default = True
        self.isStyle_1 = False
        self.isStyle_2 = False
        self.isStyle_3 = False
        # Стиль №1:цвет фона - "Светло-желтый", тип шрифта "Arial"
        self.style_1 = "background-color:  rgb(255, 255, 221);\n" "font: 75 {}pt 'Arial';"
        # Стиль №2:цвет фона - "Светло-желтый", тип шрифта "Times New Roman"
        self.style_2 = "background-color:  rgb(255, 255, 221);\n" "font: 75 {}pt 'Times New Roman';"
        # Стиль №3:цвет фона - "Светло-желтый", тип шрифта "Book Antiqua"
        self.style_3 = "background-color:  rgb(255, 255, 221);\n" "font: 75 {}pt 'Book Antiqua';"
        # Стиль по умолчанию :цвет фона - "Белый", тип шрифта "Arial"
        self.style_default = "background-color:  rgb(255, 255, 255);\n" "font: 75 {}pt 'Arial';"

    # СТАТУС БАР
        # Создаем экземпляр класса  QLable Выводим сообщение в статус бар со статусом загрузки
        #self.lbl = QLabel()
        # Добавляем стиль к экземпляру класса
        #self.lbl.setStyleSheet("border-left: 3px solid;")
        #
        #self.lbl.setAlignment(QtCore.Qt.AlignLeft)
        # Добавляем в статус бар наш экземпляр класса lbl
        #self.lbl.setText("<img src={}>  Готово".format(self.path_icon_done))
        # Выводим Надпись с изображением в статус Бар
        #self.statusbar.addWidget(self.lbl)

        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, получить ip-адрес где модель устройства cisco из таблицы Devices
            data = sql.get_values_list_db('ip', model='cisco', table='Devices')
        if data:
            # Перебираем список одновременно распаковав кортеж на ip адрес и все остальное
            for ip, in data:
                # Получаем количество значений в селекторе 
                index = self.comboBox_4.count()
                # Добавляем ip адрес в селектор 
                self.comboBox_4.addItem("")
                if isinstance(ip, str): 
                    # Поскольку нумерация в селекторе начинается с 0 то подставляя значение index это будет следующим значеием в списке
                    self.comboBox_4.setItemText(index, ip)
        
        # Метод добавляет имена голосов в выпадающий список
        self._add_name_voice_comboBox()
        
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            speech_speed = sql.get_db('value', description='speed_speech', table='Styles')
        if speech_speed and isinstance(speech_speed[0], int):
            # Устанавливаем значение скорости воспроизведения речи
            self.window_second.speech_text.speed_speech = speech_speed[0]
        # Выводим значение 
        self.textBrowser_29.append(str(self.window_second.speech_text.speed_speech))

    # ОБРАБОТКА НАЖАТИЕ КНОПКИ
        # Вызываем у нашей кнопки метод pressed(сигнал) и прикрепляем к нему с помощью connect нашу функцию как атрибут,
        # т.е. без скобок, поскольку мы ее не вызываем. При срабатывании сигнала pressed будет вызываться тот метод, который прикреплен к кнопке.
        self.Add_User_btn.pressed.connect(self.button_pressed_add)
        self.Delet_User_btn.pressed.connect(self.button_pressed_del)
        self.Show_Users_btn.pressed.connect(self.button_pressed_show_users)
        self.Clear_btn.pressed.connect(self.button_pressed_clear_show_users)
        self.Add_device_btn.pressed.connect(self.button_pressed_add_device)
        self.Add_switch_port_btn.pressed.connect(self.button_pressed_add_port)
        self.Delete_switch_port_btn.pressed.connect(self.button_pressed_del_port)
        self.Check_device_btn.pressed.connect(self.button_pressed_check_device)
        self.Clear_btn_2.pressed.connect(self.button_pressed_clear_check_device)
        self.Show_Devices_btn.pressed.connect(self.button_pressed_show_device)
        self.Show_ports_btn.pressed.connect(self.button_pressed_show_ports)
        self.Find_Device_btn.pressed.connect(self.button_pressed_find_device)
        self.Clear_btn_3.pressed.connect(self.button_pressed_clear_show_devices)
        self.Clear_btn_4.pressed.connect(self.button_pressed_clear_show_ports)
        self.Run_btn.clicked.connect(self.button_pressed_run_monitor)
        self.Stop_btn.pressed.connect(self.button_pressed_stop_monitor)
        self.Run_snmp_btn.pressed.connect(self.button_pressed_run_snmp)
        self.Stop_snmp_btn.pressed.connect(self.button_pressed_stop_snmp)
        self.Start_bot_btn.pressed.connect(self.button_pressed_run_bot)
        self.Stop_bot_btn.pressed.connect(self.button_pressed_stop_bot)
        self.Delete_device_btn.pressed.connect(self.button_pressed_del_device)
        self.Set_btn.pressed.connect(self.set_interval_snmp_btn)
        self.Set_snmp_interval_btn.pressed.connect(self.set_interval_snmp_switch_btn)
        self.Set_monitor_btn.pressed.connect(self.set_interval_monitor_btn)
        self.Set_temp_hight_btn.pressed.connect(self.set_temp_hight_monitor_btn)
        self.Open_window_button.pressed.connect(self.show_second_window)
        self.Set_window_interval_time_btn.pressed.connect(self.set_interval_window_btn)
        self.Set_temp_low_btn.pressed.connect(self.set_temp_low_monitor_btn)
        self.Set_volt_low_btn.pressed.connect(self.set_volt_low_monitor_btn)
        self.Set_oil_low_btn.pressed.connect(self.set_oil_low_monitor_btn)
        self.Set_window_temp_hight_btn.pressed.connect(self.set_temp_hight_window_btn)
        self.Set_window_temp_low_btn.pressed.connect(self.set_temp_low_window_btn)
        self.Set_window_oil_low_btn.pressed.connect(self.set_oil_low_window_btn)
        self.Set_window_font_size_btn.pressed.connect(self.set_font_size_text)
        self.Set_window_font_size_channel_btn.pressed.connect(self.set_font_size_channel_window)
        self.Set_window_style_sheet_btn.pressed.connect(self.set_style_window)
        self.Set_window_low_volt_btn.pressed.connect(self.set_volt_low_window_btn)
        self.Set_window_hight_volt_btn.pressed.connect(self.set_volt_hight_window_btn)
        self.Set_window_font_size_alarm_btn.pressed.connect(self.set_font_size_curent_alarm_window)
        self.Set_window_power_sign_btn.pressed.connect(self.set_signal_low_ddm_window_btn)
        self.Set_window_low_temp_ddm_btn.pressed.connect(self.set_temp_low_ddm_window_btn)
        self.Set_window_high_temp_ddm_btn.pressed.connect(self.set_temp_hight_ddm_window_btn)
        self.Set_monitor_low_temp_ddm_btn.pressed.connect(self.set_temp_low_ddm_monitor_btn)
        self.Set_monitor_high_temp_ddm_btn.pressed.connect(self.set_temp_hight_ddm_monitor_btn)
        self.Set_monitor_power_sign_btn.pressed.connect(self.set_signal_low_ddm_monitor_btn)
        self.Set_monitor_count_btn.pressed.connect(self.set_count_check_monitor_btn)
        self.Set_font_size_btn.pressed.connect(self.set_font_size_message_box)
        self.View_message_box_btn.pressed.connect(self.button_press_view_message_box)
        self.Set_voice_speech_btn.pressed.connect(self._button_press_voice_speech)
        self.Set_speed_speech_btn.pressed.connect(self._button_press_speed_speech)
        self.Check_speed_speech_btn.pressed.connect(self._button_press_leasen_to_speech)

    # ДОБАВЛЕНИЕ ИКОНКИ С ИЗОБРАЖЕНИЕМ ДЛЯ КНОПКИ
        # Вызываем у кнопки Add_User_btn метод setIcon, передаем в качестве аргумента экземпляр класса icon_btn_add унаследованный от класса 
        # AplicationWidget, метод добавляет иконку с изображением.
        self.Add_User_btn.setIcon(self.icon_btn_add)
        self.Delete_device_btn.setIcon(self.icon_btn_del)
        self.Delet_User_btn.setIcon(self.icon_btn_del)
        self.Show_Users_btn.setIcon(self.icon_btn_show)
        self.Clear_btn.setIcon(self.icon_btn_clear)
        self.Add_device_btn.setIcon(self.icon_btn_add)
        self.Add_switch_port_btn.setIcon(self.icon_btn_add)
        self.Delete_switch_port_btn.setIcon(self.icon_btn_del)
        self.Check_device_btn.setIcon(self.icon_btn_run)
        self.Clear_btn_2.setIcon(self.icon_btn_clear)
        self.Show_Devices_btn.setIcon(self.icon_btn_show)
        self.Find_Device_btn.setIcon(self.icon_btn_find)
        self.Clear_btn_3.setIcon(self.icon_btn_clear)
        self.Run_btn.setIcon(self.icon_btn_run)
        self.Stop_btn.setIcon(self.icon_btn_stop)
        self.Run_snmp_btn.setIcon(self.icon_btn_run)
        self.Stop_snmp_btn.setIcon(self.icon_btn_stop)
        self.Start_bot_btn.setIcon(self.icon_btn_run)
        self.Stop_bot_btn.setIcon(self.icon_btn_stop)
        self.Set_btn.setIcon(self.icon_btn_set)
        self.Set_snmp_interval_btn.setIcon(self.icon_btn_set)
        self.Set_monitor_btn.setIcon(self.icon_btn_set)
        self.Open_window_button.setIcon(self.icon_btn_run)
        self.Set_window_interval_time_btn.setIcon(self.icon_btn_set)
        self.Set_oil_low_btn.setIcon(self.icon_btn_set)
        self.Set_volt_low_btn.setIcon(self.icon_btn_set)
        self.Set_temp_low_btn.setIcon(self.icon_btn_set)
        self.Set_temp_hight_btn.setIcon(self.icon_btn_set)
        self.Set_window_temp_hight_btn.setIcon(self.icon_btn_set)
        self.Set_window_temp_low_btn.setIcon(self.icon_btn_set)
        self.Set_window_oil_low_btn.setIcon(self.icon_btn_set)
        self.Set_window_font_size_btn.setIcon(self.icon_btn_set)
        self.Set_window_hight_volt_btn.setIcon(self.icon_btn_set)
        self.Set_window_low_volt_btn.setIcon(self.icon_btn_set)
        self.Set_window_power_sign_btn.setIcon(self.icon_btn_set)
        self.Set_window_low_temp_ddm_btn.setIcon(self.icon_btn_set)
        self.Set_window_high_temp_ddm_btn.setIcon(self.icon_btn_set)
        self.Set_monitor_low_temp_ddm_btn.setIcon(self.icon_btn_set)
        self.Set_monitor_high_temp_ddm_btn.setIcon(self.icon_btn_set)
        self.Set_monitor_power_sign_btn.setIcon(self.icon_btn_set)
        self.Set_monitor_count_btn.setIcon(self.icon_btn_set)
        self.Set_window_font_size_alarm_btn.setIcon(self.icon_btn_set)
        self.Set_window_font_size_channel_btn.setIcon(self.icon_btn_set)
        self.Set_window_style_sheet_btn.setIcon(self.icon_btn_set)
        self.Show_ports_btn.setIcon(self.icon_btn_show)
        self.Set_font_size_btn.setIcon(self.icon_btn_set)
        self.Set_voice_speech_btn.setIcon(self.icon_btn_set)
        self.Set_speed_speech_btn.setIcon(self.icon_btn_set)
        self.View_message_box_btn.setIcon(self.icon_btn_show)
        self.Check_speed_speech_btn.setIcon(self.icon_btn_play_sound)

        # Вызываем метод который получает значение и настривает стиль Главной страницы приложения
        self._get_style_values()
        # Вызывем метод который получает значение параметров и выводит их на Главную страницу приложения
        self._get_setting_values()
     
    # СОЗДАНИЕ ВКЛАДОК ДЛЯ МЕНЮ 
        # Для Меню добавляем действия(вкладки) при нажатии на которые будет вызываться метод action_clicked который, будет выполнять
        # действия в зависимости от названия вкладки, так же первым аргументом передаем экземпляр класс icon_menu_open унаследованный
        # у класса AplicationWidget, который содержит изображение
        self.menu.addAction(self.icon_menu_open, 'Open', self.action_clicked)
        self.actionSave = self.menu.addAction(self.icon_menu_save, 'Save', self.action_clicked)
        # Деактивируем вкладку Save
        self.actionSave.setEnabled(False)
        #if isinstance(self.inf_close_page.exec_, Callable):
        # Создаем вкладку Close, добавляем иконку с изображением, название вкладки и метод который будет выполняться при нажатии на вкладку
        self.actionClosePage = self.menu.addAction(self.icon_close_page, 'Close Page', self.inf_close_page.exec_) # type: ignore[arg-type] 
        # Деактивируем вкладку Close Page
        self.actionClosePage.setEnabled(False)

        # Создаем экземпляр классса, которому передаем параметры иконку с изображением, название вкладки и экземпляр класса (self) нашего приложения, которое будет закрываться при нажати на вкладку 
        self.exit_app = QAction(self.icon_menu_exit, 'Exit', self)
        # Вызываем у экземпляра класса exit_app меттод trigger, который будет реагировать при каждом нажатие на вкладку Exit к которому 
        # прикрепляем экземпляр класса нашего приложения у которого вызываем метод close
        self.exit_app.triggered.connect(self.close)
        # Добавляем в наше созданное меню вкладку Exit
        self.menu.addAction(self.exit_app)       
        
    # ОБРАБОТКА НАЖАТИЕ КНОПКИ ДИАЛОГОВОГО ОКНА
        # Вызываем у экземпляра класса QMessageBox() метод buttonClicked(сигнал) и спомощью connect прикрепляем к нему 
        # метод click_btn, котрый будет срабатывать при каждом вызове(нажатии) сигнала buttonClicked, т.е. нажатие на кнопки.
        self.inf_del.buttonClicked.connect(self.click_btn)
        self.inf_del_device.buttonClicked.connect(self.click_btn_del_device)
        self.inf_del_switch.buttonClicked.connect(self.click_btn_del_switch)
        self.inf_del_join_data.buttonClicked.connect(self.click_btn_del_join_data)
        self.inf_del_port.buttonClicked.connect(self.click_btn_del_port)
        self.inf_del_sla.buttonClicked.connect(self.click_btn_del_sla)
        self.inf_close_page.buttonClicked.connect(self.click_btn_close_page)
        self.req_stop_bot.buttonClicked.connect(self.click_btn_stop_bot)
        
    # СТАТУС БАР
        # Выводим Надпись Готово с изображением в статус Бар
        self.statusbar.addWidget(self.lbl)
        # Выводим Надпись SNMP с изображением в статус Бар
        self.statusbar.addWidget(self.snmp_lbl, 4)
        # Выводим Надпись TelegramBot с изображением в статус Бар
        self.statusbar.addWidget(self.bot_lbl, 2)
        # Выводим Надпись AlarmMonitoring с изображением в статус Бар
        self.statusbar.addWidget(self.alarm_lbl, 1)
    
    # Метод закрывает диалоговое окно, когда установленно сетевое подключение(Чат Бот)
    def close_dialog_box_network_err(self):
        # Если диалоговое окно открыто (Информирует, что есть проблемы с доступом к сети Интернет)
        if self.runtime_error.isVisible():
            self.runtime_error.close()
        # Если диалоговое окно открыто (Информирует, что запущенно два экземпляра Telegram Bot)
        elif self.req_stop_bot.isVisible():
            self.req_stop_bot.close()
    
    # Метод обрабатывает Qt сигнал, когда возникла ошибка сетевого подключения
    def handler_signal_bot_network_err(self):
        # Если диалоговое окно не выведено
        if not self.runtime_error.isVisible():
            self.runtime_error.setText('Ошибка сетевого подключения')
            # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
            # указать дополнительную информацию об ошибке
            self.runtime_error.setDetailedText(f"Проверьте доступ к интернету")
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
            self.runtime_error.exec_()

    # Метод обрабатывает Qt сигнал, когда возникла ошибка сетевого подключения
    def show_dialog_box_network_err(self):
        # Если диалоговое окно не выведено
        if not self.runtime_error.isVisible():
            self.runtime_error.setText('Ошибка сетевого подключения')
            # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
            # указать дополнительную информацию об ошибке
            self.runtime_error.setDetailedText(f"Проверьте доступ к интернету")
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
            self.runtime_error.exec_()

    # Метод вызывается когда испускается сигнал Qt обрабатывает исключение при запуске Telegram Bot
    def handler_signal_bot_conflict(self, error):
        # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором 
        # указываем дополнительную информацию об ошибке
        self.req_stop_bot.setDetailedText(f"Убедитесь, что запущен только один экземпляр Telegram Бота с введенным токен ключом\n{error}")
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.req_stop_bot.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
        self.req_stop_bot.exec_()
    
    # Метод обрабатывает исключения при возникновении ошибок при запуске Чат Бота
    def handler_signal_bot_error(self, err):
        #
        if not self.runtime_error.isVisible():
            # Если тип ошибки совпадает
            if type(err) is error.Unauthorized or type(err) is error.InvalidToken:
                eror = err.message
                self.runtime_error.setText('Ошибка подключения')
                # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
                # указать дополнительную информацию об ошибке
                self.runtime_error.setDetailedText(f"Проверьте введенный токен ключ {eror}")
            elif type(err) is error.TimedOut or type(err) is error.NetworkError:
                eror = err.message
                self.runtime_error.setText('Ошибка сетевого подключения')
                # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
                # указать дополнительную информацию об ошибке
                self.runtime_error.setDetailedText(f"Проверьте доступ к интернету\n{eror}")
            # Деактивируем кнопку Stop
            self.Stop_bot_btn.setEnabled(False)
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
            self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
            self.runtime_error.exec_()

    # Метод получает значения стилей и выводит их на страницу приложения при запуске программы
    def _get_style_values(self) -> None:
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение значения размера текста аварийных сообщений Диалогового окна
            font_size_dialog_box = sql.get_db('value', description='font_size_dialog_box', table='Styles')[0]
            # Если тип переменной число
            if isinstance(font_size_dialog_box, int): 
                # Присваиваем переменной font_size_text_dialog_box полученное значение
                self.window_second.font_size_dialog_box = font_size_dialog_box
            # Выводим значение размера текста аварийных сообщений Диалогового окна при запуске программы
            self.textBrowser_27.append(str(self.window_second.font_size_dialog_box))
            # Делаем запрос к БД, на получение размера текста сообщений в каждом фрейме окна 
            font_size_frame1 = sql.get_db('value', description='font_size_frame1', table='Styles')[0]
            font_size_frame2 = sql.get_db('value', description='font_size_frame2', table='Styles')[0]
            font_size_frame3 = sql.get_db('value', description='font_size_frame3', table='Styles')[0]
            font_size_frame4 = sql.get_db('value', description='font_size_frame4', table='Styles')[0]
            # Если тип переменной число
            if isinstance(font_size_frame1, int):
                # Присваиваем значение переменной font_size_frame
                self.window_second.font_size_frame1 = font_size_frame1
            if isinstance(font_size_frame2, int):
                self.window_second.font_size_frame2 = font_size_frame2 
            if isinstance(font_size_frame3, int): 
                self.window_second.font_size_frame3 = font_size_frame3
            if isinstance(font_size_frame4, int): 
                self.window_secondfont_size_frame4 = font_size_frame4
            # Выводим значения Размера ширифта
            self.textBrowser_14.append(f"{self.window_second.font_size_frame1}/{self.window_second.font_size_frame2}/{self.window_second.font_size_frame3}/{self.window_second.font_size_frame4}")
            # Делаем запрос к БД, на получение значения размера шрифта текста в окне Текущие аварии
            font_size_current_alarm = sql.get_db('value', description='font_size_current_alarm', table='Styles')[0]
            # Если тип переменной число 
            if isinstance(font_size_current_alarm, int): 
                self.window_second.font_size_current_alarm = font_size_current_alarm
            # Выводим значение Размера ширифта SecondWindow вкладка Current Alarms
            self.textBrowser_18.append(str(self.window_second.font_size_current_alarm))
            # Делаем запрос к БД, на получение значения размера шрифта текста в окне Каналы
            font_size_channel = sql.get_db('value', description='font_size_channel', table='Styles')[0]
            # Если тип переменной число 
            if isinstance(font_size_channel, int): 
                # Присваиваем переменной font_size_channel значение
                self.window_second.font_size_channel_frame = font_size_channel
            # Выводим значение Размера ширифта SecondWindow вкладка Каналы
            self.textBrowser_28.append(str(self.window_second.font_size_channel_frame))
            # Делаем запрос к БД, на получение установленного Стиля Окна вывода аврий
            style_type = sql.get_db('value', description='style_sheet', table='Styles')[0]
            # Если тип переменной строка 
            if isinstance(style_type, str):
                # Вызываем метод передаем строку и установливаем Стиль страницы приложения 
                self.set_style_window(style_type)
    
    # Метод получает значения порога сработки аврий и выводит их на страницу приложения при запуске программы
    def _get_setting_values(self) -> None:
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение порога значения сработки аварий
            snmp_interval_time = sql.get_db('num', alarms='snmp_interval_time', table='Settings')[0]
            # Если тип переменной число 
            if isinstance(snmp_interval_time, int): 
                # Присваиваем переменной interval_time полученное значение
                self.snmp_ask.interval_time = snmp_interval_time
            # Вывводим значение интервала между опросами SNMPAsk
            self.textBrowser_4.append(str(self.snmp_ask.interval_time))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            snmp_switch_interval_time = sql.get_db('num', alarms='snmp_switch_interval_time', table='Settings')[0]
            # Если тип переменной число 
            if isinstance(snmp_switch_interval_time, int):
                # присваиваем переменной interval_time полученное значение 
                self.snmp_switch.interval_time = snmp_switch_interval_time
            # Вывводим значение интервала между опросами SNMPSwitch
            self.textBrowser_26.append(str(self.snmp_switch.interval_time))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_interval_time = sql.get_db('num', alarms='monitor_interval_time', table='Settings')[0]
            # Если тип переменной число 
            if isinstance(monitor_interval_time, int): 
                # присваиваем переменной interval_time полученное значение
                self.monitoring_alarms.interval_time = monitor_interval_time
            # Вывводим значение интервала времени между опросами Alarm Monitoring
            self.textBrowser_5.append(str(self.monitoring_alarms.interval_time))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_interval_time = sql.get_db('num', alarms='window_interval_time', table='Settings')[0]
            # Если тип переменной число 
            if isinstance(window_interval_time, int): 
                # присваиваем переменной interval_time полученное значение
                self.window_second.interval_time = window_interval_time
            # Вывводим значение интервала времени между опросами SecondWindowBrowser
            self.textBrowser_6.append(str(self.window_second.interval_time))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_hight_temp = sql.get_db('num', alarms='monitor_hight_temp', table='Settings')[0]
            # Вывводим значение Порога высокой температуры Alarm Monitoring
            self.textBrowser_7.append(str(monitor_hight_temp))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_hight_temp = sql.get_db('num', alarms='window_hight_temp', table='Settings')[0]
            # Вывводим значение Порога высокой температуры SecondWindow, переобразовываем число в строку
            self.textBrowser_8.append(str(window_hight_temp))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_low_temp = sql.get_db('num', alarms='monitor_low_temp', table='Settings')[0]
            # Вывводим значение Порога низкой температуры Alarm Monitoring
            self.textBrowser_10.append(str(monitor_low_temp))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_low_temp = sql.get_db('num', alarms='window_low_temp', table='Settings')[0]
            # Вывводим первоначальное значение Порога низкой температуры SecondWindow
            self.textBrowser_13.append(str(window_low_temp))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_low_volt = sql.get_db('num', alarms='monitor_low_volt', table='Settings')[0]
            # Вывводим первоначальное значение Порога низкого напряжения Alarm Monitoring, переобразовываем число в строку
            self.textBrowser_11.append(str(monitor_low_volt))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_low_volt = sql.get_db('num', alarms='window_low_volt', table='Settings')[0]
            # Вывводим первоначальное значение Порога Низкого напряжения SecondWindow, переобразовываем число в строку
            self.textBrowser_17.append(str(window_low_volt))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_low_oil = sql.get_db('num', alarms='monitor_low_oil', table='Settings')[0]
            # Вывводим первоначальное значение Порога низкого количества топлива Alarm Monitoring, переобразовываем число в строку
            self.textBrowser_12.append(str(monitor_low_oil))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_low_oil = sql.get_db('num', alarms='window_low_oil', table='Settings')[0]
            # Вывводим первоначальное значение Порога низкого количества топлива SecondWindow, переобразовываем число в строку
            self.textBrowser_16.append(str(window_low_oil))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_hight_voltage = sql.get_db('num', alarms='window_hight_voltage', table='Settings')[0]
            # Вывводим первоначальное значение Порога Высокого напряжения SecondWindow, переобразовываем число в строку
            self.textBrowser_15.append(str(window_hight_voltage))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_signal_level = sql.get_db('num', alarms='monitor_signal_level', table='Settings')[0]
            # Выводим первоначальное значение Порог уровня сигнала DDM(dBm) Monitor Alarm
            self.textBrowser_9.append(str(monitor_signal_level))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_low_temp_fiber = sql.get_db('num', alarms='monitor_low_temp_fiber', table='Settings')[0]
            # Выводим первоначальное значение Порог низкой температуры DDM Monitor Alarm
            self.textBrowser_19.append(str(monitor_low_temp_fiber))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_hight_temp_fiber = sql.get_db('num', alarms='monitor_hight_temp_fiber', table='Settings')[0]
            # Выводим первоначальное значение Порог высокой температуры DDM Monitor Alarm
            self.textBrowser_20.append(str(monitor_hight_temp_fiber))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_signal_level = sql.get_db('num', alarms='window_signal_level', table='Settings')[0]
            # Выводим первоначальное значение Порог уровня сигнала DDM(dBm) SecondWindow
            self.textBrowser_21.append(str(window_signal_level))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_low_temp_fiber = sql.get_db('num', alarms='window_low_temp_fiber', table='Settings')[0]
            # Выводим первоначальное значение Порог низкой температуры DDM SecondWindow
            self.textBrowser_22.append(str(window_low_temp_fiber))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            window_hight_temp_fiber = sql.get_db('num', alarms='window_hight_temp_fiber', table='Settings')[0]
            # Выводим первоначальное значение Порог высокой температуры DDM SecondWindow
            self.textBrowser_23.append(str(window_hight_temp_fiber))
            # Делаем запрос к БД, на получение порога значения сработки аварий
            monitor_count = sql.get_db('num', alarms='monitor_count', table='Settings')[0]
            # Выводим первоначальное значение Число проверок перед отправкой сообщения Monitor Alarm
            self.textBrowser_25.append(str(monitor_count))

    # Метод закрывает приложение
    def closeEvent(self, event: Any) -> None:
        # Устанавливаем по умолчанию, что при всплывающем окне будет подсвечиваться кнопка Yes
        self.inf_exit_app.setDefaultButton(QMessageBox.Yes)
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.inf_exit_app.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Вызываем диалоговое окно
        reply = self.inf_exit_app.exec_()
        if reply == QMessageBox.Yes:
            # Проверяем если кнопка Stop у SNMP опрощика активирована, значит он запущен, то останавливаем его работу и выходим из приложения
            if self.Stop_snmp_btn.isEnabled():
                try:
                    # Останавливаем поток метод run экземпляра класса snmp_ask
                    self.snmp_ask.terminate()
                    # Останавливаем поток метод run экземпляра класса snmp_switch
                    self.snmp_switch.terminate()
                    # После этого закрываем SNMPAsk и SNMPSwitch
                    self.snmp_ask.snmp_stop()
                    self.snmp_switch.snmp_stop()
                except:
                    pass
            # Проверяем если кнопка Stop активна, значит Monitoring Alarm запущен, тогда останавливаем работу перед выходом из программы
            if self.Stop_btn.isEnabled():
                try:
                    self.monitoring_alarms.terminate()
                except:
                    pass
            # Проверяем если кнопка Stop активна И бот запущен, останавливаем работу Бота перед выходом из программы 
            if self.Stop_bot_btn.isEnabled() and self.bot.is_running():
                try:
                    # Останавливаем работу чат Бота
                    self.bot.disconnect()
                    # Останавливаем работу потока класса ThreadTelegramBot
                    self.bot.terminate()
                except:
                    pass
            # Проверяем если кнопка Open не активна, то значит открыто второе окно, тогда мы его закрываем
            if not self.Open_window_button.isEnabled():
                self.window_second.close()
            event.accept()
            # Вызываем метод _stop_process, который останавливает запущенный процесс exe, передаем номер процесса 
            self._stop_process(self.proc_pid)
        else:
            event.ignore()
        return None
        
    # Декоратор
    @QtCore.pyqtSlot()
    # Метод обрабатывает нажатие на вкладки в меню
    def action_clicked(self) -> None:
        # Метод позволяет получить все сигналы из menu Bar
        signal = self.sender()
        if signal.text() == 'Open': # type: ignore[attr-defined] 
            try:
                # Вызываем метод котрый окрывает диалоговое окно из которого выбираем файл, а в переменную path_file записываем путь
                path_file = QFileDialog.getOpenFileName(self)[0]
                # Открываем выбранный файл
                with open(f"{path_file}") as f:
                    data = f.read()
                # Делаем проверку если количество вкладок(TabWidget) равно 7, то  очищаем поле(textEdit_10) для ввода текста
                if self.tabWidget.count() == 7:
                    self.textEdit_10.clear()
                else:
                    # Создаем TabWidget с именем "Page" и поле для ввода(textEdit_10) на которое будем выводить содержимое файла, 
                    # который мы открываем
                    self.tab_7 = QtWidgets.QWidget()
                    self.tab_7.setObjectName("tab_7")
                    self.textEdit_10 = QtWidgets.QTextEdit(self.tab_7)
                    self.textEdit_10.setGeometry(QtCore.QRect(0, 0, 400, 391))
                    self.textEdit_10.setObjectName("textEdit_10")
                    self.tabWidget.addTab(self.tab_7, "Page")
                # Переключаемся на созданный нами TabWidget, т.е. на вкладку Page
                self.tabWidget.setCurrentIndex(6)
                # Выводим содержимое файла
                self.textEdit_10.setText(data)
                # Активируем вкладку "Save"
                self.actionSave.setEnabled(True)
                # Активируем вкладку "Close page"
                self.actionClosePage.setEnabled(True)
            except FileNotFoundError:
                pass
        elif signal.text() == 'Save': # type: ignore[attr-defined]
            try:
                # Вызываем метод котрый окрывает диалоговое окно из которого выбираем место, куда мы сохраним файл.
                path_file = QFileDialog.getSaveFileName(self)[0]
                # Получаем содержимое поля textEdit_10
                data = self.textEdit_10.toPlainText()
                # Открываем файл для записи
                with open(f"{path_file}", 'w') as f:
                    f.write(data)
                # Деактивируем вкладку "Сохранить"
                self.actionSave.setEnabled(False)
                # Деактивируем вкладку "Close page"
                self.actionClosePage.setEnabled(False)
                # Переключаем TabWidget на вкладку Runner
                self.tabWidget.setCurrentIndex(0)
                # Удаляем tabWidget
                self.tab_7.deleteLater()
            except FileNotFoundError:
                pass
        return None
    
    # Метод обрабатывает нажатие кнопки в диалоговом окне, останавливает работу Telegram Bot       
    def click_btn_stop_bot(self, btn: Any) -> None:
        if btn.text() == 'OK': 
            # Закрываем диалоговое окно
            self.req_stop_bot.close() 
            # Вызываем метод который останавливает работу Telegram Bot
            self.button_pressed_stop_bot()
        elif btn.text() == 'Cancel':
            return None
    
    # Метод обрабатывает нажатие кнопок в диалоговом окне, удаляет данные из таблицы Users БД
    def click_btn(self, btn: Any) -> None:
        # Удаление пользователя
        if btn.text() == 'OK':
            # Закрываем диалоговое окно с вопросом удалить пользователя или нет
            self.inf_del.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление данных из таблицы Users
                    sql.del_db(user_name=self.first_name, description=self.surname, table='Users')
                # Очищаем поля для ввода Имени и ФИО 
                self.textEdit_2.clear()
                self.textEdit_12.clear()
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox метод exec_(), который вызывает диалоговое окно
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.runtime_error.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit_2.clear()
            self.textEdit_12.clear()
        return None

    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет данные из таблицы Devices БД       
    def click_btn_del_device(self, btn: Any) -> None:
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_device.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление ip адреса из таблицы Devices 
                    sql.del_db(ip=self.ip_addr, table='Devices')
                if self.window_second.dict_set.get(self.ip_addr):
                    # Очищаем список сообщений класса ThreadSNMPAsck
                    self.snmp_ask.snmp_trap = []
                    # Очищаем список сообщений класса SecondWindow
                    self.window_second.snmp_traps = []
                    # Удаляем ip адрес из словаря dict_set класса Secondwindow
                    del self.window_second.dict_set[self.ip_addr] 
                # Очищаем поля ввода текста
                self.textEdit.clear()
                self.textEdit_4.clear()
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox метод exec_(), который вызывает диалоговое окно
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.runtime_error.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit.clear()
            self.textEdit_4.clear()
        return None

    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет коммутатор из таблицы Devices БД       
    def click_btn_del_switch(self, btn: Any) -> None:
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_switch.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление ip адреса из таблицы Devices 
                    sql.del_db(ip = self.ip_addr, table='Devices')
                # Очищаем поля ввода текста
                self.textEdit.clear()
                self.textEdit_4.clear()
                # Определяем индекс ip_addr в селекторе comboBox   
                index = self.comboBox_4.findText(self.ip_addr)
                # Удаляем значение ip_addr из селектора comboBox
                self.comboBox_4.removeItem(index)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox метод exec_(), который вызывает диалоговое окно
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.runtime_error.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit.clear()
            self.textEdit_4.clear()
        return None
    
    # Метод обрабатывает нажатие кнопки в диалоговом окне, удалить устройство и связанные с ним данные
    def click_btn_del_join_data(self, btn:Any) -> None:
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_join_data.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление ip адреса из таблицы Ports 
                    sql.del_db(ip_addr=self.ip_addr, table='Ports')
                    # Делаем запрос к БД на удаление ip адреса из таблицы Devices
                    sql.del_db(ip = self.ip_addr, table='Devices')
                # Перебираем полученные данные
                for parametrs in self.join_data:
                    # Распаковываем кортеж с параметрами
                    ip_addr, port, sla = parametrs
                    if port:
                        if self.window_second.dict_set.get(f'{ip_addr}/{port}'):
                            # Удаляем из словаря DICT_SET класса SecondWindow
                            del self.window_second.dict_set[f'{ip_addr}/{port}']
                    elif sla:
                        if self.window_second.dict_set.get(f'{ip_addr}/{sla}'):
                            # Удаляем из словаря DICT_SET класса SecondWindow
                            del self.window_second.dict_set[f'{ip_addr}/{sla}']
                    # Очищаем список сообщений класса ThreadSwitch
                    self.snmp_switch.snmp_switch_trap = []
                    # Очищаем список сообщений класса SecondWindow
                    self.window_second.snmp_traps = []
                # Очищаем поля ввода текста
                self.textEdit.clear()
                self.textEdit_4.clear()
                # Определяем индекс ip_addr в селекторе comboBox   
                index = self.comboBox_4.findText(self.ip_addr)
                # Удаляем значение ip_addr из селектора comboBox
                self.comboBox_4.removeItem(index)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса inf_add метод exec_(), который вызывает всплывающее окно об успешном удалении ip адреса
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.runtime_error.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit.clear()
            self.textEdit_4.clear()
        return None
    
    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет данные из таблицы Ports БД
    def click_btn_del_port(self, btn: Any) -> None:
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_port.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление порта из таблицы Ports 
                    sql.del_db(port=self.port, ip_addr=self.ip_addr, table='Ports')
                if self.window_second.dict_set.get(f'{self.ip_addr}/{self.port}'):
                    # Очищаем список сообщений класса ThreadSwitch
                    self.snmp_switch.snmp_switch_trap = []
                    # Очищаем список сообщений класса SecondWindow
                    self.window_second.snmp_traps = []
                    # Удаляем значение из словря dict_set класса SecondWindow
                    del self.window_second.dict_set[f'{self.ip_addr}/{self.port}']
                # Очищаем поля ввода текста
                self.textEdit_31.clear()
                # Устанавливаем значение селектора к первоначальному значению
                self.comboBox_4.setCurrentIndex(0)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса метод exec_(), который вызывает диалоговое окно
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое
                self.runtime_error.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit_31.clear()
            # Устанавливаем значение селектора к первоначальному значению
            self.comboBox_4.setCurrentIndex(0)
        return None
    
    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет данные из таблицы в БД
    def click_btn_del_sla(self, btn: Any) -> None:
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_sla.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление sla из таблицы Ports 
                    sql.del_db(sla=int(self.sla), ip_addr=self.ip_addr, table='Ports')

                if self.window_second.dict_set.get(f'{self.ip_addr}/{self.sla}'):
                    # Очищаем список сообщений класса ThreadSwitch
                    self.snmp_switch.snmp_switch_trap = []
                    # Очищаем список сообщений класса SecondWindow
                    self.window_second.snmp_traps = []
                    # УДАЛЯЕМ ИЗ СЛОВАРЯ DICT_SET в SecondWindow значение ip/sla
                    del self.window_second.dict_set[f'{self.ip_addr}/{self.sla}']
                # Очищаем поля ввода текста
                self.textEdit_36.clear()
                # Устанавливаем значение селектора к первоначальному значению
                self.comboBox_4.setCurrentIndex(0)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса inf_success метод exec_(), который вызывает всплывающее окно об успешном удалении sla
                self.inf_success.exec_()
            except KeyError:
                pass 
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.runtime_error.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit_36.clear()
            # Устанавливаем значение селектора к первоначальному значению
            self.comboBox_4.setCurrentIndex(0)
        return None
    
    # Метод обрабатывает нажатие кнопки диалогового окна, закрывает страницу TabWidget с именем Page.
    def click_btn_close_page(self, btn: Any) -> None:
        # Если нажата кнопка Yes
        if btn.text() == 'Close':
            # Переключаем TabWidget на вкладку Runner
            self.tabWidget.setCurrentIndex(0)
            # Удаляем tabWidget
            self.tab_7.deleteLater()
            # Деактивируем вкладку "Close page"
            self.actionClosePage.setEnabled(False)
            # Деактивируем вкладку "Save"
            self.actionSave.setEnabled(False)
        elif btn.text() == 'Cancel':
            btn.setEnabled(False)
            btn.setEnabled(True)
    
    # Метод устанавливает размер шрифта сообщения Диалогового окна, которое будет выводится при возникновении аварии  
    def set_font_size_message_box(self) -> None:
        try:
            # Получаем значение размера шрифта которое ввел пользователь
            font_size_dialog_box = self.textEdit_35.toPlainText().strip('')
            # Добавляем полученное значение в таблицу Стилей БД
            with ConnectSqlDB() as sql:
                sql.replace_val_db(description='font_size_dialog_box', value=font_size_dialog_box, table='Styles')
            # Присваиваем полученное значение переменной из класса SecondWindow
            self.window_second.font_size_dialog_box = int(font_size_dialog_box)
            # Очищаем поле textBrowser_27
            self.textBrowser_27.clear()
            # Выводим введенное значение размера шрифта текста
            self.textBrowser_27.append(font_size_dialog_box)
            # Выравниваем значение по центру
            self.textBrowser_27.setAlignment(QtCore.Qt.AlignCenter)
            # Очищаем поле для ввода текста
            self.textEdit_35.clear()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_35.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_invalid.exec_()
        return None

    # Метод добавляет в выподающий список имена доступных голосов
    def _add_name_voice_comboBox(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос на получение значения голосового индентификатора
            id_voice = sql.get_db('value', description='speech_name', table='Styles')
        # Перебираем словарь голосов
        for name_voice in self.window_second.speech_text.dic_voices:
            # Получаем количество значений в селекторе 
            index = self.comboBox_5.count()
            # Добавляем имя в селектор 
            self.comboBox_5.addItem("")
            # Поскольку нумерация в селекторе начинается с 0 то подставляя значение index это будет следующим значеием в списке
            self.comboBox_5.setItemText(index, name_voice)
        if isinstance(id_voice[0], str):
            # Устанавливаем текущее значение в селектор которое получили из БД
            self.comboBox_5.setCurrentText(id_voice[0])

    # Метод при нажатии кнопки устанавливает голосовую речь
    def _button_press_voice_speech(self) -> None:
        # Обращаемся к селектору comboBox_5, получаем значение (voice) котрое выбрал пользователь
        voice_name = self.comboBox_5.currentText()
        # Обращаемся к словарю получаем id голоса по имени
        voice_id = self.window_second.speech_text.dic_voices.get(voice_name)
        # Обращаемся к переменной voice_id присваиваем ей id
        self.window_second.speech_text.voice_id = voice_id
        with ConnectSqlDB() as sql:
            sql.replace_val_db(description='speech_name', value=voice_name, table='Styles')
    
    # Метод при нажатии кнопки устанавливает скорость воспроизведения речи
    def _button_press_speed_speech(self) -> None:
        try:
            # Получаем значение которое ввел пользователь
            speech_speed = self.textEdit_38.toPlainText()
            # Присваиваем значение скорости воспроизведения речи
            self.window_second.speech_text.speed_speech = int(speech_speed)
            self.textBrowser_29.clear()
            # Выводим значение 
            self.textBrowser_29.append(speech_speed)
            #
            self.textEdit_38.clear()
            # Подключаемся к БД
            with ConnectSqlDB() as sql:
                # Делаем запрос на замену значения в таблице Стилей
                sql.replace_val_db(description='speed_speech', value=speech_speed, table='Styles')
        except ValueError:
            return None
            #TODO Всплывающее диалоговое окно

    # Метод воспроизводит речь при нажатии на кнопку "Прослушать"
    def _button_press_leasen_to_speech(self) -> None:
        #
        self.window_second.speech_text.start()
        return None

    # Метод при нажатии кнопки "Просмотр" выводит Диалоговое окно с текстом сообщения во вкладки "Настройки"  
    def button_press_view_message_box(self) -> None:
        host_name = 'ААУС Б. Тира (КП2)'
        description = 'Отключение электроэнергии'
        # Добавляем текст сообщения который будет выводится с вызовом Диалогово окна
        self.test_font_size.setText(f'<b style="font-size:{self.window_second.font_size_dialog_box}px">{host_name}: {description}</b>')
        self.test_font_size.exec()

    # Метод проверяет, если пользователь начал ввод текста в поле textEdit, то активируем кнопки иначе кнопки деактивированы, а
    # так же запускает метод _get_position_window, этот метод получает координаты основного окна. 
    def update_textEdit(self) -> None: 
        # Вызываем метод, который получает координаты основного окна программы относительно расположения его на экране монитора.
        self._get_position_window()
        # Присваиваем полученный список аварий переменной класса ThreadMonitirAlarms snmp_traps от класса ThreadSNMPAsck
        self.monitoring_alarms.snmp_traps = self.snmp_ask.snmp_trap + self.snmp_switch.snmp_switch_trap
        # Присваиваем полученный список аварий переменной класса SecondWindow snmp_traps от класса ThreadSNMPAsck
        self.window_second.snmp_traps = self.snmp_ask.snmp_trap + self.snmp_switch.snmp_switch_trap
        
        # Кнопка добавления пользователя и кнопка удаления пользователя
        if self.textEdit_2.toPlainText() and self.textEdit_12.toPlainText():
            self.Add_User_btn.setEnabled(True)
            self.Delet_User_btn.setEnabled(True)
        else:
            self.Add_User_btn.setEnabled(False)
            self.Delet_User_btn.setEnabled(False)
        # Кнопка добавления устройства в базу данных
        if self.textEdit.toPlainText() and self.textEdit_4.toPlainText():
            self.Add_device_btn.setEnabled(True)
        else:
            self.Add_device_btn.setEnabled(False)
        # Кнопка удаления устройства из базы данных
        if self.textEdit.toPlainText():
            self.Delete_device_btn.setEnabled(True)
        else:
            self.Delete_device_btn.setEnabled(False)
        # Кнопка поиска устройства по ip адресу
        if self.textEdit_5.toPlainText():
            self.Find_Device_btn.setEnabled(True)
        else:
           self.Find_Device_btn.setEnabled(False)
        # Кнопка проверки к какой группе OID относится устройство
        if self.textEdit_3.toPlainText():
            self.Check_device_btn.setEnabled(True)
        else:
            self.Check_device_btn.setEnabled(False)
        # Кнопка запуска чат Бота
        if self.textEdit_6.toPlainText() and not self.Stop_bot_btn.isEnabled():
            self.Start_bot_btn.setEnabled(True)
        else:
            self.Start_bot_btn.setEnabled(False)
        # Кнопка установки значения интервала опроса SNMPAsk
        if self.textEdit_7.toPlainText():
            self.Set_btn.setEnabled(True)
        else:
            self.Set_btn.setEnabled(False)
        # Кнопка установки значения интервала опроса SNMPSwitch
        if self.textEdit_34.toPlainText():
            self.Set_snmp_interval_btn.setEnabled(True)
        else:
            self.Set_snmp_interval_btn.setEnabled(False)
        # Кнопка установки значения интервала опроса Мониторинга аварий
        if self.textEdit_8.toPlainText():
            self.Set_monitor_btn.setEnabled(True)
        else:
            self.Set_monitor_btn.setEnabled(False)
        # Кнопка установки значения интервала между опросами Secondwindows
        if self.textEdit_9.toPlainText():
             self.Set_window_interval_time_btn.setEnabled(True)
        else:
            self.Set_window_interval_time_btn.setEnabled(False)
        # Кнопка открытия второго окна
        if self.window_second.isClose_window:
            self.Open_window_button.setEnabled(True)
        # Кнопка установки значения высокой температуры, вкладка Monitoring Alarm
        if self.textEdit_10.toPlainText():
            self.Set_temp_hight_btn.setEnabled(True)
        else:
            self.Set_temp_hight_btn.setEnabled(False)
        # Кнопка установки значения низкой температуры, вкладка Monitoring Alarm
        if self.textEdit_13.toPlainText():
            self.Set_temp_low_btn.setEnabled(True)
        else:
            self.Set_temp_low_btn.setEnabled(False)
        # Кнопка установки значения низкого напряжения, вкладка Monitoring Alarm
        if self.textEdit_14.toPlainText():
            self.Set_volt_low_btn.setEnabled(True)
        else:
            self.Set_volt_low_btn.setEnabled(False)
         # Кнопка установки значения низкого уровня топлива,вкладка Monitoring Alarm
        if self.textEdit_15.toPlainText():
            self.Set_oil_low_btn.setEnabled(True)
        else:
            self.Set_oil_low_btn.setEnabled(False)
        # Кнопка установки значения высокой температуры, SecondWindow
        if self.textEdit_11.toPlainText():
            self.Set_window_temp_hight_btn.setEnabled(True)
        else:
            self.Set_window_temp_hight_btn.setEnabled(False)
        # Кнопка установки значения низкой температуры, SecondWindow
        if self.textEdit_16.toPlainText():
            self.Set_window_temp_low_btn.setEnabled(True)
        else:
            self.Set_window_temp_low_btn.setEnabled(False)
        # Кнопка установки значения низкого уровня топлива, SecondWindow
        if self.textEdit_20.toPlainText():
            self.Set_window_oil_low_btn.setEnabled(True)
        else:
            self.Set_window_oil_low_btn.setEnabled(False)
        # Кнопка установки значения размера ширифта, SecondWindow
        if self.textEdit_17.toPlainText() or self.textEdit_28.toPlainText() or self.textEdit_29.toPlainText() \
            or self.textEdit_30.toPlainText():
            self.Set_window_font_size_btn.setEnabled(True)
        else:
            self.Set_window_font_size_btn.setEnabled(False)
        # Кнопка установки значения размера ширифта во вкладке "Каналы"
        if self.textEdit_37.toPlainText():
            self.Set_window_font_size_channel_btn.setEnabled(True)
        else:
            self.Set_window_font_size_channel_btn.setEnabled(False)
        # Кнопка установки значения порога высокого напряжения, SecondWindow
        if self.textEdit_18.toPlainText():
            self.Set_window_hight_volt_btn.setEnabled(True)
        else:
            self.Set_window_hight_volt_btn.setEnabled(False)
        # Кнопка установки значения порога низкого напряжения, SecondWindow
        if self.textEdit_19.toPlainText():
            self.Set_window_low_volt_btn.setEnabled(True)
        else:
            self.Set_window_low_volt_btn.setEnabled(False)
        # Кнопка установки размера ширифта SecondWindow вкладка curent Alarm
        if self.textEdit_32.toPlainText():
            self.Set_window_font_size_alarm_btn.setEnabled(True)
        else:
            self.Set_window_font_size_alarm_btn.setEnabled(False)
        # Кнопка установки Порог уровня сигнала DDM(dBm) SecondWindow
        if self.textEdit_25.toPlainText():
            self.Set_window_power_sign_btn.setEnabled(True)
        else:
            self.Set_window_power_sign_btn.setEnabled(False)
        # Кнопка установки Порог низкой температуры DDM SecondWindow
        if self.textEdit_26.toPlainText():
            self.Set_window_low_temp_ddm_btn.setEnabled(True)
        else:
            self.Set_window_low_temp_ddm_btn.setEnabled(False)
        # Кнопка установки Порог высокой температуры DDM SecondWindow
        if self.textEdit_24.toPlainText():
            self.Set_window_high_temp_ddm_btn.setEnabled(True)
        else:
            self.Set_window_high_temp_ddm_btn.setEnabled(False)
        # Кнопка установки Порог уровня сигнала DDM(dBm) Monitoring Alarm
        if self.textEdit_21.toPlainText():
            self.Set_monitor_power_sign_btn.setEnabled(True)
        else:
            self.Set_monitor_power_sign_btn.setEnabled(False)
        # Кнопка установки Порог низкой температуры DDM Monitoring Alarm
        if self.textEdit_22.toPlainText():
            self.Set_monitor_low_temp_ddm_btn.setEnabled(True)
        else:
            self.Set_monitor_low_temp_ddm_btn.setEnabled(False)
        # Кнопка установки Порог высокой температуры DDM Monitoring Alarm
        if self.textEdit_23.toPlainText():
            self.Set_monitor_high_temp_ddm_btn.setEnabled(True)
        else:
            self.Set_monitor_high_temp_ddm_btn.setEnabled(False)
        # Кнопка установки Число проверок наличия аварий Monitoring Alarm
        if self.textEdit_27.toPlainText():
            self.Set_monitor_count_btn.setEnabled(True)
        else:
            self.Set_monitor_count_btn.setEnabled(False)
        # Кнопка добавления порта коммутатора в базу данных
        if (self.textEdit_31.toPlainText() and self.textEdit_33.toPlainText()) or (self.textEdit_36.toPlainText() and self.textEdit_33.toPlainText()):
            self.Add_switch_port_btn.setEnabled(True)
        else:
            self.Add_switch_port_btn.setEnabled(False)
        # Кнопка удаления порта коммутатора из базы данных
        if self.textEdit_31.toPlainText() or self.textEdit_36.toPlainText():
            self.Delete_switch_port_btn.setEnabled(True)
        else:
            self.Delete_switch_port_btn.setEnabled(False)
        # Кнопка установки размера шрифта текста в диалоговом окне
        if self.textEdit_35.toPlainText():
            self.Set_font_size_btn.setEnabled(True)
        else:
            self.Set_font_size_btn.setEnabled(False)
        # Кнопка установки скорости воспроизведения речи
        if self.textEdit_38.toPlainText():
            self.Set_speed_speech_btn.setEnabled(True)
        else:
           self.Set_speed_speech_btn.setEnabled(False) 
        #self.Clear_btn_3

    # Метод добавляет данные пользователя в БД 
    def button_pressed_add(self) -> None:
        # Получаем из поля textEdit Имя введенное пользователем и записываем в переменную first_name.
        first_name = self.textEdit_2.toPlainText().strip()
        # Получаем из поля textEdit ФИО введенное пользователем и записываем в переменную surname.
        surname = self.textEdit_12.toPlainText().strip()
        # Добавляем пользователя в БД
        try:
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Делает запрос к БД и добавляет пользователя 
                sql.add_db(user_name=first_name, description=surname, table='Users')
            # Очищаем поля для ввода Имени и ФИО 
            self.textEdit_2.clear()
            self.textEdit_12.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса inf_add метод exec_(), который вызывает всплывающее окно об успешном добавлении данных
            time.sleep(0.5)
            self.inf_success.exec_()
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            self.runtime_error.setText('Ошибка запроса!')
            # Задаем сдвиг диалогового окна относительно основного окна приложения, где бы основное окно не располагалась на экране,
            # диалоговое окно будет появляться по середине основного окна.
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой: "Ошибка запроса к БД"
            self.runtime_error.exec_()

    # Метод удаляет пользователя из файла, тем самым закрывая доступ к Чат Боту, при нажатии кнопки "Delet User"
    def button_pressed_del(self) -> None:
        # Получаем Имя, которое ввел пользователь и записываем в переменную first_name
        self.first_name = self.textEdit_2.toPlainText().strip()
        # Получаем из поля textEdit ФИО введенное пользователем и записываем в переменную surname.
        self.surname = self.textEdit_12.toPlainText().strip()
        try:
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД на получить user_name ГДЕ name И description из таблицы Users
                user_name = sql.get_db('user_name', user_name=self.first_name, description=self.surname, table='Users')
            # Проверяем если мы получили данные из запроса
            if user_name:
                # Вызываем экземпляр класса inf_del метод setText, котрый задает текста, который будет выводится при появлении диалогового окна
                self.inf_del.setText(f'Удалить пользователя "{user_name[0]}"?')
                # Вызываем экземпляр класса inf_del метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                # подсвечиваться кнопка "Ок" при появлении диалогового окна
                self.inf_del.setDefaultButton(QMessageBox.Ok)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_del.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса inf_del метод exec_(), который вызывает диалоговое окно с вопрос удалить пользователя 
                self.inf_del.exec_()
            else:
                # Вызываем экземпляр класса QMessageBox метод setText, котрый задает текст, который будет выводится при вызове диалогового окна
                self.inf_empty.setText(f'Пользователя с Nikname "{self.first_name}" нет в БД')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса warn_del метод exec_(), который вызывает диалоговое окно
                self.inf_empty.exec_()
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            self.runtime_error.setText('Ошибка запроса!')
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой: "Ошибка запроса к БД"
            self.runtime_error.exec_()
        return None

    # Метод выводит всех пользователей, которые имеют доступ к чат Боту при нажатие кнопки "Show Users"
    def button_pressed_show_users(self) -> None:
        # Переменая для нумерации пользователей в таблице при выводе
        num = 0
        # Очищаем поле вывода textBrowser
        self.textBrowser.clear()
        try:
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД на получение данных из таблицы Users
                data = sql.get_values_list_db('user_name', 'chat_id', 'description', table='Users')
            # Проверяем что получили из запроса данные
            if data:
                # Устанавливаем фон шрифта
                #self.textBrowser.setFontWeight(1000)
                # Формируем заголовки столбцов, данные которых будут выводиться
                self.textBrowser.append(f'{"№":<10}{"Nikname":25}{"ChatId":30}{"ФИО":<30}')
                for name, chat_id, description in data:
                    num +=1
                    if isinstance(name, str):
                        # Что бы выравнить строки разной длины создаем коэффициент, который компенсирует эту разность
                        length = 2*(18 - len(name))
                        leng = 2*(3 - len(str(num)))
                        len_id = 2*(11 - len(str(chat_id)))
                        # Выводим данные в поле textBrowser_3
                        self.textBrowser.append(f'{num}{" "*leng}{name}{" "*length}{chat_id}{" "*len_id}{description:<30}')
            else:
                self.textBrowser.append('Информация о пользователях в БД отсутствует')
            # Активируем кнопку Clear
            self.Clear_btn.setEnabled(True)
        # Если мы попали в исключения, то выводим сообщение, "Ошибка запроса к БД"
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            self.runtime_error.setText('Ошибка запроса!')
            # Задаем сдвиг диалогового окна относительно основного окна приложения, диалоговое окно будет появляться по середине основного окна.
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой: "Ошибка запроса к БД"
            self.runtime_error.exec_()
        return None

    # Метод очищает окно вывода textBrowser при нажатие кнопки "Clear"
    def button_pressed_clear_show_users(self) -> None:
        # Очищаем поле textBrowser
        self.textBrowser.clear()
        # Деактивируем кнопку Clear
        self.Clear_btn.setEnabled(False)
        return None

    # Метод выводит все устройства, которые имеются в базе при нажатии кнопки "Show Devices"
    def button_pressed_show_device(self) -> None:
        # Переменная для нумерации устройств при выводе их в поле
        num = 0
        # Очищаем поле вывода textBrowser
        self.textBrowser_3.clear()
        # Пытаемся считать данные из файла DataBase и записываем в переменную data вызвам метод _read_data_json
        try:
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Вызываем метод который делает запрос к БД и добавляет данные, которые мы передали 
                data = sql.get_values_list_db('ip', 'description', table='Devices' )
            if data:
                # Устанавливаем стиль шрифта (жирный), который будет выводиться в поле textBrowser_3
                self.textBrowser_3.setFontWeight(1000)
                # Формируем заголовки столбцов, данные которых будут выводиться
                self.textBrowser_3.append(f'{"Номер":<10}{"IP адрес":30}{"Описание":<30}')
                for ip, description in data:
                    num += 1
                    if isinstance(ip, str):
                        # Что бы выравнить строки разной длины создаем коэффициент, который компенсирует эту разность
                        length = 2*(17 - len(ip))
                        leng = 2*(5 - len(str(num)))
                        # Формируем строку со значениями, а промежуток (пробел) между ними домножаем на коэффициент и выводим в поле textBrowser_3 
                        self.textBrowser_3.append(f'{num}{" "*leng}{ip}{" "*length}{description:30}')
                        # Перемещаем ползунок скролбара в верхнее положение
                        self.textBrowser_3.verticalScrollBar().setSliderPosition(1)
            else:
                # Иначе выводим, что оборудование для мониторинга отсутствует
                self.textBrowser_3.append('Данные в БД отсутствуют')
            # Активируем кнопку Clear
            self.Clear_btn_3.setEnabled(True)
        # Попали в исключение, выводим сообщение, что файл не найден
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            self.runtime_error.setText('Ошибка запроса!')
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
            self.runtime_error.exec_()
        return None
    
    # Метод выводит список портов при нажатии кнопки "Показать"
    def button_pressed_show_ports(self) -> None:
        # Переменная для нумерации устройств при выводе их в поле
        num = 0
        # Очищаем поле вывода textBrowser
        self.textBrowser_30.clear()
        # Пытаемся считать данные из файла DataBase и записываем в переменную data вызвам метод _read_data_json
        try:
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД, получаем список с данными 
                data = sql.get_values_list_db('ip_addr', 'port', 'sla', 'description', table='Ports')
            if data:
                # Устанавливаем стиль шрифта жирный
                self.textBrowser_30.setFontWeight(1000)
                # Формируем заголовки столбцов, данные которых будут выводиться
                self.textBrowser_30.append(f'{"№":<5}{"IP адрес":15}{"Порт":15}{"SLA":30}{"Описание":<40}')
                for ip, port, sla, description in data:
                    num += 1
                    if isinstance(ip, str):
                        # Что бы выравнить строки разной длины создаем коэффициент, который компенсирует эту разность
                        length = 2*(15 - len(ip))
                        leng = 2*(3 - len(str(num)))
                        len_port = 2*(8 - len(str(port)))
                        len_sla = 2*(8 - len(str(sla)))
                        # Выводим данные в поле textBrowser_3
                        self.textBrowser_30.append(f'{num}{" "*leng}{ip}{" "*length}{port}{" "*len_port}{sla}{" "*len_sla}{description:30}')
                        # Перемещаем ползунок скролбара в верхнее положение
                        self.textBrowser_30.verticalScrollBar().setSliderPosition(1)
            else:
                # Иначе выводим, что оборудование для мониторинга отсутствует
                self.textBrowser_30.append('Данные в БД отсутствуют')
            # Активируем кнопку Clear
            self.Clear_btn_4.setEnabled(True)
        # Попали в исключение, выводим сообщение, что файл не найден
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            self.runtime_error.setText('Ошибка запроса!')
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно: "Ошибка запроса к БД"
            self.runtime_error.exec_()
        return None

    # Метод очищает окно вывода при нажатие кнопки "Clear"
    def button_pressed_clear_show_devices(self) -> None:
        self.textBrowser_3.clear()
        # Деактивируем кнопку Clear
        self.Clear_btn_3.setEnabled(False)
        return None
    
    # Метод очищает окно вывода при нажатие кнопки "Clear"
    def button_pressed_clear_show_ports(self) -> None:
        self.textBrowser_30.clear()
        # Деактивируем кнопку Clear
        self.Clear_btn_4.setEnabled(False)
        return None

    # Метод ищет устройство по ip адресу при нажатии кнопки Find Device во вкладке Show/Find Devices
    def button_pressed_find_device(self) -> None:
        # Получаем ip адрес введеный пользователем в поле textEdit_5 и записываем в переменную ip  
        ip = self.textEdit_5.toPlainText().strip()
        # Проверяем, что пользователь ввел корректно Ip адрес
        if self._check_ip_address(ip):
            try:
                # Создаем экземпляр класса через менеджер контекста
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД, получить описание устройства ГДЕ ip из таблицы Devices 
                    description = sql.get_db('description', ip=ip, table='Devices')
                # Проверяем, что получили данные из запроса
                if description:
                    # Очищаем поле для вывода
                    self.textBrowser_3.clear()
                    # Выводим ip адрес и Описание устройства в поле textBrowser
                    self.textBrowser_3.append(f'{ip:20}{description[0]:30}')
                    # Активируем кнопку Clear метод button_pressed_clear_show_devices
                    self.Clear_btn_3.setEnabled(True)
                else:
                    # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, который будет выводится при появлении диалогового окна
                    self.inf_empty.setText(f'IP-адреса "{ip}" нет в БД')
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с предупреждением
                    self.inf_empty.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса к БД"
                self.runtime_error.exec_()
        # Иначе ip адрес введен некорректно
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Иначе, если ip адрес введен некорректно, то вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
            self.inf_value_invalid.exec_()
        return None

    # Метод добавляет в БД: ip адрес, описание, тип устройства и Номер окна при нажатии кнопки "Добавить"
    def button_pressed_add_device(self) -> None:
        # Обращаемся к селектору comboBox, получаем тип устройства, которое выбрал пользователь
        self.type_device = self.comboBox.currentText().lower()
        # Получаем ip адрес который ввел пользователь в поле textEdit и записываем в переменную ip_address
        self.ip_address = self.textEdit.toPlainText().strip()
        # Получаем описание устройства
        self.device_name = self.textEdit_4.toPlainText().strip()
        # Проверяем если тип устройства не равен Cisco
        if self.type_device != 'cisco':
            # Если флажок установлен то присваиваем переменной window значение 1
            if self.window_1_radioButton.isChecked():
                window = 1
            elif self.window_2_radioButton.isChecked():
                window = 2
            elif self.window_3_radioButton.isChecked():
                window = 3
            elif self.window_4_radioButton.isChecked():
                window = 4
            else:
                self.inf_empty.setText('Не выбран номер окна')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с уведомлением, что не выбран Номер Окна.
                self.inf_empty.exec_()
                return None 
        else:
           window = 4
        # Вызываем метод, который проверяет, что ip адрес введен корректно
        if self._check_ip_address(self.ip_address):
            try:
                # Подключаемся к БД
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД  на добавление данных в таблицу Devices 
                    sql.add_db(model=self.type_device, ip=self.ip_address, description=self.device_name, num_window=window, table='Devices')
                # Проверяем если тип устройства Cisco
                if self.type_device == 'cisco':
                    index = self.comboBox_4.count()
                    # Добавляем ip адрес в селектор 
                    self.comboBox_4.addItem("")
                    self.comboBox_4.setItemText(index, self.ip_address)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно об успешном добавлении данных
                self.inf_success.exec_()
                # Очищаем поле для ввода ip адреса
                self.textEdit.clear()
                # Очищаем поле для ввода Описания устройства
                self.textEdit_4.clear()
                # Возвращаем селектор к первоначальному значению
                self.comboBox.setCurrentIndex(0)
            except (sqlite3.IntegrityError, sqlite3.OperationalError):
                # Вызываем у экземпляра класса QMessageBox() метод setText, который будет выводить сообщение
                # при появлении диалогового окна, подставляем в текст ip адрес
                self.inf_empty.setText(f'IP-адрес {self.ip_address} уже добавлен')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
                self.inf_empty.exec_()
        # Иначе, если ip адрес введен некорректно
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с предупреждением.
            self.inf_value_invalid.exec_()

    # Метод удаляет устройство из файла, при нажатии кнопки "Delete Device"
    def button_pressed_del_device(self) -> None:
        # Получаем ip адрес, который ввел пользователь и записываем в переменную ip
        self.ip_addr = self.textEdit.toPlainText().strip(' ')
        # Проверяем, что ip адрес введен корректно
        if self._check_ip_address(self.ip_addr):
            try:
                # Создаем экземпляр класса
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД, получить модель устройства ГДЕ ip
                    type_device = sql.get_db('model', ip=self.ip_addr, table='Devices')
                if type_device:
                    if type_device[0] == 'cisco':
                        # Создаем экземпляр класса
                        with ConnectSqlDB() as sql:
                            # Делаем запрос к БД на получение данных из таблиц Devices и Ports 
                            self.join_data = sql.get_join_data(self.ip_addr)
                        if self.join_data:
                            # Вызываем у экземпляра класса QMessageBox() метод setText, котрый задает текст
                            self.inf_del_join_data.setText(f'Удалить выбранное устройство "{self.ip_addr}" и связанные с ним номер порта и sla?')
                            # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                            # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                            self.inf_del_join_data.setDefaultButton(QMessageBox.Ok)
                            # Задаем сдвиг диалогового окна относительно основного окна приложения
                            self.inf_del_join_data.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                            self.inf_del_join_data.exec_()
                        # Иначе если к устройству нет ссылок 
                        else:
                            # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, 
                            # который будет выводится при появлении всплывающего окна
                            self.inf_del_switch.setText(f'Удалить выбранное устройство "{self.ip_addr}"?')
                            # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                            # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                            self.inf_del_switch.setDefaultButton(QMessageBox.Ok)
                            # Задаем сдвиг диалогового окна относительно основного окна приложения
                            self.inf_del_switch.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                            self.inf_del_switch.exec_()
                    # Иначе если тип устройства не Cisco
                    else:
                        # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, 
                        # который будет выводится при появлении всплывающего окна
                        self.inf_del_device.setText(f'Удалить выбранное устройство "{self.ip_addr}"?')
                        # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                        # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                        self.inf_del_device.setDefaultButton(QMessageBox.Ok)
                        # Задаем сдвиг диалогового окна относительно основного окна приложения
                        self.inf_del_device.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                        self.inf_del_device.exec_()
                else:
                    # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, который будет выводится при появлении диалогового окна
                    self.inf_empty.setText(f'Устройства" {self.ip_addr}" нет в БД')
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
                    self.inf_empty.exec_()
            except (sqlite3.IntegrityError, sqlite3.OperationalError):
                self.runtime_error.setText('Ошибка запроса!')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое
                self.runtime_error.exec_()
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Иначе, если ip адрес введен некорректно, то вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно.
            self.inf_value_invalid.exec_()
        return None

    # Метод добавляет порт коммутатора в БД для мониторинга количества трафика на порту
    def button_pressed_add_port(self) -> None:
        # Обращаемся к полю textEdit_31, получаем значение (порт коммутатора) которое ввел пользователь
        port = self.textEdit_31.toPlainText()
        # Обращаемся к полю textEdit_36, получаем значение (номер ip sla) которое ввел пользователь
        sla = self.textEdit_36.toPlainText()
        # Обращаемся к полю textEdit_33, получаем значение (описание) которое ввел пользователь
        description = self.textEdit_33.toPlainText()
        # Обращаемся к селектору comboBox_4, получаем значение (ip адрес) котрое выбрал пользователь
        ip_addr = self.comboBox_4.currentText()
        # Обращаемся к селектору comboBox_8, получаем значение котрое выбрал пользователь
        #provider = self.comboBox_8.currentText()
        # Если установлена галочка то устанавливаем значение load_low = 1 иначе 0
        load_low = 1 if self.checkBox.isChecked() else 0
        # Если установлена галочка то устанавливаем значение icmp_echo = 1 иначе 0
        icmp_echo = 1 if self.icmp_echo.isChecked() else 0
        try:
            # Подключаемся к БД
            with ConnectSqlDB() as sql:
                if port:
                    # Делаем запрос к БД получить ip_addr и порт ГДЕ ip И port из таблицы Ports
                    data = sql.get_db('ip_addr', 'port', ip_addr=ip_addr, port=int(port), sla='ISNULL', table='Ports')
                    if not data:
                        # Делаем запрос на добавление данных.
                        sql.add_db(ip_addr=ip_addr, port=int(port), description=description, loading=load_low, table='Ports')
                    else:
                        # Вызываем у экземпляра класса QMessageBox() метод setText, который добавляет текст в диалоговое окно
                        self.inf_empty.setText(f'Порт {port} уже добавлен')
                        # Задаем сдвиг диалогового окна относительно основного окна приложения
                        self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с
                        # уведомлением, что устройство с таким ip адресом уже есть в БД.
                        self.inf_empty.exec_()
                        return None
                elif sla:
                    # Делаем запрос к БД получить ip_addr и sla ГДЕ ip И sla из таблицы Ports
                    data = sql.get_db('ip_addr', 'sla', ip_addr=ip_addr, sla=int(sla), port='ISNULL', table='Ports')
                    if not data:
                        # Делаем запрос на добавление данных.
                        sql.add_db(ip_addr=ip_addr, sla=int(sla), description=description, icmp_echo=icmp_echo, table='Ports')
                    else:
                        # Вызываем у экземпляра класса QMessageBox() метод setText, который добавляет текст в диалоговое окно
                        self.inf_empty.setText(f'SLA {sla} уже добавлен')
                        # Задаем сдвиг диалогового окна относительно основного окна приложения
                        self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
                        self.inf_empty.exec_()
                        return None
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно об успешном добавлении данных
            self.inf_success.exec_()
            # Очищаем поле для ввода порта устройства
            self.textEdit_31.clear()
            # Очищаем поле для ввода sla
            self.textEdit_36.clear()
            # Очищаем поле для ввода Описания 
            self.textEdit_33.clear()
            # Возвращаем селектор к первоначальному значению
            self.comboBox_4.setCurrentIndex(0)
            # Снимаем галочку в ICMP ECHO если она была установлена
            self.icmp_echo.setChecked(False)
            # Снимаем галочку "Низкая нагрузка" если она была установлена
            self.checkBox.setChecked(False)
        except (sqlite3.IntegrityError, sqlite3.OperationalError, ValueError):
            self.runtime_error.setText('Ошибка запроса!')
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
            self.runtime_error.exec_()
        return None
    
    #  Метод удаляет порт коммутатора из БД при нажатии кнопки удалить
    def button_pressed_del_port(self) -> None:
        # Обращаемся к полю textEdit_31, получаем значение (порт коммутатора) которое ввел пользователь
        self.port = int(self.textEdit_31.toPlainText())
        # Обращаемся к полю textEdit_36, получаем значение (номер ip sla) которое ввел пользователь
        self.sla = self.textEdit_36.toPlainText()
        # Обращаемся к селектору comboBox_4, получаем значение (ip адрес) котрое выбрал пользователь
        self.ip_addr = self.comboBox_4.currentText()
        try:
            # Если тип переменной число
            if isinstance(self.port, int):
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на получение данных из таблицы Ports
                    data = sql.get_db('ip_addr', 'port', ip_addr=self.ip_addr, port=self.port, table='Ports')
                if data:
                    # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, 
                    # который будет выводится при появлении всплывающего окна
                    self.inf_del_port.setText(f'Удалить порт {self.port}?')
                    # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                    # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                    self.inf_del_port.setDefaultButton(QMessageBox.Ok)
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_del_port.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                    self.inf_del_port.exec_()      
                else:
                    # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, который подставляет текст в диалоговое окно
                    self.inf_empty.setText(f'Такого порта нет в БД')
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
                    self.inf_empty.exec_()
            # Проверяем если передано значение sla устройства
            elif self.sla:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на получение данных из таблицы Ports
                    data = sql.get_db('ip_addr', 'sla', ip_addr=self.ip_addr, sla=int(self.sla), table='Ports')
                if data:
                    # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, 
                    # который будет выводится при появлении диалогового окна
                    self.inf_del_sla.setText(f'Удалить выбранный sla {self.sla}?')
                    # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                    # подсвечиваться кнопка "Ок" при вызове диалогового окна
                    self.inf_del_sla.setDefaultButton(QMessageBox.Ok)
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_del_sla.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                    self.inf_del_sla.exec_()      
                else:
                    # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, который будет выводится при появлении диалогового окна
                    self.inf_empty.setText(f'Такого порта нет в БД')
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
                    self.inf_empty.exec_()
        except (sqlite3.IntegrityError, sqlite3.OperationalError, ValueError):
            self.runtime_error.setText('Ошибка запроса!')
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно, что значение введено некорректно
            self.runtime_error.exec_()
        return None
        
    # Метод проверяет модель устройства
    def button_pressed_check_device(self) -> None:
        # Очищаем поле textBrowser_2
        self.textBrowser_2.clear()
        # Получаем ip адрес, который ввел пользователь в поле textEdit
        ip_address = self.textEdit_3.toPlainText().strip()
        # Проверяем, что поьзователь ввел ip адрес корректно
        if self._check_ip_address(ip_address):
            # Добавляем в статус бар наш экземпляр класса lbl
            self.lbl.setText('<img src="{}">  Выполняется'.format(self.path_icon_progress))
            # Обращаемся к переменной ip_address у экземпляра класса check_model
            self.check_model.ip_address = ip_address
            # Запускаем в отдельном потоке проверку
            self.check_model.start()
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Иначе, если ip адрес введен некорректно, то вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно
            self.inf_value_invalid.exec_()
        return None
    
    # Метод выводт результат проверки модели устройства
    def outpu_result(self, model) -> None:
        # Выводим полученый результат в поле textBrowser 
        self.textBrowser_2.append(model)
        # Активируем кнопку Clear
        self.Clear_btn_2.setEnabled(True)
        # Добавляем в статус бар наш экземпляр класса lbl
        self.lbl.setText('<img src="{}">  Готово'.format(self.path_icon_done))
        # Останавливаем работу потока
        self.check_model.terminate()
        return None

    # Метод очищает окно вывода при нажатие кнопки "Clear"
    def button_pressed_clear_check_device(self) -> None:
        self.textBrowser_2.clear()
        # Деактивируем кнопку Clear
        self.Clear_btn_2.setEnabled(False)
        return None
    
    # Метод запускае работу экземпляра класса ThreadMonitorAlarms в отдельном потоке при нажатии кнопки Run
    def button_pressed_run_monitor(self) -> None:
        # Запускаем метод run у экземпляра класса ThreadMonitorAlarms в отдельном потоке 
        self.monitoring_alarms.start()
        # Активируем кнопку Stop
        self.Stop_btn.setEnabled(True)
        # Деактивируем кнопку Run
        self.Run_btn.setEnabled(False)
        # Добавляем в статус бар экземпляр класса alarm_lbl текст с изображением, вызвав метод setText
        self.alarm_lbl.setText('<img src="{}">  AlarmMonitoring'.format(self.path_icon_done))
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
        time.sleep(0.2)
        self.inf_success.exec_()
        return None
    
    # Метод останавливает работу экземрляра класса ThreadMonitorAlarms при нажатии кнопки Stop
    def button_pressed_stop_monitor(self) -> None:
        # Останавливаем работу потока функция run экземпляра класса ThreadMonitorAlarms вызвав метод terminate
        self.monitoring_alarms.terminate()
        # Активируем кнопку Run
        self.Run_btn.setEnabled(True)
        # Деактивируем кнопку Stop
        self.Stop_btn.setEnabled(False)
        # Добавляем в статус бар экземпляр класса alarm_lbl текст с изображением, вызвав метод setText
        self.alarm_lbl.setText('<img src="{}">  AlarmMonitoring'.format(self.path_icon_not_runn))
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
        time.sleep(0.2)
        self.inf_success.exec_()
        return None
    
    # Метод запускает экземпляр класса ThreadSNMPAsk в отдельном потоке при нажатии кнопки Run snmp
    def button_pressed_run_snmp(self) -> None:
        # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
        self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_progress))
        # Запускаем метод run у экземпляра класса ThreadSNMPAsk в отдельном потоке  
        self.snmp_ask.start()
        # Запускаем метод run у экземпляра класса ThreadSNMPSwitch в отдельном потоке 
        self.snmp_switch.start()
        # Активируем кнопку Stop
        self.Stop_snmp_btn.setEnabled(True)
        # Деактивируем кнопку Run
        self.Run_snmp_btn.setEnabled(False)
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
        self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_done))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
        self.inf_success.exec_()

    # (МЕТОД НЕ ИСПОЛЬЗУЕТСЯ ) Метод делает проверку, обрабатывает исключения при запуске ThreadSNMPAsck.
    def check_update_start_snmp(self) -> None:
        try:
            ''' Далее делаем запрос вызвав у экземпляра line класса Queue метод get, который удаляет и 
            возвращает элемент из очереди. Полученный результат из запроса преобразуем в строку и записываем
            в переменную  exception
            параметры: block=True - говорит заблокируй до тех пор пока элемент из очереди не станет доступен, 
            а timeout=2.0 говорит, если в течении 2 секунд мы не получили элемент, то сгенирируется исключение Emty
            block=false - элемент вернется сразу если он доступен или сгенерируется исключение Emty (timeout - игнорируется)
            '''
            exception = str(self.line.get(block=True, timeout=2.0))
            # Проверяем если в переменной exception содержатся исключения OSError
            if 'OSError' in exception:
                # Останавливаем работу потока в котором запущена функция run класса ThreadSNMPAsk и ThreadSNMPSwitch
                self.snmp_ask.terminate()
                self.snmp_switch.terminate()
                # Останавливаем работу snmp вызвам метод snmp_stop
                self.snmp_ask.snmp_stop()
                self.snmp_switch.snmp_stop()
                self.runtime_error.setText('Ошибка сетевого подключения')
                # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который добавляет доп. текстовую информацию об ошибке в диалоговое окно
                self.runtime_error.setDetailedText(f"{exception.split(',')[-5]}")
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
                self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_not_runn))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
                self.runtime_error.exec_()
            # Иначе snmp запущен
            else:
                # Активируем кнопку Stop
                self.Stop_snmp_btn.setEnabled(True)
                # Деактивируем кнопку Run
                self.Run_snmp_btn.setEnabled(False)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
                self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_done))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно
                self.inf_success.exec_()
        except Empty:
            return None      
    
    # Метод останавливает работу класса ThreadSNMPAsk при нажатии кнопки Stop
    def button_pressed_stop_snmp(self) -> None:
        # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
        self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_progress))
        # Останавливаем работу потока в котором запущена функция run класса ThreadSNMPAsk
        self.snmp_ask.terminate()
        self.snmp_ask.snmp_stop()
        # Останавливаем работу потока в котором запущена функция run класса ThreadSNMPSwitch
        self.snmp_switch.terminate()
        self.snmp_switch.snmp_stop()
        # Активируем кнопку Run snmp
        self.Run_snmp_btn.setEnabled(True)
        # Деактивируем кнопку Stop
        self.Stop_snmp_btn.setEnabled(False)
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
        self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_not_runn))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с уведомлением об остановке приложения
        time.sleep(0.5)
        self.inf_success.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_btn "Интервал времени между опросами SNMPAsk"
    def set_interval_snmp_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            interval_time = int(self.textEdit_7.toPlainText().strip(''))
            # Проверяем если значение, которое ввел пользователь больше нуля
            if interval_time > 0:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='snmp_interval_time', num=interval_time, table='Settings')
                # Вызываем у экземпляра класса snmp_ask атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                self.snmp_ask.interval_time = interval_time
                # Очищаем поле textBrowser_4
                self.textBrowser_4.clear()
                # Выводим введенное значение временного интервала
                self.textBrowser_4.append(str(self.snmp_ask.interval_time))
                # Выравниваем значение по центру
                self.textBrowser_4.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_7.clear()
            # Иначе выводим диалоговое окно с сообщением, что значение не может быть равно 0
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у QMessageBox() метод setDetailedText, в которм задает можно указать дополнительную информацию об ошибке
                self.inf_value_invalid.setDetailedText('Значение "Интервал времени опроса" от 1 и выше')
                # Вызываем диалоговое окно с ошибкой, что введено неверное значение
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_7.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_snmp_interval_btn "Интервал времени между опросами SNMPSwitch"
    def set_interval_snmp_switch_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            interval_time = int(self.textEdit_34.toPlainText().strip())
            # Проверяем если значение, которое ввел пользователь больше нуля
            if interval_time >= 15:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='snmp_switch_interval_time', num=interval_time, table='Settings')
                # Вызываем у экземпляра класса snmp_switch атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                self.snmp_switch.interval_time = interval_time
                # Очищаем поле textBrowser
                self.textBrowser_26.clear()
                # Выводим введенное значение временного интервала
                self.textBrowser_26.append(str(self.snmp_switch.interval_time))
                # Выравниваем значение по центру
                self.textBrowser_26.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_34.clear()
            # Иначе выводим диалоговое окно с сообщением, что значение не может быть равно 0
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у QMessageBox() метод setDetailedText, в которм задает можно указать дополнительную информацию об ошибке
                self.inf_value_invalid.setDetailedText('Значение "Интервал времени опроса" от 15 и выше')
                # Вызываем диалоговое окно с ошибкой, что введено неверное значение 
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_34.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_monitor_btn "Интервал времени между опросами MonitorAlarm"
    def set_interval_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            interval_time = int(self.textEdit_8.toPlainText().strip())
            # Если введенное значение больше 0 или меньше/равно значению интервала времени SNMP-опросчика, то 
            if 0 < interval_time <= self.snmp_ask.interval_time:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_interval_time', num=interval_time, table='Settings')
                # Вызываем у экземпляра класса monitoring_alarms атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                self.monitoring_alarms.interval_time = interval_time
                # Очищаем поле textBrowser_5
                self.textBrowser_5.clear()
                # Выводим введенное значение временного интервала
                self.textBrowser_5.append(str(self.monitoring_alarms.interval_time))
                # Выравниваем значение по центру
                self.textBrowser_5.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_8.clear()
            # Иначе, выводим диалоговое окно с сообщением, что значение не может быть больше 0 и меньше или равно интервалу времени SNMP-опросчика
            else:
                self.inf_value_invalid.setDetailedText('Значение >0 и <= интервалу времени опроса SNMP-опросчика')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение не может быть больше 0 и меньше или равно интервалу времени SNMP-опросчика
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_8.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_window_interval_time_btn "Интервал времени между опросами SecondWindow"
    def set_interval_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            interval_time = int(self.textEdit_9.toPlainText().strip(' '))
            # Если введенное значение больше 0 или меньше/равно значению интервала времени SNMP-опросчика, то
            if 0 < interval_time <= self.snmp_ask.interval_time:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_interval_time', num=interval_time, table='Settings')
                # Вызываем у экземпляра класса window атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                self.window_second.interval_time = interval_time
                # Очищаем поле textBrowser_6
                self.textBrowser_6.clear()
                # Выводим введенное значение временного интервала
                self.textBrowser_6.append(str( interval_time))
                # Выравниваем значение по центру
                self.textBrowser_6.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_9.clear()
            # Иначе, выводим диалоговое окно с сообщением, что значение не может быть больше 0 и меньше или равно интервалу времени SNMP-опросчика
            else:
                self.inf_value_invalid.setDetailedText('Значение >0 и <= интервалу времени опроса SNMP-опросчика')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение не может быть больше 0 и меньше или равно интервалу времени SNMP-опросчика
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_9.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_window_temp_hight_btn "Порог высокой температуры SecondWindow"   
    def set_temp_hight_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            window_hight_temp = int(self.textEdit_11.toPlainText().strip())
            if window_hight_temp >= 25:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_hight_temp', num=window_hight_temp, table='Settings')
                # Очищаем поле textBrowser_8
                self.textBrowser_8.clear()
                # Выводим введенное значение порога высокой температуры
                self.textBrowser_8.append(str(window_hight_temp))
                # Выравниваем значение по центру
                self.textBrowser_8.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_11.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Высокая температура" от 25 и выше')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение не может быть меньше 25
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_11.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_temp_hight_btn "Порог высокой температуры MonitoringAlarm"   
    def set_temp_hight_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            monitor_hight_temp = int(self.textEdit_10.toPlainText().strip())
            if monitor_hight_temp >= 25:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_hight_temp', num=monitor_hight_temp, table='Settings')
                # Очищаем поле textBrowser_7
                self.textBrowser_7.clear()
                # Выводим введенное значение порога высокой температуры
                self.textBrowser_7.append(str(monitor_hight_temp))
                # Выравниваем значение по центру
                self.textBrowser_7.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_10.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Высокая температура" от 25 и выше')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение не может быть меньше 25
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_10.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_window_temp_low_btn "Порог низкой температуры SecondWindow"
    def set_temp_low_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            window_low_temp = int(self.textEdit_16.toPlainText().strip())
            if  window_low_temp <= 10:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_low_temp', num=window_low_temp, table='Settings')
                # Очищаем поле textBrowser_13
                self.textBrowser_13.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_13.append(str(window_low_temp))
                # Выравниваем значение по центру
                self.textBrowser_13.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_16.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкая температура" от 10 и ниже')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкой температуры не может быть больше 10
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_16.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_temp_low_btn "Порог низкой температуры MonitorAlarm"
    def set_temp_low_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            monitor_low_temp = int(self.textEdit_13.toPlainText().strip())
            if  monitor_low_temp < 10:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_low_temp', num=monitor_low_temp, table='Settings')
                # Очищаем поле textBrowser_10
                self.textBrowser_10.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_10.append(str(monitor_low_temp))
                # Выравниваем значение по центру
                self.textBrowser_10.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_13.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкая температура" от 10 и ниже')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкой температуры не может быть больше 10
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_13.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_volt_low_btn "Порог низкого напряжения MonitorAlarm"
    def set_volt_low_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            monitor_low_volt = float(self.textEdit_14.toPlainText().strip())
            if monitor_low_volt <= 50.0:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_low_volt', num=monitor_low_volt, table='Settings')
                # Очищаем поле textBrowser_11
                self.textBrowser_11.clear()
                # Выводим введенное значение порога низкого напряжения
                self.textBrowser_11.append(str(monitor_low_volt))
                # Выравниваем значение по центру
                self.textBrowser_11.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_14.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкое напряжение" от 50.0 и ниже')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкого напряжения не может быть больше 50
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_14.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_window_low_volt_btn "Порог низкого напряжения SecondWindow"
    def set_volt_low_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            window_low_volt = float(self.textEdit_19.toPlainText().strip())
            if  window_low_volt < 51.0:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_low_volt', num=window_low_volt, table='Settings')
                # Очищаем поле textBrowser_17
                self.textBrowser_17.clear()
                # Выводим введенное значение порога низкого напряжения
                self.textBrowser_17.append(str(window_low_volt))
                # Выравниваем значение по центру
                self.textBrowser_17.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_19.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкое напряжение" от 50.0 и ниже')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкого напряжения не может быть больше 50
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_19.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_window_oil_low_btn "Низкий порог топлива Secondwindow"
    def set_oil_low_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            low_oil_window = int(self.textEdit_20.toPlainText().strip())
            # Добавдяем полученное значение в таблицу Настроек БД
            with ConnectSqlDB() as sql:
                sql.replace_val_db(alarms='window_low_oil', num=low_oil_window, table='Settings')
            # Очищаем поле textBrowser_16
            self.textBrowser_16.clear()
            # Выводим введенное значение порога низкого напряжения
            self.textBrowser_16.append(str(low_oil_window))
            # Выравниваем значение по центру
            self.textBrowser_16.setAlignment(QtCore.Qt.AlignCenter)
            # Очищаем поле для ввода текста
            self.textEdit_20.clear()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_20.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_oil_low_btn "Низкий порог топлива MonitoringAlarm"
    def set_oil_low_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            low_oil = int(self.textEdit_15.toPlainText().strip())
            # Добавдяем полученное значение в таблицу Настроек БД
            with ConnectSqlDB() as sql:
                sql.replace_val_db(alarms='monitor_low_oil', num=low_oil, table='Settings')
            # Вызываем у экземпляра класса monitoring_alarms атрибут low_oil_limit и задаем ему значение порога низкого уровня топлива
            # Очищаем поле textBrowser_12
            self.textBrowser_12.clear()
            # Выводим введенное значение порога низкого напряжения
            self.textBrowser_12.append(str(low_oil))
            # Выравниваем значение по центру
            self.textBrowser_12.setAlignment(QtCore.Qt.AlignCenter)
            # Очищаем поле для ввода текста
            self.textEdit_15.clear()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_15.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_window_hight_volt_btn "Порог высокого напряжения SecondWindow"
    def set_volt_hight_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            hight_voltage = int(self.textEdit_18.toPlainText().strip())
            if hight_voltage >= 230:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_hight_voltage', num=hight_voltage, table='Settings')
                # Очищаем поле textBrowser_12
                self.textBrowser_15.clear()
                # Выводим введенное значение порога низкого напряжения
                self.textBrowser_15.append(str(hight_voltage))
                # Выравниваем значение по центру
                self.textBrowser_15.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_18.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Высокое напряжение" от 230 и выше')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение высокого напряжения не может быть меньше 230
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_18.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_window_power_sign_btn "Порог низкого уровня сигнала DDM SecondWindow"
    def set_signal_low_ddm_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            power_signal_ddm = int(self.textEdit_25.toPlainText().strip())
            # Проверяем что значение уровня сигнала меньше или равно -20
            if power_signal_ddm <= -20:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_signal_level', num=power_signal_ddm, table='Settings')
                # Очищаем поле textBrowser_21
                self.textBrowser_21.clear()
                # Выводим введенное значение порога уровня сигнала DDM
                self.textBrowser_21.append(str(power_signal_ddm))
                # Выравниваем значение по центру
                self.textBrowser_21.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_25.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкий уровень сигнала" от -20dBm и меньше')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение высокого напряжения не может быть меньше 230
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_25.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_window_low_temp_ddm_btn "Порог низкой температуры DDM SecondWindow"
    def set_temp_low_ddm_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            low_temp_ddm = int(self.textEdit_26.toPlainText().strip())
            if low_temp_ddm <= 10:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_low_temp_fiber', num=low_temp_ddm, table='Settings')
                # Очищаем поле textBrowser_22
                self.textBrowser_22.clear()
                # Выводим введенное значение порога низкой температуры DDM
                self.textBrowser_22.append(str(low_temp_ddm))
                # Выравниваем значение по центру
                self.textBrowser_22.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_26.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкая температура DDM" от 10 и ниже')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_26.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_window_high_temp_ddm_btn "Порог высокой температуры DDM SecondWindow"
    def set_temp_hight_ddm_window_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            hight_temp_ddm = int(self.textEdit_24.toPlainText().strip())
            if hight_temp_ddm >= 40:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='window_hight_temp_fiber', num=hight_temp_ddm, table='Settings')
                # Очищаем поле textBrowser_23
                self.textBrowser_23.clear()
                # Выводим введенное значение порога высокой температуры DDM
                self.textBrowser_23.append(str(hight_temp_ddm))
                # Выравниваем значение по центру
                self.textBrowser_23.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_24.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Высокая температура DDM" от 40 и выше')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_24.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_monitor_power_sign_btn "Порог низкого уровня сигнала DDM MonitoringAlarm"
    def set_signal_low_ddm_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            monitor_signal_level = int(self.textEdit_21.toPlainText().strip())
            if  monitor_signal_level < -15:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_signal_level', num=monitor_signal_level, table='Settings')
                # Очищаем поле textBrowser_9
                self.textBrowser_9.clear()
                # Выводим введенное значение порога уровня сигнала
                self.textBrowser_9.append(str(monitor_signal_level))
                # Выравниваем значение по центру
                self.textBrowser_9.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_21.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкий уровень сигнала DDM" от -20 и ниже')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_21.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_monitor_low_temp_ddm_btn "Порог низкой температуры DDM MonitoringAlarm"
    def set_temp_low_ddm_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            monitor_low_temp_fiber = int(self.textEdit_22.toPlainText().strip())
            if  monitor_low_temp_fiber <= 10:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_low_temp_fiber', num=monitor_low_temp_fiber, table='Settings')
                # Очищаем поле textBrowser_19
                self.textBrowser_19.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_19.append(str(monitor_low_temp_fiber))
                # Выравниваем значение по центру
                self.textBrowser_19.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_22.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Низкая температура DDM" от 10 и ниже')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_22.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None

    # Метод обрабатывает нажатие кнопки Set_monitor_high_temp_ddm_btn "Порог высокой температуры DDM"
    def set_temp_hight_ddm_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            monitor_hight_temp_fiber = int(self.textEdit_23.toPlainText().strip())
            if  monitor_hight_temp_fiber >= 40:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_hight_temp_fiber', num=monitor_hight_temp_fiber, table='Settings')
                # Очищаем поле textBrowser_20
                self.textBrowser_20.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_20.append(str(monitor_hight_temp_fiber))
                # Выравниваем значение по центру
                self.textBrowser_20.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_23.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Высокая температура DDM" от 40 и выше')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_23.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
        return None
    
    # Метод обрабатывает нажатие кнопки Set_monitor_count_btn "Количество подтверждений аварии" перед отправкой сообщения
    def set_count_check_monitor_btn(self) -> None:
        try:
            # Получаем значение которое ввел пользователь, преобразуем строку в число
            monitor_count = int(self.textEdit_27.toPlainText().strip())
            if  0 <= monitor_count <= 10:
                # Добавдяем полученное значение в таблицу Настроек БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(alarms='monitor_count', num=monitor_count, table='Settings')
                # Очищаем поле textBrowser_25
                self.textBrowser_25.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_25.append(str(monitor_count))
                # Выравниваем значение по центру
                self.textBrowser_25.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_27.clear()
            else:
                self.inf_value_invalid.setDetailedText('Значение "Количество проверок" в диапазоне от 0 до 10')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_value_invalid.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_value_invalid.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_27.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.inf_value_error.exec_()
    
    # Метод устанавливает размер шрифта текущих аварий во вкладке "Текущие аварии"
    def set_font_size_curent_alarm_window(self) -> None:
        # Получаем значение которое ввел пользователь, преобразуем строку в число
        font_size_current_alarm = int(self.textEdit_32.toPlainText().strip())
        # Добавляем данные в БД
        with ConnectSqlDB() as sql:
            sql.replace_val_db(description='font_size_current_alarm', value=font_size_current_alarm, table='Styles')
        # Проверяем если используется Стиль_1 то меняем только размер ширифта, остальные настройки стиля оставляем без изменений
        if self.isStyle_1:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_6.setStyleSheet(self.style_1.format(font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_1.format(font_size_current_alarm))
        elif self.isStyle_2:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_6.setStyleSheet(self.style_2.format(font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_2.format(font_size_current_alarm))
        elif self.isStyle_3:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_6.setStyleSheet(self.style_3.format(font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_3.format(font_size_current_alarm))
        # Иначе, у нас установлен стиль по умолчанию 
        else:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_6.setStyleSheet(self.style_default.format(font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_default.format(font_size_current_alarm))
        # Вызываем у экземпляра класса window атрибут font_size_current_alarm и задаем ему значение размера ширифта
        self.window_second.font_size_current_alarm = font_size_current_alarm
        # Очищаем поле от предыдущего значения
        self.textBrowser_18.clear()
        # Выводим полученное значение размера ширифта
        self.textBrowser_18.append(str(self.window_second.font_size_current_alarm))
        # Выравниваем значение по центру
        self.textBrowser_18.setAlignment(QtCore.Qt.AlignCenter)
        # Очищаем поле для ввода текста
        self.textEdit_32.clear()
        return None
    
    # Метод устанавливает размер ширифта текста в окне SecondWindows вкладка All devices с учетом выбранного стиля          
    def set_font_size_text(self) -> None:
        try:
            # Проверяем, если получили данные от пользователя
            if self.textEdit_17.toPlainText().strip():
                # Получаем значение которое ввел пользователь, преобразуем строку в число
                font_size_frame1 = int(self.textEdit_17.toPlainText().strip())
                # Добавляем данные в БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(description='font_size_frame1', value=font_size_frame1, table='Styles')
                # Проверяем если пользователь установил стиль окна Style_1, тогда
                if self.isStyle_1:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_3.setStyleSheet(self.style_1.format(font_size_frame1))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_2 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_3.setStyleSheet(self.style_2.format(font_size_frame1))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_3 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_3.setStyleSheet(self.style_3.format(font_size_frame1))
                # Иначе если у нас не установлен ни один из стилей т.е. выбран стиль по умолчанию
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window_second.textBrowser_3.setStyleSheet(self.style_default.format(font_size_frame1))
                # Очищаем поле для ввода текста
                self.textEdit_17.clear()
                # Вызываем у экземпляра класса window атрибут font_size и задаем ему значение размера ширифта
                self.window_second.font_size_frame1 = font_size_frame1
            # Проверяем, если получили данные от пользователя
            if self.textEdit_28.toPlainText().strip():
                # Получаем значение которое ввел пользователь, преобразуем строку в число
                font_size_frame2 = int(self.textEdit_28.toPlainText().strip())
                # Добавляем данные в БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(description='font_size_frame2', value=font_size_frame2, table='Styles')
                # Проверяем если установлен стиль окна isStyle_1
                if self.isStyle_1:
                    # Применяем настройки стиля self.style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser.setStyleSheet(self.style_1.format(font_size_frame2))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser.setStyleSheet(self.style_2.format(font_size_frame2))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser.setStyleSheet(self.style_3.format(font_size_frame2))
                # Иначе если у нас не установлен ни один из стилей то
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window_second.textBrowser.setStyleSheet(self.style_default.format(font_size_frame2))
                # Очищаем поле для ввода текста
                self.textEdit_28.clear()
                # Вызываем у экземпляра класса window атрибут font_size_frame2 и задаем ему значение размера ширифта
                self.window_second.font_size_frame2 = font_size_frame2
            # Проверяем, если получили данные от пользователя
            if self.textEdit_29.toPlainText().strip():
                # Получаем значение которое ввел пользователь, преобразуем строку в число
                font_size_frame3 = int(self.textEdit_29.toPlainText().strip(' '))
                # Добавляем данные в БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(description='font_size_frame3', value=font_size_frame3, table='Styles')
                # Проверяем если установлен стиль окна isStyle_1
                if self.isStyle_1:
                    # Применяем настройки стиля self.style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_2.setStyleSheet(self.style_1.format(font_size_frame3))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_2.setStyleSheet(self.style_2.format(font_size_frame3))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_2.setStyleSheet(self.style_3.format(font_size_frame3))
                # Иначе если у нас не установлен ни один из стилей то
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window_second.textBrowser_2.setStyleSheet(self.style_default.format(font_size_frame3))
                # Очищаем поле для ввода текста
                self.textEdit_29.clear()
                # Вызываем у экземпляра класса window атрибут font_size_frame3 и задаем ему значение размера ширифта
                self.window_second.font_size_frame3 = font_size_frame3
            # Проверяем, если получили данные от пользователя
            if self.textEdit_30.toPlainText().strip():
                # Получаем значение которое ввел пользователь, преобразуем строку в число
                font_size_frame4 = int(self.textEdit_30.toPlainText().strip())
                # Добавляем данные в БД
                with ConnectSqlDB() as sql:
                    sql.replace_val_db(description='font_size_frame4', value=font_size_frame4, table='Styles')
                # Проверяем если установлен стиль окна isStyle_1
                if self.isStyle_1:
                    # Применяем настройки стиля self.style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_4.setStyleSheet(self.style_1.format(font_size_frame4))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_4.setStyleSheet(self.style_2.format(font_size_frame4))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window_second.textBrowser_4.setStyleSheet(self.style_3.format(font_size_frame4))
                # Иначе если у нас не установлен ни один из стилей то
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window_second.textBrowser_4.setStyleSheet(self.style_default.format(font_size_frame3))
                # Очищаем поле для ввода текста
                self.textEdit_30.clear()
                # Вызываем у экземпляра класса window атрибут font_size_frame4 и задаем ему значение размера ширифта
                self.window_second.font_size_frame4 = font_size_frame4
            # Очищаем поле textBrowser_14
            self.textBrowser_14.clear()
            # Выводим введенное значение размера ширифта в окно textBrowser_14
            self.textBrowser_14.append(f"{self.window_second.font_size_frame1}/{self.window_second.font_size_frame2}/{self.window_second.font_size_frame3}/{self.window_second.font_size_frame4}")  
            # Выравниваем значение по центру
            self.textBrowser_14.setAlignment(QtCore.Qt.AlignCenter)  
        except ValueError:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_value_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой что введено не допустимое значение
            self.inf_value_error.exec_()
        return None

    # Метод устанавливает размер шрифта во вкладке "Каналы"
    def set_font_size_channel_window(self) -> None:
        # Получаем значение которое ввел пользователь, преобразуем строку в число
        font_size_channel = int(self.textEdit_37.toPlainText().strip())
        # Добавляем данные в БД
        with ConnectSqlDB() as sql:
            sql.replace_val_db(description='font_size_channel', value=font_size_channel, table='Styles')
        # Проверяем если используется Стиль_1 то меняем только размер ширифта, остальные настройки стиля оставляем без изменений
        if self.isStyle_1:
            # Вызываем у экземпляра класса window атрибут textBrowser_7 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_7 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_7.setStyleSheet(self.style_1.format(font_size_channel))
        elif self.isStyle_2:
            # Вызываем у экземпляра класса window атрибут textBrowser_7 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_7 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_7.setStyleSheet(self.style_2.format(font_size_channel))
        elif self.isStyle_3:
            # Вызываем у экземпляра класса window атрибут textBrowser_7 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_7 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_7.setStyleSheet(self.style_3.format(font_size_channel))
        # Иначе, у нас установлен стиль по умолчанию 
        else:
            # Вызываем у экземпляра класса window атрибут textBrowser_7 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_7 передаем ему настройки стиля ширифта ввиде строки
            self.window_second.textBrowser_7.setStyleSheet(self.style_default.format(font_size_channel))
        # Вызываем у экземпляра класса window атрибут font_size_current_alarm и задаем ему значение размера ширифта
        self.window_second.font_size_channel_frame = font_size_channel
        # Очищаем поле от предыдущего значения
        self.textBrowser_28.clear()
        # Выводим полученное значение размера ширифта
        self.textBrowser_28.append(str(self.window_second.font_size_channel_frame))
        # Выравниваем значение по центру
        self.textBrowser_28.setAlignment(QtCore.Qt.AlignCenter)
        # Очищаем поле для ввода текста
        self.textEdit_37.clear()
        return None
    
    # Метод устанавливает Стиль Страницы окна приложения
    def set_style_window(self, style_sheet: Optional[str] =None) -> None:
        # Проверяем, если не передано значение style_sheet
        if style_sheet is None:
            # Обращаемся к селектору comboBox и получаем значение которое выбрал пользователь
            style_sheet = self.comboBox_3.currentText()
            # Добавляем данные в БД
            with ConnectSqlDB() as sql:
                sql.replace_val_db(description='style_sheet', value=style_sheet, table='Styles')
        # Если выбран первый вариант стиля
        if style_sheet == 'Стиль_1':
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки All info 
            self.window_second.textBrowser_4.setStyleSheet(self.style_1.format(self.window_second.font_size_frame1))
            self.window_second.textBrowser_2.setStyleSheet(self.style_1.format(self.window_second.font_size_frame2))
            self.window_second.textBrowser.setStyleSheet(self.style_1.format(self.window_second.font_size_frame3))
            self.window_second.textBrowser_3.setStyleSheet(self.style_1.format(self.window_second.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window_second.textBrowser_6.setStyleSheet(self.style_1.format(self.window_second.font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_1.format(self.window_second.font_size_current_alarm))
            # Обращаемся к объекту textBrowser и выставляем для фрейма стиль во вкладке "Каналы"
            self.window_second.textBrowser_7.setStyleSheet(self.style_1.format(self.window_second.font_size_channel_frame))
            #
            self.textBrowser_24.clear()
            #
            self.textBrowser_24.append('Стиль_1')
            # Выравниваем значение по центру
            self.textBrowser_24.setAlignment(QtCore.Qt.AlignCenter)
            # Переводим флаг isStyle_1 в значение True
            self.isStyle_1 = True
            # Переводим остальные флаги в значение False
            self.isStyle_default = False
            self.isStyle_2 = False
            self.isStyle_3 = False
        elif style_sheet == 'Стиль_2':
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки All info 
            self.window_second.textBrowser_4.setStyleSheet(self.style_2.format(self.window_second.font_size_frame1))
            self.window_second.textBrowser_2.setStyleSheet(self.style_2.format(self.window_second.font_size_frame2))
            self.window_second.textBrowser.setStyleSheet(self.style_2.format(self.window_second.font_size_frame3))
            self.window_second.textBrowser_3.setStyleSheet(self.style_2.format(self.window_second.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window_second.textBrowser_6.setStyleSheet(self.style_2.format(self.window_second.font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_2.format(self.window_second.font_size_current_alarm))
            # Обращаемся к объекту textBrowser и выставляем для фрейма стиль во вкладке "Каналы"
            self.window_second.textBrowser_7.setStyleSheet(self.style_2.format(self.window_second.font_size_channel_frame))
            #
            self.textBrowser_24.clear()
            #
            self.textBrowser_24.append('Стиль_2')
            # Выравниваем значение по центру
            self.textBrowser_24.setAlignment(QtCore.Qt.AlignCenter)
            # Переводим флаг isStyle_2 в значение True
            self.isStyle_2 = True
            # Переводим остальные флаги в значение False
            self.isStyle_default = False
            self.isStyle_1= False
            self.isStyle_3= False
        elif style_sheet == 'Стиль_3':
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки All info 
            self.window_second.textBrowser_4.setStyleSheet(self.style_3.format(self.window_second.font_size_frame1))
            self.window_second.textBrowser_2.setStyleSheet(self.style_3.format(self.window_second.font_size_frame2))
            self.window_second.textBrowser.setStyleSheet(self.style_3.format(self.window_second.font_size_frame3))
            self.window_second.textBrowser_3.setStyleSheet(self.style_3.format(self.window_second.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window_second.textBrowser_6.setStyleSheet(self.style_3.format(self.window_second.font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_3.format(self.window_second.font_size_current_alarm))
            # Обращаемся к объекту textBrowser и выставляем для фрейма стиль во вкладке "Каналы"
            self.window_second.textBrowser_7.setStyleSheet(self.style_3.format(self.window_second.font_size_channel_frame))
            #
            self.textBrowser_24.clear()
            #
            self.textBrowser_24.append('Стиль_3')
            # Выравниваем значение по центру
            self.textBrowser_24.setAlignment(QtCore.Qt.AlignCenter)
            # Переводим флаг isStyle_3 в значение True
            self.isStyle_3 = True
            # Переводим остальные флаги в значение False
            self.isStyle_default = False
            self.isStyle_1= False
            self.isStyle_2= False
        elif style_sheet == 'Стандартный':
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки All info 
            self.window_second.textBrowser_4.setStyleSheet(self.style_default.format(self.window_second.font_size_frame1))
            self.window_second.textBrowser_2.setStyleSheet(self.style_default.format(self.window_second.font_size_frame2))
            self.window_second.textBrowser.setStyleSheet(self.style_default.format(self.window_second.font_size_frame3))
            self.window_second.textBrowser_3.setStyleSheet(self.style_default.format(self.window_second.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window_second.textBrowser_6.setStyleSheet(self.style_default.format(self.window_second.font_size_current_alarm))
            self.window_second.textBrowser_5.setStyleSheet(self.style_default.format(self.window_second.font_size_current_alarm))
            # Обращаемся к объекту textBrowser и выставляем для фрейма стиль во вкладке "Каналы"
            self.window_second.textBrowser_7.setStyleSheet(self.style_default.format(self.window_second.font_size_channel_frame))
            #
            self.textBrowser_24.clear()
            #
            self.textBrowser_24.append('Стандартный')
            # Выравниваем значение по центру
            self.textBrowser_24.setAlignment(QtCore.Qt.AlignCenter)
            # Переводим флаг isStyle_default в значение True
            self.isStyle_default = True
            # Переводим остальные флаги в значение False
            self.isStyle_1 = False
            self.isStyle_2= False
            self.isStyle_3= False
        return None
       
    # Метод обрабатывает нажатие кнопки Run bot
    def button_pressed_run_bot(self) -> None:
        # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
        self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_progress))
        # Получаем токен введенный пользователем в поле textEdit и записываем в переменную token
        token = self.textEdit_6.toPlainText()
        # Вызываем атрибут(переменную) token у экземпляра класса monitoring_alarms, класса ThreadMonitorAlarms и присваиваем ей
        # полученное значение переменной  token, token нужен для работы метода send_messages
        self.monitoring_alarms.token = token
        try:
            self.bot = TelegramBot(token, self.helper)
            # Подключаем к сигналу signal_error Слот (метод handler_signal_bot_error)
            self.bot.signal_error.connect(self.handler_signal_bot_error)
            # Подключаем к сигналу signal_to_bot_run_successes Слот (метод finish_running_bot)
            self.bot.signal_to_bot_run_successes.connect(self.finish_running_bot)
            # Запускаем чат Бот в отдельном потоке вызвав у экземпляра класса bot метод start
            self.bot.start()
        except (error.InvalidToken, error.Unauthorized) as err:
            self.runtime_error.setText('Ошибка подключения')
            # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
            # указать дополнительную информацию об ошибке
            self.runtime_error.setDetailedText(f"Проверьте введенный токен ключ {err}") 
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
            self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
            self.runtime_error.exec_()
        except (error.TimedOut, error.NetworkError) as err:
            self.runtime_error.setText('Ошибка сетевого подключения')
            # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
            # указать дополнительную информацию об ошибке
            self.runtime_error.setDetailedText(f"Проверьте доступ к интернету\n' {err}")
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.runtime_error.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
            self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
            self.runtime_error.exec_()
        
    # Метод завершает запуск Чат Бота и выводит диалоговое окно об успешном его запуске 
    def finish_running_bot(self) -> None:
        # Если чат Бот запущен, вызывам метод is_running у экземпляра класса bot
        if self.bot.is_running():
            # Активируем кнопку Stop
            self.Stop_bot_btn.setEnabled(True)
            # Очищаем поле ввода textEdit
            self.textEdit_6.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
            self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_done))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с уведомлением о запуске Бота
            self.inf_success.exec_()   

    # Метод обрабатывает нажатие кнопки Stop останавливает работу чат Бота
    def button_pressed_stop_bot(self) -> None:
        # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
        self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_progress))
        # Останавливаем работу чат Бота, переводим флаг в True
        self.bot.is_stop_bot = True
        # Подключаем к сигналу слот (функция), которая будет выполняться при испускании сигнала
        self.bot.signal_to_bot_stop_successes.connect(self.finish_stop_bot)
    
    # Метод завершает остановку Чат Бота и выводит диалоговое окно об успешном его остановке
    def finish_stop_bot(self):
       if not self.bot.is_running():
            # Деактивируем кнопку Stop
            self.Stop_bot_btn.setEnabled(False)
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
            self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно 
            self.inf_success.exec_()
        
    # Метод открывает второе окно у приложения 
    def show_second_window(self) -> None:
        # Проверяем, если кнопка Stop_snmp_btn активна, значит SNMP опросчик запущен
        if self.Stop_snmp_btn.isEnabled():
            # Создаем экземпляр класса window и вызываем у него метод show, который открываем второе окно
            self.window_second.show()
            # У экземпляра класса вызываем метод start, который запускает оброботчик сообщений, который будет выводить значения на второй экран
            self.window_second.start()
            # Деактивируем кнопку Open
            self.Open_window_button.setEnabled(False)
        # Иначе выводим уведомление о том что SNMP не запущен
        else:
            time.sleep(0.5)
            self.inf_empty.setText('SNMP-опрощик не запущен')
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_empty.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            self.inf_empty.exec_()

    # Метод проверяет что пользователь ввел корректно ip адрес
    def _check_ip_address(self, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    # Метод получает координаты расположения окна Приложения на экране.
    def _get_position_window(self) -> None:
        # Получаем координаты окна в виде кортежа, записываем в переменную position_main_window
        self.position_main_window = self.frameGeometry().getRect()

    # Функция останавливает работу запущенного процесса exe
    def _stop_process(self, proc_pid: Optional[int]) -> None:
        try:
            # Создаем экземпляр класса Process с именем process модуля(библиотеке) psutil, которому передаем номер запущенного процессса (Pid)
            process = Process(proc_pid)
            # Проверяем запущен данный процес или нет, вызыв метод is_running()
            if process.is_running():
                # Говорим, верните дочерние элементы этого процесса в виде списка экземпляров процесса, предварительно проверив, 
                # был ли повторно использован PID. Если *рекурсивный* имеет значение True (recursive=True), верните всех родительских потомков.
                for proc in process.children(recursive=True):
                    # Удаляем все запущенные дочерние процессы нашего родительского(нашего основного запущенного) процесса
                    proc.kill()
                # Удаляем родительский(основной) процесс
                process.kill()
        except NoSuchProcess:
            return None


app = QtWidgets.QApplication(sys.argv)
#app = QtWidgets.QApplication([])
#app.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
# Создаем экземпляр класса Application
#windows =  Application(None, QtCore.Qt.WindowFlags(QtCore.Qt.WA_DeleteOnClose))
windows =  Application()
#windows.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
#print(Application.mro())
# Вызываем метод show, который мы унаследовали от классса QMainWindow
windows.show()
#windows.close()
# Вызываем метод exec_()(execute) - выполнить
app.exec_()
#sys.exit(app.exec_())
#windows.close()

