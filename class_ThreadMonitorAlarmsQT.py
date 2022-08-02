#
import re
#import os
import json
import time
import logging
import requests
import sqlite3
from pathlib import Path
from PyQt5.QtCore import QThread
from datetime import datetime
from class_SqlLite import ConnectSqlDB

class ThreadMonitorAlarms(QThread):

    def __init__(self):
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
        self.token = ""
        # Переменная определяет интервал между опросами метода run
        self.interval_time = 5
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
        self.hight_temp_fiber = 60
        
        # Записываем значения аврий в словарь
        self.dict_messages = {'power_alarm':{},
                            'low_voltage':{},
                            'limit_oil':{},
                            'hight_temp':{},
                            'low_temp':{},
                            'low_signal_power':{},
                            'date':{}
                            }
        # Записываем промежуточное значение аврий в словарь
        self.dict_intermediate_messages = {'power_alarm':{},
                            'low_voltage':{},
                            'limit_oil':{},
                            'alarm_stop_of_motor':{},
                            'hight_temp':{},
                            'low_temp':{},
                            'date':{}
                            }
        # Записываем результат snmp опроса оборудования в список 
        self.snmp_traps = []

    # Функция делает подмену ip адреса на Имя устройства
    def _dns(self, ip):
        # Создаем экземпляр класса sql
        sql = ConnectSqlDB()
        try:
            # Делаем запрос к БД, получаем описание Ip адреса
            description = sql.get_db(ip=ip, table='Devices')[1]
            return description
        except (sqlite3.IntegrityError, IndexError) :
            self.logger_err.error(f'ThreadMonitorAlarm "dns": не смог распарсить ip адрес: {ip}') 

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
        ip = line.split()[2].strip()
        return ip

    # ДГУ АВТОБУС 

    # Функция из полученных на вход данных, парсит значение количества топлива и возвращает это значение
    def _parse_limit_oil(self, line):
        match = re.match(r'.+Топл\.:(?P<limit>\d+)%', line)
        if match:
            limit_oil = match.group('limit').strip()
            return limit_oil

    def _parse_hight_temp_water(self, line):
        match = re.match(r'.+Высокая температура О/Ж: [(?P<hight_water>\d+)]', line)
        if match:
            hight_temp_water = match.group('hight_water').strip()
            return hight_temp_water


    def _parse_alarm_motor(self, line):
        match = re.match(r'.+Двиг\.:(?P<motor>\d*)', line)
        if match:
            alarm_stop_of_motor = match.group('motor').strip()
            return alarm_stop_of_motor

    # Функция из полученных на вход данных, парсит значение температуры и возвращает это значение
    def _parse_temperature(self, line):
        match = re.match(r'.+\*C: +(?P<temp_value>-*\d+)', line)
        if match:
            temperature_value = match.group('temp_value').strip()
            return temperature_value

    # Функция из полученных данных парсит значение даты, все параметры оборудования и возвращает эти значения
    def _parse_message(self, line):
        match = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>IN.+)', line)
        match1 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>ОПС.+)', line)
        match2 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>TxFiber2.+)', line)
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
        else:
            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение строка с данными message из: {line}')
            
    # Функция вычисляет время работы оборудования на АКБ и вовращает это значение 
    def _battery_operating_time(self, ip, time_end):
        # Создаем экземпляр класса sql
        sql = ConnectSqlDB()
        try:
            # Делаем запрос к БД получаем словарь
            db_alarm = sql.get_values_list_db('data', table='Alarms')
            #
            if db_alarm['date']:
                try:
                    # Изменяем формат даты и времени начала возникновения аварии
                    start_time = datetime.strptime((db_alarm['date'][ip]).strip(), "%d-%m-%Y  %H:%M:%S")
                    # Изменяем формат даты и времени окончании аварии
                    end_time = datetime.strptime((time_end).strip(), "%d-%m-%Y  %H:%M:%S")
                    # Вычисляем интервал времени в минутах в течении которого продолжалось авария
                    deltatime = round((end_time - start_time).seconds / 60, 2)# Отнимаем до 2 чисел после запятой
                    # Возвращаем результат
                    return deltatime
                except KeyError:
                    return 0
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


    # Функция отправляет сообщение чат Ботом 
    def _sender(self, message):
        # Создаем экземпляр класса sql
        sql = ConnectSqlDB()
        try:
            # Делаем запрос к БД получаем список chat_id пользователей
            chat_id = sql.get_values_list_db('chat_id', table='Users')
            if chat_id:
                for id in chat_id:
                    try:
                        # отправляем сообщенние вызывав метод send_message, результат записываем в переменную code_status
                        code_status = self.send_message(id, message) # --> int
                        # Если code_status не равен 200
                        if code_status != 200:
                            self.sleep(5)
                            self.send_message(id, message) 
                    except:
                        self.logger_err.error('ThreadMonitorAlarm "sender". Ошибка передачи сообщения, Чат Бот не запущен')    
            else:
                self.logger_err.error('ThreadMonitorAlarm "sender". Ошибка, нет данных об chat_id, сообщение не отправленно')
        except sqlite3.IntegrityError():
            self.logger_err.error('ThreadMonitorAlarm "sender". Ошибка, запроса данных из БД')

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
        self.counters = 0
        while True:
            # Если в переменной snmp_traps есть данные, то
            if self.snmp_traps:
                # Перебираем список с данными по строкам
                for line in self.snmp_traps:
                    # Получаем значение ip адреса вызвав метод _parse_ip
                    ip = self._parse_ip(line)

               # ПРОВЕРКА КОЛИЧЕСТВА ТОПЛИВА И СОСТОЯНИЕ РАБОТЫ ДВИГАТЕЛЯ

                    if 'ОПС' in line:
                        # Получаем значения количества топлива вызвав метод _parse_limit_oil и записываем в переменную limit_oil
                        limit_oil = self._parse_limit_oil(line)
                        # Получаем значение состояния работы двигателя вызвав метод _parse_alarm_motor
                        alarm_stop_of_motor = self._parse_alarm_motor(line)
                        # Проверяем если получили значение состояния двигателя alarm_stop_of_motor
                        if alarm_stop_of_motor:
                            # Если значение равно и ip адреса нет в ловаре
                            if alarm_stop_of_motor == 1 and ip not in self.dict_intermediate_messages['alarm_stop_of_motor']:
                                # Получаем имя устройства вызвав метод _dns передав ему ip адрес и записываем в переменную name
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку вывода с оборудования, получаем дату и описание и записываем их в переменные
                                date, description = self._parse_message(line)
                                # Формируем сообщение, которое будет отправленно пользователям
                                message = f"{date} {name}: АВАРИЙНАЯ ОСТАНОВКА ДВИГАТЕЛЯ: {description}"
                                # Добавляем значение Ip в словарь dict_intermediate_messages
                                self.dict_intermediate_messages['alarm_stop_of_motor'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)
                            # Если значение равно 0 И ip адрес есть в словаре
                            elif alarm_stop_of_motor == 0 and ip in self.dict_intermediate_messages['alarm_stop_of_motor']:
                            # Удаляем сообщение об аварии из dict_messages
                                try:
                                    # Удаляем значение из словаря
                                    del self.dict_intermediate_messages['alarm_stop_of_motor'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии alarm_stop_of_motor')

                        # Проверяем если получили значение переменной limit_oil
                        if limit_oil:
                            # Проверяем если значение уровеня топлива меньше порогу и dict_messages не содержит сообщение с таким ip адресом
                            if int(limit_oil) < self.low_oil_limit and ip not in self.dict_intermediate_messages['limit_oil']:
                                # Добавляем в словарь dict_intermediate_messages индекс сообщения 1, это значит мы получили
                                # сообщение об аврии первый раз, а так же количество итераций в цикле.
                                self.dict_intermediate_messages['limit_oil'][ip] = [1, self.counters]
                            # Проверяем если значение уровеня топлива меньше порогу И индекс сообщения равен 1 И
                            # количество итераций цикла меньше или равно 5
                            elif int(limit_oil) < self.low_oil_limit and self.dict_intermediate_messages['limit_oil'][ip][0] == 1 \
                                and (self.counters - self.dict_intermediate_messages['limit_oil'][ip][1]) <=5:
                                # Получаем имя устройства вызвав метод _dns передав ему ip адрес и записываем в переменную name
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку вывода с оборудования, получаем дату и описание и записываем их в переменные
                                date, description = self._parse_message(line)
                                # Формируем сообщение, которое будет отправленно пользователям
                                message = f"{date} {name}: Низкий уровень топлива: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['limit_oil'][ip] = message
                                # Добавляем в dict_intermediate_messages идекс сообщения 2, который говорит, что мы второй раз
                                # получили одну и туже аврию. И значение counters (по сути это формальность он никакой роли здесь не играет)
                                self.dict_intermediate_messages['limit_oil'][ip] = [2, self.counters]
                                # Отправляем сообщение
                                self._sender(message)
                            # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше 5, значит мы второй раз не получили одну и туже аварию
                            elif self.dict_intermediate_messages['limit_oil'].get(ip):
                                if self.dict_intermediate_messages['limit_oil'][ip][0] == 1 \
                                and (self.counters - self.dict_intermediate_messages['limit_oil'][ip][1]) > 5:
                                    try:
                                        # Удаляем не подтвержденную аварию из словаря dict_intermediate_messages
                                        del self.dict_intermediate_messages['limit_oil'][ip]
                                    except KeyError:
                                        self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии limit_oil')

                            # Проверяем если значение уровня топлива больше на 10 порога
                            if int(limit_oil) > (self.low_oil_limit +10) and ip in self.dict_messages['limit_oil']:
                                # Удаляем сообщение об аварии из dict_messages
                                try:
                                    # Удаляем значение из словаря
                                    del self.dict_messages['limit_oil'][ip]
                                    del self.dict_intermediate_messages['limit_oil'][ip]
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
                            # Проверяем если значение уровня приемного и передающего сигналов меньше signal_level_fiber
                            # И ip нет в dict_messages, то отправляем cообщение об аварии и добавляем данные в dict_messages
                            if (int(rx_fiber2) < self.signal_level_fiber or int(rx_fiber3) < self.signal_level_fiber or 
                                int(tx_fiber2) < self.signal_level_fiber or int(tx_fiber3) < self.signal_level_fiber) and ip not in self.dict_messages['low_signal_power']:
                                # Получаем имя объекта по ip
                                name = self._dns(ip)
                                # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                                date, description = self._parse_message(line)
                                # Формируем сообщение которое отпавим пользователю
                                message = f"{date} {name}: Низкий уровень сигнала транспондера MAC&C {description}."
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['low_signal_power'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)
                            
                            # Проверяем если значение уровня приемного и передающего сигналов больше signal_level_fiber И в dict_messages есть сообщение с таким ip
                            if (int(rx_fiber2) > self.signal_level_fiber and int(rx_fiber3) > self.signal_level_fiber and
                                int(tx_fiber2) > self.signal_level_fiber and int(tx_fiber3) > self.signal_level_fiber) and ip in self.dict_messages['low_signal_power']:
                                # Получаем имя объекта по ip
                                name = self._dns(ip)
                                date, description = self._parse_message(line)                
                                message = f"{date} {name}: Уровень сигнала транспондера MAC&C восстановлен: {description}."
                                # Отправляем сообщение
                                self._sender(message)
                                # Удаляем сообщение об аварии из dict_messages
                                try:
                                    del self.dict_messages['low_signal_power'][ip]
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
                                name = self._dns(ip)
                                # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                                date, description = self._parse_message(line)
                                # Формируем сообщение которое отправим пользователю
                                message = f"{date} {name}: Высокая температура транспондера MAC&C: {description}."
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
                                name = self._dns(ip)
                                # Вызываем метод parse_message получаем дату возникновения аварии и парамеры с оборудования
                                date, description = self._parse_message(line)
                                # Формируем сообщение которое отпавим пользователю
                                message = f"{date} {name}: Низкая температура транспондера MAC&C: {description}."
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

                    elif 'SNMP:REQEST_ERROR' in line:
                        pass

                    elif 'ДГУ' in line:
                        hight_temp_water = self._parse_hight_temp_water(line)
                        print(hight_temp_water)


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
                            # Проверяем если значение входного напряжение равно 0 И ip адреса нет в dict_messages, то отправляем 
                            # сообщение об аварии и добавляем данные в dict_messages
                            if 'IN: 0' in line and ip not in self.dict_messages['power_alarm']:
                                # Получаем имя объекта по ip
                                name = self._dns(ip)
                                date, description = self._parse_message(line)
                                message = f"{date} {name}: Отключение электроэнергии: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['power_alarm'][ip] = message
                                # Добавляем дату возникновения аварии в dict_messages
                                self.dict_messages['date'][ip] = date
                                # Отправляем сообщение
                                self._sender(message)
        
                            # Проверяем если входное напряжение больше 180 И в dict_messages есть сообщение с таким ip
                            if int(voltage_in) > 180 and ip in self.dict_messages['power_alarm']:
                                # Получаем имя объекта, передав методу _dns ip адрес
                                name = self._dns(ip)
                                date, description = self._parse_message(line)
                                battery_time = self._battery_operating_time(ip, date)
                                message = f"{date} {name}: Электричество восстановлено: {description}. Время работы на АКБ {battery_time} минут"
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
                            # Проверяем если входное напряжение равно нулю
                            if 'IN: 0' in line:      
                                # Проверяем если значение выходного напряжения ниже порога и ip адреса нет в словаре
                                if float(voltage_out) < self.low_volt and ip not in self.dict_intermediate_messages['low_voltage']:
                                    # Добавляем в словарь dict_intermediate_messages индекс сообщения 1, это значит мы получили
                                    # сообщение об аврии первый раз, а так же количество итераций в цикле.
                                    self.dict_intermediate_messages['low_voltage'][ip] = [1, self.counters]
                                # Проверяем если значение низкого напряжения ниже порогового значения И индекс сообщения равен 1 И
                                # количество итераций цикла меньше или равно 5
                                elif float(voltage_out) < self.low_volt and self.dict_intermediate_messages['low_voltage'][ip][0] == 1 \
                                    and (self.counters - self.dict_intermediate_messages['low_voltage'][ip][1]) <=5:
                                    # Вызываем метод _dns передав ему ip адрес, получаем имя устройства
                                    name = self._dns(ip)
                                    # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                    date, description = self._parse_message(line)
                                    # Формируем сообщение для отправки
                                    message = f"{date} {name}: Низкое напряжение: {description}"
                                    # Добавляем данные об аварии в dict_messages
                                    self.dict_messages['low_voltage'][ip] = message
                                    # Добавляем в dict_messages идекс сообщения 2, который говорит, что мы второй раз
                                    # получили одну и туже аврию и значение counter (по сути это формальность он никакой роли здесь не играет)
                                    self.dict_intermediate_messages['low_voltage'][ip] = [2, self.counters]
                                    # Отправляем сообщение
                                    self._sender(message)
                                
                                # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше 5, значит мы второй раз не получили одну и туже аварию
                                elif self.dict_intermediate_messages['low_voltage'].get(ip):
                                    if self.dict_intermediate_messages['low_voltage'][ip][0] == 1 \
                                    and (self.counters - self.dict_intermediate_messages['low_voltage'][ip][1]) > 5:
                                        try:
                                            # Удаляем не подтвержденную аварию из словаря dict_intermediate_messages
                                            del self.dict_intermediate_messages['low_voltage'][ip]
                                        except KeyError:
                                            self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии low_voltage')
                            # Проверяем если значение выходного напряжения больше порога на +2В и ip адрес есть в словаре dict_messages
                            if float(voltage_out) > (self.low_volt +2) and ip in self.dict_messages['low_voltage']:
                                try:
                                    # Удаляем значение из словаря
                                    del self.dict_messages['low_voltage'][ip]
                                    del self.dict_intermediate_messages['low_voltage'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии low_voltage')
                        else:
                            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение выходного напряжения voltage_out из: {line}')

                     # ПРОВЕРКА ВЫСОКОЙ И НИЗКОЙ ТЕМПЕРАТУРЫ

                        # Проверяем если значение температуры temp_value существует, то осуществляем дальше проверку
                        if temp_value:
                            # Проверяем если значение температуры выше порогового И ip адреса нет в словаре dict_intermediate_messages
                            if int(temp_value) >= self.hight_temp and ip not in self.dict_intermediate_messages['hight_temp']:
                                # Добавляем в словарь dict_intermediate_messages индекс сообщения 1, это значит мы получили
                                # сообщение об аврии первый раз, а так же количество итераций в цикле.
                                self.dict_intermediate_messages['hight_temp'][ip] = [1, self.counters]
                            # Проверяем если значение температуры выше порогового значения И индекс сообщения равен 1 И
                            # количество итераций цикла меньше или равно 5
                            elif int(temp_value) >= self.hight_temp and self.dict_intermediate_messages['hight_temp'][ip][0] == 1 \
                                and (self.counters - self.dict_intermediate_messages['hight_temp'][ip][1]) <=5:
                                # Вызываем метод _dns передав ему ip адрес, получаем имя устройства
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {name}: Высокая температура: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['hight_temp'][ip] = message
                                # Добавляем в dict_messages идекс сообщения 2, который говорит, что мы второй раз
                                # получили одну и туже аврию и значение counter (по сути это формальность он никакой роли здесь не играет)
                                self.dict_intermediate_messages['hight_temp'][ip] = [2, self.counters]
                                # Отправляем сообщение
                                self._sender(message)
                            # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше 5, значит мы второй раз не получили одну и туже аварию
                            elif self.dict_intermediate_messages['hight_temp'].get(ip):
                                if self.dict_intermediate_messages['hight_temp'][ip][0] == 1 \
                                and (self.counters - self.dict_intermediate_messages['hight_temp'][ip][1]) > 5:
                                    try:
                                        # Удаляем не подтвержденную аварию из словаря dict_intermediate_messages
                                        del self.dict_intermediate_messages['hight_temp'][ip]
                                    except KeyError:
                                        self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии hight_temp')

                            # Проверяем если значение температуры ниже порогового И ip адреса нет в словаре dict_intermediate_messages
                            if int(temp_value) <= self.low_temp and ip not in self.dict_intermediate_messages['low_temp']:
                                # Добавляем в словарь dict_intermediate_messages индекс сообщения 1, это значит мы получили
                                # сообщение об аврии первый раз, а так же количество итераций в цикле.
                                self.dict_intermediate_messages['low_temp'][ip] = [1, self.counters]
                            # Проверяем если температура меньше порогового значения И индекс сообщения равен 1 И
                            # количество итераций цикла меньше или равно 5
                            elif int(temp_value) <= self.low_temp and self.dict_intermediate_messages['low_temp'].get(ip)[0] == 1 \
                                and (self.counters - self.dict_intermediate_messages['low_temp'][ip][1]) <=5:
                                # Вызываем метод _dns передав ему ip адрес, получаем имя устройства
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {name}: Низкая температура: {description}"
                                # Добавляем в словарь dict_messages сообщение
                                self.dict_messages['low_temp'][ip] = message
                                # Добавляем в dict_messages идекс сообщения 2, который говорит, что мы второй раз
                                # получили одну и туже аврию и значение счетчика(по сути это формальность он никакой роли здесь не играет)
                                self.dict_intermediate_messages['low_temp'][ip] = [2, self.counters]
                                # Отправляем сообщение
                                self._sender(message)
                            # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше 5, значит мы второй
                            # раз не получили одну и туже аварию
                            elif self.dict_intermediate_messages['low_temp'].get(ip):
                                if self.dict_intermediate_messages['low_temp'][ip][0]== 1 \
                                    and (self.counters - self.dict_intermediate_messages['low_temp'][ip][1]) > 5:
                                    try:
                                        # Удаляем не подтвержденную аварию из словаря dict_intermediate_messages
                                        del self.dict_intermediate_messages['low_temp'][ip]
                                    except KeyError:
                                        self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_value из: {line}')

                            # Если полученное значение температуры больше значения низкой температуры +3 градуса
                            # и меньше значения высокой температуры - 3 гр И ip адрес есть в dict_messages
                            if (self.low_temp + 3) < int(temp_value) < (self.hight_temp - 2) and ip in self.dict_messages['low_temp']:
                                try:
                                    # Удаляем аврию из словаря dict_messages
                                    del self.dict_messages['low_temp'][ip]
                                    # Удаляем аварию из словаря dict_intermediate_messages
                                    del self.dict_intermediate_messages['low_temp'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии low_temp')
                            #
                            if (self.low_temp + 3) < int(temp_value) < (self.hight_temp - 2) and ip in self.dict_messages['hight_temp']:
                                try:
                                    del self.dict_messages['hight_temp'][ip]
                                    del self.dict_intermediate_messages['hight_temp'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии hight_temp')
                        else:
                            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение температуры temp_value из: {line}')
            # Иначе, если в переменной snmp_traps нет данных, то заснуть на interval_time секунд и пропустить все операции ниже
            else:
                self.sleep(self.interval_time)
                continue
            # Создаем экземпляр класса sql
            sql = ConnectSqlDB()
            try:
                sql.add_alarm(self.dict_messages)
            except (sqlite3.IntegrityError, sqlite3.OperationalError):
                self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка записи в БД')  
            self.sleep(self.interval_time)

if __name__ == '__main__':
    myThread = ThreadMonitorAlarms()
    print(myThread.is_running_alarm_monitoring)
    time.sleep(5)
    myThread.start()
    time.sleep(5)
    print(myThread.is_running_alarm_monitoring)