#
import sqlite3
import time
import sys
from pathlib import Path
#from tabulate import tabulate
import ipaddress
from telegram import error
from class_ThreadSNMPAsc import ThreadSNMPAsk
from class_ThreadSNMPSwitch import ThreadSNMPSwitch
from PyQt5 import QtWidgets, QtCore
from PlaineAccessui import Ui_MainWindow
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox
from queue import Queue, Empty
#from class_ThreadMonitorAlarmsQT import ThreadMonitorAlarms
from class_ThreadMonitorAlarmsQT_new import ThreadMonitorAlarms
from class_ThreadTelegramBot import ThreadTelegramBot
from class_ApplicationWidget import AplicationWidget
from class_SecondWindowBrowser import SecondWindowBrowser
from class_SqlLiteMain import ConnectSqlDB
from psutil import Process, NoSuchProcess
import multiprocessing


class Application(Ui_MainWindow, QtWidgets.QMainWindow, AplicationWidget):

    def __init__(self):
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
        self.timer_start_bot = QtCore.QTimer(self)
        self.timer_start_snmp = QtCore.QTimer(self)
        self.timer_stop_bot = QtCore.QTimer(self)
        self.timer_check_device = QtCore.QTimer(self)
        # Задаем интервал запуска timer(обновления)
        self.timer.setInterval(1000)
        self.timer_start_bot.setInterval(200)
        self.timer_start_snmp.setInterval(500)
        self.timer_stop_bot.setInterval(500)
        self.timer_check_device.setInterval(300)
        # Вызываем у экземпляра timer метод timeout(сигнал) и с помощью connect прикрепляем наш метод update_textEdit, который будет
        # вызываться при каждом срабатывании сигналя(timeout) через указанный промежуток времени
        self.timer.timeout.connect(self.update_textEdit)
        # Вызываем у экземпляра timer_start_bot метод timeout(сигнал) и с помощью connect прикрепляем наш метод check_update_start_bot, который будет
        # вызываться при каждом срабатывании сигналя(timeout) через указанный промежуток времени
        self.timer_start_bot.timeout.connect(self.check_update_start_bot)
        # Вызываем у экземпляра timer_stop_bot метод timeout(сигнал) и с помощью connect прикрепляем наш метод check_update_stop_bot, который будет
        # вызываться при каждом срабатывании сигналя(timeout) через указанный промежуток времени
        self.timer_stop_bot.timeout.connect(self.check_update_stop_bot)
        #
        self.timer_start_snmp.timeout.connect(self.check_update_start_snmp)
        # Вызываем у экземпляра timer_check_device метод timeout(сигнал) и с помощью connect прикрепляем наш метод check_oid_device, который будет
        # вызываться при каждом срабатывании сигналя(timeout) через указанный промежуток времени
        self.timer_check_device.timeout.connect(self.check_oid_device)
        # Запускаем экземпляр класса timer, вызвав у него метод start
        self.timer.start()
        
    # СОЗДАЕМ ЭКЗЕМПЛЯРЫ КЛАССОВ 
        
        # Создаем экземпляр класса Queue(очередь)
        self.line = Queue()
        # Создаем экземпляр класса ThreadSNMPASwitch
        self.snmp_switch = ThreadSNMPSwitch()
        # Создаем экземпляр класса ThreadSNMPAsk
        self.snmp_ask = ThreadSNMPAsk()
        # Создаем экземпляр класса ThreadMonitorAlarms
        self.monitoring_alarms = ThreadMonitorAlarms()
        # Создаем экземпляр класса SecondWindowBrowser
        self.window = SecondWindowBrowser()

    # ПЕРЕМЕННАЯ ФЛАГ
        # Создаем переменную флаг is_not_user, для метода button_pressed_del, которая определяет есть пользователь в списке или нет
        #self.is_not_user = True
        # Создаем переменную флаг is_not_device, для метода button_pressed_del_device, которая определяет есть устройство в списке или нет
        #self.is_not_device = True
        # Создаем переменную флаг is_not_find для метода button_pressed_find_device, значение которого определяет если устройство в списке или нет
        #self.is_not_find = True

    # ПЕРЕМЕННЫЕ PATH
        # Создаем переменные указывающие путь открытия\записи файла
        #self.path_users = Path(Path.cwd(), "Resources", "Users.json")
        #self.path_db = Path(Path.cwd(), "Resources", "DataBase.json")

    # ПЕРЕМЕННАЯ КООРДИНАТА

        # Создаем переменные координаты X, Y, значение которых будет задавть сдвиг диалогового окна относительно основного окна приложения
        self.X = 100
        self.Y = 150

    # ПЕРЕМЕННАЯ ФЛАГ СТИЛЬ SecondWindow

        self.isStyle_default = True
        self.isStyle_1 = False
        self.isStyle_2 = False
        self.isStyle_3 = False

        self.style_1 = "background-color:  rgb(255, 255, 221);\n" "font: 75 {}pt 'Arial';"
        #
        self.style_2 = "background-color:  rgb(255, 255, 221);\n" "font: 75 {}pt 'Times New Roman';"
        #
        self.style_3 = "background-color:  rgb(255, 255, 221);\n" "font: 75 {}pt 'Book Antiqua';"
        #
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
            data = sql.get_db('ip', model='cisco', table='Devices')
        if data:
            # Перебираем список одновременно распаковав кортеж на ip адрес и все остальное
            for ip, in data:
                # Получаем количество значений в селекторе 
                index = self.comboBox_4.count()
                # Добавляем ip адрес в селектор 
                self.comboBox_4.addItem("")
                # Поскольку нумерация в селекторе начинается с 0 то подставляя значение index это будет следующим значеием в списке
                self.comboBox_4.setItemText(index, ip)

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
        #self.checkBox.pressed.connect(self.set_low_trafffic)

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
        self.Open_window_button.setIcon(self.icon_btn_open_second_window)
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
        self.Set_window_style_sheet_btn.setIcon(self.icon_btn_set)

    # Вывводим первоначальное значение интервала между опросами SNMPAsk
        self.textBrowser_4.append(str(self.snmp_ask.interval_time))

    # Вывводим первоначальное значение интервала между опросами SNMPSwitch
        self.textBrowser_26.append(str(self.snmp_switch.interval_time))

    # Вывводим первоначальное значение интервала времени между опросами Alarm Monitoring
        self.textBrowser_5.append(str(self.monitoring_alarms.interval_time))

    # Вывводим первоначальное значение интервала времени между опросами SecondWindowBrowser
        self.textBrowser_6.append(str(self.window.interval_time))

    # Вывводим первоначальное значение Порога высокой температуры Alarm Monitoring, переобразовываем число в строку
        self.textBrowser_7.append(str(self.monitoring_alarms.hight_temp))

    # Вывводим первоначальное значение Порога высокой температуры SecondWindow, переобразовываем число в строку
        self.textBrowser_8.append(str(self.window.hight_temp))

    # Вывводим первоначальное значение Порога низкой температуры Alarm Monitoring, переобразовываем число в строку
        self.textBrowser_10.append(str(self.monitoring_alarms.low_temp))

    # Вывводим первоначальное значение Порога низкой температуры SecondWindow, переобразовываем число в строку
        self.textBrowser_13.append(str(self.window.low_temp))

    # Вывводим первоначальное значение Порога низкого напряжения Alarm Monitoring, переобразовываем число в строку
        self.textBrowser_11.append(str(self.monitoring_alarms.low_volt))

    # Вывводим первоначальное значение Порога низкого количества топлива Alarm Monitoring, переобразовываем число в строку
        self.textBrowser_12.append(str(self.monitoring_alarms.low_oil_limit))

    # Вывводим первоначальное значение Порога низкого количества топлива SecondWindow, переобразовываем число в строку
        self.textBrowser_16.append(str(self.window.low_oil_limit))

    # Вывводим первоначальное значение Порога Высокого напряжения SecondWindow, переобразовываем число в строку
        self.textBrowser_15.append(str(self.window.hight_voltage))

    # Вывводим первоначальное значение Порога Низкого напряжения SecondWindow, переобразовываем число в строку
        self.textBrowser_17.append(str(self.window.low_voltage))
    
    # Выводим первоначальное значение Размера ширифта SecondWindow вкладка All devices
        self.textBrowser_14.append(f"{self.window.font_size_frame1}/{self.window.font_size_frame2}/{self.window.font_size_frame3}/{self.window.font_size_frame4}")
    
    # Выводим первоначальное значение Размера ширифта SecondWindow вкладка Alarms
        self.textBrowser_18.append(self.window.font_size_alarm)

    # Выводим первоначальное значение Стиля SecondWindow вкладки All info и Alarms
        self.textBrowser_24.append('Стандартный')

    # Выводим первоначальное значение Порог уровня сигнала DDM(dBm) Monitor Alarm
        self.textBrowser_9.append(str(self.monitoring_alarms.signal_level_fiber))

    # Выводим первоначальное значение Порог низкой температуры DDM Monitor Alarm
        self.textBrowser_19.append(str(self.monitoring_alarms.low_temp_fiber))

    # Выводим первоначальное значение Порог высокой температуры DDM Monitor Alarm
        self.textBrowser_20.append(str(self.monitoring_alarms.hight_temp_fiber))

    # Выводим первоначальное значение Порог уровня сигнала DDM(dBm) SecondWindow
        self.textBrowser_21.append(str(self.window.signal_level_fiber))

    # Выводим первоначальное значение Порог низкой температуры DDM SecondWindow
        self.textBrowser_22.append(str(self.window.low_temp_fiber))

    # Выводим первоначальное значение Порог высокой температуры DDM SecondWindow
        self.textBrowser_23.append(str(self.window.hight_temp_fiber))

    # Выводим первоначальное значение Число проверок перед отправкой сообщения Monitor Alarm
        self.textBrowser_25.append(str(self.monitoring_alarms.num))
     
    # СОЗДАНИЕ ВКЛАДОК ДЛЯ МЕНЮ 
        # Для Меню добавляем действия(вкладки) при нажатии на которые будет вызываться метод action_clicked который, будет выполнять
        # действия в зависимости от названия вкладки, так же первым аргументом передаем экземпляр класс icon_menu_open унаследованный
        # у класса AplicationWidget, который содержит изображение
        self.menu.addAction(self.icon_menu_open, 'Open', self.action_clicked)
        self.actionSave = self.menu.addAction(self.icon_menu_save, 'Save', self.action_clicked)
        # Деактивируем вкладку Save
        self.actionSave.setEnabled(False)
        # Создаем вкладку Close, добавляем иконку с изображением, название вкладки и метод который будет выполняться при нажатии на вкладку
        self.actionClosePage = self.menu.addAction(self.icon_close_page, 'Close Page', self.inf_close_page.exec_)
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
        #self.inf_exit_app.buttonClicked.connect(self.click_btn)
        self.inf_del_device.buttonClicked.connect(self.click_btn_del_device)
        self.inf_del_switch.buttonClicked.connect(self.click_btn_del_switch)
        self.inf_del_join_data.buttonClicked.connect(self.click_btn_del_join_data)
        self.inf_del_port.buttonClicked.connect(self.click_btn_del_port)
        #self.warn_dubl_name.buttonClicked.connect(self.click_btn_add_name)
        #self.warn_dubl_ip_device.buttonClicked.connect(self.click_btn_add_ip_device)
        self.inf_close_page.buttonClicked.connect(self.click_btn_close_page)
        #self.err_token_bot.triggered.connect(self.close)
    
    # СТАТУС БАР
        # Выводим Надпись Готово с изображением в статус Бар
        self.statusbar.addWidget(self.lbl)
        # Выводим Надпись SNMP с изображением в статус Бар
        self.statusbar.addWidget(self.snmp_lbl, 4)
        # Выводим Надпись TelegramBot с изображением в статус Бар
        self.statusbar.addWidget(self.bot_lbl, 2)
        # Выводим Надпись AlarmMonitoring с изображением в статус Бар
        self.statusbar.addWidget(self.alarm_lbl, 1)

    # Метод закрывает приложение
    def closeEvent(self, event):
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
            # Проверяем если кнопка Stop активна, значит Чат Бот запущен, тогда останавливаем работу Бота перед выходом из программы
            if self.Stop_bot_btn.isEnabled():
                try:
                    # Останавливаем работу чат Бота вызввам метод disconnect
                    self.bot.disconnect()
                    time.sleep(1.8)
                    # Останавливаем работу потока класса ThreadTelegramBot
                    self.bot.terminate()
                except:
                    pass
            # Проверяем если кнопка Open не активна, то значит открыто второе окно, тогда мы его закрываем
            if not self.Open_window_button.isEnabled():
                self.window.close()
            event.accept()
            # Вызываем метод _stop_process, который останавливает запущенный процесс exe, передаем номер процесса 
            self._stop_process(self.proc_pid)
        else:
            event.ignore()
        
    # Декоратор
    @QtCore.pyqtSlot()
    # Метод обрабатывает нажатие на вкладки в меню
    def action_clicked(self):
        # Метод позволяет получить все сигналы из menu Bar
        action = self.sender()
        if action.text() == 'Open':
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
        elif action.text() == 'Save':
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
    
    # Метод обрабатывает нажатие кнопок в диалоговом окне, удаляет данные из таблицы Users БД
    def click_btn(self, btn):
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
                # Вызываем у экземпляра класса inf_add метод exec_(), который вызывает всплывающее окно об успешном удалении пользователя
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.err_request_db.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit_2.clear()
            self.textEdit_12.clear()

    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет данные из таблицы Devices БД       
    def click_btn_del_device(self, btn):
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_device.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление ip адреса из таблицы Devices 
                    sql.del_db(ip = self.ip_addr, table='Devices')
                # Очищаем поля ввода текста
                self.textEdit.clear()
                self.textEdit_4.clear()
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса inf_add метод exec_(), который вызывает всплывающее окно об успешном удалении ip адреса
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.err_request_db.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit.clear()
            self.textEdit_4.clear()

    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет коммутатор из таблицы Devices БД       
    def click_btn_del_switch(self, btn):
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
                # Вызываем у экземпляра класса inf_add метод exec_(), который вызывает всплывающее окно об успешном удалении ip адреса
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.err_request_db.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit.clear()
            self.textEdit_4.clear()
    
    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет данные из таблиц Devices и Ports БД
    def click_btn_del_join_data(self, btn):
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_join_data.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление ip адреса из таблицы Ports 
                    sql.del_db(ip = self.ip_addr, table='Ports')
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
                # Вызываем у экземпляра класса inf_add метод exec_(), который вызывает всплывающее окно об успешном удалении ip адреса
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.err_request_db.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit.clear()
            self.textEdit_4.clear()
    
    # Метод обрабатывает нажатие кнопки в диалоговом окне, удаляет данные из таблицы Ports БД
    def click_btn_del_port(self, btn):
        if btn.text() == 'OK':
            # Закрываем диалоговое окно
            self.inf_del_port.close()
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД на удаление порта из таблицы Ports 
                    sql.del_db(port=int(self.port), ip=self.ip_addr, table='Ports')
                # Очищаем поля ввода текста
                self.textEdit_31.clear()
                # Устанавливаем значение селектора к первоначальному значению
                self.comboBox_4.setCurrentIndex(0)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса inf_add метод exec_(), который вызывает всплывающее окно об успешном удалении порта
                self.inf_success.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.err_request_db.exec_()
        elif btn.text() == 'Cancel':
            # Очищаем поля ввода текста
            self.textEdit_31.clear()
            # Устанавливаем значение селектора к первоначальному значению
            self.comboBox_4.setCurrentIndex(0)
    
    # Метод обрабатывает нажатие кнопки диалогового окна, закрывает страницу TabWidget с именем Page.
    def click_btn_close_page(self, btn):
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
        elif btn.text() == 'OK':
            self.err_token_bot.clearFocus()

    # Метод проверяет, если пользователь начал ввод текста в поле textEdit, то активируем кнопки иначе кнопки деактивированы, а
    # так же запускает метод _get_position_window, этот метод получает координаты основного окна. 
    def update_textEdit(self): 
        # Вызываем метод, который получает координаты основного окна программы относительно расположения его на экране монитора.
        self._get_position_window()
        # Присваиваем полученный список аварий переменной класса ThreadMonitirAlarms snmp_traps от класса ThreadSNMPAsck
        self.monitoring_alarms.snmp_traps = self.snmp_ask.snmp_trap + self.snmp_switch.snmp_switch_trap
        # Присваиваем полученный список аварий переменной класса SecondWindow snmp_traps от класса ThreadSNMPAsck
        self.window.snmp_traps = self.snmp_ask.snmp_trap
        
        # Кнопка добавления пользователя и кнопка удаления пользователя из базы данных
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
        if self.window.isClose_window:
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
        if self.textEdit_31.toPlainText() and self.textEdit_33.toPlainText():
            self.Add_switch_port_btn.setEnabled(True)
        else:
            self.Add_switch_port_btn.setEnabled(False)
        # Кнопка удаления порта коммутатора из базы данных
        if self.textEdit_31.toPlainText():
            self.Delete_switch_port_btn.setEnabled(True)
        else:
            self.Delete_switch_port_btn.setEnabled(False)

    # Метод добавляет пользователя в файл Users, т.е. тем самым дает доступ к чат Боту, при нажатие кнопки "Add User" 
    def button_pressed_add(self):
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
            # Задаем сдвиг диалогового окна относительно основного окна приложения, где бы основное окно не располагалась на экране,
            # диалоговое окно будет появляться по середине основного окна.
            self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой: "Ошибка запроса к БД"
            self.err_request_db.exec_()

    # Метод удаляет пользователя из файла, тем самым закрывая доступ к Чат Боту, при нажатии кнопки "Delet User"
    def button_pressed_del(self):
        # Получаем Имя, которое ввел пользователь и записываем в переменную first_name
        self.first_name = self.textEdit_2.toPlainText().strip()
        # Получаем из поля textEdit ФИО введенное пользователем и записываем в переменную surname.
        self.surname = self.textEdit_12.toPlainText().strip()
        try:
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД на получить user_name ГДЕ name И description из таблицы Users
                user_name = sql.get_db('user_name', name=self.first_name, description=self.surname, table='Users')
            # Проверяем если мы получили данные из запроса
            if user_name:
                # Вызываем экземпляр класса inf_del метод setText, котрый задает текста, который будет выводится при появлении диалогового окна
                self.inf_del.setText(f'Удалить пользователя "{user_name[0][0]}"?')
                # Вызываем экземпляр класса inf_del метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                # подсвечиваться кнопка "Ок" при появлении диалогового окна
                self.inf_del.setDefaultButton(QMessageBox.Ok)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_del.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса inf_del метод exec_(), который вызывает диалоговое окно с вопрос удалить пользователя 
                self.inf_del.exec_()
            else:
                # Вызываем экземпляр класса warn_del метод setText, котрый задает текст, который будет выводится при появлении всплывающего окна
                self.inf_no_user_del.setText(f'Пользователя с Nikname "{self.first_name}" нет в БД')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_no_user_del.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса warn_del метод exec_(), который вызывает диалоговое окно с предупреждением
                self.inf_no_user_del.exec_()
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой: "Ошибка запроса к БД"
            self.err_request_db.exec_()

    # Метод выводит всех пользователей, которые имеют доступ к чат Боту при нажатие кнопки "Show Users"
    def button_pressed_show_users(self):
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
            # Задаем сдвиг диалогового окна относительно основного окна приложения, диалоговое окно будет появляться по середине основного окна.
            self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой: "Ошибка запроса к БД"
            self.err_request_db.exec_()

    # Метод очищает окно вывода textBrowser при нажатие кнопки "Clear"
    def button_pressed_clear_show_users(self):
        # Очищаем поле textBrowser
        self.textBrowser.clear()
        # Деактивируем кнопку Clear
        self.Clear_btn.setEnabled(False)

    # Метод выводит все устройства, которые имеются в базе при нажатии кнопки "Show Devices"
    def button_pressed_show_device(self):
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
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_no_such_file_device.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно: "Ошибка запроса к БД"
            self.err_no_such_file_device.exec_()
    
    #
    def button_pressed_show_ports(self):
        # Переменная для нумерации устройств при выводе их в поле
        num = 0
        # Очищаем поле вывода textBrowser
        self.textBrowser_3.clear()
        # Пытаемся считать данные из файла DataBase и записываем в переменную data вызвам метод _read_data_json
        try:
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД, получаем список с данными 
                data = sql.get_values_list_db('ip_addr', 'port', 'description', table='Ports' )
            if data:
                # Устанавливаем стиль шрифта жирный
                self.textBrowser_3.setFontWeight(1000)
                # Формируем заголовки столбцов, данные которых будут выводиться
                self.textBrowser_3.append(f'{"№":<5}{"IP адрес":15}{"Порт":30}{"Описание":<40}')
                for ip, port, description in data:
                    num += 1
                    # Что бы выравнить строки разной длины создаем коэффициент, который компенсирует эту разность
                    length = 2*(15 - len(ip))
                    leng = 2*(3 - len(str(num)))
                    len_port = 2*(8 - len(str(port)))
                    # Выводим данные в поле textBrowser_3
                    self.textBrowser_3.append(f'{num}{" "*leng}{ip}{" "*length}{port}{" "*len_port}{description:30}')
                    # Перемещаем ползунок скролбара в верхнее положение
                    self.textBrowser_3.verticalScrollBar().setSliderPosition(1)
            else:
                # Иначе выводим, что оборудование для мониторинга отсутствует
                self.textBrowser_3.append('Данные в БД отсутствуют')
            # Активируем кнопку Clear
            self.Clear_btn_3.setEnabled(True)
        # Попали в исключение, выводим сообщение, что файл не найден
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_no_such_file_device.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно: "Ошибка запроса к БД"
            self.err_no_such_file_device.exec_()

    # Метод очищает окно вывода при нажатие кнопки "Clear"
    def button_pressed_clear_show_devices(self):
        self.textBrowser_3.clear()
        # Деактивируем кнопку Clear
        self.Clear_btn_3.setEnabled(False)

    # Метод ищет устройство по ip адресу при нажатии кнопки Find Device во вкладке Show/Find Devices
    def button_pressed_find_device(self):
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
                    self.inf_no_device_del.setText(f'Устройства с ip адресом "{ip}" нет в БД')
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_no_device_del.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с предупреждением
                    self.inf_no_device_del.exec_()
            except (sqlite3.OperationalError, sqlite3.IntegrityError):
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса к БД"
                self.err_request_db.exec_()
        # Иначе ip адрес введен некорректно
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_ip_correct.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Иначе, если ip адрес введен некорректно, то вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с предупреждением.
            self.err_ip_correct.exec_()

    # Метод добавляет ip адрес и Описание устройства в Базу данных chatbot
    def button_pressed_add_device(self):
        # Обращаемся к селектору comboBox, получаем значение которое выбрал пользователь и записываем в переменную type_device
        self.type_device = self.comboBox.currentText().lower()
        # Получаем ip адрес который ввел пользователь в поле textEdit и записываем в переменную ip_address
        self.ip_address = self.textEdit.toPlainText().strip()
        # Получаем описание места установки устройства, которое ввел пользователь в поле textEdit и записываем в переменную device_name
        self.device_name = self.textEdit_4.toPlainText().strip()
        # Проверяем, что ip адрес введен корректно
        if self._check_ip_address(self.ip_address):
            # Создаем экземпляр класса
            try:
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД  на добавление данных в таблицу Devices 
                    sql.add_db(model=self.type_device, ip=self.ip_address, description=self.device_name, table='Devices')
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
                self.inf_dubl_ip_address.setText(f'Устройство с ip адресом {self.ip_address} уже есть в БД')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_dubl_ip_address.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с
                # уведомлением, что устройство с таким ip адресом уже есть в БД.
                self.inf_dubl_ip_address.exec_()
        # Иначе, если ip адрес введен некорректно
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_ip_correct.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с предупреждением.
            self.err_ip_correct.exec_()

    # Метод удаляет устройство из файла, при нажатии кнопки "Delete Device"
    def button_pressed_del_device(self):
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
                            join_data = sql.get_join_data(self.ip_addr)
                        if join_data:
                            # Вызываем у экземпляра класса QMessageBox() метод setText, котрый задает текст, 
                            # который будет выводится при появлении диалогового окна
                            self.inf_del_join_data.setText(f'В БД есть данные из таблицы "Ports" ссылающиеся \nна устройство {self.ip_addr} из таблицы "Devices".\nВсе равно удалить данные из БД?')
                            # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                            # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                            self.inf_del_join_data.setDefaultButton(QMessageBox.Ok)
                            # Задаем сдвиг диалогового окна относительно основного окна приложения
                            self.inf_del_join_data.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                            self.inf_del_join_data.exec_()
                        else:
                            # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, 
                            # который будет выводится при появлении всплывающего окна
                            self.inf_del_switch.setText(f'Удалить устройство "{self.ip_addr}"?')
                            # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                            # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                            self.inf_del_switch.setDefaultButton(QMessageBox.Ok)
                            # Задаем сдвиг диалогового окна относительно основного окна приложения
                            self.inf_del_switch.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                            self.inf_del_switch.exec_()
                    else:
                        # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, 
                        # который будет выводится при появлении всплывающего окна
                        self.inf_del_device.setText(f'Удалить устройство "{self.ip_addr}"?')
                        # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                        # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                        self.inf_del_device.setDefaultButton(QMessageBox.Ok)
                        # Задаем сдвиг диалогового окна относительно основного окна приложения
                        self.inf_del_device.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                        self.inf_del_device.exec_()
                else:
                    # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, который будет выводится при появлении диалогового окна
                    self.inf_no_device_del.setText(f'Устройства с ip адресом "{self.ip_addr}" нет в БД')
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_no_device_del.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с предупреждением
                    self.inf_no_device_del.exec_()
            except (sqlite3.IntegrityError, sqlite3.OperationalError):
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_request_db.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое: "Ошибка запроса БД"
                self.err_request_db.exec_()
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_ip_correct.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Иначе, если ip адрес введен некорректно, то вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с ошибкой.
            self.err_ip_correct.exec_()

    # Метод добавляет порт коммутатора в БД для мониторинга количества трафика на порту
    def button_pressed_add_port(self):
        # Обращаемся к полю textEdit_31, получаем значение (порт коммутатора) которое ввел пользователь
        port = self.textEdit_31.toPlainText()
        # Обращаемся к полю textEdit_33, получаем значение (описание) которое ввел пользователь
        description = self.textEdit_33.toPlainText()
        # Обращаемся к селектору comboBox_4, получаем значение (ip адрес) котрое выбрал пользователь
        ip_addr = self.comboBox_4.currentText()
        # Обращаемся к селектору comboBox_8, получаем значение котрое выбрал пользователь
        provider = self.comboBox_8.currentText()
        #
        if self.checkBox.isChecked():
            load_low = 1
        else:
            load_low = 0
        try:
            with ConnectSqlDB() as sql:
                sql.add_db(ip=ip_addr, port=int(port), description=description, provider=provider, load = load_low, table='Ports')
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.inf_success.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно об успешном добавлении данных
            self.inf_success.exec_()
            # Очищаем поле для ввода порта устройства
            self.textEdit_31.clear()
            # Очищаем поле для ввода Описания 
            self.textEdit_33.clear()
            # Возвращаем селектор к первоначальному значению
            self.comboBox_4.setCurrentIndex(0)
            # Возвращаем селектор к первоначальному значению
            self.comboBox_8.setCurrentIndex(0)
        except (sqlite3.IntegrityError, sqlite3.OperationalError, ValueError):
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_port_correct.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно, что значение введено некорректно
            self.err_port_correct.exec_()
    
    #  Метод удаляет порт коммутатора из БД при нажатии кнопки удалить
    def button_pressed_del_port(self):
        # Обращаемся к полю textEdit_31, получаем значение (порт коммутатора) которое ввел пользователь
        self.port = self.textEdit_31.toPlainText()
        # Обращаемся к селектору comboBox_4, получаем значение (ip адрес) котрое выбрал пользователь
        self.ip_addr = self.comboBox_4.currentText()
        try:
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД получить ip_addr и порт ГДЕ ip И port из таблицы Ports
                data = sql.get_db('ip_addr', 'port', ip=self.ip_addr, port=int(self.port), table='Ports')
            if data:
                # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, 
                # который будет выводится при появлении всплывающего окна
                self.inf_del_port.setText(f'Удалить порт коммутатора {self.port} из БД?')
                # Вызываем экземпляр класса QMessageBox() метод setDefaultButton, котрый устанавливат, что по умолчанию будет
                # подсвечиваться кнопка "Ок" при вызове всплывающего окна
                self.inf_del_port.setDefaultButton(QMessageBox.Ok)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_del_port.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением
                self.inf_del_port.exec_()      
            else:
                # Вызываем экземпляр класса QMessageBox() метод setText, котрый задает текст, который будет выводится при появлении диалогового окна
                self.inf_no_device_del.setText(f'Устройства {self.ip_addr} с портом "{self.port}" нет в БД')
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_no_device_del.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с предупреждением
                self.inf_no_device_del.exec_()
        except (sqlite3.IntegrityError, sqlite3.OperationalError, ValueError):
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_port_correct.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно, что значение введено некорректно
            self.err_port_correct.exec_()
    
    # Метод проверяет принадлежность Ip адреса к OID
    def button_pressed_check_device(self):
        # Очищаем поле textBrowser_2
        self.textBrowser_2.clear()
        # Получаем ip адрес, который ввел пользователь в поле textEdit
        self.ip_address = self.textEdit_3.toPlainText().strip()
        # Проверяем, что поьзователь ввел ip адрес корректно
        if self._check_ip_address(self.ip_address):
            # Добавляем в статус бар наш экземпляр класса lbl
            self.lbl.setText('<img src="{}">  Выполняется'.format(self.path_icon_progress))
            # Создаем экземпляр класса snmp_ask_check
            self.snmp_ask_check = ThreadSNMPAsk()
            # Запускаем работу timer_check_device, который вызывает метод check_oid_device
            self.timer_check_device.start()
        else:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_ip_correct.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Иначе, если ip адрес введен некорректно, то вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с предупреждением.
            self.err_ip_correct.exec_()
    
    # Метод делает проверку к какому типу принадлежит устройство с веденным ip адресом
    def check_oid_device(self):
            # Обращаемся к селектору comboBox и получаем значение которое выбрал пользователь и записываем в переменную method
            method = self.comboBox_2.currentText().lower()
            # Вызываем метод forpost2 передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
            if method == 'forpost':
                # Вызываем метод forpost из класса "class_SNMPAsc" передавая на вход ip адрес устройства, полученный результат записываем в переменную result
                result = self.snmp_ask_check.forpost(self.ip_address, timeout=5, flag=True)
                # Выводим полученый результат в поле textBrowser 
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'forpost_2':
                # Вызываем метод forpost2 передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.forpost_2(self.ip_address, timeout=5, flag=True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'forpost_3':
                # Вызываем метод forpost_3 передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.forpost_3(self.ip_address, timeout=5, flag=True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'eaton':
                # Вызываем метод eaton передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.eaton(self.ip_address, timeout=5, flag=True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'sc200':
                # Вызываем метод sc200 передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.sc200(self.ip_address, timeout=5, flag=True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'legrand':
                # Вызываем метод legrand передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.legrand(self.ip_address, timeout=5, flag=True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'apc':
                # Вызываем метод apc передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.apc(self.ip_address, timeout=5, flag=True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'eltek':
                # Вызываем метод eltek передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.eltek(self.ip_address, timeout=5, flag=True, next=True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'macc':
                # Вызываем метод eltek передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.eltek(self.ip_address, timeout=5, flag=True, next = True)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            elif method == 'modbus':
                # Вызываем метод modbus передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
                result = self.snmp_ask_check.modbus(self.ip_address, time_out=5)
                self.textBrowser_2.append(result)
                # Активируем кнопку Clear
                self.Clear_btn_2.setEnabled(True)
            # Добавляем в статус бар наш экземпляр класса lbl
            self.lbl.setText('<img src="{}">  Готово'.format(self.path_icon_done))
            # Останавливаем работу таймера timer_check_device
            self.timer_check_device.stop() 
            # Возвращаем селектор comboBox к первоначальному значению
            #self.comboBox_2.setCurrentIndex(0)

    # Метод очищает окно вывода при нажатие кнопки "Clear"
    def button_pressed_clear_check_device(self):
        self.textBrowser_2.clear()
        # Деактивируем кнопку Clear
        self.Clear_btn_2.setEnabled(False)
    
    # Метод запускае работу экземпляра класса ThreadMonitorAlarms в отдельном потоке при нажатии кнопки Run
    def button_pressed_run_monitor(self):
        # Запускаем метод run у экземпляра класса ThreadMonitorAlarms в отдельном потоке 
        self.monitoring_alarms.start()
        # Активируем кнопку Stop
        self.Stop_btn.setEnabled(True)
        # Деактивируем кнопку Run
        self.Run_btn.setEnabled(False)
        # Добавляем в статус бар экземпляр класса alarm_lbl текст с изображением, вызвав метод setText
        self.alarm_lbl.setText('<img src="{}">  AlarmMonitoring'.format(self.path_icon_done))
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.info_done.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением об успешном запуске приложения
        time.sleep(0.2)
        self.info_done.exec_()
    
    # Метод останавливает работу экземрляра класса ThreadMonitorAlarms при нажатии кнопки Stop
    def button_pressed_stop_monitor(self):
        # Останавливаем работу потока функция run экземпляра класса ThreadMonitorAlarms вызвав метод terminate
        self.monitoring_alarms.terminate()
        # Активируем кнопку Run
        self.Run_btn.setEnabled(True)
        # Деактивируем кнопку Stop
        self.Stop_btn.setEnabled(False)
        # Добавляем в статус бар экземпляр класса alarm_lbl текст с изображением, вызвав метод setText
        self.alarm_lbl.setText('<img src="{}">  AlarmMonitoring'.format(self.path_icon_not_runn))
        # Задаем сдвиг диалогового окна относительно основного окна приложения
        self.info_done.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением об остановке приложения
        time.sleep(0.2)
        self.info_done.exec_()
    
    # Метод запускает экземпляр класса ThreadSNMPAsk в отдельном потоке при нажатии кнопки Run snmp
    def button_pressed_run_snmp(self):
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
        self.info_done.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
        self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_done))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением об запуске приложения
        self.info_done.exec_()

    # Метод делает проверку, обрабатывает исключения при запуске ThreadSNMPAsck.(МЕТОД НЕ ИСПОЛЬЗУЕТСЯ )
    def check_update_start_snmp(self):
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
                # Останавливаем экземпляр класса timer_start_snmp вызвав у него метод stop
                self.timer_start_snmp.stop()
                # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
                # указать дополнительную информацию об ошибке
                self.err_socket_snmp.setDetailedText(f"{exception.split(',')[-5]}")
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_socket_snmp.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
                self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_not_runn))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
                self.err_socket_snmp.exec_()
            # Иначе snmp запущен
            else:
                # Останавливаем экземпляр класса timer_start_snmp вызвав у него метод stop
                self.timer_start_snmp.stop()
                # Активируем кнопку Stop
                self.Stop_snmp_btn.setEnabled(True)
                # Деактивируем кнопку Run
                self.Run_snmp_btn.setEnabled(False)
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.info_run_app.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
                self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_done))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает всплывающее окно с уведомлением об запуске приложения
                self.info_run_app.exec_()
        except Empty:
            pass       
    
    # Метод останавливает работу класса ThreadSNMPAsk при нажатии кнопки Stop
    def button_pressed_stop_snmp(self):
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
        self.info_done.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
        # Добавляем в статус бар экземпляр класса snmp_lbl текст с изображением, вызвав метод setText
        self.snmp_lbl.setText('<img src="{}">  SNMP'.format(self.path_icon_not_runn))
        # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с уведомлением об остановке приложения
        time.sleep(0.5)
        self.info_done.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_btn "Интервал времени между опросами SNMPAsk"
    def set_interval_snmp_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную interval_time
                interval_time = self.textEdit_7.toPlainText().strip(' ')
                # Проверяем если значение, которое ввел пользователь больше нуля
                if int(interval_time) > 0:
                    # Вызываем у экземпляра класса snmp_ask атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                    self.snmp_ask.interval_time = int(interval_time)
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
                    self.inf_snmp_interval_time.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у QMessageBox() метод setDetailedText, в которм задает можно указать дополнительную информацию об ошибке
                    self.inf_snmp_interval_time.setDetailedText('Значение должно быть больше 0')
                    # Вызываем диалоговое окно с ошибкой, что введено неверное значение
                    self.inf_snmp_interval_time.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_7.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_snmp_interval_btn "Интервал времени между опросами SNMPSwitch"
    def set_interval_snmp_switch_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную interval_time
                interval_time = self.textEdit_34.toPlainText().strip()
                # Проверяем если значение, которое ввел пользователь больше нуля
                if int(interval_time) >= 15:
                    # Вызываем у экземпляра класса snmp_switch атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                    self.snmp_switch.interval_time = int(interval_time)
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
                    self.inf_snmp_interval_time.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем у QMessageBox() метод setDetailedText, в которм задает можно указать дополнительную информацию об ошибке
                    self.inf_snmp_interval_time.setDetailedText('Значение должно быть больше равно 15')
                    # Вызываем диалоговое окно с ошибкой, что введено неверное значение 
                    self.inf_snmp_interval_time.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_34.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_monitor_btn "Интервал времени между опросами MonitorAlarm"
    def set_interval_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную interval_time
                interval_time = self.textEdit_8.toPlainText().strip(' ')
                # Если введенное значение больше 0 или меньше/равно значению интервала времени SNMP-опросчика, то 
                if 0 < int(interval_time) <= self.snmp_ask.interval_time:
                    # Вызываем у экземпляра класса monitoring_alarms атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                    self.monitoring_alarms.interval_time = int(interval_time)
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
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_interval_time.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем диалоговое окно с ошибкой, что значение не может быть больше 0 и меньше или равно интервалу времени SNMP-опросчика
                    self.inf_interval_time.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_8.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_window_interval_time_btn "Интервал времени между опросами SecondWindow"
    def set_interval_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную interval_time
                interval_time = self.textEdit_9.toPlainText().strip(' ')
                # Если введенное значение больше 0 или меньше/равно значению интервала времени SNMP-опросчика, то
                if 0 < int(interval_time) <= self.snmp_ask.interval_time:
                    # Вызываем у экземпляра класса window атрибут interval_time и задаем ему значение интервала времени преобразовав в число 
                    self.window.interval_time = int(interval_time)
                    # Очищаем поле textBrowser_6
                    self.textBrowser_6.clear()
                    # Выводим введенное значение временного интервала
                    self.textBrowser_6.append(str( self.window.interval_time))
                    # Выравниваем значение по центру
                    self.textBrowser_6.setAlignment(QtCore.Qt.AlignCenter)
                    # Очищаем поле для ввода текста
                    self.textEdit_9.clear()
                # Иначе, выводим диалоговое окно с сообщением, что значение не может быть больше 0 и меньше или равно интервалу времени SNMP-опросчика
                else:
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_interval_time.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем диалоговое окно с ошибкой, что значение не может быть больше 0 и меньше или равно интервалу времени SNMP-опросчика
                    self.inf_interval_time.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_9.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_window_temp_hight_btn "Порог высокой температуры SecondWindow"   
    def set_temp_hight_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем если значение больше 25
                if int(self.textEdit_11.toPlainText().strip(' ')) > 25:
                    # Вызываем у экземпляра класса window атрибут hight_temp и задаем ему значение порога высокой температуры преобразовав в число 
                    self.window.hight_temp = int(self.textEdit_11.toPlainText().strip(' '))
                    # Очищаем поле textBrowser_8
                    self.textBrowser_8.clear()
                    # Выводим введенное значение порога высокой температуры
                    self.textBrowser_8.append(str(self.window.hight_temp))
                    # Выравниваем значение по центру
                    self.textBrowser_8.setAlignment(QtCore.Qt.AlignCenter)
                    # Очищаем поле для ввода текста
                    self.textEdit_11.clear()
                else:
                    # Задаем сдвиг диалогового окна относительно основного окна приложения
                    self.inf_hight_temp.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                    # Вызываем диалоговое окно с ошибкой, что значение не может быть меньше 25
                    self.inf_hight_temp.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_11.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_temp_hight_btn "Порог высокой температуры MonitoringAlarm"   
    def set_temp_hight_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем если значение больше 25
            if int(self.textEdit_10.toPlainText().strip(' ')) > 25:
                # Вызываем у экземпляра класса monitoring_alarms атрибут hight_temp и задаем ему значение порога высокой температуры преобразовав в число 
                self.monitoring_alarms.hight_temp = int(self.textEdit_10.toPlainText().strip(' '))
                # Очищаем поле textBrowser_7
                self.textBrowser_7.clear()
                # Выводим введенное значение порога высокой температуры
                self.textBrowser_7.append(str(self.monitoring_alarms.hight_temp))
                # Выравниваем значение по центру
                self.textBrowser_7.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_10.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_hight_temp.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение не может быть меньше 25
                self.inf_hight_temp.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_10.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_window_temp_low_btn "Порог низкой температуры SecondWindow"
    def set_temp_low_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и если значение меньше 10
            if int(self.textEdit_16.toPlainText().strip(' ')) < 10:
                # Вызываем у экземпляра класса window атрибут low_temp и задаем ему значение порога низкой температуры преобразовав в число 
                self.window.low_temp = int(self.textEdit_16.toPlainText().strip(' '))
                # Очищаем поле textBrowser_13
                self.textBrowser_13.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_13.append(str(self.window.low_temp))
                # Выравниваем значение по центру
                self.textBrowser_13.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_16.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_low_temp.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкой температуры не может быть больше 10
                self.inf_low_temp.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_16.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_temp_low_btn "Порог низкой температуры MonitorAlarm"
    def set_temp_low_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем если значение меньше 10
            if int(self.textEdit_13.toPlainText().strip(' ')) < 10:
                # Вызываем у экземпляра класса monitoring_alarms атрибут low_temp и задаем ему значение порога низкой температуры преобразовав в число 
                self.monitoring_alarms.low_temp= int(self.textEdit_13.toPlainText().strip(' '))
                # Очищаем поле textBrowser_10
                self.textBrowser_10.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_10.append(str(self.monitoring_alarms.low_temp))
                # Выравниваем значение по центру
                self.textBrowser_10.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_13.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_low_temp.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкой температуры не может быть больше 10
                self.inf_low_temp.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_13.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_volt_low_btn "Порог низкого напряжения MonitorAlarm"
    def set_volt_low_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем что значение меньше 50
            if float(self.textEdit_14.toPlainText().strip(' ')) < 50.0:
                # Вызываем у экземпляра класса monitoring_alarms атрибут low_volt и задаем ему значение порога низкого напряжения преобразовав в число 
                self.monitoring_alarms.low_volt= float(self.textEdit_14.toPlainText().strip(' '))
                # Очищаем поле textBrowser_11
                self.textBrowser_11.clear()
                # Выводим введенное значение порога низкого напряжения
                self.textBrowser_11.append(str(self.monitoring_alarms.low_volt))
                # Выравниваем значение по центру
                self.textBrowser_11.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_14.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_low_volt.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкого напряжения не может быть больше 50
                self.inf_low_volt.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_14.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_window_low_volt_btn "Порог низкого напряжения SecondWindow"
    def set_volt_low_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем что значение меньше 50
            if float(self.textEdit_19.toPlainText().strip(' ')) < 50.0:
                # Вызываем у экземпляра класса monitoring_alarms атрибут low_volt и задаем ему значение порога низкого напряжения преобразовав в число 
                self.window.low_voltage = float(self.textEdit_19.toPlainText().strip(' '))
                # Очищаем поле textBrowser_17
                self.textBrowser_17.clear()
                # Выводим введенное значение порога низкого напряжения
                self.textBrowser_17.append(str(self.window.low_voltage))
                # Выравниваем значение по центру
                self.textBrowser_17.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_19.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_low_volt.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкого напряжения не может быть больше 50
                self.inf_low_volt.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_19.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_window_oil_low_btn "Низкий порог топлива Secondwindow"
    def set_oil_low_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную low_oil_window
            low_oil_window = self.textEdit_20.toPlainText().strip(' ')
            # Вызываем у экземпляра класса window атрибут low_oil_limit и задаем ему значение порога низкого уровня топлива преобразовав в число 
            self.window.low_oil_limit = int(low_oil_window)
            # Очищаем поле textBrowser_16
            self.textBrowser_16.clear()
            # Выводим введенное значение порога низкого напряжения
            self.textBrowser_16.append(str(self.window.low_oil_limit))
            # Выравниваем значение по центру
            self.textBrowser_16.setAlignment(QtCore.Qt.AlignCenter)
            # Очищаем поле для ввода текста
            self.textEdit_20.clear()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_20.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_oil_low_btn "Низкий порог топлива MonitoringAlarm"
    def set_oil_low_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную low_oil
            low_oil = self.textEdit_15.toPlainText().strip(' ')
            # Вызываем у экземпляра класса monitoring_alarms атрибут low_oil_limit и задаем ему значение порога низкого уровня топлива преобразовав в число 
            self.monitoring_alarms.low_oil_limit = int(low_oil)
            # Очищаем поле textBrowser_12
            self.textBrowser_12.clear()
            # Выводим введенное значение порога низкого напряжения
            self.textBrowser_12.append(str(self.monitoring_alarms.low_oil_limit))
            # Выравниваем значение по центру
            self.textBrowser_12.setAlignment(QtCore.Qt.AlignCenter)
            # Очищаем поле для ввода текста
            self.textEdit_15.clear()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_15.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_window_hight_volt_btn "Порог высокого напряжения SecondWindow"
    def set_volt_hight_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную hight_voltage
            hight_voltage = self.textEdit_18.toPlainText().strip(' ')
            if int(hight_voltage) >= 230:
                # Вызываем у экземпляра класса window атрибут hight_voltage и задаем ему значение порога высокого напряжения преобразовав в float
                self.window.hight_voltage = int(hight_voltage)
                # Очищаем поле textBrowser_12
                self.textBrowser_15.clear()
                # Выводим введенное значение порога низкого напряжения
                self.textBrowser_15.append(str(self.window.hight_voltage))
                # Выравниваем значение по центру
                self.textBrowser_15.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_18.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_window_hight_volt.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение высокого напряжения не может быть меньше 230
                self.inf_window_hight_volt.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_18.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_window_power_sign_btn "Порог низкого уровня сигнала DDM SecondWindow"
    def set_signal_low_ddm_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную power_signal_ddm
            power_signal_ddm = self.textEdit_25.toPlainText().strip(' ')
            # Проверяем что значение уровня сигнала меньше или равно -20
            if int(power_signal_ddm) <= -20:
                # Вызываем у экземпляра класса window атрибут power_signal_ddm и задаем ему значение порога уровня сигнала ddm
                self.window.signal_level_fiber = int(power_signal_ddm)
                # Очищаем поле textBrowser_21
                self.textBrowser_21.clear()
                # Выводим введенное значение порога уровня сигнала DDM
                self.textBrowser_21.append(str(self.window.signal_level_fiber))
                # Выравниваем значение по центру
                self.textBrowser_21.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_25.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_signal_low_ddm.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение высокого напряжения не может быть меньше 230
                self.inf_signal_low_ddm.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_25.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_window_low_temp_ddm_btn "Порог низкой температуры DDM SecondWindow"
    def set_temp_low_ddm_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную low_temp_ddm
            low_temp_ddm = self.textEdit_26.toPlainText().strip(' ')
            if int(low_temp_ddm) <= 10:
                # Вызываем у экземпляра класса window атрибут low_temp_ddm и задаем ему значение порога низкой темп-ры ddm
                self.window.low_temp_fiber = int(low_temp_ddm)
                # Очищаем поле textBrowser_22
                self.textBrowser_22.clear()
                # Выводим введенное значение порога низкой температуры DDM
                self.textBrowser_22.append(str(self.window.low_temp_fiber))
                # Выравниваем значение по центру
                self.textBrowser_22.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_26.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_temp_low_ddm.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_temp_low_ddm.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_26.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_window_high_temp_ddm_btn "Порог высокой температуры DDM SecondWindow"
    def set_temp_hight_ddm_window_btn(self):
        try:
            # Получаем значение которое ввел пользователь и записываем в переменную hight_temp_ddm
            hight_temp_ddm = self.textEdit_24.toPlainText().strip(' ')
            if int(hight_temp_ddm) > 40:
                # Вызываем у экземпляра класса window атрибут hight_temp_ddm и задаем ему значение порога высокой темп-ры ddm
                self.window.hight_temp_fiber = int(hight_temp_ddm)
                # Очищаем поле textBrowser_23
                self.textBrowser_23.clear()
                # Выводим введенное значение порога высокой температуры DDM
                self.textBrowser_23.append(str(self.window.hight_temp_fiber))
                # Выравниваем значение по центру
                self.textBrowser_23.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_24.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_temp_hight_ddm.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_temp_hight_ddm.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_24.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_monitor_power_sign_btn "Порог низкого уровня сигнала DDM MonitoringAlarm"
    def set_signal_low_ddm_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем что значение меньше -15
            if int(self.textEdit_21.toPlainText().strip(' ')) < -15:
                # Вызываем у экземпляра класса monitoring_alarms атрибут self.signal_level_fiber и задаем ему значение порога уровня сигнала 
                self.monitoring_alarms.signal_level_fiber= int(self.textEdit_21.toPlainText().strip(' '))
                # Очищаем поле textBrowser_9
                self.textBrowser_9.clear()
                # Выводим введенное значение порога уровня сигнала
                self.textBrowser_9.append(str(self.monitoring_alarms.signal_level_fiber))
                # Выравниваем значение по центру
                self.textBrowser_9.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_21.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_signal_low_ddm.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_signal_low_ddm.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_21.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_monitor_low_temp_ddm_btn "Порог низкой температуры DDM MonitoringAlarm"
    def set_temp_low_ddm_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем что значение меньше 10
            if int(self.textEdit_22.toPlainText().strip(' ')) < 10:
                # Вызываем у экземпляра класса monitoring_alarms атрибут low_temp_fiber и задаем ему значение порога низкой температуры 
                self.monitoring_alarms.low_temp_fiber= int(self.textEdit_22.toPlainText().strip(' '))
                # Очищаем поле textBrowser_19
                self.textBrowser_19.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_19.append(str(self.monitoring_alarms.low_temp_fiber))
                # Выравниваем значение по центру
                self.textBrowser_19.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_22.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_temp_low_ddm.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_temp_low_ddm.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_22.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    # Метод обрабатывает нажатие кнопки Set_monitor_high_temp_ddm_btn "Порог высокой температуры DDM MonitoringAlarm"
    def set_temp_hight_ddm_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем что значение больше 30
            if int(self.textEdit_23.toPlainText().strip(' ')) > 30:
                # Вызываем у экземпляра класса monitoring_alarms атрибут hight_temp_fiber и задаем ему значение порога высокой температуры 
                self.monitoring_alarms.hight_temp_fiber= int(self.textEdit_23.toPlainText().strip(' '))
                # Очищаем поле textBrowser_20
                self.textBrowser_20.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_20.append(str(self.monitoring_alarms.hight_temp_fiber))
                # Выравниваем значение по центру
                self.textBrowser_20.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_23.clear()
            else:
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.inf_temp_hight_ddm.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение уровня сигнала не может быть больше -20dBm
                self.inf_temp_hight_ddm.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_23.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()
    
    # Метод обрабатывает нажатие кнопки Set_monitor_count_btn "Количество итераций цикла перед отправкой сообщения MonitoringAlarm"
    def set_count_check_monitor_btn(self):
        try:
            # Получаем значение которое ввел пользователь, переводим в число и проверяем что значение больше 30
            if int(self.textEdit_27.toPlainText().strip(' ')) < 10:
                # Вызываем у экземпляра класса monitoring_alarms атрибут count и задаем ему значение  
                self.monitoring_alarms.num= int(self.textEdit_27.toPlainText().strip(' '))
                # Очищаем поле textBrowser_25
                self.textBrowser_25.clear()
                # Выводим введенное значение порога низкой температуры
                self.textBrowser_25.append(str(self.monitoring_alarms.num))
                # Выравниваем значение по центру
                self.textBrowser_25.setAlignment(QtCore.Qt.AlignCenter)
                # Очищаем поле для ввода текста
                self.textEdit_27.clear()
            else:
                pass
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                #self.err_monitor_alarm_low_volt.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Вызываем диалоговое окно с ошибкой, что значение низкого напряжения не может быть больше 50
                #self.err_monitor_alarm_low_volt.exec_()
        # Если попали в исключение, то выводим диалоговое окно, о том что не корректно введены данные
        except ValueError:
            # Очищаем поле для ввода текста
            self.textEdit_27.clear()
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой
            self.err_value.exec_()

    def set_font_size_curent_alarm_window(self):
        # Получаем значение которое ввел пользователь и записываем в переменную font_size_alarm
        font_size_alarm = self.textEdit_32.toPlainText().strip(' ')
        # Переводим полученное значение в число
        int(font_size_alarm)
        # Проверяем если используется Стиль_1 то меняем только размер ширифта, остальные настройки стиля оставляем без изменений
        if self.isStyle_1:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window.textBrowser_6.setStyleSheet(self.style_1.format(font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_1.format(font_size_alarm))
        elif self.isStyle_2:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window.textBrowser_6.setStyleSheet(self.style_2.format(font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_2.format(font_size_alarm))
        elif self.isStyle_3:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window.textBrowser_6.setStyleSheet(self.style_3.format(font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_3.format(font_size_alarm))
        # Иначе, у нас установлен стиль по умолчанию 
        else:
            # Вызываем у экземпляра класса window атрибут textBrowser_6 у которого вызываем метод setStyleSheet
            # который устанавливает стиль окна textBrowser_6 передаем ему настройки стиля ширифта ввиде строки
            self.window.textBrowser_6.setStyleSheet(self.style_default.format(font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_default.format(font_size_alarm))
        # Вызываем у экземпляра класса window атрибут font_size_alarm и задаем ему значение размера ширифта
        self.window.font_size_alarm = font_size_alarm
        # Очищаем поле от предыдущего значения
        self.textBrowser_18.clear()
        # Выводим полученное значение размера ширифта
        self.textBrowser_18.append(self.window.font_size_alarm)
        # Выравниваем значение по центру
        self.textBrowser_18.setAlignment(QtCore.Qt.AlignCenter)
        # Очищаем поле для ввода текста
        self.textEdit_32.clear()
    
    # Метод устанавливает размер ширифта текста в окне SecondWindows вкладка All devices с учетом выбранного стиля          
    def set_font_size_text(self):
        try:
            # Проверяем, если получили данные от пользователя
            if self.textEdit_17.toPlainText().strip():
                # Получаем значение которое ввел пользователь преобразуем в число и записываем в переменную font_size_frame1
                font_size_frame1 = int(self.textEdit_17.toPlainText().strip())
                # Проверяем если пользователь установил стиль окна Style_1, тогда
                if self.isStyle_1:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_4.setStyleSheet(self.style_1.format(font_size_frame1))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_2 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_4.setStyleSheet(self.style_2.format(font_size_frame1))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_3 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_4.setStyleSheet(self.style_3.format(font_size_frame1))
                # Иначе если у нас не установлен ни один из стилей т.е. выбран стиль по умолчанию
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window.textBrowser_4.setStyleSheet(self.style_default.format(font_size_frame1))
                # Очищаем поле для ввода текста
                self.textEdit_17.clear()
                # Вызываем у экземпляра класса window атрибут font_size и задаем ему значение размера ширифта
                self.window.font_size_frame1 = font_size_frame1
            # Проверяем, если получили данные от пользователя
            if self.textEdit_28.toPlainText().strip():
                # Преобразуем полученное значение в число и записываем значение в переменную
                font_size_frame2 = int(self.textEdit_28.toPlainText().strip())
                # Проверяем если установлен стиль окна isStyle_1
                if self.isStyle_1:
                    # Применяем настройки стиля self.style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_2.setStyleSheet(self.style_1.format(font_size_frame2))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_2.setStyleSheet(self.style_2.format(font_size_frame2))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_2.setStyleSheet(self.style_3.format(font_size_frame2))
                # Иначе если у нас не установлен ни один из стилей то
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window.textBrowser_2.setStyleSheet(self.style_default.format(font_size_frame2))
                # Очищаем поле для ввода текста
                self.textEdit_28.clear()
                # Вызываем у экземпляра класса window атрибут font_size_frame2 и задаем ему значение размера ширифта
                self.window.font_size_frame2 = font_size_frame2
            # Проверяем, если получили данные от пользователя
            if self.textEdit_29.toPlainText().strip():
                # Преобразуем полученное значение в число и записываем в переменную
                font_size_frame3 = int(self.textEdit_29.toPlainText().strip(' '))
                # Проверяем если установлен стиль окна isStyle_1
                if self.isStyle_1:
                    # Применяем настройки стиля self.style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser.setStyleSheet(self.style_1.format(font_size_frame3))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser.setStyleSheet(self.style_2.format(font_size_frame3))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser.setStyleSheet(self.style_3.format(font_size_frame3))
                # Иначе если у нас не установлен ни один из стилей то
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window.textBrowser.setStyleSheet(self.style_default.format(font_size_frame3))
                # Очищаем поле для ввода текста
                self.textEdit_29.clear()
                # Вызываем у экземпляра класса window атрибут font_size_frame3 и задаем ему значение размера ширифта
                self.window.font_size_frame3 = font_size_frame3
            # Проверяем, если получили данные от пользователя
            if self.textEdit_30.toPlainText().strip():
                # Преобразуем полученное значение в число
                font_size_frame4 = int(self.textEdit_30.toPlainText().strip())
                # Проверяем если установлен стиль окна isStyle_1
                if self.isStyle_1:
                    # Применяем настройки стиля self.style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_3.setStyleSheet(self.style_1.format(font_size_frame4))
                elif self.isStyle_2:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_3.setStyleSheet(self.style_2.format(font_size_frame4))
                elif self.isStyle_3:
                    # Применяем настройки стиля style_1 подставив размер ширифта тот который установил пользователь
                    self.window.textBrowser_3.setStyleSheet(self.style_3.format(font_size_frame4))
                # Иначе если у нас не установлен ни один из стилей то
                else:
                    # Устанавливаем размер ширифта с дефолтными настройками стиля окна.
                    self.window.textBrowser_3.setStyleSheet(self.style_default.format(font_size_frame3))
                # Очищаем поле для ввода текста
                self.textEdit_30.clear()
                # Вызываем у экземпляра класса window атрибут font_size_frame4 и задаем ему значение размера ширифта
                self.window.font_size_frame4 = font_size_frame4
            # Очищаем поле textBrowser_14
            self.textBrowser_14.clear()
            # Выводим введенное значение размера ширифта в окно textBrowser_14
            self.textBrowser_14.append(f"{self.window.font_size_frame1}/{self.window.font_size_frame2}/{self.window.font_size_frame3}/{self.window.font_size_frame4}")  
            # Выравниваем значение по центру
            self.textBrowser_14.setAlignment(QtCore.Qt.AlignCenter)  
        except ValueError:
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_value.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Вызываем диалоговое окно с ошибкой что введено не допустимое значение
            self.err_value.exec_()

    def set_style_window(self):
        # Обращаемся к селектору comboBox и получаем значение которое выбрал пользователь
        style_sheet = self.comboBox_3.currentText()
        # Если выбран первый вариант стиля
        if style_sheet == 'Стиль_1':
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки All info 
            self.window.textBrowser_4.setStyleSheet(self.style_1.format(self.window.font_size_frame1))
            self.window.textBrowser_2.setStyleSheet(self.style_1.format(self.window.font_size_frame2))
            self.window.textBrowser.setStyleSheet(self.style_1.format(self.window.font_size_frame3))
            self.window.textBrowser_3.setStyleSheet(self.style_1.format(self.window.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window.textBrowser_6.setStyleSheet(self.style_1.format(self.window.font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_1.format(self.window.font_size_alarm))
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
            self.window.textBrowser_4.setStyleSheet(self.style_2.format(self.window.font_size_frame1))
            self.window.textBrowser_2.setStyleSheet(self.style_2.format(self.window.font_size_frame2))
            self.window.textBrowser.setStyleSheet(self.style_2.format(self.window.font_size_frame3))
            self.window.textBrowser_3.setStyleSheet(self.style_2.format(self.window.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window.textBrowser_6.setStyleSheet(self.style_2.format(self.window.font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_2.format(self.window.font_size_alarm))
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
            self.window.textBrowser_4.setStyleSheet(self.style_3.format(self.window.font_size_frame1))
            self.window.textBrowser_2.setStyleSheet(self.style_3.format(self.window.font_size_frame2))
            self.window.textBrowser.setStyleSheet(self.style_3.format(self.window.font_size_frame3))
            self.window.textBrowser_3.setStyleSheet(self.style_3.format(self.window.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window.textBrowser_6.setStyleSheet(self.style_3.format(self.window.font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_3.format(self.window.font_size_alarm))
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
            self.window.textBrowser_4.setStyleSheet(self.style_default.format(self.window.font_size_frame1))
            self.window.textBrowser_2.setStyleSheet(self.style_default.format(self.window.font_size_frame2))
            self.window.textBrowser.setStyleSheet(self.style_default.format(self.window.font_size_frame3))
            self.window.textBrowser_3.setStyleSheet(self.style_default.format(self.window.font_size_frame4))
            # Обращаемся к объекту textBrowser и выставляем для каждого из фреймов стиль для вкладки Curent Alarm
            self.window.textBrowser_6.setStyleSheet(self.style_default.format(self.window.font_size_alarm))
            self.window.textBrowser_5.setStyleSheet(self.style_default.format(self.window.font_size_alarm))
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
       
    # Метод обрабатывает нажатие кнопки Run bot
    def button_pressed_run_bot(self):
        # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
        self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_progress))
        # Получаем токен введенный пользователем в поле textEdit и записываем в переменную token
        token = self.textEdit_6.toPlainText()
        # Вызываем атрибут(переменную) token у экземпляра класса monitoring_alarms, класса ThreadMonitorAlarms и присваиваем ей
        # полученное значение переменной  token, token нужен для работы метода send_messages
        self.monitoring_alarms.token = token
        try:
            # Создаем экземпляр класса ThreadTelegramBot, передаем token и экземпляр line, класса Queue( обработчик очередей)
            self.bot = ThreadTelegramBot(token, self.line)
            # Запускаем чат Бот в отдельном потоке вызвав у экземпляра класса bot метод start
            self.bot.start()
            # Запускаем экземпляр класса timer_start_bot вызвав у него метод start, который в свою очередь запускает check_update_start_bot
            self.timer_start_bot.start()
        except (error.InvalidToken, error.Unauthorized) as err:
            # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
            # указать дополнительную информацию об ошибке
            self.err_token_bot.setDetailedText(f"Проверьте корректно ли введен токен для подключения к чат Боту \n'{err}") 
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_token_bot.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
            self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
            self.err_token_bot.exec_()
        
    # Метод делает проверку, обрабатывает исключения при запуске чат Бота.
    def check_update_start_bot(self):
        try:
            '''
            Далее делаем запрос вызвав у экземпляра line класса Queue метод get, который удаляет и 
            возвращает элемент из очереди. Полученный результат из запроса преобразуем в строку и записываем
            в переменную  exception
            параметры: block=True - говорит заблокируй до тех пор пока элемент из очереди не станет доступен, 
            а timeout - говорит, если в течении указанного времени секунд мы не получили элемент, то сгенирируется исключение Emty
            block=false - элемент вернется сразу если он доступен или сгенерируется исключение Emty (timeout - игнорируется)
            '''
            exception = str(self.line.get(block=True)[-3])
            # Проверяем если в переменной exception содержатся исключения Unauthorized или InvalidToken
            if 'Unauthorized' in exception or 'InvalidToken' in exception:
                # Останавливаем работу потока класса ThreadTelegramBot
                self.bot.terminate()
                # Останавливаем экземпляр класса timer_start_bot вызвав у него метод stop
                self.timer_start_bot.stop()
                # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
                # указать дополнительную информацию об ошибке
                self.err_token_bot.setDetailedText(f"Проверьте корректно ли введен токен для подключения к чат Боту \n'{exception}")
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_token_bot.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
                self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
                self.err_token_bot.exec_()
            # Проверяем если в переменной exception содержатся исключения NetworkError или TimedOut
            elif 'NetworkError' in exception or 'TimedOut' in exception:
                # Останавливаем работу потока класса ThreadTelegramBot
                self.bot.terminate()
                # Останавливаем экземпляр класса timer_start_bot вызвав у него метод stop
                self.timer_start_bot.stop()
                # Вызываем у экземпляра класса QMessageBox() метод setDetailedText, который задает раскрывающийся текст в котором можно 
                # указать дополнительную информацию об ошибке
                self.err_network_bot.setDetailedText(f"Проверьте доступ к интернету\n' {exception}")
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.err_network_bot.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
                self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с ошибкой.
                self.err_network_bot.exec_()
            # Проверяем запущен ли чат Бот, вызывам метод is_running у экземпляра класса bot
            elif self.bot.is_running():
                # Останавливаем экземпляр класса timer_start_bot вызвав у него метод stop
                self.timer_start_bot.stop()
                # Активируем кнопку Stop
                self.Stop_bot_btn.setEnabled(True)
                # Очищаем поле ввода textEdit
                self.textEdit_6.clear()
                # Задаем сдвиг диалогового окна относительно основного окна приложения
                self.info_done.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
                # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
                self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_done))
                # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно с уведомлением о запуске Бота
                self.info_done.exec_()
        except Empty:
            pass       

    # Метод обрабатывает нажатие кнопки Stop останавливает работу чат Бота
    def button_pressed_stop_bot(self):
        # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
        self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_progress))
        # Останавливаем работу чат Бота вызввам метод disconnect
        self.bot.disconnect()
        # Запускаем экземпляр класса timer_stop_bot вызвав у него метод start
        self.timer_stop_bot.start()

    # Метод делает проверку, что работа чат Бота остановлена
    def check_update_stop_bot(self):
        # Если updater завершен, значит False
        if not self.bot.is_running():
            # Деактивируем кнопку Stop
            self.Stop_bot_btn.setEnabled(False)
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.info_done.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            # Добавляем в статус бар экземпляр класса bot_lbl текст с изображением, вызвав метод setText
            self.bot_lbl.setText('<img src="{}">  TelegramBot'.format(self.path_icon_not_runn))
            # Вызываем у экземпляра класса QMessageBox() метод exec_(), который вызывает диалоговое окно 
            self.info_done.exec_()
            # Останавливаем поток
            self.bot.terminate()
            # Останавливаем экземпляр класса timer_stop_bot вызвав у него метод stop
            self.timer_stop_bot.stop()
    
    # Метод открывает второе окно у приложения 
    def show_second_window(self):
        # Проверяем, если кнопка Stop_snmp_btn активна, значит SNMP опросчик запущен
        if self.Stop_snmp_btn.isEnabled():
            # Создаем экземпляр класса window и вызываем у него метод show, который открываем второе окно
            self.window.show()
            # У экземпляра класса вызываем метод start, который запускает оброботчик сообщений, который будет выводить значения на второй экран
            self.window.start()
            # Деактивируем кнопку Open
            self.Open_window_button.setEnabled(False)
        # Иначе выводим уведомление о том что SNMP не запущен
        else:
            time.sleep(0.5)
            # Задаем сдвиг диалогового окна относительно основного окна приложения
            self.err_run_snmp.move((self.position_main_window[0] + self.X), (self.position_main_window[1] + self.Y))
            self.err_run_snmp.exec_()

    # Метод проверяет что пользователь ввел корректно ip адрес
    def _check_ip_address(self, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    # Метод получает координаты расположения окна Приложения на экране.
    def _get_position_window(self):
        # Получаем координаты окна в виде кортежа, записываем в переменную position_main_window
        self.position_main_window = self.frameGeometry().getRect()

    # Функция останавливает работу запущенного процесса exe
    def _stop_process(self, proc_pid) -> bool:
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
            pass


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

