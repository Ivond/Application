#
import logging
import re
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from SecondWindow import Ui_MainWindow
from PyQt5.QtCore import QThread
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QLabel
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
        # Словарь для хранения информации для какого типа аварии и ip адреса воспроизводилась мелодия. 
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
        # Словарь для хранения информации для какого типа аварии и ip адреса выводилось диалоговое окно.
        self.dic_massege_box = {'low_voltage': {},
                                'low_signal_power': {},
                                'hight_temp': {},
                                'motor': {},
                                'level_water': {},
                                'low_pressure_oil': {},
                                'low_temp_water': {},
                                'hi_temp_water': {},
                                'low_oil': {},
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
        self.switch_off_sound_btn.pressed.connect(self._presse_stop_sound)

        # ДОБАВЛЕНИЕ ИКОНКИ К КНОПКЕ
        self.switch_off_sound_btn.setIcon(self.icon_sound_stop)

        # Вызываем у экземпляра класса QMessageBox() метод buttonClicked(сигнал) и спомощью connect прикрепляем к нему 
        # метод click_btn, котрый будет срабатывать при каждом вызове(нажатии) сигнала buttonClicked, т.е. нажатие на кнопки.
        self.critical_alarm_low_valtage.buttonClicked.connect(self.click_btn)
        self.critical_alarm_fiber_low_level.buttonClicked.connect(self.click_btn)
        self.critical_alarm_temp_fiber.buttonClicked.connect(self.click_btn)
        self.critical_alarm_low_pressure_oil.buttonClicked.connect(self.click_btn)
        self.critical_alarm_low_level_oil.buttonClicked.connect(self.click_btn)
        self.critical_alarm_motor_work.buttonClicked.connect(self.click_btn)
        self.critical_alarm_level_water.buttonClicked.connect(self.click_btn)
        self.critical_alarm_low_temp_water.buttonClicked.connect(self.click_btn)
        self.critical_alarm_hi_temp_water.buttonClicked.connect(self.click_btn)

    # Метод обрабатывает нажатие кнопок в диалоговом окне, останавливает воспроизведение мелодии
    def click_btn(self, btn):
        # Удаление пользователя
        if btn.text() == 'OK':
            print('click_btn: Close massege')
            # Вызываем метод который останавливает воспроизведение мелодии.
            self._presse_stop_sound()
            print('click_btn: Stop sound')

    # Метод выводит диалоговое окно с сообщением об аврии
    def _show_massege_box(self, class_instance, host_name, description):
        print('_show_massege_box: Show massege')
        # Подставляем текст сообщения который будет выводится в Диалоговом окне 
        class_instance.setText(f'<b style="font-size:72px">{host_name}: {description}</b>')
        # Выводим диалоговое окно
        class_instance.show()

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

    # Метод выводит строки сообщения в одно из окон во вкладке Общая информация 
    def _show_message_on_window(self, num_window, message):
        if num_window == 1:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_3.append(message)
        elif num_window == 2:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser.append(message)
        elif num_window == 3:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_2.append(message)
        elif num_window == 4:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_4.append(message)
        else:
            # Выводим аварийное сообщение во вкладку All devices
            self.textBrowser_4.append(message) 
    
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
        else:
            # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец
            self.textBrowser_5.append(message)

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
    
    # Метод получает дату и время и возвращает заачение в нужном формате
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
    
    # Метод преобразует дату и время в строку и подставляет ее значение в меню Статус Бар
    def show_clock(self) ->str:
        # Получаем дату и время
        date = datetime.today().strftime('%H:%M:%S %d-%m-%Y')
        # Выравниваем по правому краю
        #self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        # В экземпляр класса QLable подставляем изображение и полученную дату и время
        self.lbl_clock.setText('<img src="{}" width="20" height="20"> <strong>{}</strong>'.format(self.path_icon_time, date))
    
    # Метод вызывается при нажатии кнопки "Отключить мелодию" и останавливает воспроизведение мелодии
    def _presse_stop_sound(self):
        print('_presse_stop_sound: Stop sound')
        # Проверяем если мелодия запущена
        if self.play_sound.is_play():
            # Отключаем воспроизведение мелодии
            self.play_sound.stop()
            self.play_sound.terminate()
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
        print('_run_play_sound: Run sound')
        # Проверяем если галочка "Без звука" не установлена, то воспроизводим мелодию
        if not self.checkSound.isChecked():
            # Проверяем если мелодия не запущена
            if not self.play_sound.is_play():
                # Запускаем мелодию
                self.play_sound.start()

    # Метод проверяет, если медодия не была запущена для текущей аварий, возвращает True
    def _isplay_sound_current_alarm(self, key_alarm, ip):
        # Если в словаре нет ключа с ip адресом
        if self.dic_alarm_sound[key_alarm].get(ip) == None:
            # Добавляем в словарь ключ ip адрес и значение Alarm
            self.dic_alarm_sound[key_alarm][ip] = 'Alarm'
            return True
        else:
            False
    # Метод проверяет выводилось ли диалоговое окно для текущей аварии, если не выводилось возвращает True
    def _isrun_timer_massegebox(self, key_alarm, ip):
        # Если в словаре нет ключа с ip адресом
        if self.dic_massege_box[key_alarm].get(ip) == None:
            # Добавляем в словарь ключ ip адрес и значение Alarm
            self.dic_massege_box[key_alarm][ip] = 'Alarm'
            return True
        else:
            False

    # Метод останавливает воспроизведение мелодии
    def _stop_play_sound(self):
        # Проверяем если мелодия запущена
        if self.play_sound.is_play():
            # Создаем генератор списка, обращаемся к словарю dic_alarm_sound по значениям (values) полученные 
            # данные преобразуем в список перебираем в цикле список словарей, если словарь не пустой
            #  добавлеям в созданный список ls проверяем если этот список пустой.
            ls = [list(dic.values()) for dic in list(self.dic_alarm_sound.values()) if dic]
            for num, alarms in enumerate(ls, start=1):
                print(alarms)
                # Если в словаре есть значение  Alarm, значит есть не подтвержденная авария
                if 'Alarm' in alarms:
                    # Останавливаем цикл, мелодию не отключаем.
                    break
                # Если число итераций равно длине списка, значит мы дошли до конца списка
                elif num == len(ls):
                    # Останавливаем мелодию
                    self.play_sound.stop()
                    self.play_sound.terminate()
    
    # Метод удаляет запись об аврии из словарей date_alarm и dic_alarm_sound
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

    # Метод закрывает диалоговое окно и удаляет запись об аварии из словаря
    def _close_massegebox(self, class_instance, ip, alarm_key):
        # Если в словаре есть запись с этим ip
        if self.dic_massege_box[alarm_key].get(ip):
            # Удаляем запись из словаря
            del self.dic_massege_box[alarm_key][ip]
            # Проверяем, если диалоговое окно открыто
            if class_instance.isEnabled():
                # Закрываем диалоговое окно, т.к. аварии нет
                class_instance.close()
        
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
                    # Низкий уровень топлива
                    if low_oil >= self.low_oil_limit:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}</span></p>'''.format(self.path_icon_inf, row)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'low_oil')
                        # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                        self._stop_play_sound()
                        # Вызываем метод, проверяем если есть запись в словаре и дилоговое окно открыто, закрываем его
                        self._close_massegebox(self.critical_alarm_low_level_oil, ip, 'low_oil')
                    else:
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
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound_current_alarm('low_oil', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                        if self._isrun_timer_massegebox('low_oil', ip):
                            # Создаем переменную в которую записываем значение аврии
                            description = 'НИЗКИЙ УРОВЕНЬ ТОПЛИВА'
                            # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                            self._show_massege_box(self.critical_alarm_low_level_oil, host_name, description)
                    # Аварийная остановка двигателя
                    if motor == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{} АВАРИЙНАЯ ОСТАНОВКА ДВИГАТЕЛЯ
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'motor')
                        # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                        self._stop_play_sound()
                        # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                        self._close_massegebox(self.critical_alarm_motor_work, ip, 'motor')
                    elif motor == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='motor')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['motor'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} АВАРИЙНАЯ ОСТАНОВКА ДВИГАТЕЛЯ</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} АВАРИЙНАЯ ОСТАНОВКА ДВИГАТЕЛЯ</span></p>'''.format(self.path_icon_critical, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound_current_alarm('motor', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                        if self._isrun_timer_massegebox('motor', ip):
                            description = 'АВАРИЙНАЯ ОСТАНОВКА ДВИГАТЕЛЯ'
                            # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                            self._show_massege_box(self.critical_alarm_motor_work, host_name, description)
                    # Низкий уровень О/Ж
                    if level_water == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}: НИЗКИЙ УРОВЕНЬ О/Ж
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'level_water')
                        # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                        self._stop_play_sound()
                        # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                        self._close_massegebox(self.critical_alarm_level_water, ip, 'level_water')
                    elif level_water == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='level_water')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['level_water'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} НИЗКИЙ УРОВЕНЬ О/Ж</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} НИЗКИЙ УРОВЕНЬ О/Ж</span></p>'''.format(self.path_icon_critical, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound_current_alarm('level_water', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                        if self._isrun_timer_massegebox('level_water', ip):
                            description = 'НИЗКИЙ УРОВЕНЬ О/Ж'
                            # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                            self._show_massege_box(self.critical_alarm_level_water, host_name, description)
                    # Низкое давление масла
                    if low_pressure_oil == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}: НИЗКОЕ ДАВЛЕНИЕ МАСЛА
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'low_pressure_oil')
                        # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                        self._stop_play_sound()
                        # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                        self._close_massegebox(self.critical_alarm_low_pressure_oil, ip, 'low_pressure_oil')
                    elif low_pressure_oil == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='low_pressure_oil')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['low_pressure_oil'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} НИЗКОЕ ДАВЛЕНИЕ МАСЛА</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} НИЗКОЕ ДАВЛЕНИЕ МАСЛА</span></p>'''.format(self.path_icon_critical, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound_current_alarm('low_pressure_oil', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                        if self._isrun_timer_massegebox('low_pressure_oil', ip):
                            description = 'НИЗКОЕ ДАВЛЕНИЕ МАСЛА'
                            # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                            self._show_massege_box(self.critical_alarm_low_pressure_oil, host_name, description)
                    # Низкая температура О/Ж
                    if low_temp_water == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{}: НИЗКАЯ ТЕМПЕРАТУРА О/Ж
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word)
                        # Вызываем метод который удаляет запись об аварии из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'low_temp_water')
                        # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                        self._stop_play_sound()
                        # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                        self._close_massegebox(self.critical_alarm_low_temp_water, ip, 'low_temp_water')
                    elif low_temp_water == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='low_temp_water')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['low_temp_water'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} НИЗАЯ ТЕМПЕРАТУРА О/Ж</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} НИЗКАЯ ТЕМПЕРАТУРА О/Ж</span></p>'''.format(self.path_icon_critical, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound_current_alarm('low_temp_water', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                        if self._isrun_timer_massegebox('low_temp_water', ip):
                            description = 'НИЗКАЯ ТЕМПЕРАТУРА О/Ж'
                            # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                            self._show_massege_box(self.critical_alarm_low_temp_water, host_name, description)
                    # Высокая температура О/Ж
                    if hi_temp_water == 0:
                        # Подсвечиваем строку зеленым цветом
                        word = '''<p><img src="{}"> <span style="background-color:#00ff00;">{} ВЫСОКАЯ ТЕМПЕРАТУРА О/Ж
                        </span></p>'''.format(self.path_icon_inf, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word)
                        # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
                        self._remove_ip_from_dict_alarms(ip, 'hi_temp_water')
                        # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                        self._stop_play_sound()
                        # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                        self._close_massegebox(self.critical_alarm_hi_temp_water, ip, 'hi_temp_water')
                    elif hi_temp_water == 1:
                        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                        date_time = self._get_alarm_date_time(ip, key='hi_temp_water')
                        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                        delta_time = self._convert_time(time.time() - self.date_alarm['hi_temp_water'][ip].get('start_time'))
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{} {} ВЫСОКАЯ ТЕМПЕРАТУРА О/Ж</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                        # Подсвечиваем строку бордовым цветом и цвет текста белый
                        word_alarm1 = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                        ">{}: ВЫСОКАЯ ТЕМПЕРАТУРА О/Ж</span></p>'''.format(self.path_icon_critical, host_name)
                        # Выводим значение на экран во вкладку All devices
                        self.textBrowser_4.append(word_alarm1)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(word_alarm)
                        # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                        if self._isplay_sound_current_alarm('hi_temp_water', ip):
                            # Вызываем метод который запускает мелодию
                            self._run_play_sound()
                        # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                        if self._isrun_timer_massegebox('hi_temp_water', ip):
                            description = 'ВЫСОКАЯ ТЕМПЕРАТУРА О/Ж'
                            # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                            self._show_massege_box(self.critical_alarm_hi_temp_water, host_name, description)
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
                        if int(voltege_in) < 10:
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
                            # Вызываем метод, проверяем, если мелодия не воспроизводилась для текущей аварии, верни True
                            if self._isplay_sound_current_alarm('power_alarm', ip):
                                # Вызываем метод который запускает мелодию
                                self._run_play_sound()
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
                                if self._isplay_sound_current_alarm('low_voltage', ip):
                                    # Вызываем метод который запускает мелодию
                                    self._run_play_sound()
                                # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                                if self._isrun_timer_massegebox('low_voltage', ip):
                                    description = 'НИЗКОЕ НАПРЯЖЕНИЕ АКБ'
                                    # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                                    self._show_massege_box(self.critical_alarm_low_valtage, host_name, description)
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
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')
                            # Останавливаем воспроизведение мелодии
                            self._stop_play_sound()
                            # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                            self._close_massegebox(self.critical_alarm_low_valtage, ip, 'low_voltage')

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
                            if self._isplay_sound_current_alarm('low_signal_power', ip):
                                # Вызываем метод который запускает мелодию
                                self._run_play_sound()
                            # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                            if self._isrun_timer_massegebox('low_signal_power', ip):
                                description = 'НИЗКИЕ ПРИЕМНЫЕ УРОВНИ ТРАНСПОНДЕРА'
                                # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                                self._show_massege_box(self.critical_alarm_fiber_low_level, host_name, description)
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
                            # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                            self._stop_play_sound()
                            # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                            self._close_massegebox(self.critical_alarm_fiber_low_level, ip, 'low_signal_power')

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
                            if self._isplay_sound_current_alarm('hight_temp', ip):
                                # Вызываем метод который запускает мелодию
                                self._run_play_sound()
                            # Вызываем метод, проверяем, если диалоговое окно не выводилось для текущей аварии, верни True 
                            if self._isrun_timer_massegebox('hight_temp', ip):
                                description = 'ВЫСОКАЯ ТЕМПЕРАТУРА ТРАНСПОНДЕРА'
                                # Вызываем метод, который выводит Диалоговое окно с сообщением об аварии
                                self._show_massege_box(self.critical_alarm_temp_fiber, host_name, description)
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
                            # Вызываем метод который проверяет если мелодия запущена, он ее останавливает
                            self._stop_play_sound()
                            # Вызываем метод, проверяем есть ли запись в словаре и если дилоговое окно открыто, закрываем его
                            self._close_massegebox(self.critical_alarm_temp_fiber, ip, 'hight_temp')

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
    app.show()
    app._show_massege_box()
    #s = SecondWindowBrowser()
    #s._play_sound()

