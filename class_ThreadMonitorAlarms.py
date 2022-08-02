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
        # Записываем значения аврий в словарь
        self.dict_messages = {'power_alarm':{},
                            'low_voltage':{},
                            'limit_oil':{},
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

    # Функция из полученных на вход данных, парсит значение количества топлива и возвращает это значение
    def _parse_limit_oil(self, line):
        match = re.match(r'.+Топл\.:(?P<limit>\d+)%', line)
        if match:
            limit_oil = match.group('limit').strip()
            return limit_oil

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
        if match:
            date = match.group('date').strip()
            description = match.group('description').strip()
            return date, description
        # Это условия для сообщения приходящего по протоколу ModBus
        elif match1:
            date = match1.group('date').strip()
            description = match1.group('description').strip(' ')
            return date, description

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
        while True:
            # Если в переменной snmp_traps есть данные, то
            if self.snmp_traps:
                # Перебираем список с данными по строкам
                for line in self.snmp_traps:
                    # Получаем значение ip адреса вызвав метод _parse_ip
                    ip = self._parse_ip(line)

                # ПРОВЕРКА КОЛИЧЕСТВА ТОПЛИВА

                    if 'ОПС' in line:
                        # Получаем значения количества топлива вызвав метод _parse_limit_oil и записываем в переменную limit_oil
                        limit_oil = self._parse_limit_oil(line)
                        # Проверяем если переменная limit_oil True, то дальше делаем проверку
                        if limit_oil:
                            # проверяем если уровень топлива меньше 35% и dict_messages не содержит сообщение с таким ip адресом
                            if (int(limit_oil) <= self.low_oil_limit and ip not in self.dict_messages['limit_oil']):
                                # Получаем имя устройства вызвав метод _dns передав ему ip адрес и записываем в переменную name
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку вывода с оборудования, получаем дату и описание и записываем их в переменные
                                date, description = self._parse_message(line)
                                # Формируем сообщение, которое будет отправленно пользователям
                                message = f"{date} {name}: Низкий уровень топлива: {description}"
                                # Отправляем сообщение
                                self._sender(message)
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['limit_oil'][ip] = message

                            if int(limit_oil) > (self.low_oil_limit +15) and ip in self.dict_messages['limit_oil']:
                                # Удаляем сообщение об аварии из dict_messages
                                try:
                                    del self.dict_messages['limit_oil'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии limit_oil')
                        else:
                            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение количества топлива limit_oil из: {line}')

                # ПРОВЕРКА НА ОШИБКИ

                    elif 'SNMP:REQEST_ERROR' in line:
                        pass

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
                            # Проверяем если напряжение ниже указанного предела и значение ip равно 10.184.50.201(Автобус)
                            if float(voltage_out) < self.low_volt and ip == '10.184.50.201' and \
                                                        ip not in self.dict_messages['low_voltage']:
                                name = self._dns(ip)
                                date, description = self._parse_message(line)
                                message = f"{date} {name}: Низкое напряжение: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['low_voltage'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)  

                            # Проверяем если выходное напряжение ниже указанного предела это для всех остальных ИБП
                            if float(voltage_out) < self.low_volt and ip not in self.dict_messages['low_voltage']:
                                # Вызываем метод _dns передав ему ip адрес, получаем имя устройства
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {name}: Низкое напряжение: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['low_voltage'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)
                            # Проверяем если входное напряжение больше значения низкого напряжения +2В и ip адрес есть в словаре dict_messages
                            if float(voltage_out) > (self.low_volt +2) and ip in self.dict_messages['low_voltage']:
                                try:
                                    del self.dict_messages['low_voltage'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "run". Ошибка удаления аварии low_voltage')
                        else:
                            self.logger_err.error(f'ThreadMonitorAlarm: не удалось получить значение выходного напряжения voltage_out из: {line}')

                    # ПРОВЕРКА ВЫСОКОЙ И НИЗКОЙ ТЕМПЕРАТУРЫ

                        # Проверяем если значение температуры temp_value существует, то осуществляем дальше проверку
                        if temp_value:
                            if int(temp_value) >= self.hight_temp and ip not in self.dict_messages['hight_temp']:
                                # Вызываем метод _dns передав ему ip адрес, получаем имя устройства
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {name}: Высокая температура: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['hight_temp'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)
                            # 
                            if int(temp_value) <= self.low_temp and ip not in self.dict_messages['low_temp']:
                                # Вызываем метод _dns передав ему ip адрес, получаем имя устройства
                                name = self._dns(ip)
                                # Вызываем метод _parse_message передав ему строку с выводом с оборудования и получаем дату и описание
                                date, description = self._parse_message(line)
                                # Формируем сообщение для отправки
                                message = f"{date} {name}: Низкая температура: {description}"
                                # Добавляем данные об аварии в dict_messages
                                self.dict_messages['low_temp'][ip] = message
                                # Отправляем сообщение
                                self._sender(message)
                        
                            # Если значение температуры больше значения низкой температуры +2 и меньше значения высокой температуры - 2, то
                            if (self.low_temp + 3) < int(temp_value) < (self.hight_temp - 3) and ip in self.dict_messages['low_temp']:
                                try:
                                    del self.dict_messages['low_temp'][ip]
                                except KeyError:
                                    self.logger_err.error('ThreadMonitorAlarm: функция "parse_output". Ошибка удаления аварии low_temp')

                            if (self.low_temp + 3) < int(temp_value) < (self.hight_temp - 3) and ip in self.dict_messages['hight_temp']:
                                try:
                                    del self.dict_messages['hight_temp'][ip]
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