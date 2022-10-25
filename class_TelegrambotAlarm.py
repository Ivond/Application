#
#import json
import sqlite3 
import re
from class_ThreadSNMPAscMain import ThreadSNMPAsk
from pathlib import Path
from class_SqlLiteMain import ConnectSqlDB

# Проверяет актуальные параметры оборудования по которым есть аваии
class TelegramBotAlarmStatus(ThreadSNMPAsk):
    # Поскольку класс ThreadSNMPAsk принимает на вход экземпляр класса queue (класс Queue), то при вызове 
    # клсса TelegramBotAlarmStatus должны передать это значение
    #def __init__(self, queue):
    def __init__(self):
        #super().__init__(queue)
        super().__init__()
        #self.path_db_alarm = Path(Path.cwd(), "Resources", "db_alarm.json")
        #self.path_db = Path(Path.cwd(), "Resources", "DataBase.json")

        # Создаем пустую переменную тип строка, куда будем записывать данные
        #self.status_alarm = []
    
    # Метод получает из базы данных список активных аварий и опрашивает устройства повторно на предмет получения актуальных данных по авриям
    def get_active_alarms(self):
        # Создаем пустую переменную тип строка, куда будем записывать данные
        self.status_alarm = []
        try:
            # Создаем экземпляр класса sql_db
            with ConnectSqlDB() as sql_db:
                # Делаем запрос к БД на получение данных словарь с авариями
                active_alarms = sql_db.get_values_list_db('data', table='Alarms') # --> dict
            # Проверяем если из БД мы получили аварии
            if active_alarms:
                # Проходимся по ключам и значениям словаря, где key это OID, а value словарь в котором key это ip адрес, а value это описание
                for key, value in active_alarms.items():
                    # Проверяем если ключ словаря не равен date, т.к. в date хранится время отключения электроэнергии и оно нам не нужно для проверки аварий
                    if key != 'date':
                        # Проходимся по ключам словаря value
                        for ip in value:
                            # Вызываем метод, который получает OID, передав на вход методу ip адрес устройства
                            self.get_oid_type(ip)
                # Возвращаем список актуальных аварий 
                return self.status_alarm # -> list[] 
        except (sqlite3.IntegrityError, sqlite3.InterfaceError):
            # TODO Ошибка запроса к БД
            pass     
        
    # Метод определяет к какой группе OID относится устройство и вызывает метод, который опрашивает устройство
    def get_oid_type(self, ip):
        try:
            with ConnectSqlDB() as sql_db:
                # Делаем запрос к БД, получить model и описание ГДЕ ip из таблицы Devices
                model, host_name = sql_db.get_db('model', 'description', ip=ip, table='Devices')
            # Если model равна
            if model == 'forpost':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.forpost(ip, timeout=5, flag=True)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Делаем подмену ip адреса на host_name
                #result = line.replace(line.split()[2], description)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'forpost_2':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.forpost_2(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'forpost_3':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.forpost_3(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'eaton':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.eaton(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'sc200':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.sc200(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'legrand':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.legrand(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'apc':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.apc(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'eltek':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.eltek(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'macc':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.macc(ip, timeout=5, flag=True)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
            elif model == 'modbus':
                # Вызываем метод и получаем значение параметров, которые записываем в переменную line
                line = self.modbus(ip, time_out=5)
                # Делаем подмену ip адреса на description
                #result = line.replace(line.split()[2], description)
                # Вызываем метод _parse_message передаем на вход вывод SNMP запроса, получаем дату и параметры 
                date, description = self._parse_message(line)
                # Формируем строку сообщения 
                massege = f"{date} {host_name} {description}"
                # Добавляем сообщение в список status_alarm
                self.status_alarm.append(massege)
        except (sqlite3.IntegrityError, sqlite3.InterfaceError, TypeError, ValueError, IndexError):
            # TODO ошибка запроса к БД
            pass

    def _parse_message(self, line):
        match = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>IN.+)', line)
        match1 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>ОПС.+)', line)
        match2 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>TxFiber2.+)', line)
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


if __name__ == '__main__':
    alarms = TelegramBotAlarmStatus()
    alarms.get_active_alarms()
