#
from typing import Optional, List, Tuple, Any
import sqlite3 
import re
from class_ThreadSNMPAsc import ThreadSNMPAsk
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler

# Проверяет актуальные параметры оборудования по которым есть аваии
class TelegramBotAlarmStatus(ThreadSNMPAsk, ValueHandler):
    def __init__(self) -> None:
        super().__init__()
    
    # Метод получает из базы данных список активных аварий и опрашивает устройства повторно на предмет получения актуальных данных по авриям
    def get_active_alarms(self) -> Optional[List[str]]:
        # Словарь для хранения записей 
        dict_alarms = {}
        try:
            # Создаем экземпляр класса sql_db
            with ConnectSqlDB() as sql_db:
                # Делаем запрос к БД на получение данных словарь с авариями
                active_alarms = sql_db.get_values_dict_db('data', table='Alarms') # --> dict
            # Проверяем если из БД мы получили аварии
            if active_alarms:
                # Проходимся по ключам и значениям словаря, где name_alarm - название авариии, а dic словарь в котором key ip адрес, а value это описание
                for name_alarm, dic in active_alarms.items():
                    # Проверяем если ключ словаря не равен date, т.к. в date хранится время отключения электроэнергии и оно нам не нужно для проверки аварий
                    if name_alarm == 'power_alarm' or name_alarm == 'hight_temp' or name_alarm == 'low_temp' or \
                    name_alarm == 'phase_alarm' or name_alarm == 'hight_temp_macc' or name_alarm == 'low_signal_power' or \
                        name_alarm == 'low_temp_macc' or name_alarm == 'low_level_oil':
                        # Проходимся по ключам словаря dic
                        for ip in dic:
                            with ConnectSqlDB() as sql_db:
                                # Делаем запрос к БД, получить model и Название хоста ГДЕ ip из таблицы Devices
                                model, host_name = sql_db.get_db('model', 'description', ip=ip, table='Devices')
                            # Вызываем метод, который выполняет запрос в зависимости от модели устройства
                            result = self.make_snmp_request(ip, model)
                            if result:
                                # Вызываем метод передаем на вход полученную строку вывода, метод возвращает кортеж(дата и параметры)  
                                params = self._parse_message(result)
                                if params:
                                    # Распаковываем кортеж
                                    date, description = params
                                    # Формируем строку сообщения 
                                    massege = f"{date} {host_name} {description}"
                                    # Добавляем сообщение в словарь
                                    dict_alarms[ip] = massege
                # Получаем список сообщений 
                status_alarm = list(dict_alarms.values())
                # Возвращаем список актуальных аварий 
                return status_alarm # -> list[] 
        except (sqlite3.IntegrityError, sqlite3.InterfaceError):
            # TODO Ошибка запроса к БД
            pass  
        return None   
        
    # Метод выполняе snmp-запрос в зависимости от модели устройства, возвращает результат
    def make_snmp_request(self, ip, model: str) -> None:
        # Если model равна
        if model == 'forpost':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.forpost(ip, timeout=5, block=True)
            return out
        elif model == 'forpost_2':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.forpost_2(ip, timeout=5, block=True)
            return out
        elif model == 'forpost_3':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.forpost_3(ip, timeout=5, block=True)
            return out
        elif model == 'eaton':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.eaton(ip, timeout=5, block=True)
            return out
        elif model == 'sc200':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.sc200(ip, timeout=5, block=True)
            return out
        elif model == 'mc2600':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.mc2600(ip, timeout=5, block=True)
            return out
        elif model == 'legrand':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.legrand(ip, timeout=5, block=True)
            return out
        elif model == 'apc':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.apc(ip, timeout=5, block=True)
            return out
        elif model == 'eltek':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.eltek(ip, timeout=5, block=True)
            return 
        elif model == 'macc':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.macc(ip, timeout=5, block=True)
            return out
        elif model == 'modbus':
            # Вызываем метод и получаем строку вывод сделанного SNMP запроса
            out = self.modbus(ip, time_out=5)
            return out
        return None


if __name__ == '__main__':
    alarms = TelegramBotAlarmStatus()
    alarms.get_active_alarms()
