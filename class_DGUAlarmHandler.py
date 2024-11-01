#
from typing import  Union, Tuple
import random
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_alarms, dict_interim_alarms

class DGUAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()     
        # Записываем значения низкого уровня топлива
        self.low_level_oil = 35
        
    # Метод устанавливает пороговые значения      
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение порогового значения низкого уровня топлива
            low_level_oil = sql.get_db('num', alarms='monitor_low_oil', table='Settings')[0]
            if isinstance(low_level_oil, int):
                self.low_level_oil = low_level_oil
        return None

    def alarm_handler(self, line: str) -> Union[str, None]:
        # Вызываем метод, который устанавливает пороговые значения возниконовения аварии
        self._set_threshold_value_alarms()
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
        # Вызываем метод получаем значения количества топлива
        level_oil = self._parse_level_oil(line)
        hight_temp_water = self._parse_hight_temp_water(line)
        motor = self._parse_motor_work(line)
        low_temp_water = self._parse_low_temp_water(line)
        low_pressure_oil = self._parse_low_pressure_oil(line)
        #low_level_oil = self._parse_low_level_oil(line)
        switch_motor = self._parse_switch_motor(line)
        low_level_water = self._parse_level_water(line)
        low_batt = self._parse_low_batt(line)
        # Вызываем метод _parse_count, получаем количество итераций цикла
        counter = self._parse_count(line)

        # Если тип значения "Уровень топлива" число И значение меньше порога И
        if isinstance(level_oil, int) and level_oil < self.low_level_oil:
            # Вызываем метод, который проверяет и возращает True если авария подтвердилась
            if self._confirme_alarm('low_level_oil', ip, counter):
                # Вызываем метод, возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, dgu_parametrs = params
                    # Формируем случайным образом номер ID сообщения
                    id = random.randint(1001, 2000)
                    # Формируем сообщение, которое будет отправленно пользователям
                    message = f"{date} <b>{name}: Низкий уровень топлива:</b> {dgu_parametrs.replace('Топл.:{}%'.format(level_oil), '<b>Топл.:{}%</b>'.format(level_oil))} ID:{id}"
                    # Добавляем данные об аварии в dict_interim_alarms
                    dict_alarms['low_level_oil'][ip] = message
                    return message
        # Если тип значения "Уровень топлива" число и значение больше порога на 10
        elif isinstance(level_oil, int) and level_oil > (self.low_level_oil +10) and ip in dict_alarms['low_level_oil']:
            # Удаляем сообщение об аварии из словаря аврий
            del dict_alarms['low_level_oil'][ip]
            if dict_interim_alarms['low_level_oil'].get(ip):
                del dict_interim_alarms['low_level_oil'][ip]
            

        #  Высокой температуры охлаждающей жидкости ДГУ
        if hight_temp_water == 1 and ip not in dict_alarms['hight_temp_water']:
            # Вызываем метод передаем строку, метод возвращает кортеж из двух строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж получаем дату возникновения аварии 
                date, _ = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(1001, 2000)
                # Формируем сообщение которое отправим пользователю
                message = f"{date} <b>{name}: Высокая температура О/Ж</b> ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                dict_alarms['hight_temp_water'][ip] = message
                return message
        # Если значение "Температура О/Ж" равно 0 И значение ip есть в в словаре аварий
        elif hight_temp_water == 0 and ip in dict_alarms['hight_temp_water']:
            # Удаляем аврию из словаря dict_alarms
            del dict_alarms['hight_temp_water'][ip]

        # Если значение "Аварийноая остановка двигателя" равно 1 И значение ip нет в словаре аварий
        if motor == 1 and ip not in dict_alarms['motor']:
            # Вызываем метод передаем строку, метод возвращает кортеж из двух строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж получаем дату возникновения аварии 
                date, _ = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(1001, 2000)
                # Формируем сообщение которое отпавим пользователю
                message = f"{date} <b>{name}: ЭКСТРЕННАЯ ОСТАНОВКА ДВИГАТЕЛЯ</b> ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                dict_alarms['motor'][ip] = message
                return message
        elif motor == 0 and ip in dict_alarms['motor']:
            # Удаляем аврию из словаря dict_alarms
            del dict_alarms['motor'][ip]

        # Если значение "Низкая температура О/Ж" равно 1 И названия аварии нет в словаре аварий  
        if low_temp_water == 1 and  ip not in dict_alarms['low_temp_water']:
            # Вызываем метод передаем строку, метод возвращает кортеж из двух строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж получаем дату возникновения аварии 
                date, _ = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(1001, 2000)
                # Формируем сообщение которое отпавим пользователю
                message = f"{date} <b>{name}: Низкая температура О/Ж</b> ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                dict_alarms['low_temp_water'][ip] = message
                return message
        elif low_temp_water == 0 and ip in dict_alarms['low_temp_water']:
            # Удаляем аврию из словаря dict_alarms
            del dict_alarms['low_temp_water'][ip]
        
        # Если значение "Низкое давление масла" равно 1 И значения ip нет в словаре аварий 
        if low_pressure_oil  == 1 and ip not in dict_alarms['low_pressure_oil']:
            # Вызываем метод передаем строку, метод возвращает кортеж из двух строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж получаем дату возникновения аварии 
                date, _ = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(1001, 2000)
                # Формируем сообщение которое отпавим пользователю
                message = f"{date} <b>{name}: Низкое давление масла</b> ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                dict_alarms['low_pressure_oil'][ip] = message
                return message
        elif low_pressure_oil  == 0 and ip in dict_alarms['low_pressure_oil']:
            # Удаляем аврию из словаря dict_alarms
            del dict_alarms['low_pressure_oil'][ip]

        # Если значение "Переключатель ДГУ" равно 1 И значения ip нет в словаре аварий 
        if switch_motor == 1 and ip not in dict_alarms['switch_motor']:
            # Вызываем метод передаем строку, метод возвращает кортеж из двух строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж получаем дату возникновения аварии 
                date, _ = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(1001, 2000)
                # Формируем сообщение которое отпавим пользователю
                message = f"{date} <b>{name}: Переключатель управления двигателем в ручном режиме</b> ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                dict_alarms['switch_motor'][ip] = message
                return message  
        elif switch_motor == 0 and ip in dict_alarms['switch_motor']:
            # Удаляем аврию из словаря dict_alarms
            del dict_alarms['switch_motor'][ip]

        # Если значение "Низкий уровень О/Ж" равно 1 И значения ip нет в словаре аварий 
        if low_level_water == 1 and ip not in dict_alarms['low_level_water']:
            # Вызываем метод передаем строку, метод возвращает кортеж из двух строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж получаем дату возникновения аварии 
                date, _ = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(1001, 2000)
                # Формируем сообщение которое отпавим пользователю
                message = f"{date} <b>{name}: Низкий уровень О/Ж</b> ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                dict_alarms['low_level_water'][ip] = message
                return message
        elif low_level_water == 0 and ip in dict_alarms['low_level_water']:
            # Удаляем аврию из словаря dict_alarms
            del dict_alarms['low_level_water'][ip]

        # Если значение "Низкий заряд АКБ" равно 1 И значения ip нет в словаре аварий 
        if low_batt == 1 and ip not in dict_alarms['low_batt']:
            # Вызываем метод передаем строку, метод возвращает кортеж из двух строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж получаем дату возникновения аварии 
                date, _ = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(1001, 2000)
                # Формируем сообщение которое отпавим пользователю
                message = f"{date} <b>{name}: Низкий заряд АКБ</b> ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                dict_alarms['low_batt'][ip] = message
                return message
        elif low_batt == 0 and ip in dict_alarms['low_batt']:
            # Удаляем аврию из словаря dict_alarms
            del dict_alarms['low_batt'][ip]
        return None
    
if __name__ == "__main__":
    handler = DGUAlarmHandler()
    handler.alarm_handler('123,1312,312,1231,2')
