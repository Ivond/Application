#
import re
import time
import logging
import requests
import sqlite3
from pathlib import Path
from PyQt5.QtCore import QThread
from datetime import datetime
from class_SqlLiteMain import ConnectSqlDB

class ThreadMonitorAlarms(QThread):

    def __init__(self):
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
        # Настройка логирования
        self.path_logs = Path(Path.cwd(), "logs", "logs_monitor_alarm.txt")
        self.logger_err = logging.getLogger('monitor_alarm')
        self.logger_err.setLevel(logging.INFO)
        fh_err = logging.FileHandler(self.path_logs, 'w')
        formatter_err = logging.Formatter('%(asctime)s %(name)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_err.setFormatter(formatter_err)
        self.logger_err.addHandler(fh_err)
        
        # Создаем переменную в которой будем хранить адрес сервера Telegram переданное при запуске Бота.
        self.url = "https://api.telegram.org/bot"
        # Создаем переменную token в которой будем хранить токен нашего бота
        self.token = "5412146072:AAF8TW4mDK_N7folBpjVmN1sAGG6fDlV_iU"
        # Переменная определяет интервал между опросами метода run
        self.interval_time = 5
        # Значение количества проверок перед отправкой сообщения
        self.num = 3
        # Записываем значение высокой температуры
        self.hight_temp = 35
        # Записываем значение низкой температуры
        self.low_temp = 0
        # Записываем значение низкого напряжения
        self.low_volt = 48.0
        # Записываем значения низкого значения топлива
        self.low_oil_limit = 35
        # Записываем дефолтное(начальное) значение уровня сигнала Fiber транспондера MAC&C
        self.signal_level_fiber = -25
        # Записываем дефолтное(начальное) значение низкой температуры Fiber транспондера MAC&C
        self.low_temp_fiber = 5
        # Записываем дефолтное(начальное) значение высокой температуры Fiber транспондера MAC&C
        self.hight_temp_fiber = 50
        
        # Создаем экземпляр класса sql
        #with ConnectSqlDB() as sql:
            #try:
                # Делаем запрос к БД и получаем словарь с данными (дата и время возникновения аварий)
                #self.dict_messages = sql.get_values_list_db('data', table='Alarms')
            #except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
                #self.logger_err.error("Ошибка запроса из БД: sql.get_values_list_db('data', table='Alarms')")
                # Записываем значения аврий в словарь
        self.dict_messages = {'power_alarm':{},
                                'low_voltage':{},
                                'limit_oil':{},
                                'hight_temp':{},
                                'low_temp':{},
                                'low_signal_power':{},
                                'channel': {},
                                'error': {},
                                'date':{}
                            }
            #try:
                # Делаем запрос к БД и получаем словарь с текущими авариями
                #self.dict_interim_messages = sql.get_values_list_db('data', table='Interim')
            #except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
                #self.logger_err.error("Ошибка запроса из БД: sql.get_values_list_db('data', table='Interim')")
                # Если попали в исключение значит не смогли получить данные из БД, тогда подставляем словарь   
        self.dict_interim_messages = {'power_alarm':{},
                                        'low_voltage':{},
                                        'limit_oil':{},
                                        'alarm_stop_of_motor':{},
                                        'hight_temp':{},
                                        'low_temp':{},
                                        'low_signal_power':{},
                                        'channel': {},
                                        'error': {}
                                        }
        # Словарь для хранения параметров по ДГУ АВТОБУС
        self.dict_DGU = {}
        # Записываем результат snmp опроса оборудования в список 
        self.snmp_traps = []

    # Функция делает подмену ip адреса на Имя устройства
    def _dns(self, ip):
        try:
            # Создаем экземпляр класса sql
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД, получаем имя устройства соответствующее Ip адреса
                description = sql.get_db('description', ip=ip, table='Devices')[0]
            return description
        except (sqlite3.IntegrityError, IndexError, TypeError) :
            self.logger_err.error(f'ThreadMonitorAlarm "_dns": Ошибка запроса данных из таблицы Devices: {ip}') 

    # Метод возращает описание устройства, принимает на вход ip адрес устройства и строку со значениями полученными при SNMP запросе
    def _parse_channel_name(self, ip, port):
        # Получаем значение порта из строки
        #match = re.match(r'.+Port: (?P<port>\d*)', line)
        #if match:
            #port = match.group('port')
        try:
            # Создаем экземпляр класса sql
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД, получаем список в котором кортеж со значениями (количества трафика и имя канала)
                channel_name = sql.get_db('description', ip=ip, port=port, table='Ports')[0][0]
            return channel_name
        except (sqlite3.IntegrityError, IndexError, TypeError) :
            self.logger_err.error(f'ThreadMonitorAlarm "_parse_name": ошибка при получении описании устройства с ip адресом: {ip}')

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

    # Функция из полученных на вход данных, парсит ip адрес устройства и возвращает это значение
    def _parse_ip(self, line):
        try:
            ip = line.split()[2].strip()
            return ip
        except (TypeError, IndexError):
            pass

    # ДГУ АВТОБУС

    # Функция из полученных на вход данных, парсит значение количества топлива и возвращает это значение
    def _parse_limit_oil(self, line):
        match = re.match(r'.+Топл\.:(?P<limit>\d+)%', line)
        if match:
            limit_oil = match.group('limit').strip()
            return limit_oil

    #
    def _parse_alarm_motor(self, line):
        match = re.match(r'.+Двиг\.:(?P<motor>\d*)', line)
        if match:
            alarm_stop_of_motor = match.group('motor').strip()
            return alarm_stop_of_motor

    #
    def _parse_hight_temp_water(self, line):
        bit_2 = re.match(r'.+Высокая температура О/Ж: \[(?P<hight_water>\d*)\]', line)
        if bit_2:
            hight_temp_water = bit_2.group('hight_water').strip()
            return hight_temp_water

    #
    def _parse_motor(self, line):
        bit_0 = re.match(r'.+Работа двигателя: \[(?P<motor>\d*)\]', line)
        if bit_0:
            motor = bit_0.group('motor').strip()
            return motor

    #      
    def _parse_low_temp_water(self, line):
        bit_3 = re.match(r'.+Низкая температура О/Ж: \[(?P<low_water>\d*)\]', line)
        if bit_3:
            low_water = bit_3.group('low_water').strip()
            return low_water

    #
    def _parse_low_pressure_oil(self, line):
        bit_4 = re.match(r'.+Низкое давление масла: \[(?P<low_oil>\d*)\]', line)
        if bit_4:
            low_oil = bit_4.group('low_oil').strip()
            return low_oil

    #
    def _parse_level_water(self, line):
        bit_6 = re.match(r'.+Низкий уровень О/Ж: \[(?P<level_water>\d*)\]', line)
        if bit_6:
            level_water = bit_6.group('level_water').strip()
            return level_water

    #   
    def _parse_low_level_oil(self, line):
        bit_7 = re.match(r'.+Уровень топлтва: \[(?P<level_oil>\d*)\]', line)
        if bit_7:
            level_oil = bit_7.group('level_oil').strip()
            return level_oil

    #
    def _parse_switch_motor(self, line):
        bit_8 = re.match(r'.+Переключатель авт\.: \[(?P<switch_motor>\d*)\]', line)
        if bit_8:
            switch_motor = bit_8.group('switch_motor').strip()
            return switch_motor

    #
    def _parse_low_batt(self, line):
        bit_10 = re.match(r'.+Низкий заряд АКБ: \[(?P<low_batt>\d*)\]', line)
        if bit_10:
            low_batt = bit_10.group('low_batt').strip()
            return low_batt

    # Функция из полученных на вход данных, парсит значение температуры и возвращает это значение
    def _parse_temperature(self, line):
        match = re.match(r'.+\*C: +(?P<temp_value>-*\d+)', line)
        if match:
            temperature_value = match.group('temp_value').strip()
            return temperature_value

    def _parse_line(self, line, value=None):
        match = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>IN.+\*C) (?P<temp>\d*)', line)
        if match:
           date = match.group('date').strip()  
           description = match.group('description').strip()
           temp = match.group('temp').strip()
           line = description + ' ' + f'<strong>{temp}<\strong>'
           return date, line

    # Функция из полученных данных парсит значение даты, все параметры оборудования и возвращает эти значения
    def _parse_message(self, line):
        match = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>IN.+) ', line)
        match1 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>ОПС.+)', line)
        match2 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>TxFiber2.+)', line)
        match3 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>ДГУ:.+):', line)
        match4 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>InOctets.+)', line)
        match5 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>CISCO.+)', line)
        # Это условие для ИБЭП
        if match:
            date = match.group('date').strip()
            description = match.group('description').strip()
            return date, description
        # Это условия для сообщения приходящего по протоколу ModBus
        elif match1:
            date = match1.group('date').strip()
            description = match1.group('description').strip(' ')
            return date, description
        # Это условие для MAC&C
        elif match2:
            date = match2.group('date').strip()
            description = match2.group('description').strip(' ')
            return date, description
        # Это для ДГУ АВТОБУС
        elif match3:
            date = match3.group('date').strip()
            description = match3.group('description').strip()
            return date, description
        # Это условие для Cisco
        elif match4:
            date = match4.group('date').strip()
            description = match4.group('description').strip()
            return date, description
        # Это условие для Cisco ERROR
        elif match5:
            date = match5.group('date').strip()
            description = match5.group('description').strip()
            return date, description
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: "_parse_message" не удалось получить значение строка с данными message из: {line}')
            
    # Функция вычисляет время работы оборудования на АКБ и вовращает это значение 
    def _battery_operating_time(self, ip, time_end):
        try:
            # Создаем экземпляр класса sql
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД получаем словарь
                db_alarm = sql.get_values_list_db('data', table='Alarms')
            #
            if db_alarm['date']:
                # Изменяем формат даты и времени начала возникновения аварии
                start_time = datetime.strptime((db_alarm['date'][ip]).strip(), "%d-%m-%Y  %H:%M:%S")
                # Изменяем формат даты и времени окончании аварии
                end_time = datetime.strptime((time_end).strip(), "%d-%m-%Y  %H:%M:%S")
                # Вычисляем время работы от АКБ оборудования в секундах
                sec = (end_time - start_time).seconds
                # Вычисляем количество часов поделив на 3600 без остатка
                hour = sec // 3600
                if hour:
                    # Вычисляем остаток от деления на 3600 и записываем в переменную sec
                    sec = sec % 3600
                    # Вычиляем количество минут поделив на 60 без остатка
                    min = sec // 60
                    if min:
                        # Вычисляем остаток от деления на 60
                        sec = sec % 60
                        # Возвращаем результат
                    return f'{hour}ч. {min}мин. {sec}сек.'
                # Вычисляем количество минут поделив на 60 без остатка
                min = sec // 60
                if min:
                    # Вычисляем остаток от деления на 60 и записываем в переменную sec
                    sec = sec % 60
                    # Возвращаем результат
                    return f'{min}мин. {sec}сек.'
                else:
                    # Возвращаем результат
                    return f'{sec}сек.'
            else:
                return 0
        except sqlite3.IntegrityError:
            pass

    # MAC&C

    # Функция из полученных на вход данных, парсит значение температуры модуля SFP_2 и возвращает это значение
    def _parse_temp_fiber2(self, line):
        match = re.match(r'.+TempFiber2: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber2 = match.group('temp_value').strip()
            return temp_fiber2
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_fiber2 из: {line}')

    # Функция из полученных на вход данных, парсит значение температуры  модуля SFP_3 и возвращает это значение
    def _parse_temp_fiber3(self, line):
        match = re.match(r'.+TempFiber3: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber3 = match.group('temp_value').strip()
            return temp_fiber3
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_fiber2 из: {line}')

    # Функция из полученных на вход данных, парсит значение уровня сигнала передачи модуля SFP_2 и возвращает это значение
    def _parse_tx_fiber2(self, line):
        match = re.match(r'.+TxFiber2: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber2 = match.group('tx_value').strip()
            return tx_fiber2
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_fiber2 из: {line}')

    # Функция из полученных на вход данных, парсит значение уровня сигнала передачи модуля SFP_3 и возвращает это значение
    def _parse_tx_fiber3(self, line):
        match = re.match(r'.+TxFiber3: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber3 = match.group('tx_value').strip()
            return tx_fiber3
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_fiber2 из: {line}')
    
    # Функция из полученных на вход данных, парсит значение приемного уровня сигнала модуля SFP_2 и возвращает это значение
    def _parse_rx_fiber2(self, line):
        match = re.match(r'.+RxFiber2: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber2 = match.group('rx_value').strip()
            return rx_fiber2
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_fiber2 из: {line}')

    # Функция из полученных на вход данных, парсит значение приемного уровня сигнала модуля SFP_3 и возвращает это значение
    def _parse_rx_fiber3(self, line):
        match = re.match(r'.+RxFiber3: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber3 = match.group('rx_value').strip()
            return rx_fiber3
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_fiber2 из: {line}')

    # CISCO

    # Метод возращает порт устройства, принимает на вход строку со значениями полученными при SNMP запросе
    def _parse_port(self, line):
        # Получаем значение порта из строки
        match = re.match(r'.+Port: (?P<port>\d*)', line)
        if match:
            port = match.group('port')
            return port

    # Метод возвращает рабочее состояние порта коммутатора, принимает на вход строку с параметрами полученную при SNMP запросе
    def _parse_status_port(self, line):
        match = re.match(r'.+OperStatus: (?P<status_port>\w+)', line)
        if match:
            oper_status = match.group('status_port').strip()
            return oper_status
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: "_parse_status_port "ошибка получения значения статуса порта oper_status из: {line}')
    
    # Метод возвращает значение количества трафика на порту коммутатора, принимает на вход строку с параметрами полученную при SNMP запросе
    def _parse_octets_on_port(self, line):
        match = re.match(r'.+OutOctets: \d* (?P<bs>\S+)', line)
        if match:
            bs = match.group('bs').strip()
            return bs
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: "_parse_counters_port "ошибка получения значения количества трафика OutOctets из: {line}')

    # Метод возвращает значение количества входящего трафика на порту коммутатора, принимает на вход строку с параметрами полученную при SNMP запросе
    def _parse_in_octets_on_port(self, line):
        match = re.match(r'.+InOctets: \d* (?P<bs>\S+);', line)
        if match:
            bs = match.group('bs').strip()
            return bs
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: "_parse_in_octets_on_port "ошибка получения значения количества трафика IntOctets из: {line}')
    
    # Функция отправляет сообщение чат Ботом 
    def _sender(self, message):
        try:
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД получаем список chat_id пользователей
                chat_id = sql.get_values_list_db('chat_id', table='Users')
            if chat_id:
                for id in chat_id:
                    # отправляем сообщенние вызывав метод send_message, результат записываем в переменную code_status
                    code_status = self.send_message(id, message) # --> int
                    # Если code_status не равен 200
                    if code_status != 200:
                        self.sleep(5)
                        self.send_message(id, message) 
            else:
                self.logger_err.error('ThreadMonitorAlarm "_sender". Нет информации об chat_id в таблицы Users')
        except sqlite3.IntegrityError():
            self.logger_err.error('ThreadMonitorAlarm "_sender". Ошибка получения chat_id из таблицы Users')

    # Метод отправляет ботом сообщение пользователю, принимая на вход id пользователя и текс сообщения
    def send_message(self, chat_id, text):
        # Создаем метод для post запроса 
        method = self.url + self.token + "/sendMessage"
        # Формируем параметры которые мы будем передавать при post запросе на url API
        data={"chat_id":chat_id, "text":text}
        result = requests.post(method, json=data)
        return result.status_code

    # Функция обрабатывает входящие значения из файла.
    def run(self):
        # Счетчик записываем количество итераций сделанных циклом while
        self.counters = 1
        while True:
            # Если в переменной snmp_traps есть данные, то
            if self.snmp_traps:
                # Перебираем список с данными по строкам
                for line in self.snmp_traps:
                    try:
                        # Получаем значение ip адреса вызвав метод _parse_ip
                        ip = self._parse_ip(line)
                        # Получаем имя устройства вызвав метод _dns передав ему ip адрес и записываем в переменную name
                        self.name = self._dns(ip)
                    except TypeError:
                        continue

               # ПРОВЕРКА КОЛИЧЕСТВА ТОПЛИВА И СОСТОЯНИЕ РАБОТЫ ДВИГАТЕЛЯ

                    if 'ОПС' in line:
                        # Получаем значения количества топлива вызвав метод _parse_limit_oil и записываем в переменную limit_oil
                        limit_oil = self._parse_limit_oil(line)
                        # Получаем значение состояния работы двигателя вызвав метод _parse_alarm_motor
                        alarm_stop_of_motor = self._parse_alarm_motor(line)
                        # Проверяем если получили значение состояния двигателя alarm_stop_of_motor
                        if alarm_stop_of_motor:
                            # Если значение равно и ip адреса нет в словаре
                            if alarm_stop_of_motor == 1 and ip not in self.dict_interim_messages['alarm_stop_of_motor']:
                                # Получаем имя устройства вызвав метод _dns передав ему ip адрес и записываем в переменную name
                                #name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку вывода с оборудования, получаем дату и описание и записываем их в переменные
                                date, description = self._parse_message(line)
                                # Формируем сообщение, которое будет отправленно пользователям
                                message = f"{date} {self.name}: АВАРИЙНАЯ ОСТАНОВКА ДВИГАТЕЛЯ: {description}"
                                # Добавляем значение Ip в словарь dict_interim_messages
                                self.dict_interim_messages['alarm_stop_of_motor'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)
                            # Если значение равно 0 И ip адрес есть в словаре
                            elif alarm_stop_of_motor == 0 and ip in self.dict_interim_messages['alarm_stop_of_motor']:
                            # Удаляем сообщение об аварии из dict_messages
                                try:
                                    # Удаляем значение из словаря
                                    del self.dict_interim_messages['alarm_stop_of_motor'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии alarm_stop_of_motor')

                        # Проверяем если получили значение количества топлива limit_oil
                        if limit_oil:
                            # Проверяем если значение уровня топлива меньше порога и dict_interim_messages не содержит сообщение с таким ip адресом
                            if int(limit_oil) < self.low_oil_limit and ip not in self.dict_interim_messages['limit_oil']:
                                # Добавляем в словарь dict_interim_messages индекс сообщения 1 - это значит мы получили
                                # сообщение об аврии первый раз, а так же количество итераций цикла.
                                self.dict_interim_messages['limit_oil'][ip] = [1, self.counters]
                            # Проверяем если значение уровня топлива меньше порога И индекс сообщения = 1 И разность итераций цикла равно num ИЛИ num+1
                            elif int(limit_oil) < self.low_oil_limit and self.dict_interim_messages['limit_oil'][ip][0] == 1 \
                                and ((self.counters - self.dict_interim_messages['limit_oil'][ip][1]) == self.num \
                                    or (self.counters - self.dict_interim_messages['limit_oil'][ip][1]) == self.num + 1):
                                # Получаем имя устройства вызвав метод _dns передав ему ip адрес и записываем в переменную name
                                #name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку вывода с оборудования, получаем дату и описание и записываем их в переменные
                                date, description = self._parse_message(line)
                                # Формируем сообщение, которое будет отправленно пользователям
                                message = f"{date} {self.name}: Низкий уровень топлива: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['limit_oil'][ip] = message
                                # Добавляем в dict_interim_messages идекс сообщения = 2, который говорит, что мы повторно в течение нескольких итераций цикла
                                # получили одну и туже аврию
                                self.dict_interim_messages['limit_oil'][ip][0] = 2
                                # Отправляем сообщение
                                self._sender(message)

                            # Проверяем, что ip адрес есть в словаре, если ip нет, то функция get вернет None
                            elif self.dict_interim_messages['limit_oil'].get(ip):
                                # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num, значит мы второй раз не получили одну и туже аварию
                                # в течении нескольких итераций цикла
                                if self.dict_interim_messages['limit_oil'][ip][0] == 1 \
                                and (self.counters - self.dict_interim_messages['limit_oil'][ip][1]) > self.num +2:
                                    try:
                                        # Удаляем не подтвержденную аварию из словаря dict_interim_messages
                                        del self.dict_interim_messages['limit_oil'][ip]
                                    except KeyError:
                                        self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии limit_oil')

                            # Проверяем если значение уровня топлива больше порога на 10
                            if int(limit_oil) > (self.low_oil_limit +10) and ip in self.dict_messages['limit_oil']:
                                # Удаляем сообщение об аварии из dict_messages
                                try:
                                    # Удаляем значение из словаря
                                    del self.dict_messages['limit_oil'][ip]
                                    del self.dict_interim_messages['limit_oil'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии limit_oil')
                        else:
                            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение количества топлива limit_oil из: {line}')

                # ПРОВЕРКА АВАРИЙ НА MAC&C

                    elif 'TxFiber2' in line:
                        # Вызываем метод parse_tx_fiber2 получаем значение уровня передающего сигнала SFP_2 модуля
                        tx_fiber2 = self._parse_tx_fiber2(line)
                        # Вызываем метод parse_tx_fiber3 получаем значение уровня передающего сигнала SFP_3 модуля
                        tx_fiber3 = self._parse_tx_fiber3(line)
                        # Вызываем метод parse_rx_fiber2 получаем значение приемного уровня сигнала SFP_2 модуля
                        rx_fiber2 = self._parse_rx_fiber2(line)
                        # Вызываем метод parse_rx_fiber3 получаем значение приемного уровня сигнала SFP_3 модуля
                        rx_fiber3 = self._parse_rx_fiber3(line)
                        # Вызываем метод parse_temp_fiber2 получаем значение температуры SFP_2 модуля
                        temp_fiber2 = self._parse_temp_fiber2(line)
                        # Вызываем метод parse_temp_fiber3 получаем значение температуры SFP_3 модуля
                        temp_fiber3 = self._parse_temp_fiber3(line)

                    # ПРОВЕРКА УРОВНЯ СИГНАЛА FIBER2 И FIBER3
                        
                        if rx_fiber2 and rx_fiber3 and tx_fiber3 and tx_fiber2:
                            # Проверяем если значение уровня приемного и передающего сигналов меньше signal_level_fiber И ip нет в dict_interim_messages                             
                            if (int(rx_fiber2) < self.signal_level_fiber or int(rx_fiber3) < self.signal_level_fiber or int(tx_fiber2) < self.signal_level_fiber \
                                or int(tx_fiber3) < self.signal_level_fiber) and ip not in self.dict_interim_messages['low_signal_power']:
                                # Добавляем в словарь dict_interim_messages индекс сообщения 1 - это значит мы получили
                                # сообщение об аврии первый раз, а так же количество итераций цикла.
                                self.dict_interim_messages['low_signal_power'][ip] = [1, self.counters]
                            #
                            elif (int(rx_fiber2) < self.signal_level_fiber or int(rx_fiber3) < self.signal_level_fiber or int(tx_fiber2) < self.signal_level_fiber \
                                or int(tx_fiber3) < self.signal_level_fiber) and self.dict_interim_messages['low_signal_power'][ip][0] == 1 \
                                and ((self.counters - self.dict_interim_messages['low_signal_power'][ip][1]) == self.num \
                                or (self.counters - self.dict_interim_messages['low_signal_power'][ip][1]) == self.num + 1):
                                # Получаем имя объекта по ip
                                #name = self._dns(ip)
                                # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                                date, description = self._parse_message(line)
                                # Формируем сообщение которое отпавим пользователю
                                message = f"{date} {self.name}: Низкий уровень сигнала транспондера MAC&C {description}."
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['low_signal_power'][ip] = message
                                # Добавляем в dict_interim_messages идекс сообщения = 2, который говорит, что мы повторно в течение нескольких итераций цикла
                                # получили одну и туже аврию
                                self.dict_interim_messages['low_signal_power'][ip][0] = 2
                                # Отправляем сообщение
                                self._sender(message)
                            # Проверяем, что ip адрес есть в словаре, если ip нет, то функция get вернет None
                            elif self.dict_interim_messages['low_signal_power'].get(ip):
                                # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num, значит мы второй раз не получили одну и туже аварию
                                # в течении нескольких итераций цикла
                                if self.dict_interim_messages['low_signal_power'][ip][0] == 1 \
                                and (self.counters - self.dict_interim_messages['low_signal_power'][ip][1]) > self.num +2:
                                    try:
                                        # Удаляем не подтвержденную аварию из словаря dict_interim_messages
                                        del self.dict_interim_messages['low_signal_power'][ip]
                                    except KeyError:
                                        self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии low_signal_power')
                            
                            # Проверяем если значение уровня приемного и передающего сигналов больше signal_level_fiber И в dict_messages есть сообщение с таким ip
                            if (int(rx_fiber2) > self.signal_level_fiber and int(rx_fiber3) > self.signal_level_fiber and
                                int(tx_fiber2) > self.signal_level_fiber and int(tx_fiber3) > self.signal_level_fiber) and ip in self.dict_messages['low_signal_power']:
                                # Получаем имя объекта по ip
                                #name = self._dns(ip)
                                date, description = self._parse_message(line)                
                                message = f"{date} {self.name}: Уровень сигнала транспондера MAC&C восстановлен: {description}."
                                # Отправляем сообщение
                                self._sender(message)
                                # Удаляем сообщение об аварии из dict_messages
                                try:
                                    # Удаляем значение из словаря
                                    del self.dict_messages['low_signal_power'][ip]
                                    del self.dict_interim_messages['low_signal_power'][ip]
                                except KeyError:
                                        self.logger_err.error('ThreadMonitorAlarm. Ошибка удаления аварии low_signal_power')
                        else:
                            self.logger_err.error(f'Не удалось получить значение уровня сигнала rx_fiber2 из: {line}')
                    
                    # ПРОВЕРКА ВЫСОКОЙ НИЗКОЙ ТЕМПЕРАТУРЫ FIBER2 И FIBER3

                        if temp_fiber2 and temp_fiber3:
                            # Проверяем если значение уровня температуры больше hight_temp_fiber
                            # И ip нет в dict_messages, то отправляем cообщение об аварии и добавляем данные в dict_messages
                            if (int(temp_fiber2) > self.hight_temp_fiber or int(temp_fiber3) > self.hight_temp_fiber) and ip not in self.dict_messages['hight_temp']:
                                # Получаем имя объекта по ip
                                #name = self._dns(ip)
                                # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                                date, description = self._parse_message(line)
                                # Формируем сообщение которое отправим пользователю
                                message = f"{date} {self.name}: Высокая температура транспондера MAC&C: {description}."
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['hight_temp'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)

                            # Проверяем если значение уровня высокой температуры меньше hight_temp_fiber на +3 И ip есть в dict_messages, 
                            # то удаляем данные из dict_messages
                            if (int(temp_fiber2) < (self.hight_temp_fiber - 3) and int(temp_fiber3) < (self.hight_temp_fiber - 3)) and ip in self.dict_messages['hight_temp']:
                                try:
                                    # Удаляем аврию из словаря dict_messages
                                    del self.dict_messages['hight_temp'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии hight_temp MAC&C')

                            # Проверяем если значение уровня низкой температуры меньше low_temp_fiber И ip нет в dict_messages, 
                            # то отправляем cообщение об аварии и добавляем данные в dict_messages
                            if (int(temp_fiber2) < self.low_temp_fiber or int(temp_fiber3) < self.low_temp_fiber) and ip not in self.dict_messages['low_temp']:
                                # Получаем имя объекта по ip
                                #name = self._dns(ip)
                                # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                                date, description = self._parse_message(line)
                                # Формируем сообщение которое отпавим пользователю
                                message = f"{date} {self.name}: Низкая температура транспондера MAC&C: {description}."
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['low_temp'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)

                            # Проверяем если значение уровня низкой температуры больше low_temp_fiber на +3 И ip есть в dict_messages, 
                            # то удаляем данные из dict_messages
                            if (int(temp_fiber2) > (self.low_temp_fiber + 3) and int(temp_fiber3) > (self.low_temp_fiber + 3)) and ip in self.dict_messages['low_temp']:
                                try:
                                    # Удаляем аврию из словаря dict_messages
                                    del self.dict_messages['low_temp'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии low_temp MAC&C')
                        else:
                            self.logger_err.error(f'Не удалось получить значение уровня сигнала rx_fiber2 из: {line}')

                # ПРОВЕРКА НА ОШИБКИ

                    #elif 'SNMP:REQEST_ERROR' in line:
                        #pass
                    
                    # 
                    elif 'CISCO_SNMP:REQEST_ERROR' in line:
                        # Проверяем если получили ошибку И ip адреса нет в словаре dict_interim_messages
                        if 'CISCO_SNMP:REQEST_ERROR' in line and ip not in self.dict_interim_messages['error']:
                            # Добавляем в словарь dict_interim_messagess индекс сообщения 1 - это значит мы получили
                            # сообщение об аврии первый раз, а так же количество итераций цикла.
                            self.dict_interim_messages['error'][ip] = [1, self.counters]  
                        # Проверяем если получили ошибку И индекс сообщения равен 1 И разность итераций цикла равно num ИЛИ num+1
                        elif 'CISCO_SNMP:REQEST_ERROR' in line and self.dict_interim_messages['error'][ip][0] == 1 \
                            and ((self.counters - self.dict_interim_messages['error'][ip][1]) == self.num \
                                or (self.counters - self.dict_interim_messages['error'][ip][1]) == self.num + 1):
                            # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание неисправности
                            date, description= self._parse_message(line)
                            # Формируем сообщение для отправки
                            message = f"{date} {self.name}: Оборудование недоступно! {description}"
                            # Добавляем данные об аварии в dict_messages
                            self.dict_messages['error'][ip] = message
                            # Добавляем в dict_interim_messages идекс сообщения 2, который говорит, что мы второй раз
                            # получили одну и туже аврию в течении нескольких итераций цикла
                            self.dict_interim_messages['error'][ip][0] = 2
                            # Отправляем сообщение
                            self._sender(message)
                            print(message)
                        # Проверяем, что ip адрес есть в словаре, если ip нет, то функция get вернет None
                        elif self.dict_interim_messages['error'].get(ip):
                            # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num+2, значит мы второй раз не получили одну и туже аварию
                            if self.dict_interim_messages['error'][ip][0] == 1 \
                            and (self.counters - self.dict_interim_messages['error'][ip][1]) > self.num + 2:
                                try:
                                    # Удаляем не подтвержденную аварию из словаря dict_interim_messages
                                    del self.dict_interim_messages['error'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии error') 

                    elif 'SNMP:REQEST_ERROR' in line:
                        pass        
                
                # ПРОВЕРКА ПАРАМЕТРОВ ДГУ

                    elif 'ДГУ' in line:
                        hight_temp_water = self._parse_hight_temp_water(line)
                        motor = self._parse_motor(line)
                        low_temp_water = self._parse_low_temp_water(line)
                        low_pressure_oil = self._parse_low_pressure_oil(line)
                        low_level_oil = self._parse_low_level_oil(line)
                        switch_motor = self._parse_switch_motor(line)
                        low_level_water = self._parse_level_water(line)
                        low_batt = self._parse_low_batt(line)
                        #
                        if hight_temp_water and int(hight_temp_water) == 1 and 'hight_temp_water' not in self.dict_DGU:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['hight_temp_water'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        elif motor and int(motor) == 1:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['motor'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        elif low_temp_water and int(low_temp_water) == 1 and 'low_temp_water' not in self.dict_DGU:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['low_temp_water'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        elif low_pressure_oil and int(low_pressure_oil)  == 1 and 'low_pressure_oil' not in self.dict_DGU:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['low_pressure_oil'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        elif low_level_oil and int(low_level_oil) == 1 and 'low_level_oil' not in self.dict_DGU:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['low_level_oil'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        elif switch_motor and int(switch_motor) == 1 and 'switch_motor' not in self.dict_DGU:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['switch_motor'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        elif low_level_water and int(low_level_water) == 1 and 'low_level_water' not in self.dict_DGU:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['low_level_water'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        elif low_batt and int(low_batt) == 1 and 'low_batt' not in self.dict_DGU:
                            # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                            date, description = self._parse_message(line)
                            # Формируем сообщение которое отпавим пользователю
                            message = f"{date} {self.name}: {description}."
                            # Добавляем данные об аварии в dict_messages
                            self.dict_DGU['low_batt'] = message
                            # Отправляем сообщение
                            self._sender(message)
                        try:
                            #
                            if hight_temp_water and int(hight_temp_water) == 0 and 'hight_temp_water' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['hight_temp_water']
                            #
                            if motor and int(motor) == 0 and 'motor' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['motor']
                            #
                            if low_temp_water and int(low_temp_water) == 0 and 'low_temp_water' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['low_temp_water']
                            #
                            if low_pressure_oil and int(low_pressure_oil)  == 0 and 'low_pressure_oil' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['low_pressure_oil']
                            #
                            if low_level_oil and int(low_level_oil) == 0 and 'low_level_oil' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['low_level_oil']
                            #
                            if switch_motor and int(switch_motor) == 0 and 'switch_motor' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['switch_motor']
                            #
                            if low_level_water and int(low_level_water) == 0 and 'low_level_water' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['low_level_water']
                            #
                            if low_batt and int(low_batt) == 0 and 'low_batt' in self.dict_DGU:
                                # Удаляем аврию из словаря dict_messages
                                del self.dict_DGU['low_batt']
                        except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии ModBus ДГУ')

                # CISCO
                    #
                    elif 'Port' in line:
                        port = self._parse_port(line)
                        channel_name = self._parse_channel_name(ip, port)
                        out_octets = self._parse_octets_on_port(line)
                        in_octets = self._parse_in_octets_on_port(line)
                        oper_status = self._parse_status_port(line)
                        #
                        if out_octets and oper_status and in_octets:
                            #
                            if (out_octets == 'bs' or in_octets == 'bs' or oper_status == 'Down') and ip not in self.dict_messages['channel']:
                                # Вызываем метод _parse_message, получаем дату и время возниконовения аварии и описание неисправности
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f'{date} Пропадание канала "{channel_name}": {description}'
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['channel'][ip] = {port:message}
                                # Отправляем сообщение
                                self._sender(message)
                            
                            elif (out_octets == 'bs' or in_octets == 'bs' or oper_status == 'Down') and port not in self.dict_messages['channel'][ip]:
                                # Вызываем метод _parse_message, получаем дату и время возниконовения аварии и описание неисправности
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f'{date} Пропадание канала "{channel_name}": {description}'
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['channel'][ip][port] = message
                                # Отправляем сообщение
                                self._sender(message)

                            # Проверяем если количество трафика равно Мбит/c или Кбит/c и статсу порта Up и сообщение с таким ip есть в словаре
                            elif (out_octets == 'Mbs' or (out_octets == 'Kbs' and in_octets == 'Kbs')) and oper_status == 'Up' and ip in self.dict_messages['channel']:
                                #
                                if self.dict_messages['channel'][ip].get(port):
                                    # Вызываем метод _parse_message, получаем дату и время устранения аварии и описание параметров порта
                                    date, description = self._parse_message(line)
                                    message = f'{date} Работа канала "{channel_name}" восстановлена: {description}'
                                    # Отправляем сообщение
                                    self._sender(message)
                                    # Удаляем сообщение об аварии из dict_messages
                                    try:
                                         del self.dict_messages['channel'][ip][port]
                                    except KeyError:
                                        self.logger_err.error(f'Ошибка удаления аварии channel_alarm IP: {ip}, port: {port}')

                            # Если ip адрес есть в dict_messages
                            if ip in self.dict_messages['error']:
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание неисправности
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {self.name}: Оборудование доступно {description}"
                                # Отправляем сообщение
                                self._sender(message)
                                try:
                                    # Удаляем аврию из словаря dict_messages
                                    del self.dict_messages['error'][ip]
                                    # Удаляем аварию из словаря dict_interim_messages
                                    del self.dict_interim_messages['erorr'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии low_temp')
                        else:
                            self.logger_err.error(f'Ошибка получения значения out_octets и  oper_status из: {line}')

                # ПРОВЕРКА НА ОСТАЛЬНЫЕ АВАРИИ

                    else:
                        # Вызываем метод _parse_voltage_in получаем значение входного напряжения и записываем в переменную voltage_in
                        voltage_in = self._parse_voltage_in(line)
                        # Вызываем метод _parse_voltage_out получаем значение выходного напряжения и записываем в переменную voltage_out
                        voltage_out = self._parse_voltage_out(line)
                        # Вызываем метод _parse_temperature получаем значение температуры и записываем в переменную temp_value
                        temp_value = self._parse_temperature(line)
                        # 
                        limit_oil = None

                    # ПРОВЕРКА ОТСУТСТВИЯ ЭЛЕКТРИЧЕСТВА

                        # Проверяем если значение входного напряжения voltage_in существует, то осуществляем дальше проверку
                        if voltage_in:
                            # Проверяем если значение входного напряжение меньше 10 И ip адреса нет в dict_messages, то отправляем 
                            # сообщение об аварии и добавляем данные в dict_messages
                            if int(voltage_in) < 10 and ip not in self.dict_messages['power_alarm']:
                                # Получаем имя объекта по ip
                                date, description = self._parse_message(line)
                                message = f"{date} {self.name}: Отключение электроэнергии: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['power_alarm'][ip] = message
                                # Добавляем дату возникновения аварии в dict_messages
                                self.dict_messages['date'][ip] = date
                                # Отправляем сообщение
                                self._sender(message)
        
                            # Проверяем если входное напряжение больше 180 И в dict_messages есть сообщение с таким ip
                            if int(voltage_in) > 180 and ip in self.dict_messages['power_alarm']:
                                # Получаем имя объекта, передав методу _dns ip адрес
                                #name = self._dns(ip)
                                date, description = self._parse_message(line)
                                battery_time = self._battery_operating_time(ip, date)
                                message = f"{date} {self.name}: Электричество восстановлено: {description}. Время работы на АКБ {battery_time}"
                                # Отправляем сообщение
                                self._sender(message)
                                # Удаляем сообщение об аварии из dict_messages
                                try:
                                    del self.dict_messages['power_alarm'][ip]
                                    del self.dict_messages['date'][ip]
                                except KeyError:
                                        self.logger_err.error('Функция "run". Ошибка удаления аварии power_alarm')
                        else:
                            self.logger_err.error(f'Не удалось получить значение входного напряжения voltage_in из: {line}')
                                
                    # ПРОВЕРКА НИЗКОГО НАПРЯЖЕНИЯ

                        # Проверяем если мы получили значение выходного напряжения voltage_out, то осуществляем дальше проверку
                        if voltage_out:
                            # Проверяем если входное напряжение меньше 10
                            if int(voltage_in) < 10:      
                                # Проверяем если значение выходного напряжения ниже порога и ip адреса нет в словаре dict_interim_messages
                                if float(voltage_out) < self.low_volt and ip not in self.dict_interim_messages['low_voltage']:
                                    # Добавляем в словарь dict_interim_messages индекс сообщения 1 - это значит мы получили
                                    # сообщение об аврии первый раз, а так же количество итераций цикла.
                                    self.dict_interim_messages['low_voltage'][ip] = [1, self.counters]
                                # Проверяем если значение низкого напряжения ниже порога И индекс сообщения равен 1 И разность итераций цикла равно num ИЛИ num+1
                                elif float(voltage_out) < self.low_volt and self.dict_interim_messages['low_voltage'][ip][0] == 1 \
                                    and ((self.counters - self.dict_interim_messages['low_voltage'][ip][1]) == self.num \
                                        or (self.counters - self.dict_interim_messages['low_voltage'][ip][1]) == self.num + 1):
                                    # Вызываем метод _dns передав ему ip адрес, получаем имя устройства 
                                    #name = self._dns(ip)
                                    # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                    date, description = self._parse_message(line)
                                    # Формируем сообщение для отправки
                                    message = f"{date} {self.name}: Низкое напряжение: {description}"
                                    # Добавляем данные об аварии в dict_messages
                                    self.dict_messages['low_voltage'][ip] = message
                                    # Добавляем в dict_interim_messages идекс сообщения 2, который говорит, что мы второй раз
                                    # получили одну и туже аврию в течении нескольких итераций цикла
                                    self.dict_interim_messages['low_voltage'][ip][0] = 2
                                    # Отправляем сообщение
                                    self._sender(message)
                                # Проверяем, что ip адрес есть в словаре, если ip нет, то функция get вернет None
                                elif self.dict_interim_messages['low_voltage'].get(ip):
                                    # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num+2, 
                                    # значит мы второй раз не получили одну и туже аварию в течение нескольких итераций цикла
                                    if self.dict_interim_messages['low_voltage'][ip][0] == 1 \
                                    and (self.counters - self.dict_interim_messages['low_voltage'][ip][1]) > self.num + 2:
                                        try:
                                            # Удаляем не подтвержденную аварию из словаря dict_interim_messages
                                            del self.dict_interim_messages['low_voltage'][ip]
                                        except KeyError:
                                            self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии low_voltage')

                            # Проверяем если значение выходного напряжения больше порога на +2В и ip адрес есть в словаре dict_messages
                            if float(voltage_out) > (self.low_volt +2) and ip in self.dict_messages['low_voltage']:
                                try:
                                    # Удаляем значение из словаря
                                    del self.dict_messages['low_voltage'][ip]
                                    del self.dict_interim_messages['low_voltage'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии low_voltage')
                        else:
                            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение выходного напряжения voltage_out из: {line}')

                     # ПРОВЕРКА ВЫСОКОЙ И НИЗКОЙ ТЕМПЕРАТУРЫ

                        # Проверяем если значение температуры temp_value существует, то осуществляем дальше проверку
                        if temp_value:
                            # Проверяем если значение температуры выше порогового И ip адреса нет в словаре dict_interim_messages
                            if int(temp_value) >= self.hight_temp and ip not in self.dict_interim_messages['hight_temp']:
                                # Добавляем в словарь dict_interim_messagess индекс сообщения 1 - это значит мы получили
                                # сообщение об аврии первый раз, а так же количество итераций цикла.
                                self.dict_interim_messages['hight_temp'][ip] = [1, self.counters]  
                            # Проверяем если значение температуры выше порога И индекс сообщения равен 1 И
                            # разность итераций цикла равно num ИЛИ num+1
                            elif int(temp_value) >= self.hight_temp and self.dict_interim_messages['hight_temp'][ip][0] == 1 \
                                and ((self.counters - self.dict_interim_messages['hight_temp'][ip][1]) == self.num \
                                    or (self.counters - self.dict_interim_messages['hight_temp'][ip][1]) == self.num + 1):
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {self.name}: Высокая температура: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['hight_temp'][ip] = message
                                # Добавляем в dict_interim_messages идекс сообщения 2, который говорит, что мы второй раз
                                # получили одну и туже аврию в течении нескольких итераций цикла
                                self.dict_interim_messages['hight_temp'][ip][0] = 2
                                # Отправляем сообщение
                                self._sender(message)
                            # Проверяем, что ip адрес есть в словаре, если ip нет, то функция get вернет None
                            elif self.dict_interim_messages['hight_temp'].get(ip):
                                # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num+2, значит мы второй раз не получили одну и туже аварию
                                if self.dict_interim_messages['hight_temp'][ip][0] == 1 \
                                and (self.counters - self.dict_interim_messages['hight_temp'][ip][1]) > self.num + 2:
                                    try:
                                        # Удаляем не подтвержденную аварию из словаря dict_interim_messages
                                        del self.dict_interim_messages['hight_temp'][ip]
                                    except KeyError:
                                       self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии hight_temp')
                
                            # Проверяем если значение температуры ниже порогового И ip адреса нет в словаре dict_interim_messages
                            if int(temp_value) <= self.low_temp and ip not in self.dict_interim_messages['low_temp']:
                                # Добавляем в словарь dict_interim_messages индекс сообщения 1 - это значит мы получили
                                # сообщение об аврии первый раз, а так же количество итераций цикла.
                                self.dict_interim_messages['low_temp'][ip] = [1, self.counters]
                            # Проверяем если температура меньше порогового значения И индекс сообщения равен 1 И
                            # количество итераций цикла меньше или равно 5
                            elif int(temp_value) <= self.low_temp and self.dict_interim_messages['low_temp'].get(ip)[0] == 1 \
                                and ((self.counters - self.dict_interim_messages['low_temp'][ip][1]) == self.num \
                                    or (self.counters - self.dict_interim_messages['low_temp'][ip][1]) == self.num + 1):
                                # Вызываем метод _dns передав ему ip адрес, получаем имя устройства
                                #name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {self.name}: Низкая температура: {description}"
                                # Добавляем в словарь dict_messages сообщение
                                self.dict_messages['low_temp'][ip] = message
                                # Добавляем в dict_messages идекс сообщения 2, который говорит, что мы второй раз
                                # получили одну и туже аврию в течении нескольких итераций цикла
                                self.dict_interim_messages['low_temp'][ip][0] = 2
                                # Отправляем сообщение
                                self._sender(message)
                            # Проверяем, что ip адрес есть в словаре, если ip нет, то функция get вернет None
                            elif self.dict_interim_messages['low_temp'].get(ip):
                                # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num+2, значит мы второй раз не получили одну и туже аварию
                                if self.dict_interim_messages['low_temp'][ip][0]== 1 \
                                    and (self.counters - self.dict_interim_messages['low_temp'][ip][1]) > self.num + 2:
                                    try:
                                        # Удаляем не подтвержденную аварию из словаря dict_interim_messages
                                        del self.dict_interim_messages['low_temp'][ip]
                                    except KeyError:
                                        self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_value из: {line}')
                            
                            # Если полученное значение температуры больше значения низкой температуры +3 градуса
                            # и меньше значения высокой температуры - 3 гр И ip адрес есть в dict_messages
                            if (self.low_temp + 3) < int(temp_value) < (self.hight_temp - 2) and ip in self.dict_messages['low_temp']:
                                try:
                                    # Удаляем аврию из словаря dict_messages
                                    del self.dict_messages['low_temp'][ip]
                                    # Удаляем аварию из словаря dict_interim_messages
                                    del self.dict_interim_messages['low_temp'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии low_temp')
                            #
                            if (self.low_temp + 3) < int(temp_value) < (self.hight_temp - 2) and ip in self.dict_messages['hight_temp']:
                                try:
                                    del self.dict_messages['hight_temp'][ip]
                                    del self.dict_interim_messages['hight_temp'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии hight_temp')
                        else:
                            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_value из: {line}')
            # Иначе, если в переменной snmp_traps нет данных, то заснуть на interval_time секунд и пропустить все операции ниже
            else:
                self.sleep(self.interval_time)
                continue
            # Увеличиваем счетчик на 1
            self.counters += 1
            # Создаем экземпляр класса sql
            with ConnectSqlDB() as sql:
                try:
                    # Делаем запрос к БД и добавляем в таблицу Alarms словарь с авариями
                    sql.add_alarm(self.dict_messages)
                    # Делаем запрос к БД и добавляем в таблицу Interim словарь с промежуточными авариями.
                    sql.add_interim_alarm(self.dict_interim_messages)
                except (sqlite3.IntegrityError, sqlite3.OperationalError):
                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка записи в БД') 
            # Устанавливаем интервал времени на который нужно заснуть 
            self.sleep(self.interval_time)

if __name__ == '__main__':
    monitor = ThreadMonitorAlarms()
    print(monitor.send_message('489848468', 'Привет'))
    time.sleep(5)
    