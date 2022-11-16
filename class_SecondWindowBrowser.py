#
import logging
import re
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from SecondWindow import Ui_MainWindow
from PyQt5.QtCore import QThread, Qt 
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QLabel, QMessageBox
from class_SqlLiteMain import ConnectSqlDB
from class_WindPlaySound import WindPlaySound
from class_ApplicationWidget import AplicationWidget

class SecondWindowBrowser(QtWidgets.QMainWindow, Ui_MainWindow, QThread, AplicationWidget):
    def __init__(self):
        # Настройка логирования
        path_logs = Path(Path.cwd(), "logs", "logs_second_window.txt")
        self.logger = logging.getLogger('second_window')
        self.logger.setLevel(logging.INFO)
        fh_logs = logging.FileHandler(path_logs, 'w')
        formatter_logs = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_logs.setFormatter(formatter_logs)
        self.logger.addHandler(fh_logs)

        super().__init__()
        #QThread.__init__(self)
        # Вызываем метод setupUi, в котором настроены все наши виджеты (кнопки, поля и т.д.)
        self.setupUi(self)
        # Создаем переменные в которых записываем путь к файлам
        self.path_icon_second_window = str(Path(Path.cwd(), "Resources", "Icons", "icn61.ico"))
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_error = str(Path(Path.cwd(), "Resources", "Icons", "icn23.ico"))
        self.path_icon_load = str(Path(Path.cwd(), "Resources", "Icons", "icn8.ico"))
        self.path_icon_time = str(Path(Path.cwd(), "Resources", "Icons", "icn18.ico"))
        self.path_icon_done = str(Path(Path.cwd(), "Resources", "Icons", "icn15.ico"))
        self.path_icon_progress = str(Path(Path.cwd(), "Resources", "Icons", "icn16.ico"))
        self.path_icon_critical = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        
        # Переменная определяет интервал между запросами
        self.interval_time = 1
        # Переменная порог высокой температуры
        self.hight_temp = 35
        # Переменная порог низкой температуры
        self.low_temp = 0
        # Порог низкого уровня топлива
        self.low_oil_limit = 35
        # Порог высокого напряжения
        self.hight_voltage = 245
        # Порог низкого напряжения
        self.low_voltage = 48.0
        # Записываем дефолтное(начальное) значение уровня сигнала Fiber транспондера MAC&C
         # Записываем дефолтное(начальное) значение уровня сигнала Fiber транспондера MAC&C
        self.signal_level_fiber = -22
        # Записываем дефолтное(начальное) значение низкой температуры Fiber транспондера MAC&C
        self.low_temp_fiber = 5
        # Записываем дефолтное(начальное) значение высокой температуры Fiber транспондера MAC&C
        self.hight_temp_fiber = 50
        # Размер ширифта
        self.font_size_frame1 = self.textBrowser_4.styleSheet().split()[-2].rstrip('pt')
        # Получаем стили ширифта примененные для окна textBrowser_2, получаем значение размера ширифта и записываем в переменную
        self.font_size_frame2 = self.textBrowser_2.styleSheet().split()[-2].rstrip('pt')
        # Получаем стили ширифта примененные для окна textBrowser_3, получаем значение размера ширифта и записываем в переменную
        self.font_size_frame3 = self.textBrowser.styleSheet().split()[-2].rstrip('pt')
        # Получаем стили ширифта примененные для окна textBrowser_4, получаем значение размера ширифта и записываем в переменную
        self.font_size_frame4 = self.textBrowser_3.styleSheet().split()[-2].rstrip('pt')
        # Получаем стили ширифта примененные для окна textBrowser_6, получаем значение размера ширифта и записываем в переменную
        self.font_size_alarm = self.textBrowser_6.styleSheet().split()[-2].rstrip('pt')
        # Создаем переменную в которую записываем значение размера шрифта текста сообщения диалогового окна, значение присваивается из класса Application
        # по умолчанию не установлено
        self.font_size_message_alarm = None 
        # Количество подтверждений аварии перед тем как она отобразится
        self.num = 2
    
        # Создаем экзепляр класса WindPlaySound
        self.play_sound = WindPlaySound()
        # Создаем экземпляр классса Таймер запуска метода run
        self.timer = QtCore.QTimer(self)
        # Таймер запуска часов
        self.timer_clock = QtCore.QTimer(self)
        # Задаем интервал запуска timer(обновления)
        self.timer.setInterval(self.interval_time*1000)
        self.timer_clock.setInterval(1000)
        # Определяем какую функцию будет запускать Таймер через указанный промежуток времени
        self.timer.timeout.connect(self.run)
        self.timer_clock.timeout.connect(self.show_clock)

        # Флаг определяет закрыто или открыто второе окно
        self.isClose_window = False
        # Флаг определяет состояние воспроизведения мелодии
        self.isPlaySoundOff = True
        # Создаем переменную в котрую добавляем ключ IP адрес и значение строка с параметрами устройства
        self.dict_set = {}
        #
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД и получаем словарь с данными (дата и время возникновения аварий)
            try:
                self.date_alarm = sql.get_values_list_db('data', table='Duration')
            except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
                self.logger.error("Ошибка запроса из БД: sql.get_values_list_db('data', table='Duration')" )
                # Если попали в исключения значит мы не смогли считать данные, подставляем готовый словарь
                self.date_alarm =  {'power_alarm':{},
                                    'low_voltage':{},
                                    'hight_voltage':{},
                                    'low_oil':{},
                                    'motor': {},
                                    'level_water': {},
                                    'low_pressure_oil': {},
                                    'low_temp_water': {},
                                    'hi_temp_water': {},
                                    'hight_temp':{},
                                    'low_temp':{},
                                    'low_signal_power':{},
                                    'request_err':{},
                                    }
        #                      
        self.dict_interim_messages = {'power_alarm':{},
                                    'low_voltage':{},
                                    'hight_voltage':{},
                                    'low_oil':{},
                                    'motor': {},
                                    'level_water': {},
                                    'low_pressure_oil': {},
                                    'low_temp_water': {},
                                    'hi_temp_water': {},
                                    'hight_temp':{},
                                    'low_temp':{},
                                    'low_signal_power':{},
                                    'request_err':{},
                                    }

        # Словарь для хранения ip адресов устройств для которых воспроизводилась мелодия. 
        self.dic_alarm_sound = {'power_alarm': {},
                                'low_voltage': {},
                                'low_signal_power': {},
                                'hight_temp': {},
                                'motor': {},
                                'level_water': {},
                                'low_pressure_oil': {},
                                'low_temp_water': {},
                                'hi_temp_water': {},
                                'low_oil': {},
                                'request_err': {},
                                'hight_voltage':{},
                                'low_temp':{},
                                }
        # Словарь для хранения информации ip адресов устройств для которых выводилось диалоговое окно.
        self.dic_massege_box = {'power_alarm': {},
                                'low_voltage': {},
                                'low_signal_power': {},
                                'hight_temp': {},
                                'motor': {},
                                'level_water': {},
                                'low_pressure_oil': {},
                                'low_temp_water': {},
                                'hi_temp_water': {},
                                'low_oil': {},
                                'request_err': {},
                                'hight_voltage':{},
                                'low_temp':{},
                                }
        # Переменная список куда записываем результат опроса snmp
        self.snmp_traps = []

     # СОЗДАЕМ ЭКЗЕМПЛЯР КЛАССА QIcon, ДОБАВЛЕНИЕ ИЗОБРАЖЕНИЯ ДЛЯ MAIN WINDOW
        # Создаем экземпляр класса icon_second_window, класс QIcon - отвечает за добавления иконки с изображением для основного окна программы
        icon_second_window = QtGui.QIcon()
        # Вызываем у экземпляра класса icon_second_window метод addFile, указываем путь где находится изображение
        icon_second_window.addFile(self.path_icon_second_window)
        # У QMainWindow вызываем метод setWindowIcon, которому передаем экземпляр класса нашего второго окна self и экземпляр класса icon_second_window в котором содержится изображение
        QtWidgets.QMainWindow.setWindowIcon(self, icon_second_window)

        # Создаем экземпляр класса  QLable Выводим сообщение в статус бар со статусом загрузки
        self.lbl = QLabel()
        # Добавляем стиль к экземпляру класса
        self.lbl.setStyleSheet("border-left: 3px solid;")
        # Делаем выравнивание по левому краю нашей иконки с изображением
        self.lbl.setAlignment(QtCore.Qt.AlignLeft)
        # Добавляем в статус бар наш экземпляр класса lbl
        #self.lbl.setText("<img src={}>  Выполняется загрузка...".format(self.path_icon_load))
        # Выводим Надпись с изображением в статус Бар
        self.statusbar.addWidget(self.lbl)
        
        # Создаем экземпляр класса QLable Выводим сообщение в статус бар с датой и временем
        self.lbl_clock = QLabel()
        # Добавляем стиль к экземпляру класса
        #self.lbl_clock.setStyleSheet("border-right: 3px solid; font-size: 36px")
        # Выравниваем по правому краю
        #self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        # Получаем дату и время в нужной нам форме
        date = datetime.today().strftime('%H:%M:%S %d-%m-%Y')
        # Добавляем изображение и дату и время в экземпляр класса lbl_clock
        self.lbl_clock.setText('<img src="{}" width="20" height="20"> <strong>{}</strong>'.format(self.path_icon_time, date))
        # Добавляем в статус бар наш экземпляр класса lbl_clock
        self.statusbar.addPermanentWidget(self.lbl_clock)
        # Кнопка отключения мелодии звука
        self.switch_off_sound_btn.pressed.connect(self._presse_button_confirm_all_alarms)

        # ДОБАВЛЕНИЕ ИКОНКИ К КНОПКЕ
        self.switch_off_sound_btn.setIcon(self.icon_sound_stop)
        
        # Создаем экземпляр класса QScrollBar, который позволит обратиться к  вертикальной полосе прокрутки Окна №1,2,3,4 textBrowser
        self.vertScrollBarWind2 = self.textBrowser.verticalScrollBar()
        self.vertScrollBarWind1 = self.textBrowser_3.verticalScrollBar()
        self.vertScrollBarWind3 = self.textBrowser_2.verticalScrollBar()
        self.vertScrollBarWind4 = self.textBrowser_4.verticalScrollBar()
        self.vertScrollBarWind5 = self.textBrowser_5.verticalScrollBar()
        self.vertScrollBarWind6 = self.textBrowser_6.verticalScrollBar()
        # При наведении курсора мыши на полосу прокрутки будет появляться значек руки
        self.vertScrollBarWind2.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind1.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind3.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind4.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind5.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind6.setCursor(Qt.OpenHandCursor)
        # actionTriggered вызывается когда полоса прокрутки изменяется в результате взаимодействия с пользователем
        # прикрепляем к нему метод scroll, который будет вызываться при каждой сработке триггера. 
        self.vertScrollBarWind1.actionTriggered.connect(self.scroll_wind_1)
        self.vertScrollBarWind2.actionTriggered.connect(self.scroll_wind_2)
        self.vertScrollBarWind3.actionTriggered.connect(self.scroll_wind_3)
        self.vertScrollBarWind4.actionTriggered.connect(self.scroll_wind_4)
        self.vertScrollBarWind5.actionTriggered.connect(self.scroll_wind_5)
        self.vertScrollBarWind6.actionTriggered.connect(self.scroll_wind_6)
        # Устанавливаем первоначальное положение ползунка в верхнее положение для всех окон
        self.position_scroll_wind1 = 0
        self.position_scroll_wind2 = 0
        self.position_scroll_wind3 = 0
        self.position_scroll_wind4 = 0
        self.position_scroll_wind5 = 0
        self.position_scroll_wind6 = 0
        
    # Метод обрабатывает нажатие кнопок "ОК" в диалоговом окне, останавливает воспроизведение мелодии
    def click_btn(self, btn):
        # Удаление пользователя
        if btn.text() == 'OK':
            # Вызываем метод который подтверждает аврию.
            self._press_button_confirm_alarm()

    # Метод получает имя устройства, которое соответствует ip адресу переданному на вход
    def _dns(self, ip):
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, получаем описание Ip адреса
            host_name = sql.get_db('description', ip=ip, table='Devices')[0]
        return host_name

    # Метод получает номер окна из БД
    def _get_num_window(self, ip):
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, получаем номер окна куда выводить аврию
            window_number= sql.get_db('num_window', ip=ip, table='Devices')[0]
        return window_number
    
    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №1
    def scroll_wind_1(self):
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind1.setSingleStep(25)
        # Определяем значение положение полосы прокрутки scroll
        self.position_scroll_wind1 = self.vertScrollBarWind1.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind1.setSliderPosition(self.position_scroll_wind1)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №2
    def scroll_wind_2(self):
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind2.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind2 = self.vertScrollBarWind2.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind2.setSliderPosition(self.position_scroll_wind2)
    
    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №3
    def scroll_wind_3(self):
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind3.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind3 = self.vertScrollBarWind3.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind3.setSliderPosition(self.position_scroll_wind3)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №4
    def scroll_wind_4(self):
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind4.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind4 = self.vertScrollBarWind4.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind4.setSliderPosition(self.position_scroll_wind4)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем во вкладке "Текущие аварии"
    def scroll_wind_5(self):
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind5.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind5 = self.vertScrollBarWind5.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind5.setSliderPosition(self.position_scroll_wind5)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем во вкладке "Текущие аварии"
    def scroll_wind_6(self):
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind6.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind6 = self.vertScrollBarWind6.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind6.setSliderPosition(self.position_scroll_wind6)

    @QtCore.pyqtSlot(int)
    # Метод выводит строки сообщения в одно из окон во вкладке Общая информация 
    def _show_message_on_window(self, num_window, message):
        if num_window == 1:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_3.append(message)
            # Устанавливаем положение ползунка полосы прокрутки ScrollBar
            #self.textBrowser_3.verticalScrollBar().setSliderPosition(self.position_scroll_wind1)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind1.setSliderPosition(self.position_scroll_wind1)
        elif num_window == 2:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser.append(message)
            # Устанавливаем положение ползунка полосы прокрутки ScrollBar
            #self.textBrowser.verticalScrollBar().setSliderPosition(self.position_scroll_wind2)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind2.setSliderPosition(self.position_scroll_wind2)
        elif num_window == 3:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_2.append(message)
            # Устанавливаем положение ползунка полосы прокрутки ScrollBar
            #self.textBrowser_2.verticalScrollBar().setSliderPosition(self.position_scroll_wind3)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind3.setSliderPosition(self.position_scroll_wind3)
        elif num_window == 4:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_4.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind4.setSliderPosition(self.position_scroll_wind4)
        else:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_4.append(message) 
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind4.setSliderPosition(self.position_scroll_wind4)
    
    # Метод выводит строки сообщения в окно во вкладке Текущие аварии
    def _show_message_in_window_current_alarm(self, message):
        # Получаем количество записей в textBrowser_6
        size = self.textBrowser_6.document().size().toSize().height() # -> int
        # Получаем высоту окна textBrowser_6
        geometry = self.textBrowser_6.geometry().height() # -> int
        # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
        if (size + 40) < geometry:
            # Выводим значение на экран в первый столбец
            self.textBrowser_6.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind6.setSliderPosition(self.position_scroll_wind6)
        else:
            # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец
            self.textBrowser_5.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind5.setSliderPosition(self.position_scroll_wind5)

    # Метод получает значение ip адреса устройства
    def _parse_ip(self, line):
        try:
            ip = line.split()[2].strip()
            return ip
        except IndexError:
            pass
    
    # Метод преобразует полученное время в секундах в дни, часы, минуты, секунды
    def _convert_time(self, sec):
        # Вычисляем количество дней
        day = int(sec // (24 * 3600))
        # Если количество дней не равно 0
        if day:
            # Вычисляем остаток от количества дней(часы)
            sec %= (24 * 3600)
            # Вычисляем количество часов
            hour = int(sec // 3600)
            if len(str(hour)) == 1:
                hour = f'0{str(hour)}'
            # Вычисляем остаток от количества часов(мин)
            sec %= 3600
            # Вычисляем количество минут
            minu = int(sec//60)
            if len(str(minu)) == 1:
                minu = f'0{str(minu)}'
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'{day}д. {hour}:{minu}:{int(sec)}'
        # Вычисляем количество часов
        hour = int(sec // 3600)
        # Если количество часов не равно 0
        if hour:
            if len(str(hour)) == 1:
                hour = f'0{str(hour)}'
            # Вычисляем остаток от количества часов(мин)
            sec %= 3600
            # Вычисляем количество минут
            minu = int(sec//60)
            if len(str(minu)) == 1:
                minu = f'0{str(minu)}'
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'{hour}:{minu}:{int(sec)}'
        # Вычисляем количество минут
        minu = int(sec//60)
        if minu:
            if len(str(minu)) == 1:
                minu = f'0{str(minu)}'
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'00:{minu}:{int(sec)}'
        else:
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'00:00:{int(sec)}'
    
    # Метод получает дату и время и возвращает значение в нужном формате
    def _get_date_time(self):
        # Получаем кортеж с датой, временем и т.д.
        date_tuple = time.localtime()
        # Преобразуем дату и время в нужный нам формат
        date = time.strftime('%d-%m-%Y %H:%M:%S', date_tuple)
        return date
    
    # Метод получает дату и время возникновения аварии добавляет значение в словарь date_alarm
    def _get_alarm_date_time(self, ip, key=None) -> str:
        # Получаем текущую дату и время возникновения аварии, вызвав метод _get_date_time.  
        date_time = self._get_date_time()
        try:
            # Проверяем, если из словаря date_alarm по ключам ip и date_time мы не получили значение даты и времени
            # значит значение даты и времени возникновения аврии не добавленно в словарь
            if not self.date_alarm[key][ip].get('date_time'):
                # Добавляем дату и время возниконовения аварии  и стартовое время начла аврии в словарь date_alarm
                self.date_alarm[key][ip]= {'date_time': date_time, 'start_time': time.time()}
        # Если мы попали в исключение, значит в словаре date_alarm нет ключа с таким ip
        except KeyError:
            # Добавляем дату и время возниконовения аварии  и стартовое время начла аврии в словарь date_alarm
            self.date_alarm[key][ip]= {'date_time':date_time, 'start_time': time.time()}
        # Возвращаем дату и время возникновения аврии из словаря
        return self.date_alarm[key][ip].get('date_time')

    # Метод получает значение ошибки
    def _parse_erro(self, line) -> str:
        match = re.match(r'.+(?P<error>SNMP.+)', line)
        if match:
            error = match.group('error').strip()
            return error

    # Метод получает значение входного напряжения ИБЭП
    def _parse_voltage_in(self, line) -> str:
        match = re.match(r'.+IN: *(?P<voltage>\d+)', line)
        if match:
            voltage_in = match.group('voltage').strip()
            return voltage_in

    # Метод получает значение выходного напряжения ИБЭП
    def _parse_voltage_out(self, line) -> str:
        match = re.match(r'.+OUT: *(?P<voltage>\d+\.*\d*)', line)
        if match:
            voltage_out = match.group('voltage').strip()
            return voltage_out

    # Метод получает значение температуры ИБЭП
    def _parse_temperature(self, line) -> str:
        match = re.match(r'.+\*C: *(?P<temp_value>-*\d+)', line)
        if match:
            temperature_value = match.group('temp_value').strip()
            return temperature_value

    # Метод возвращает числовое значение количества топлива АВТОБУС
    def _parse_low_oil(self, line) -> int:
        match = re.match(r'.+Топл\.:(?P<low_oil>\d+)%', line)
        if match:
            low_oil = match.group('low_oil').strip()
            return int(low_oil)
    
    # Метод получает значение Высокой температуры О/Ж (0 или 1) ДГУ
    def _parse_hi_temp_water(self, line) -> int:
        match = re.match(r'.+Выс\.Темп_О/Ж:\[(?P<hi_temp_water>\d*)\]', line)
        if match:
            hi_temp_water = match.group('hi_temp_water').strip()
            return int(hi_temp_water)
    
    # Метод получает значение Низкой температуры О/Ж (0 или 1) ДГУ
    def _parse_low_temp_water(self, line) -> int:
        match = re.match(r'.+Низ\.Темп_О/Ж:\[(?P<low_temp_water>\d*)\]', line)
        if match:
            low_temp_water = match.group('low_temp_water').strip()
            return int(low_temp_water)

    # Метод получаем  значение Низкого давления масла (0 или 1) ДГУ
    def _parse_low_pressure_oil(self, line) -> int:
        match = re.match(r'.+ДМ:\[(?P<low_pressure_oil>\d*)\]', line)
        if match:
            low_pressure_oil = match.group('low_pressure_oil').strip()
            return int(low_pressure_oil)

    # Метод получает значение Низкого уровня О/Ж (0 или 1) ДГУ
    def _parse_level_water(self, line) -> int:
        match = re.match(r'.+Низ\.Темп_О/Ж:\[(?P<level_water>\d*)\]', line)
        if match:
            level_water = match.group('level_water').strip()
            return int(level_water)

    # Метод получает значение состояние работы двигателя (0 или 1) ДГУ
    def _parse_motor_work(self, line) -> int:
        match = re.match(r'.+Двиг\.:\[(?P<motor>\d*)\]', line)
        if match:
            motor_work = match.group('motor').strip()
            return int(motor_work)

    # Метод удаляет дату, время из строки вывода
    def _remove_date_time(self, line) -> str:
        # Получаем строку с данными без даты и времени
        string = ' '.join(line.split()[2:])
        return string

    # Метод получает значение температуры модуля SFP_2 MAC&C
    def _parse_temp_fiber2(self, line) -> str:
        match = re.match(r'.+TempFiber2: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber2 = match.group('temp_value').strip()
            return temp_fiber2

    # Метод получает значение температуры  модуля SFP_3 MAC&C
    def _parse_temp_fiber3(self, line) -> str:
        match = re.match(r'.+TempFiber3: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber3 = match.group('temp_value').strip()
            return temp_fiber3

    # Метод получает значение уровня сигнала Tx модуля SFP_2 MAC&C
    def _parse_tx_fiber2(self, line) -> str:
        match = re.match(r'.+TxFiber2: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber2 = match.group('tx_value').strip()
            return tx_fiber2

    # Метод получает значение уровня сигнала Tx модуля SFP_3 MAC&C
    def _parse_tx_fiber3(self, line) -> str:
        match = re.match(r'.+TxFiber3: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber3 = match.group('tx_value').strip()
            return tx_fiber3
    
    # Метод получает значение приемного уровня сигнала модуля SFP_2 MAC&C
    def _parse_rx_fiber2(self, line) -> str:
        match = re.match(r'.+RxFiber2: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber2 = match.group('rx_value').strip()
            return rx_fiber2

    # Метод получает значение приемного уровня сигнала модуля SFP_3 MAC&C
    def _parse_rx_fiber3(self, line) -> str:
        match = re.match(r'.+RxFiber3: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber3 = match.group('rx_value').strip()
            return rx_fiber3

    # Метод получает значение параметров состояния оборудования ИБЭП, MAC&C и ДГУ
    def _parse_message(self, line) -> str:
        match = re.match(r'^[\d+\:*].+(?P<description>IN.+)', line)
        match1 = re.match(r'[\d+\:*].+(?P<description>ОПС.+) Двиг', line)
        match2 = re.match(r'^[\d+\:*].+(?P<description>TxFiber2.+)', line)
        # Это условие для ИБЭП
        if match:
            description = match.group('description').strip()
            return description
        # Это условия для сообщения приходящего по протоколу ModBus
        elif match1:
            description = match1.group('description').strip()
            return description
        # Это условие для MAC&C
        elif match2:
            description = match2.group('description').strip()
            return description

    # Метод возращает количество итераций цикла, принимает на вход строку со значениями полученными от ThreaSNMPAsk
    def _parse_count(self, line) -> int:
        # Получаем количество итераций цикла из строки полученной от ThreadSNMPSWitch
        match = re.match(r'.+Count: (?P<count>\d*)', line)
        if match:
            count = match.group('count')
            return int(count)
    
    # Метод преобразует дату и время в строку и подставляет ее значение в меню Статус Бар
    def show_clock(self) ->str:
        # Получаем дату и время
        date = datetime.today().strftime('%H:%M:%S %d-%m-%Y')
        # Выравниваем по правому краю
        #self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        # В экземпляр класса QLable подставляем изображение и полученную дату и время
        self.lbl_clock.setText('<img src="{}" width="20" height="20"> <strong>{}</strong>'.format(self.path_icon_time, date))
    
    # Метод вызывается при нажатии кнопки "Отключить мелодию" подтверждает наличие всех аварий
    def _presse_button_confirm_all_alarms(self):
        # Обращаетмя к словарю dic_alarm_sound получаем список ключей
        keys = list(self.dic_alarm_sound.keys())
        # Проходимся по списку ключей
        for key in keys:
            # Обращаемся к словарю по ключу key, получаем словарь проверяем что если в словаре есть запись
            if self.dic_alarm_sound[key]:
                # Обращаемся к словарю и проходимся по его ключам ip 
                for ip in self.dic_alarm_sound[key]:
                    # Если значение равно 'Alarm'
                    if self.dic_alarm_sound[key][ip] == 'Alarm':
                        # Меняем значение с Alarm на Confirm, т.е. мы подтверждаем наличие аварий
                        self.dic_alarm_sound[key][ip] = 'Confirm'
    
    # Метод запускает мелодию при возникновении аварии
    def _run_play_sound(self):
        # Проверяем если галочка "Без звука" не установлена, то воспроизводим мелодию
        if not self.checkSound.isChecked():
            # Проверяем если установлена галочка "Повторять мелодию"
            if self.repeat_sound.isChecked():
                # Проверяем если мелодия не запущена
                if not self.play_sound.is_play():
                    # Запускаем мелодию до момента пока ее не отключат
                    self.play_sound.start()
            else:
                # Проверяем если мелодия не запущена
                if not self.play_sound.is_play():
                    # Воспроизвести мелодию один раз
                    self.play_sound.single_sound()
                
    # Метод проверяет воспроизводилась ли мелодия для аварии с ip адресом, проверяет наличие ключа ip в словаре dic_alarm_sound
    def _isplay_sound(self, key_alarm, ip) -> bool:
        # Если в словаре нет ключа с ip адресом
        if self.dic_alarm_sound[key_alarm].get(ip) == None:
            # Добавляем в словарь ключ ip адрес и значение Alarm
            self.dic_alarm_sound[key_alarm][ip] = 'Alarm'
            return True
        else:
            False

    # Метод проверяет выводилось Диалоговое окно с сообщением об аварии, проверяет в словаре dic_massege_box ключ с ip-адресом 
    def _is_display_dialog(self, key_alarm, ip) -> bool:
        # Если в словаре нет ключа с ip адресом
        if self.dic_massege_box[key_alarm].get(ip) == None:
            # Добавляем ip адрес в словарь со значением Add
            self.dic_massege_box[key_alarm][ip] = 'Add'
            return True
        else:
            False
    
    # Метод выводит Диалоговое окно с сообщением об аварии
    def _display_dialog(self, host_name,  description):
        # Создаем экземпляр класса
        critical_alarm = QMessageBox()
        critical_alarm.setWindowTitle('Авария')
        critical_alarm.setText('Авария')
        critical_alarm.setIcon(QMessageBox.Critical)
        critical_alarm.setWindowIcon(self.icon_err)
        # Добавляем текст сообщения который будет выводится с вызовом Диалогово окна
        critical_alarm.setText(f'<b style="font-size:{self.font_size_message_alarm}px">{host_name}: {description}</b>')
        critical_alarm.open()
        critical_alarm.buttonClicked.connect(self.click_btn)
        # Возвращаем экземпляр класса
        return critical_alarm
    
    # Метод проверяет все ли аварии были потверждены пользователем
    def _is_confirm_alarms(self) -> bool:
        # Создаем генератор списка, обращаемся к словарю dic_alarm_sound по значениям (values) полученные 
        # данные преобразуем в список перебираем в цикле список словарей, если словарь не пустой
        #  добавлеям в созданный список ls проверяем если этот список пустой.
        ls = [list(dic.values()) for dic in list(self.dic_alarm_sound.values()) if dic]
        for num, alarms in enumerate(ls, start=1):
            # Если в словаре есть значение  Alarm, значит есть не подтвержденная авария
            if 'Alarm' in alarms:
                # Возвращаем False
                return False
            # Если число итераций равно длине списка, значит мы дошли до конца списка, т.е. все аварии потверждены
            elif num == len(ls):
                return True 

    # Метод останавливает воспроизведение мелодии
    def _stop_play_sound(self) -> None:
        # Проверяем если мелодия запущена
        if self.play_sound.is_play():
            # Останавливаем мелодию
            self.play_sound.stop()
            self.play_sound.terminate()

    # Метод вызывается при нажатии кнопки "Ок" в Диалоговом окне, меняем занчение в словаре с Alarm на Confirm,
    # тем самым подтверждаем наличие аварии
    def _press_button_confirm_alarm(self) -> None:
        # Обращаетмя к словарю dic_alarm_sound получаем список ключей
        keys = list(self.dic_alarm_sound.keys())
        # Проходимся по списку ключей
        for num, key in enumerate(keys):
            # Обращаемся к словарю по ключу key, получаем словарь проверяем что если в словаре есть запись
            if self.dic_alarm_sound[key]:
                # Обращаемся к словарю и проходимся по его ключам ip 
                for ip in self.dic_alarm_sound[key]:
                    # Если значение равно 'Alarm'
                    if self.dic_alarm_sound[key][ip] == 'Alarm':
                        # Меняем значение с Alarm на Confirm, т.е. мы подтверждаем наличие аварий
                        self.dic_alarm_sound[key][ip] = 'Confirm'
                        return None 
    
    # Метод удаляет запись об аврии из словарей date_alarm, dic_alarm_sound, dict_interim_messages и dic_massege_box
    def _remove_ip_from_dict_alarms(self, ip, *key_alarms):
        for alarm in key_alarms:
            # Если есть запись в словаре с ключом ip
            if self.date_alarm[alarm].get(ip):
                # Удаляем запись из словаря date_alarm
                del self.date_alarm[alarm][ip]
            # Если есть запись в словаре с ключом ip
            if self.dic_alarm_sound[alarm].get(ip):
                # Удаляем запись из словаря alarm_sound
                del self.dic_alarm_sound[alarm][ip]
            # Если есть запись в словаре с ключом ip
            if self.dict_interim_messages[alarm].get(ip):
                # Удаляем запись из словаря alarm_sound
                del self.dict_interim_messages[alarm][ip] 
            # Если в словаре есть запись с этим ip
            if self.dic_massege_box[alarm].get(ip):
                # Удаляем запись из словаря
                del self.dic_massege_box[alarm][ip]   
            
    # Метод запускает 
    def run(self):     
        #Задаем интервал запуска timer(обновления метода run)
        self.timer.setInterval(self.interval_time*1000)
        # В экземпляр класса QLable подставляем изображение и текст 
        self.lbl.setText('<img src="{}">  Выполняется'.format(self.path_icon_progress))
        # Если мы получили данные
        if self.snmp_traps:
            for line in self.snmp_traps:
                # Получаем IP адрес вызвав метод _parse_ip
                ip_addr = self._parse_ip(line)
                # Удаляем дату и время из строки вывода
                result = self._remove_date_time(line)
                # Добавляем в словарь ключ ip_addr И значение это вывод строки с текущими значениями
                self.dict_set[ip_addr] = result
                # Очищаем окна от данных
                self.textBrowser.clear()
                self.textBrowser_2.clear()
                self.textBrowser_3.clear()
                self.textBrowser_4.clear()
                self.textBrowser_5.clear()
                self.textBrowser_6.clear()
            # Перебираем данные из словаря dict_set по ключу ip и значению value 
            for ip, value in self.dict_set.items():
                # Ловим исключение на случай удаления устройства из списка БД при работающем Окне мониторинга
                try:
                    # Получаем имя которое соответствует ip адресу
                    host_name = self._dns(ip)
                    # Получаем описание параметров устройства
                    description = self._parse_message(value)
                    # Формируем строку подставив имя устройства и описание параметров
                    row = f'{host_name} {description}'
                # Если попали в исключение то пропускаем все что ниже по коду
                except TypeError:
                    continue

        # ПРОВЕРКА ПАРАМЕТРОВ СОСТОЯНИЕ РАБОТЫ ДГУ

                if 'ДГУ' in value:
                    # Аварийный останов двигателя
                    motor = self._parse_motor_work(value)
                    # Низкий уровень О/Ж
                    level_water = self._parse_level_water(value)
                    # Низкое давление масла в двигателе
                    low_pressure_oil = self._parse_low_pressure_oil(value)
                    # Низкая температура О/Ж
                    low_temp_water = self._parse_low_temp_water(value)
                    # Высокая температура О/Ж
                    hi_temp_water = self._parse_hi_temp_water(value)
                    # Низкий уровень топлива
                    low_oil = self._parse_low_oil(value)
                    # Вызываем метод _parse_count, получаем количество итераций цикла
                    counter = self._parse_count(value)
                    # Вызываем метод, который возвращает номер окна в которое нужно вывести аврийное сообщение
                    num_window = self._get_num_window(ip)
                    # Низкий уровень топлива
                    if low_oil >= self.low_oil_limit:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}</span></p>'''.format(self.path_icon_inf, row)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'low_oil')
                    # Проверяем если значение равно 1 и dict_interim_messages не содержит сообщение с таким ip адресом 
                    elif low_oil < self.low_oil_limit and ip not in self.dict_interim_messages['low_oil']:
                        # Добавляем в словарь dict_interim_messages индекс сообщения 1 - это значит мы получили
                        # сообщение об аврии первый раз, а так же количество итераций цикла.
                        self.dict_interim_messages['low_oil'][ip] = [1, counter]
                        print('ДГУ: 1-low_oil', counter)
                    # Проверяем если значение равно 1 И индекс сообщения = 1 И разность итераций цикла равно num ИЛИ num+1
                    elif low_oil < self.low_oil_limit and self.dict_interim_messages['low_oil'][ip][0] == 1 \
                        and ((counter - self.dict_interim_messages['low_oil'][ip][1]) == self.num \
                            or (counter - self.dict_interim_messages['low_oil'][ip][1]) == self.num + 1):
                        print('ДГУ: 2 - low_oil', counter)
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        # Получаем дату возникновения аврии
                        date_time = self._get_alarm_date_time(ip, key='low_oil')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['low_oil'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым, цвет текста белый подставляем 
                        # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {}</span>  <strong>{}</strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом, цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{}</span></p>'''.format(self.path_icon_critical, row)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Меняем индекс в словаре dict_interim_messages с 1 на 2, значит получили одну и туже аврию повторно
                        self.dict_interim_messages['low_oil'][ip][0] = 2
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound('low_oil', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                        if self._is_display_dialog('low_oil', ip):
                            # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                            if not self.Hidden_message_check_box.isChecked():
                                description = 'Низкий уровень топлива'
                                # Вызываем метод который выводит диалоговое окно с сообщением об аварии 
                                critical_alarm = self._display_dialog(host_name, description)
                                # Добавляем в словарь ключ ip адрес и экземпляр класса
                                self.dic_massege_box['low_oil'][ip] = critical_alarm
                    
                    # Аварийная остановка двигателя
                    if motor == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{} Экстренная остановка двигателя
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'motor')
                    elif motor == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='motor')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['motor'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} Экстренная остановка двигателя</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} Экстренная остановка двигателя</span></p>'''.format(self.path_icon_critical, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound('motor', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                        if self._is_display_dialog('motor', ip):
                            description = 'Экстренная остановка двигателя'
                            # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                            if not self.Hidden_message_check_box.isChecked():
                                # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                critical_alarm = self._display_dialog(host_name, description)
                                # Добавляем в словарь ключ ip адрес и экземпляр класса
                                self.dic_massege_box['motor'][ip] = critical_alarm
                    
                    # Низкий уровень О/Ж
                    if level_water == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}: Низкий уровень О/Ж
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'level_water')
                    elif level_water == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='level_water')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['level_water'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} Низкий уровень О/Ж</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} Низкий уровень О/Ж</span></p>'''.format(self.path_icon_critical, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound('level_water', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                        if self._is_display_dialog('level_water', ip):
                            # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                            if not self.Hidden_message_check_box.isChecked():
                                description = 'Низкий уровень О/Ж'
                                # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                critical_alarm = self._display_dialog(host_name, description)
                                # Добавляем в словарь ключ ip адрес и экземпляр класса
                                self.dic_massege_box['level_water'][ip] = critical_alarm
                    
                    # Низкое давление масла
                    if low_pressure_oil == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}: Низкое давление масла
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'low_pressure_oil')
                    # Проверяем если значение равно 1 и dict_interim_messages не содержит сообщение с таким ip адресом 
                    elif low_pressure_oil == 1 and ip not in self.dict_interim_messages['low_pressure_oil']:
                        # Добавляем в словарь dict_interim_messages индекс сообщения 1 - это значит мы получили
                        # сообщение об аврии первый раз, а так же количество итераций цикла.
                        self.dict_interim_messages['low_pressure_oil'][ip] = [1, counter]
                    # Проверяем если значение равно 1 И индекс сообщения = 1 И разность итераций цикла равно num ИЛИ num+1
                    elif low_pressure_oil == 1 and self.dict_interim_messages['low_pressure_oil'][ip][0] == 1 \
                        and ((counter - self.dict_interim_messages['low_pressure_oil'][ip][1]) == self.num \
                            or (counter - self.dict_interim_messages['low_pressure_oil'][ip][1]) == self.num + 1):
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='low_pressure_oil')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['low_pressure_oil'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} Низкое давление масла</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} Низкое давление масла</span></p>'''.format(self.path_icon_critical, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Меняем индекс в словаре dict_interim_messages с 1 на 2, значит получили одну и туже аврию повторно
                        self.dict_interim_messages['low_pressure_oil'][ip][0] = 2
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound('low_pressure_oil', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                        if self._is_display_dialog('low_pressure_oil', ip):
                            # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                            if not self.Hidden_message_check_box.isChecked():
                                description = 'Низкое давление масла'
                                # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                critical_alarm = self._display_dialog(host_name, description)
                                # Добавляем в словарь ключ ip адрес и экземпляр класса
                                self.dic_massege_box['low_pressure_oil'][ip] = critical_alarm
                    
                    # Низкая температура О/Ж
                    if low_temp_water == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}: Низкая температура О/Ж
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word)
                        # Вызываем метод который удаляет запись об аварии из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'low_temp_water')
                    elif low_temp_water == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='low_temp_water')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['low_temp_water'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} Низкая температура О/Ж</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} Низкая температура О/Ж</span></p>'''.format(self.path_icon_critical, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound('low_temp_water', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                        if self._is_display_dialog('low_temp_water', ip):
                            # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                            if not self.Hidden_message_check_box.isChecked():
                                description = 'Низкая температура О/Ж'
                                # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                critical_alarm = self._display_dialog(host_name, description)
                                # Добавляем в словарь ключ ip адрес и экземпляр класса
                                self.dic_massege_box['low_temp_water'][ip] = critical_alarm

                    # Высокая температура О/Ж
                    if hi_temp_water == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{} Высокая температура О/Ж
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'hi_temp_water')
                    elif hi_temp_water == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='hi_temp_water')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['hi_temp_water'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} Высокая температура О/Ж</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{}: Высокая температура О/Ж</span></p>'''.format(self.path_icon_critical, host_name)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound('hi_temp_water', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                        if self._is_display_dialog('hi_temp_water', ip):
                            # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                            if not self.Hidden_message_check_box.isChecked():
                                description = 'Высокая температура О/Ж'
                                # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                critical_alarm = self._display_dialog(host_name, description)
                                # Добавляем в словарь ключ ip адрес и экземпляр класса
                                self.dic_massege_box['hi_temp_water'][ip] = critical_alarm
                else:   
                    # Получаем значение температуры
                    temperature = self._parse_temperature(value)
                    # Получаем знаение входного напряжения
                    voltege_in = self._parse_voltage_in(value)
                    # Получаем значение выходного напряжения
                    voltege_out = self._parse_voltage_out(value)
                    # Вызываем метод, который распарсивает строку сообщения об ошибке
                    error = self._parse_erro(value)
                    # Вызываем метод parse_tx_fiber2 получаем значение уровня передающего сигнала SFP_2 модуля
                    tx_fiber2 = self._parse_tx_fiber2(value)
                    # Вызываем метод parse_tx_fiber3 получаем значение уровня передающего сигнала SFP_3 модуля
                    tx_fiber3 = self._parse_tx_fiber3(value)
                    # Вызываем метод parse_rx_fiber2 получаем значение приемного уровня сигнала SFP_2 модуля
                    rx_fiber2 = self._parse_rx_fiber2(value)
                    # Вызываем метод parse_rx_fiber3 получаем значение приемного уровня сигнала SFP_3 модуля
                    rx_fiber3 = self._parse_rx_fiber3(value)
                    # Вызываем метод parse_temp_fiber2 получаем значение температуры SFP_2 модуля
                    temp_fiber2 = self._parse_temp_fiber2(value)
                    # Вызываем метод parse_temp_fiber3 получаем значение температуры SFP_3 модуля
                    temp_fiber3 = self._parse_temp_fiber3(value)
                    # Вызываем метод, который возвращает номер окна в которое нужно вывести аврийное сообщение
                    num_window = self._get_num_window(ip)
                    if temperature and voltege_in and voltege_out:
                        # Устанавливаем стили нашей строке с данными
                        word = '''<p><img src="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, row)
                        # Если входное напряжение меньше 10 (АВАРИЯ ОТКЛЮЧЕНИЕ ЭЛЕКТРОЭНЕРГИИ)
                        if int(voltege_in) < 200:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='power_alarm')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['power_alarm'][ip].get('start_time'))
                            # Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом 
                            row = row.replace(f'IN: {voltege_in} V', f'<b style = "font-weight: 900;">IN: {voltege_in} V</b>')
                            # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем 
                            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                            # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем строку
                            # подставляем строку с параметрами аварии без даты возникновения и длительности аварии  
                            word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                            # Вызываем метод, который проверяет, если мелодия не воспроизводилась для текущего ip, верни True
                            if self._isplay_sound('power_alarm', ip):
                                # Вызываем метод который запускает мелодию
                                self._run_play_sound()
                            # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                            if self._is_display_dialog('power_alarm', ip):
                                # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                                if not self.Hidden_message_check_box.isChecked():
                                    # Описание аварии
                                    description = 'Отключение электроэнергии'
                                    # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                    critical_alarm = self._display_dialog(host_name, description)
                                    # Добавляем в словарь ключ ip адрес и экземпляр класса
                                    self.dic_massege_box['power_alarm'][ip] = critical_alarm
                                
                            # Если выходное напряжение меньше или равно порогу низкого напряжения (АВАРИЯ ПО НИЗКОМУ НАПРЯЖЕНИЮ)
                            if float(voltege_out) <= self.low_voltage:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время 
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='low_voltage')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['low_voltage'][ip].get('start_time'))
                                # Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                                row = row.replace(f'OUT: {voltege_out} V', f'<b style = "font-weight: 900;">OUT: {voltege_out} V</b>')
                                # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем  дату и время возникновения аварии,
                                #  строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_critical, row)
                                # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                                if self._isplay_sound('low_voltage', ip):
                                    # Вызываем метод который запускает мелодию
                                    self._run_play_sound()
                                # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                                if self._is_display_dialog('low_voltage', ip):
                                    # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                                    if not self.Hidden_message_check_box.isChecked():
                                        description = 'Низкое напряжение АКБ'
                                        # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                        critical_alarm = self._display_dialog(host_name, description)
                                        # Добавляем в словарь ключ ip адрес и экземпляр класса
                                        self.dic_massege_box['low_voltage'][ip] = critical_alarm
                            # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word_alarm1)
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(word_alarm)
                            # Вызываем метод который проверяет есть ли запись в словаре об аварии, если запись есть, то удаляем
                            self._remove_ip_from_dict_alarms(ip, 'request_err')
                        # ОТСУТСТВИЕ АВАРИИ ПО ЭЛЕКТРОЭНЕРГИИ И НИЗКОМУ НАПРЯЖЕНИЮ
                        # Если есть запись в словаре с ключом ip
                        elif self.date_alarm['power_alarm'].get(ip): # Метод get вернет None если нет ip
                            # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word)
                            # Вызываем метод который удаляет запись об авариях из словарей.
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')

                        # Поскольку высокая, низкая температуры по степени важности ниже остальных аварий,
                        # то при выполнении одного из условий выше мы условие по высокой, низкой тем-рам не проверяем 
                        elif int(temperature) >= self.hight_temp or int(temperature) <= self.low_temp:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время 
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='hight_temp')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['hight_temp'][ip].get('start_time'))
                            # Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                            row = row.replace(f'*C: {temperature}', f'<b style = "font-weight: 900;">*C: {temperature}</b>')
                            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                            #  строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                            color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                            # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                            # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                            word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                            color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                            # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word_alarm1)
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(word_alarm)
                            # Вызываем метод который проверяет есть ли запись в словаре об аварии, если запись есть, то удаляем
                            self._remove_ip_from_dict_alarms(ip, 'request_err')
                        # Если нет аварии по температуре
                        elif self.date_alarm['hight_temp'].get(ip): # Метод get верент None если нет ip  
                            # Удаляем запись из словаря date_alarm
                            del self.date_alarm['hight_temp'][ip]
                            # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word)

                        # Поскольку высокое напряжение по степени важности ниже остальных аварий,
                        # то при выполнении одного из условий выше мы условие по высокому напряжению не проверяем 
                        elif int(voltege_in) >= self.hight_voltage:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время 
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='hight_voltage')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['hight_voltage'][ip].get('start_time'))
                            #Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                            row = row.replace(f'IN: {voltege_in} V', f'<b style = "font-weight: 900;">IN: {voltege_in} V</b>')
                            # Подсвечиваем строку оранжевым цветом и цвет текста белый, подставляем  дату и время возникновения аварии,
                            #  строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}"> <span style="background-color: #ffa500; 
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                            # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                            # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                            word_alarm1 = '''<p><img src="{}"> <span style="background-color: #ffa500; 
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                            # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word_alarm1)
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(word_alarm)
                            # Вызываем метод который удаляет ip адрес из словаря, передаем на вход значения, key ip.
                            self._remove_ip_from_dict_alarms(ip, 'request_err')
                        # Иначе, если аварии нет 
                        else:
                            # Вызываем метод который проверяет есть ли запись в словаре об аварии, если запись есть, то удаляем
                            self._remove_ip_from_dict_alarms(ip, 'request_err', 'hight_voltage')
                            # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word)
                            
                    # MAC&C 
                    # Проверка значений параметров Транспондера MAC&C
                    elif rx_fiber2 and rx_fiber3 and tx_fiber3 and tx_fiber2 and temp_fiber2 and temp_fiber3:
                        # Устанавливаем стили нашей строке с данными
                        word = '''<p><img src="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, row)
                        # Проверяем если значение уровня приемного и передающего сигналов меньше signal_level_fiber
                        if (int(rx_fiber2) < self.signal_level_fiber or int(rx_fiber3) < self.signal_level_fiber or 
                            int(tx_fiber2) < self.signal_level_fiber or int(tx_fiber3) < self.signal_level_fiber):
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='low_signal_power')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['low_signal_power'][ip].get('start_time'))
                            if int(rx_fiber2) < self.signal_level_fiber:
                                #Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                                row = row.replace(f'RxFiber2: {rx_fiber2} dBm', f'<b style = "font-weight: 900;">RxFiber2: {rx_fiber2} dBm</b>')
                            if int(rx_fiber3) < self.signal_level_fiber:
                                #Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                                row = row.replace(f'RxFiber3: {rx_fiber3} dBm', f'<b style = "font-weight: 900;">RxFiber3: {rx_fiber3} dBm</b>')
                            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
                            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем строку
                            # подставляем строку с параметрами аварии без даты возникновения и длительности аварии  
                            word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                            # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                            if self._isplay_sound('low_signal_power', ip):
                                # Вызываем метод который запускает мелодию
                                self._run_play_sound()
                            # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                            if self._is_display_dialog('low_signal_power', ip):
                                # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                                if not self.Hidden_message_check_box.isChecked():
                                    description = 'Низкие приемные уровни транспондера'
                                    # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                    critical_alarm = self._display_dialog(host_name, description)
                                    # Добавляем в словарь ключ ip адрес и экземпляр класса
                                    self.dic_massege_box['low_signal_power'][ip] = critical_alarm
                            # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word_alarm1)
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(word_alarm)
                            # Вызываем метод который проверяет есть ли запись в словаре об аварии, если запись есть, то удаляем
                            self._remove_ip_from_dict_alarms(ip, 'request_err')

                        # ОТСУТСТВИЕ АВАРИИ НИЗКОГО СИГНАЛА
                        elif self.date_alarm['low_signal_power'].get(ip):
                            # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word)
                            # Вызываем метод который удаляет ip адрес из словарей аврий
                            self._remove_ip_from_dict_alarms(ip, 'low_signal_power')

                        # Поскольку высокая температура по степени важности ниже "Низкого уровня сигнала", 
                        # то при выполнении одного из условий выше мы условие по высокой температуре не проверяем
                        elif (int(temp_fiber2) > self.hight_temp_fiber or int(temp_fiber3) > self.hight_temp_fiber):
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='hight_temp')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['hight_temp'][ip].get('start_time'))
                            # Если температура fiber2 больше target
                            if int(temp_fiber2) > self.hight_temp_fiber:
                                #Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                                row = row.replace(f'TempFiber2: {temp_fiber2} *C', f'<b style = "font-weight: 900;">TempFiber2: {temp_fiber2} *C</b>')
                            # Если температура fiber3 больше target
                            if int(temp_fiber3) > self.hight_temp_fiber:
                                #Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                                row = row.replace(f'TempFiber3: {temp_fiber3} *C', f'<b style = "font-weight: 900;">TempFiber3: {temp_fiber3} *C</b>')
                            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                            #  строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                            color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем строку
                            # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                            word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                            color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                            # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word_alarm1)
                            # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                            if self._isplay_sound('hight_temp', ip):
                                # Вызываем метод который запускает мелодию
                                self._run_play_sound()
                            # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
                            if self._is_display_dialog('hight_temp', ip):
                                # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
                                if not self.Hidden_message_check_box.isChecked():
                                    description = 'Высокая температура транспондера'
                                    # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                                    critical_alarm = self._display_dialog(host_name, description)
                                    # Добавляем в словарь ключ ip адрес и экземпляр класса
                                    self.dic_massege_box['hight_temp'][ip] = critical_alarm
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(word_alarm)
                            # Вызываем метод который проверяет есть ли запись в словаре об аварии, если есть, то удаляем
                            self._remove_ip_from_dict_alarms(ip, 'request_err')

                        # ОТСУТСТВИЕ АВАРИИ ПО ВЫСОКОЙ ТЕМПЕРАТУРЕ
                        elif self.date_alarm['hight_temp'].get(ip):
                            # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word)
                            # Вызываем метод который удаляет ip адрес из словарей аврий
                            self._remove_ip_from_dict_alarms(ip, 'hight_temp')

                        # Поскольку низкая температура по степени важности ниже "Низкого уровня сигнала", 
                        # то при выполнении одного из условий выше мы условие по высокой температуре не проверяем
                        elif (int(temp_fiber2) < self.low_temp_fiber or int(temp_fiber3) < self.low_temp_fiber):
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='low_temp')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['low_temp'][ip].get('start_time'))
                            if int(temp_fiber2) < self.low_temp_fiber:
                                #Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                                row = row.replace(f'TempFiber2: {temp_fiber2} *C', f'<b style = "font-weight: 900;">TempFiber2: {temp_fiber2} *C</b>')
                            if int(temp_fiber3) < self.low_temp_fiber:
                                #Делаем замену значения на тоже самое значение, но выделенное жирным шрифтом
                                row = row.replace(f'TempFiber3: {temp_fiber3} *C', f'<b style = "font-weight: 900;">TempFiber3: {temp_fiber3} *C</b>')
                            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                            #  строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                            color: rgb(254, 0, 0);">{} {}</span> <strong>{}</strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем строку
                            # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                            word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                            color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                            # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word_alarm1)
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(word_alarm)
                            # Вызываем метод который проверяет есть ли запись в словаре об аварии, если запись есть, то удаляем
                            self._remove_ip_from_dict_alarms(ip, 'request_err')
                        # Иначе если аварии нет 
                        else:
                            # Вызываем метод который удаляет ip адрес из словаря, передаем на вход значения, key ip.
                            self._remove_ip_from_dict_alarms(ip, 'request_err', 'low_temp')
                            # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                            self._show_message_on_window(num_window, word)
                            
                    # Если мы получили сообщение с ошибкой, то 
                    elif error:
                        # Формируем строку вывода 
                        row_error = f'{host_name} {error}'
                        # Подсвечиваем строку красным цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}"> <span style="background-color: #FF0000;
                        color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_error, row_error)
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        # Получаем дату возникновения аврии
                        date_time = self._get_alarm_date_time(ip, key='request_err')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['request_err'][ip].get('start_time'))
                        # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
                        # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                        word_alarm = '''<p><img src="{}"> <span style="background-color: #FF0000;
                        color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_error, date_time, row_error, delta_time)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                # Вызываем метод который проверяет, что все аварии потверждены пользователем перед тем как остановить мелодию
                if self._is_confirm_alarms():
                    # Вызываем метод который останавливает воспроизведение мелодии
                    self._stop_play_sound() 
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Добавляем словарь date_alarm в БД в формате json
            #try:
            sql.add_date_time(self.date_alarm)
            #except (sqlite3.IntegrityError, sqlite3.OperationalError):
                #self.logger.error("Ошибка запроса из БД: sql.add_date_time(self.date_alarm)")
            # Выводим сообщение в статус бар с изображением и текстом "Готово"
            self.lbl.setText('<img src="{}">  <span style="font-size: 22px;">Готово</span>'.format(self.path_icon_done))
    
    # Запускаем таймер, который будет запускать метод run
    def start(self):
        # Переводим флаг в False, что второе окно не закрыто
        self.isClose_window = False
        # Запускаем timer, который запускает метод run
        self.timer.start(5000)
        # Запускаем timer_clock, который запускает метод show_clock
        self.timer_clock.start()
        # Добавляем в статус бар наш экземпляр класса lbl
        self.lbl.setText('<img src="{}">  <span style="font-size: 22px;">Выполняется загрузка...</span>'.format(self.path_icon_load))
        # Выводим Надпись с изображением в статус Бар
        self.statusbar.addWidget(self.lbl)
        
    # Метод срабатывает при закрытии второго окна и останавливает работу Таймеров и переводи флаг в True
    def closeEvent(self, event):
        # Переводим флаг в True, что второе окно действительно закрыто
        self.isClose_window = True
        # Останавливаем экземпляр класса timer, класса QTimer
        self.timer.stop()
        # Останавливаем экземпляр класса timer_clock, класса QTimer
        self.timer_clock.stop()
        # Проверяем если мелодия запущена
        if self.play_sound.is_play():
            # Останавливаем play_sound
            self.play_sound.stop()
            self.play_sound.terminate()
        # Очищаем окна от данных
        self.textBrowser.clear()
        self.textBrowser_2.clear()
        self.textBrowser_3.clear()
        self.textBrowser_4.clear()
        self.textBrowser_5.clear()
        self.textBrowser_6.clear()
        event.accept()

if __name__ == '__main__':
    app = SecondWindowBrowser()
    app._create_massege_box(1)
    #app._show_massege_box()
    #s = SecondWindowBrowser()
    #s._play_sound()

