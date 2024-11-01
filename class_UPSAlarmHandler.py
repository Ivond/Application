#
from typing import Union, Tuple
import random
#from datetime import datetime
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_alarms, dict_interim_alarms

class UPSAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Записываем значение высокой температуры
        self.hight_temp: int = 35
        # Записываем значение низкой температуры
        self.low_temp: int = 0
        # Записываем значение низкого напряжения
        self.low_volt: float = 48.0
        
    # Метод устанавливает пороговые значения сработки аварии     
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение порогового значения высокой температуры
            hight_temp = sql.get_db('num', alarms='monitor_hight_temp', table='Settings')[0]
            if isinstance(hight_temp, int):
                self.hight_temp = hight_temp
            # Делаем запрос к БД, на получение порога значения низкой температуры
            low_temp = sql.get_db('num', alarms='monitor_low_temp', table='Settings')[0]
            if isinstance(low_temp, int):
                self.low_temp = low_temp
            # Делаем запрос к БД, на получение порога значения низкого напряжения
            low_volt = sql.get_db('num', alarms='monitor_low_volt', table='Settings')[0]
            if isinstance(low_volt, int):
                self.low_volt = low_volt
        return None
            
    # ПРОВЕРКА ПАРАМЕТРОВ ИБЭП
    def alarm_handler(self, line:str) -> Union[str, None]:
        # Вызываем метод, который устанавливает пороговые значения возниконовения аварии
        self._set_threshold_value_alarms()
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Получаем значение ip адреса вызвав метод _parse_ip
            ip = self._parse_ip(line)
            if isinstance(ip, str):
                # Получаем имя устройства вызвав метод _dns передав ему ip адрес и записываем в переменную name
                name = self._get_name(ip)
        # Попали в исключение, значит ip адрес устройство уже удален, пропускаем все действия ниже
        except TypeError:
            return None
        
        # Вызываем метод _parse_voltage_in получаем значение входного напряжения и записываем в переменную voltage_in
        voltage_in = self._parse_voltage_in(line)
        # Вызываем метод _parse_voltage_out получаем значение выходного напряжения и записываем в переменную voltage_out
        voltage_out = self._parse_voltage_out(line)
        # Вызываем метод _parse_temperature получаем значение температуры и записываем в переменную temp_value
        temp_value = self._parse_temperature(line)
        # Вызываем метод _parse_count, получаем количество итераций цикла, преобразуем в число
        counter = self._parse_count(line)
        # Если тип значения "Входного напряжения" число И значение меньше 10
        if isinstance(voltage_in, int) and voltage_in < 10:
            # Проверяем если ip адреса нет в dict_alarms
            if ip not in dict_alarms['power_alarm']:
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                # Если тип значения params - кортеж
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, ups_parameters = params
                    # Формируем случайным образом ID сообщения
                    id = random.randint(1, 1000)
                    # Формируем сообщение для отправки, выделяем значение жирным шрифтом, параметр которого ...
                    message = f"{date} <b>{name}: Отключение электроэнергии:</b> {ups_parameters.replace('IN: {} V'.format(voltage_in), '<b>IN: {} V</b>'.format(voltage_in))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['power_alarm'][ip] = message
                    # Добавляем дату возникновения аварии в dict_alarms
                    dict_alarms['date'][ip] = date
                    # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                    return message
            # Если тип значения "Выходное напряжение" число с "плавающей" точкой И значение меньше порогового
            elif isinstance(voltage_out, float) and voltage_out < self.low_volt:
                # Вызываем метод, который возращает True если авария подтвердилась
                if self._confirme_alarm('low_voltage', ip, counter):
                    # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                    params = self._parse_message(line)
                    if isinstance(params, tuple):
                        # Распаковываем кортеж params на дату и строку с параметрами
                        date, ups_parameters = params
                        # Формируем случайным образом ID сообщения
                        id = random.randint(1, 1000)
                        # Формируем сообщение для отправки
                        message = f"{date} <b>{name}: Низкое напряжение:</b> {ups_parameters.replace('OUT: {} V'.format(voltage_out), '<b>OUT: {} V</b>'.format(voltage_out))} ID:{id}"
                        # Добавляем данные об аварии в dict_alarms
                        dict_alarms['low_voltage'][ip] = message
                        # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                        return message
        # Если тип значения "Входное напряжение" число И значение больше 180
        elif isinstance(voltage_in, int) and voltage_in > 180:
            # Проверяем если Ip адрес есть в словаре dict_alarms
            if ip in dict_alarms['power_alarm']:
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, ups_parameters = params
                    # Определяем время работы на АКБ вызвав метод _battery_operating_time
                    battery_time = self._battery_operating_time(ip, date)
                    # Если Ip адреса нет в словаре с ключом batt_disconnect
                    if ip in dict_alarms['batt_disconnect']:
                        # Формируем сообщение для отправки
                        message = f"{date} <b>{name}: Электричество восстановлено:</b> {ups_parameters}."
                        # Удаляем значение из словаря аварий
                        del dict_alarms['batt_disconnect'][ip]
                        # Удаляем значение из словаря промежуточных аварий
                        del dict_interim_alarms['batt_disconnect'][ip]
                    else:
                        # Формируем сообщение для отправки
                        message = f"{date} <b>{name}: Электричество восстановлено:</b> {ups_parameters}. <b>Время работы на АКБ {battery_time}</b>"
                    # Удаляем значение из словаря аварий
                    del dict_alarms['power_alarm'][ip]
                    del dict_alarms['date'][ip]
                    # Проверяем если получили значение выходного напряжения и ip адрес есть в словаре dict_alarms
                    if voltage_out and ip in dict_alarms['low_voltage']:
                        # Удаляем значение из словаря аварий
                        del dict_alarms['low_voltage'][ip]
                        try:
                            # Удаляем значение из словаря промежуточных аварий
                            del dict_interim_alarms['low_voltage'][ip]
                        except KeyError:
                            pass
                    # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                    return message
            
        # ПРОВЕРКА ВЫСОКОЙ И НИЗКОЙ ТЕМПЕРАТУРЫ
        # Если тип значения температуры число И значение выше порога И ip адреса нет в словаре
        if isinstance(temp_value, int) and temp_value >= self.hight_temp:
            # Вызываем метод, который проверяет и возращает True если авария подтвердилась
            if self._confirme_alarm('hight_temp', ip, counter):
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, ups_parameters = params
                    # Формируем случайным образом ID сообщения
                    id = random.randint(1, 1000)
                    # Формируем сообщение для отправки
                    message = f"{date} {name}: Высокая температура: {ups_parameters.replace('*C: {}'.format(temp_value), '<b>*C: {}</b>'.format(temp_value))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['hight_temp'][ip] = message
                    # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                    return message
        # Если тип значения температуры число И значение больше нижнего порога на 2 градуса и меньше верхнего порога на 2 И ip есть в словаре
        if isinstance(temp_value, int) and (self.low_temp + 2) < temp_value < (self.hight_temp - 2) and ip in dict_alarms['hight_temp']:
            # Удаляем значение из словаря аварий
            del dict_alarms['hight_temp'][ip]
            # Удаляем значение из словаря промежуточных аварий
            del dict_interim_alarms['hight_temp'][ip]

        # Если тип значения температуры число И значение ниже порога И значение IP строка И IP нет в словаре
        if isinstance(temp_value, int) and temp_value <= self.low_temp and isinstance(ip, str):
            # Вызываем метод, который проверяет и возращает True если авария подтвердилась
            if self._confirme_alarm('low_temp', ip, counter):
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, ups_parameters = params
                    # Формируем случайным образом ID сообщения
                    id = random.randint(1, 1000)
                    # Формируем сообщение для отправки
                    message = f"{date} {name}: Низкая температура: {ups_parameters.replace('*C: {}'.format(temp_value), '<b>*C: {}</b>'.format(temp_value))} ID:{id}"
                    # Добавляем в словарь dict_alarms сообщение
                    dict_alarms['low_temp'][ip] = message
                    # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                    return message
        # Если тип значения температуры число И значение больше нижнего порога на +2 градуса
        # И меньше верхнего порога на 2 градуса И ip адрес есть в словаре
        if isinstance(temp_value, int) and (self.low_temp + 2) < temp_value < (self.hight_temp - 2) and ip in dict_alarms['low_temp']:
            # Удаляем значение из словаря аварий
            del dict_alarms['low_temp'][ip]
            # Удаляем значение из словаря промежуточных аварий
            del dict_interim_alarms['low_temp'][ip]
        return None

if __name__ == "__main__":
   
    handler = UPSAlarmHandler()
    print(handler.dict_alarms)




