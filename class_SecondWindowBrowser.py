#
import logging
import time
#
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

class SecondWindowBrowser(QtWidgets.QMainWindow, Ui_MainWindow, QThread):
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
        
        # Создаем экземпляр классса Таймер
        self.timer = QtCore.QTimer(self)
        self.timer_clock = QtCore.QTimer(self)

        # Переменная определяет интервал между запросами
        self.interval_time = 1
        # Переменная порог высокой температуры
        self.hight_temp = 35
        # Переменная порог низкой температуры
        self.low_temp = 0
        # Порог низкого уровня температуры
        self.low_oil_limit = 35
        # Порог высокого напряжения
        self.hight_voltage = 240
        # Порог низкого напряжения
        self.low_voltage = 47.9
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

        # Задаем интервал запуска timer(обновления)
        self.timer.setInterval(self.interval_time*1000)
        self.timer_clock.setInterval(1000)
        # Определяем какую функцию будет запускать Таймер через указанный промежуток времени
        self.timer.timeout.connect(self.run)
        self.timer_clock.timeout.connect(self.show_clock)

        # Флаг определяет закрыто или открыто второе окно
        self.isClose_window = False
        # Переменная словарь куда записываем ключ IP адрес и значение строка с параметрами устройства
        self.dict_set = {}
        #
        # Создаем экземпляр класса sql
        sql = ConnectSqlDB()
        # Делаем запрос к БД и получаем словарь с данными (дата и время возникновения аварий)
        try:
            self.date_alarm = sql.get_values_list_db('data', table='Duration')
        except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
            self.logger.error("Ошибка запроса из БД: sql.get_values_list_db('data', table='Duration')" )
            # Если попали в исключения значит мы не смогли считать данные, подставляем готовый словарь
            self.date_alarm =  {'power_alarm':{},
                                'low_voltage':{},
                                'hight_voltage':{},
                                'limit_oil':{},
                                'hight_temp':{},
                                'low_temp':{},
                                'low_signal_power':{},
                                'request_err':{},
                                }
        # Переменная список куда записываем результат опроса snmp
        self.snmp_traps = []

     # СОЗДАЕМ ЭКЗЕМПЛЯР КЛАССА QIcon, ДОБАВЛЕНИЕ ИЗОБРАЖЕНИЯ ДЛЯ ДИАЛОГОВОГО ОКНА
        # Создаем экземпляр класса icon_main_window, класс QIcon - отвечает за добавления иконки с изображением для основного окна программы
        self.icon_second_window = QtGui.QIcon()
        # Вызываем у экземпляра класса icon_main_window метод addFile, у казываем путь где находится изображение
        self.icon_second_window.addFile(self.path_icon_second_window)
        # У QMainWindow вызываем метод setWindowIcon, которому передаем экземпляр класса нашего второго окна self и экземпляр класса icon_main_window в котором содержится изображение
        QtWidgets.QMainWindow.setWindowIcon(self, self.icon_second_window)

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

    # Функция делает подмену ip адреса на Имя устройства
    def _dns(self, ip):
        # Создаем экземпляр класса sql
        sql = ConnectSqlDB()
        try:
            # Делаем запрос к БД, получаем описание Ip адреса
            name = sql.get_db(ip=ip, table='Devices')[1]
            return name
        except (sqlite3.IntegrityError, IndexError, TypeError, sqlite3.NoneType):
            self.logger.error("Ошибка запроса из БД: sql.get_db(ip=ip, table='Devices')[1]")

    # Функция из полученных на вход данных, парсит ip адрес устройства
    def _parse_ip(self, line):
        try:
            ip = line.split()[2].strip()
            return ip
        except IndexError:
            pass
    
    # Метод преобразует время в секундах в дни, часы, минуты, секунды
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
                hour = '0' + str(hour)
            # Вычисляем остаток от количества часов(мин)
            sec %= 3600
            # Вычисляем количество минут
            minu = int(sec//60)
            if len(str(minu)) == 1:
                minu = '0' + str(minu)
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'{day}д. {hour}:{minu}:{int(sec)}'
        # Вычисляем количество часов
        hour = int(sec // 3600)
        # Если количество часов не равно 0
        if hour:
            if len(str(hour)) == 1:
                hour = '0' + str(hour)
            # Вычисляем остаток от количества часов(мин)
            sec %= 3600
            # Вычисляем количество минут
            minu = int(sec//60)
            if len(str(minu)) == 1:
                minu = '0' + str(minu)
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'{hour}:{minu}:{int(sec)}'
        # Вычисляем количество минут
        minu = int(sec//60)
        if minu:
            if len(str(minu)) == 1:
                minu = '0' + str(minu)
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'00:{minu}:{int(sec)}'
        else:
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'00:00:{int(sec)}'
    
    #
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

     # Функция из полученного на вход ip адреса, парсит второй октет Ip адреса определяя принадлежность устройства к локации
    def _parse_site_id(self, ip_addr):
        try:
            site_id = ip_addr.split('.')[1]
            return site_id
        except IndexError:
            pass

    def _parse_line(self, line, key=None):
        if key == 'temp':
            match = re.match(r'^(?P<string>.+) (?P<temp>\*C: \d*)', line)
            if match:
                #date = match.group('date').strip()  
                string = match.group('string').strip()
                temp = match.group('temp').strip()
                line = string + ' ' + f'<strong>{temp}</strong>'
                return line
            else:
                return line
        elif key == 'volt_in':
            match = re.match(r'^(?P<string>.+) (?P<volt_in>IN: \d* V) (?P<string_2>.+)', line)
            if match:
                string = match.group('string').strip()
                volt_in = match.group('volt_in').strip()
                string_2 = match.group('string_2').strip()
                line = string + ' ' +f'<b>{volt_in}</b>' + ' ' + string_2
                return line
            else:
                return line
        elif key == 'volt_low':
            match = re.match(r'^(?P<string>.+) (?P<volt_low>OUT: \d*(\.\d*)* V) (?P<string_2>.+)', line)
            if match:
                string = match.group('string').strip()
                volt_low = match.group('volt_low').strip()
                string_2 = match.group('string_2').strip()
                line = string + ' ' +f'<strong>{volt_low}</strong>' + ' ' + string_2
                return line
            else:
                return line

    # Метод парсит сообщение об ошибке
    def _parse_erro(self, line):
        match = re.match(r'.+(?P<error>SNMP.+)', line)
        if match:
            error = match.group('error').strip()
            return error

    # Функция из полученных на вход данных, парсит значение входного напряжения и возвращает это значение
    def _parse_voltage_in(self, line):
        match = re.match(r'.+IN: *(?P<voltage>\d+)', line)
        if match:
            voltage = match.group('voltage').strip()
            return voltage

    # Функция из полученных на вход данных, парсит значение выходного напряжения и возвращает это значение
    def _parse_voltage_out(self, line):
        match = re.match(r'.+OUT: *(?P<voltage>\d+\.*\d*)', line)
        if match:
            voltage = match.group('voltage').strip()
            return voltage

    # Функция из полученных на вход данных, парсит значение температуры и возвращает это значение
    def _parse_temperature(self, line):
        match = re.match(r'.+\*C: +(?P<temp_value>-*\d+)', line)
        if match:
            temperature_value = match.group('temp_value').strip()
            return temperature_value

    # Функция из полученных на вход данных, парсит значение количества топлива и возвращает это значение
    def _parse_modbus_values(self, line):
        match = re.match(r'.+Топл\.:(?P<limit>\d+)%', line)
        if match:
            limit_oil = match.group('limit').strip()
        match1 = re.match(r'.+Двиг\.:(?P<stop_motor>\d*)', line)
        if match1:
            stop_motor = match1.group('stop_motor').strip()
            return limit_oil, stop_motor

    # Функция из полученных на вход данных, парсит значение работу двигателя ДГУ
    def _parse_alarm_stop_motor(self, line):
        match = re.match(r'.+Двиг\.:(?P<stop_motor>\d*)', line)
        #
        if match:
            stop_motor = match.group('stop_motor').strip()
            return stop_motor

    # Метод удаляет дату и время из строки вывода
    def _remove_date_time(self, line):
        # Получаем строку с данными без даты и времени
        string = ' '.join(line.split()[2:])
        return string

# MAC&C

    # Функция из полученных на вход данных, парсит значение температуры модуля SFP_2 и возвращает это значение
    def _parse_temp_fiber2(self, line):
        match = re.match(r'.+TempFiber2: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber2 = match.group('temp_value').strip()
            return temp_fiber2

    # Функция из полученных на вход данных, парсит значение температуры  модуля SFP_3 и возвращает это значение
    def _parse_temp_fiber3(self, line):
        match = re.match(r'.+TempFiber3: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber3 = match.group('temp_value').strip()
            return temp_fiber3

    # Функция из полученных на вход данных, парсит значение уровня сигнала передачи модуля SFP_2 и возвращает это значение
    def _parse_tx_fiber2(self, line):
        match = re.match(r'.+TxFiber2: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber2 = match.group('tx_value').strip()
            return tx_fiber2

    # Функция из полученных на вход данных, парсит значение уровня сигнала передачи модуля SFP_3 и возвращает это значение
    def _parse_tx_fiber3(self, line):
        match = re.match(r'.+TxFiber3: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber3 = match.group('tx_value').strip()
            return tx_fiber3
    
    # Функция из полученных на вход данных, парсит значение приемного уровня сигнала модуля SFP_2 и возвращает это значение
    def _parse_rx_fiber2(self, line):
        match = re.match(r'.+RxFiber2: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber2 = match.group('rx_value').strip()
            return rx_fiber2

    # Функция из полученных на вход данных, парсит значение приемного уровня сигнала модуля SFP_3 и возвращает это значение
    def _parse_rx_fiber3(self, line):
        match = re.match(r'.+RxFiber3: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber3 = match.group('rx_value').strip()
            return rx_fiber3
    
    # Метод выводит в меню Статус Бар текущую дату и время
    def show_clock(self):
        # Получаем дату и время
        date = datetime.today().strftime('%H:%M:%S %d-%m-%Y')
        # Выравниваем по правому краю
        #self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        # В экземпляр класса QLable подставляем изображение и полученную дату и время
        self.lbl_clock.setText('<img src="{}" width="20" height="20"> <strong>{}</strong>'.format(self.path_icon_time, date))
    
    # Метод запускает 
    def run(self):
        # Задаем интервал запуска timer(обновления метода run)
        self.timer.setInterval(self.interval_time*1000)
        # В экземпляр класса QLable подставляем изображение и текст 
        self.lbl.setText('<img src="{}">  Выполняется'.format(self.path_icon_progress))
        # Если мы получили данные
        if self.snmp_traps:
            for line in self.snmp_traps:
                if 'ДГУ' in line:
                    continue
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
                # Получаем количество записей в textBrowser_6
                size = self.textBrowser_6.document().size().toSize().height() # -> int
                # Получаем высоту окна textBrowser_6
                geometry = self.textBrowser_6.geometry().height() # -> int
                # Ловим исключение на случай удаления устройства из списка БД при работающем Окне мониторинга
                try:
                    # Вызываем метод, который получает второй октет ip адреса, который определяет SiteId
                    site_id = self._parse_site_id(ip)
                    # Получаем имя которое соответствует ip адресу
                    name = self._dns(ip)
                    # Делаем замену ip адреса на полученное имя устройства
                    row = value.replace(value.split()[0], name)
                # Если попали в исключение то пропускаем все что ниже по коду
                except TypeError:
                    continue

        # ПРОВЕРКА КОЛИЧЕСТВА ТОПЛИВА И СОСТОЯНИЕ РАБОТЫ ДВИГАТЕЛЯ
                if 'ОПС' in value:
                    # Получаем значение количества топлива и состояние работы двигателя ДГУ
                    items = self._parse_modbus_values(value)
                    # Запрашиваем дату и время возникновения аварии, вызвав метод _get_date_time.  
                    date_time = self._get_date_time()
                    # Если мы получили значения количества топлива и значение состояние работы двигателя modbus_values
                    if items:
                        # Преобразуем строку в список и убирем последнее занчение, это значение состояния работы двигателя
                        #oil_count = row.split()[0:-1]
                        # Получаем из строки значения параметров АВТОБУС преобразовав строку в список
                        bus_value = row.split()[:8]
                        # Получаем из строки значение работы двигателя АВТОБУС преобразовав строку в список
                        stop_motor_count = row.split()[-1]
                        # Если количество топлива выше порога
                        if int(items[0]) >= self.low_oil_limit:
                            # Подсвечиваем строку зеленым цветом
                            word = '''<p><img src="{}"> <span style="background-color:#00ff00;">
                            {}</span></p>'''.format(self.path_icon_inf, ','.join(bus_value))
                            # Выводим значение на экран во вкладку All devices
                            self.textBrowser_4.append(word)
                        else:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='limit_oil')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['limit_oil'][ip].get('start_time'))
                            # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем 
                            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, ','.join(bus_value), delta_time)
                            # Подсвечиваем строку темно красным цветом, цвет текста белый
                            word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_critical, ','.join(bus_value))
                            # Выводим значение на экран во вкладку All devices
                            self.textBrowser_4.append(word_alarm1)
                            # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                            if (size + 10) < geometry:
                                # Выводим значение на экран во вкладку Curent Devices
                                self.textBrowser_6.append(word_alarm)
                            else:
                                # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец  вкладку Curent Devices
                                self.textBrowser_5.append(word_alarm)

                        # Проверяем состояние работы двигателя 
                        if items[1] == '0':
                            # Подсвечиваем строку зеленым цветом 
                            word = '''<p><img src="{}">  <span style="background-color: #00ff00;">{} 
                            Двигатель в работе {}</span></p>'''.format(self.path_icon_inf, ','.join(bus_value[:3]), stop_motor_count)
                            # Выводим значение на экран во вкладку All devices
                            self.textBrowser_4.append(word)
                        else:
                            # Подсвечиваем строку бордовым цветом и цвет текста белый
                            word_alarm = '''<p><img src="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                            ">{}:АВАРИЙНЫЙ ОСТАНОВ ДВИГАТЕЛЯ {}</span></p>'''.format(self.path_icon_critical, ','.join(bus_value[:3]), stop_motor_count)
                            # Выводим значение на экран во вкладку All devices
                            self.textBrowser_4.append(word_alarm)
                            # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                            if (size + 10) < geometry:
                                # Выводим значение на экран в первый столбец
                                self.textBrowser_6.append(word_alarm)
                            else:
                                # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                self.textBrowser_5.append(word_alarm)
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
                    # Проверяем если siteID равен одному из значений И мы получили значения temperature И voltege_in И выходное напряжение то
                    if (site_id == '192' or site_id == '193' or site_id == '194' or site_id == '195' or site_id == '196'):
                        if temperature and voltege_in and voltege_out:
                            # Устанавливаем стили нашей строке с данными
                            word = '''<p><img src="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, row)
                            # Если входное напряжение равно 180 (АВАРИЯ ОТКЛЮЧЕНИЕ ЭЛЕКТРОЭНЕРГИИ)
                            if int(voltege_in) < 180:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='power_alarm')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['power_alarm'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'volt_in')
                                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем 
                                # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии  
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)

                                # Если выходное напряжение меньше или равно порогу низкого напряжения
                                # (АВАРИЯ ПО НИЗКОМУ НАПРЯЖЕНИЮ)
                                if float(voltege_out) <= self.low_voltage:
                                # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                                # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время 
                                    # Получаем дату возникновения аврии
                                    date_time = self._get_alarm_date_time(ip, key='low_voltage')
                                    # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                    delta_time = self._convert_time(time.time() - self.date_alarm['low_voltage'][ip].get('start_time'))
                                    #
                                    row = self._parse_line(row, key = 'volt_low')
                                    # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем  дату и время возникновения аварии,
                                    #  строку с параметрами авриии и длительность аварии
                                    word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                    # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем строку
                                    # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                    word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_critical, row)
                                # Выводим аварийное сообщение во вкладку All devices
                                self.textBrowser.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Поскольку высокое напряжение по степени важности ниже пропадания электроэнергии и низкому 
                            # напряжению то при выполнении одного из условий выше мы условие по высокому напряжению не проверяем
                            elif int(voltege_in) >= self.hight_voltage:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время 
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_voltage')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_voltage'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'volt_in')
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый, подставляем  дату и время возникновения аварии,
                                #  строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}"> <span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}"> <span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение высокого напряжения на экран во вкладку All devices
                                self.textBrowser.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран
                                    # во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]
                            
                            # Поскольку высокая, низкая температуры по степени важности ниже остальных аварий,
                            # то при выполнении одного из условий выше мы условие по высокой, низкой тем-рам не проверяем 
                            elif int(temperature) >= self.hight_temp or int(temperature) <= self.low_temp:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время 
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_temp')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_temp'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'temp')
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                                #  строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение высокой/низкой температуры на экран во вкладку All devices
                                self.textBrowser.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Иначе, если аварии нет 
                            else:
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['power_alarm'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['power_alarm'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_temp'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_temp'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['low_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['low_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]
                                # Выводим значение во вкладку ALL info 
                                self.textBrowser.append(word)
                        #
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
                                # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
                                # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии  
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим аварийное сообщение во вкладку All devices
                                self.textBrowser.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Поскольку высокая температура по степени важности ниже "Низкого уровня сигнала", 
                            # то при выполнении одного из условий выше мы условие по высокой температуре не проверяем
                            elif (int(temp_fiber2) > self.hight_temp_fiber or int(temp_fiber3) > self.hight_temp_fiber):
                                # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                                # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_temp')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_temp'][ip].get('start_time'))
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                                #  строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим аварийное сообщение во вкладку All devices
                                self.textBrowser.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Поскольку низкая температура по степени важности ниже "Низкого уровня сигнала", 
                            # то при выполнении одного из условий выше мы условие по высокой температуре не проверяем
                            elif (int(temp_fiber2) < self.low_temp_fiber or int(temp_fiber3) < self.low_temp_fiber):
                                # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                                # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='low_temp')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['low_temp'][ip].get('start_time'))
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                                #  строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим аварийное сообщение во вкладку All devices
                                self.textBrowser.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Иначе если аварии нет 
                            else:
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['low_temp'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['low_temp'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_temp'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_temp'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['low_signal_power'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['low_signal_power'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]
                                # Выводим значение во вкладку ALL info 
                                self.textBrowser.append(word)

                        # Если мы получили сообщение с ошибкой, то 
                        elif error:
                            # Подсвечиваем строку красным цветом и цвет текста белый
                            word_alarm1 = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_error, row)
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='request_err')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['request_err'][ip].get('start_time'))
                            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
                            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_error, date_time, row, delta_time)
                            #
                            self.textBrowser.append(word_alarm1)
                            # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                            if (size + 10) < geometry:
                                # Выводим значение на экран в первый столбец
                                self.textBrowser_6.append(word_alarm)
                            else:
                                # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                self.textBrowser_5.append(word_alarm)   

                    # Проверяем если siteID равен одному из значений, то
                    elif site_id == '151' or site_id == '152' or site_id == '153' or site_id == '154' or site_id == '155' \
                        or site_id == '156' or site_id == '144' or site_id == '121' or site_id == '158' or site_id == '25' \
                            or site_id == '27' or site_id == '24' or site_id == '28' or site_id == '30':
                        if temperature and voltege_in and voltege_out:
                            # Устанавливаем стили нашей строке с данными
                            word = '''<p><img src="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, row)
                            # Если входное напряжение равно (АВАРИЯ ОТКЛЮЧЕНИЕ ЭЛЕКТРОЭНЕРГИИ)
                            if int(voltege_in) < 180:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время 
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='power_alarm')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['power_alarm'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'volt_in')
                                # Подсвечиваем строку темно оранжевым цветом и цвет текста белый подставляем  дату и время возникновения аварии,
                                #  строку с параметрами авриии и длительность аварии
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку темно оранжевым цветом и цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)

                                # Если выходное напряжение равно порогу низкого напряжения (АВАРИЯ ПО НИЗКОМУ НАПРЯЖЕНИЮ)
                                if float(voltege_out) <= self.low_voltage:
                                # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                                # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                    # Получаем дату возникновения аврии
                                    date_time = self._get_alarm_date_time(ip, key='low_voltage')
                                    # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                    delta_time = self._convert_time(time.time() - self.date_alarm['low_voltage'][ip].get('start_time'))
                                    #
                                    row = self._parse_line(row, key = 'volt_low')
                                    # Подсвечиваем строку темно красным цветом и цвет текста белый подставляем  дату и время возникновения аварии,
                                    # строку с параметрами авриии и длительность аварии 
                                    word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                    # Подсвечиваем строку темно красным цветом и цвет текста белый подставляем строку
                                    # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                    word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_critical, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_2.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Поскольку высокое напряжение по степени важности ниже пропадания электроэнергии и низкому 
                            # напряжению то при выполнении одного из условий выше мы условие по высокому напряжению не проверяем
                            elif int(voltege_in) >= self.hight_voltage:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время  
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_voltage')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_voltage'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'volt_in')
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии 
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_2.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip] 

                            # Поскольку высокая, низкая температуры по степени важности ниже остальных аварий,
                            # то при выполнении одного из условий выше мы условие по высокой, низкой тем-рам не проверяем 
                            elif int(temperature) >= self.hight_temp or int(temperature) <= self.low_temp:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_temp')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии 
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_temp'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'temp')
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии 
                                word_alarm = '''<p><img src="{}">  <span style="background-color:#ffff00; 
                                color: rgb(254, 0, 0);">{} {} </span> <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color:#ffff00; 
                                color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_2.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Иначе, если аварии нет 
                            else:
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['power_alarm'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['power_alarm'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_temp'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_temp'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['low_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['low_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]
                                # Выводим значение во вкладку ALL info 
                                self.textBrowser_2.append(word)

                        # Если мы получили сообщение с ошибкой, то 
                        elif error:
                            # Подсвечиваем строку красным цветом и цвет текста белый
                            word_alarm1 = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_error, row)
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='request_err')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['request_err'][ip].get('start_time'))
                            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
                            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_error, date_time, row, delta_time)
                            #
                            self.textBrowser_2.append(word_alarm1)
                            # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                            if (size + 10) < geometry:
                                # Выводим значение на экран в первый столбец
                                self.textBrowser_6.append(word_alarm)
                            else:
                                # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                self.textBrowser_5.append(word_alarm)

                    # Проверяем если siteID равен одному из значений, то
                    elif site_id == '32' or site_id == '34' or site_id == '35' or site_id == '39' or site_id == '40' or site_id == '41'\
                        or site_id == '48' or site_id == '49' or site_id == '50' or site_id == '52' or site_id == '61' \
                        or site_id == '62' or site_id == '42' or site_id == '19' or site_id == '16' or site_id == '20':
                        # Проверяем если мы получили значения температуры temperature И входного напряжения voltege_in И выходное напряжение
                        if temperature and voltege_in and voltege_out:
                            # Устанавливаем стили нашей строке с данными
                            word = '''<p><img src="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, row)
                            # Если входное напряжение равно (АВАРИЯ ОТКЛЮЧЕНИЕ ЭЛЕКТРОЭНЕРГИИ)
                            if int(voltege_in) < 180:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='power_alarm') 
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии 
                                delta_time = self._convert_time(time.time() - self.date_alarm['power_alarm'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'volt_in')
                                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии  
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{} {}</span>  <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)

                                # Если выходное напряжение равно порогу низкого напряжения (АВАРИЯ ПО НИЗКОМУ НАПРЯЖЕНИЮ)
                                if float(voltege_out) <= self.low_voltage:
                                # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                                # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                    # Получаем дату возникновения аврии
                                    date_time = self._get_alarm_date_time(ip, key='low_voltage') 
                                    # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии 
                                    delta_time = self._convert_time(time.time() - self.date_alarm['low_voltage'][ip].get('start_time'))
                                    #
                                    row = self._parse_line(row, key = 'volt_low')
                                    # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем  дату и время возникновения аварии,
                                    # строку с параметрами авриии и длительность аварии  
                                    word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{} {}</span>  <strong>{} </strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                    # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем строку
                                    # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                    word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_critical, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_3.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Поскольку высокое напряжение по степени важности ниже пропадания электроэнергии и низкому 
                            # напряжению то при выполнении одного из условий выше мы условие по высокому напряжению не проверяем
                            elif int(voltege_in) >= self.hight_voltage:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_voltage') 
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии 
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_voltage'][ip].get('start_time'))  
                                #
                                row = self._parse_line(row, key = 'volt_in')            
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии  
                                word_alarm = '''<p><img src="{}"><span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{} {}</span>  <strong>{}</strong></span></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_3.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]
            
                            # Поскольку высокая, низкая температуры по степени важности ниже остальных аварий,
                            # то при выполнении одного из условий выше мы условие по высокой, низкой тем-рам не проверяем 
                            elif int(temperature) >= self.hight_temp or int(temperature) <= self.low_temp:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_temp')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_temp'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'temp')
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии  
                                word_alarm = '''<p><img src="{}">  <span style="background-color:#ffff00; 
                                color: rgb(254, 0, 0);">{} {}</span> <strong>{}</strong></span></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color:#ffff00; 
                                color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_3.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Иначе, если аварии нет 
                            else:
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['power_alarm'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['power_alarm'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_temp'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_temp'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['low_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['low_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]
                                # Выводим значение во вкладку ALL info 
                                self.textBrowser_3.append(word)

                        # Если мы получили сообщение с ошибкой, то 
                        elif error:
                            # Подсвечиваем строку красным цветом и цвет текста белый
                            word_alarm1 = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_error, row)
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='request_err')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['request_err'][ip].get('start_time'))
                            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
                            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{}</strong></p>'''.format(self.path_icon_error, date_time, row, delta_time)
                            #
                            self.textBrowser_3.append(word_alarm1)
                            # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                            if (size + 10) < geometry:
                                # Выводим значение на экран в первый столбец
                                self.textBrowser_6.append(word_alarm)
                            else:
                                # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                self.textBrowser_5.append(word_alarm)

                    # Иначе если значение siteID не подходит не под один критерий, то выводим в это окно сообщения
                    else:
                        # Проверяем если мы получили значения температуры temperature И входного напряжения voltege_in И выходное напряжение
                        if temperature and voltege_in and voltege_out:
                            # Устанавливаем стили нашей строке с данными
                            word = '''<p><img src="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, row)
                            # Если входное напряжение равно 0 (АВАРИЯ ОТКЛЮЧЕНИЕ ЭЛЕКТРОЭНЕРГИИ)
                            if int(voltege_in) < 180:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='power_alarm')  
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['power_alarm'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'volt_in')
                                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии  
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{} {}</span> <strong>{}</strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ff4500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)

                                # Если выходное напряжение равно порогу низкого напряжения (АВАРИЯ ПО НИЗКОМУ НАПРЯЖЕНИЮ)
                                if float(voltege_out) <= self.low_voltage:
                                # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                                # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                    # Получаем дату возникновения аврии
                                    date_time = self._get_alarm_date_time(ip, key='low_voltage')
                                    # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                    delta_time = self._convert_time(time.time() - self.date_alarm['low_voltage'][ip].get('start_time'))
                                    #
                                    row = self._parse_line(row, key = 'volt_low')
                                    # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем  дату и время возникновения аварии,
                                    # строку с параметрами авриии и длительность аварии  
                                    word_alarm = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{} {}</span> <strong>{}</strong></span></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                    # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем строку
                                    # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                    word_alarm1 = '''<p><img src="{}">  <span style="background-color: #B22222; 
                                    color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_critical, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_4.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран
                                    # во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Поскольку высокое напряжение по степени важности ниже пропадания электроэнергии и низкому 
                            # напряжению то при выполнении одного из условий выше мы условие по высокому напряжению не проверяем
                            elif float(voltege_in) >= self.hight_voltage:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_voltage')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_voltage'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'volt_in')
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии  
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{} {}</span>  <strong>{}</strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffa500; 
                                color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_4.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран
                                    # во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Поскольку высокая, низкая температуры по степени важности ниже остальных аварий,
                            # то при выполнении одного из условий выше мы условие по высокой, низкой тем-рам не проверяем 
                            elif int(temperature) >= self.hight_temp or int(temperature) <= self.low_temp:
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время
                                # Получаем дату возникновения аврии
                                date_time = self._get_alarm_date_time(ip, key='hight_temp')
                                # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                                delta_time = self._convert_time(time.time() - self.date_alarm['hight_temp'][ip].get('start_time'))
                                #
                                row = self._parse_line(row, key = 'temp')
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
                                # строку с параметрами авриии и длительность аварии  
                                word_alarm = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{} {}</span>  <strong>{}</strong></p>'''.format(self.path_icon_warn, date_time, row, delta_time)
                                # Подсвечиваем строку желтым цветом и цвет текста красный подставляем строку
                                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                                word_alarm1 = '''<p><img src="{}">  <span style="background-color: #ffff00; 
                                color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, row)
                                # Выводим значение на экран во вкладку All devices
                                self.textBrowser_4.append(word_alarm1)
                                # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                                if (size + 40) < geometry:
                                    # Выводим значение на экран в первый столбец
                                    self.textBrowser_6.append(word_alarm)
                                else:
                                    # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                    self.textBrowser_5.append(word_alarm)
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]

                            # Иначе, если аварии нет 
                            else:
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                if self.date_alarm['power_alarm'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['power_alarm'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_temp'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_temp'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['low_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['low_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['hight_voltage'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['hight_voltage'][ip]
                                # Используем метод get который запрашивает ключ(ip) у словаря, и если его нет, вместо ошибки возвращает None
                                elif self.date_alarm['request_err'].get(ip):
                                    # Удаляем запись из словаря date_alarm
                                    del self.date_alarm['request_err'][ip]
                                # Выводим значение во вкладку ALL info
                                self.textBrowser_4.append(word)
                        # Если мы получили сообщение с ошибкой, то 
                        elif error:
                            # Подсвечиваем строку красным цветом и цвет текста белый
                            word_alarm1 = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{}</span></p>'''.format(self.path_icon_error, row)
                            # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                            # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
                            # Получаем дату возникновения аврии
                            date_time = self._get_alarm_date_time(ip, key='request_err')
                            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                            delta_time = self._convert_time(time.time() - self.date_alarm['request_err'][ip].get('start_time'))
                            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
                            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
                            word_alarm = '''<p><img src="{}"> <span style="background-color: #FF0000;
                            color: rgb(255, 255, 255);">{} {}</span> <strong>{}</strong></p>'''.format(self.path_icon_error, date_time, row, delta_time)
                            #
                            self.textBrowser_4.append(word_alarm1)
                            # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
                            if (size + 10) < geometry:
                                # Выводим значение на экран в первый столбец
                                self.textBrowser_6.append(word_alarm)
                            else:
                                # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец 
                                self.textBrowser_5.append(word_alarm)

            # Создаем экземпляр класса sql
            sql = ConnectSqlDB()
            # Добавляем словарь date_alarm в БД в формате json
            try:
                sql.add_date_time(self.date_alarm)
            except (sqlite3.IntegrityError, sqlite3.OperationalError, NoneType):
                self.logger.error("Ошибка запроса из БД: sql.add_date_time(self.date_alarm)")
            # Выводим сообщение в статус бар с изображением и текстом "Готово"
            self.lbl.setText('<img src="{}">  Готово'.format(self.path_icon_done))
    
    # Запускаем таймер, который будет запускать метод run
    def start(self):
        # Переводим флаг в False, что второе окно не закрыто
        self.isClose_window = False
        # Запускаем timer, который запускает метод run
        self.timer.start(5000)
        # Запускаем timer_clock, который запускает метод show_clock
        self.timer_clock.start()
        # Добавляем в статус бар наш экземпляр класса lbl
        self.lbl.setText('<img src="{}">  Выполняется загрузка...'.format(self.path_icon_load))
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
        # Очищаем окна от данных
        self.textBrowser.clear()
        self.textBrowser_2.clear()
        self.textBrowser_3.clear()
        self.textBrowser_4.clear()
        self.textBrowser_5.clear()
        self.textBrowser_6.clear()
        event.accept()
