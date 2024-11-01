#
from typing import Optional, Tuple
import re
import random
import logging
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_alarms, dict_interim_alarms

class ERRORHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()

    # Метод принимает строку с ошибкой обрабатывет ее, возвращает сообщение об ошибке
    def handler_sw_error(self, line: str) -> Optional[str]:
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Получаем значение ip адреса вызвав метод _parse_ip
            ip = self._parse_ip(line)
            # Если тип переменной ip строка
            if isinstance(ip, str):
                # Вызываем метод, передаем на вход ip адрес устройства, метод возращает строковое значение места установки
                name = self._get_name(ip)
            else:
                return None
        # Попали в исключение, значит ip адрес устройство уже удален, пропускаем все действия ниже
        except TypeError:
            return None
        # Вызываем метод _parse_count, получаем количество итераций цикла
        counter = self._parse_count(line)
        # Вызываем метод, который проверяет и возращает True если авария подтвердилась
        if self._confirme_alarm('error', ip, counter):
            # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж params на дату и строку с параметрами
                date, name_error = params
                # Формируем случайным образом номер ID сообщения
                id1 = random.randint(2001, 3000)
                # Формируем сообщение для отправки
                message = f"{date} <b>{name}: Оборудование недоступно!</b> {name_error} ID:{id1}"
                # Добавляем данные об аварии в dict_messages
                dict_alarms['error'][ip] = message
                return message 
        
    def handler_ups_error(self, line):
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Получаем значение ip адреса вызвав метод _parse_ip
            ip = self._parse_ip(line)
            # Если тип переменной ip строка
            if isinstance(ip, str):
                # Вызываем метод, метод возращает строковое значение названия хоста
                name = self._get_name(ip)
            else:
                return None
        # Попали в исключение, значит ip адрес устройство уже удален, пропускаем все действия ниже
        except TypeError:
            return None
        # Вызываем метод _parse_count, получаем количество итераций цикла
        counter = self._parse_count(line)
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД и получаем словарь с текущими авариями
            dic_power_alarm = sql.get_values_dict_db('json_extract(data, "$.power_alarm")', table='Alarms')
        # Если ip адрес есть в словаре dic_power_alarm
        if ip in dic_power_alarm:
            # Вызываем метод, который возращает True если авария подтвердилась
            if self._confirme_alarm('batt_disconnect', ip, counter):
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, name_error = params
                    # Формируем случайным образом номер ID сообщения
                    id = random.randint(2001, 3000)
                    #
                    battery_time = self._battery_operating_time(ip, date)
                    # Формируем сообщение для отправки
                    message = f"{date} <b>{name}: БАТАРЕЙНАЯ ГРУППА ОТКЛЮЧЕНА! Время работы на АКБ {battery_time}</b> ID:{id}"
                    # Добавляем данные об аварии в dict_messages
                    dict_alarms['batt_disconnect'][ip] = message
                    return message 
        return None
    
    # Метод удаляет ip адрес из словаря dict_alarms и возвращает сообщение для отправки.
    def inservice_handler(self, line: str) -> Optional[str]:
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Вызываем метод, который возвращает ip адрес
            ip = self._parse_ip(line)
            # Если тип переменной ip строка
            if isinstance(ip, str):
                # Вызываем метод, который возвращает название канала
                name = self._get_name(ip)
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, switch_parametrs = params
                    # Формируем сообщение для отправки
                    message = f"{date} <b>{name}: Оборудование доступно</b> {switch_parametrs}"
                    # Удаляем аврию из словаря dict_alarms
                    del dict_alarms['error'][ip]
                    # Удаляем аварию из словаря dict_interim_alarms
                    del dict_interim_alarms['error'][ip]
                    return message
            else:
                return None
        # Попали в исключение, значит ip адрес устройство уже удален, пропускаем все действия ниже
        except TypeError:
            return None

if __name__ == "__main__":
    error_handler = ERRORSwitchHandler()
    error_handler._parse_message('dfgfdgfdgf')
