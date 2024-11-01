from typing import Union, Tuple
import random
from datetime import datetime
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_alarms, dict_interim_alarms

class ThreePhaseUPSAlarmHandler(ValueHandler):

    def __init__(self) -> None:
        super().__init__()
        # Записываем значение высокой температуры
        #self.hight_temp: int = 35
        # Записываем значение низкой температуры
        #self.low_temp: int = 0
        # Записываем значение низкого напряжения
        self.low_volt: float = 48.0
                  
    # Метод принимает на вход ip-адрес устройства и дату окончания аварии, возвращает время работы оборудования на АКБ 
    def _battery_operating_time(self, ip: str, time_end: str) -> str:
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД получаем словарь
            db_alarm = sql.get_values_dict_db('data', table='Alarms')
        #
        if db_alarm['date']:
            # Изменяем формат даты и времени начала возникновения аварии
            start_time = datetime.strptime((db_alarm['date'][ip]).strip(), "%d-%m-%Y  %H:%M:%S")
            # Изменяем формат даты и времени окончании аварии
            end_time = datetime.strptime((time_end).strip(), "%d-%m-%Y  %H:%M:%S")
            # Вычисляем время работы от АКБ оборудования в секундах
            sec = (end_time - start_time).seconds
            # Вычисляем количество дней поделив на 86400 без остатка
            day = sec // 86400
            if day:
                # Вычисляем остаток от деления на 86400 и записываем в переменную sec
                sec = sec % 86400
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
                        return f'{day}д. {hour}ч. {min}мин. {sec}сек.'
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
            return f"{0}сек."
    
    # Метод устанавливает пороговые значения сработки аварии     
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
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
        
        # Вызываем метод _parse_phase который возращает значение трех фаз
        three_phase = self._parse_phase(line)
        if isinstance(three_phase, tuple):
            phase1, phase2, phase3 = three_phase
        # Вызываем метод _parse_voltage_out получаем значение выходного напряжения и записываем в переменную voltage_out
        voltage_out = self._parse_voltage_out(line)
        # Вызываем метод _parse_count, получаем количество итераций цикла, преобразуем в число
        counter = self._parse_count(line)
        
        # ПРОВЕРКА ОТКЛЮЧЕНИЯ ЭЛЕКТРОЭНЕРГИИ

        # Если значение число и оно меньше меньше 10
        if (isinstance(phase1, float) and isinstance(phase2, float) and isinstance(phase2, float)):
            if phase1 < 10 and phase2 < 10 and phase3 < 10:
                # Проверяем если ip адреса нет в dict_alarms
                if not dict_alarms['power_alarm'].get(ip):
                    # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                    params = self._parse_message(line)
                    # Если тип значения params - кортеж
                    if isinstance(params, tuple):
                        # Распаковываем кортеж params на дату и строку с параметрами
                        date, ups_parameters = params
                        # Формируем случайным образом ID сообщения
                        id = random.randint(1, 1000)
                        # Формируем сообщение для отправки, выделяем значение жирным шрифтом, параметр которого ...
                        message = f"{date} <b>{name}: Отключение электроэнергии:</b> {ups_parameters.replace('Phase_A: {} V Phase_B: {} V Phase_C: {} V'.format(phase1, phase2, phase3), '<b>Phase_A: {} V Phase_B: {} V Phase_C: {} V</b>'.format(phase1, phase2, phase3))} ID:{id}"
                        if isinstance(ip, str):
                            # Добавляем данные об аварии в dict_alarms
                            dict_alarms['power_alarm'][ip] = message
                            # Добавляем дату возникновения аварии в dict_alarms
                            dict_alarms['date'][ip] = date
                        # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                        return message
                # Если значение "Выходное напряжение" число И это значение меньше порога 
                elif isinstance(voltage_out, float) and voltage_out < self.low_volt:
                    # Вызываем метод, который проверяет и возращает True если авария подтвердилась
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

            # Если тип значения "Входное напряжение" больше 180
            if phase1 > 180 or phase2 > 180 or phase3 > 180:
                # Проверяем если Ip адрес есть в словаре dict_alarms
                if dict_alarms['power_alarm'].get(ip):
                    # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                    params = self._parse_message(line)
                    if isinstance(params, tuple):
                        # Распаковываем кортеж params на дату и строку с параметрами
                        date, ups_parameters = params
                        # Определяем время работы на АКБ вызвав метод _battery_operating_time
                        battery_time = self._battery_operating_time(ip, date)
                        # Формируем сообщение для отправки
                        message = f"{date} <b>{name}: Электричество восстановлено:</b> {ups_parameters}. <b>Время работы на АКБ {battery_time}</b>"
                        # Удаляем значение из словаря аварий
                        del dict_alarms['power_alarm'][ip]
                        del dict_alarms['date'][ip]
                        # Если получили значение выходного напряжения и ip адрес есть в словаре dict_alarms
                        if voltage_out and dict_alarms['low_voltage'].get(ip):
                            # Удаляем значение из словаря аварий
                            del dict_alarms['low_voltage'][ip]
                        if dict_interim_alarms['low_voltage'].get(ip):
                            del dict_interim_alarms['low_voltage'][ip]
                        # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                        return message
                
            # Если значение одной из фаз меньше 10
            if phase1 < 10 or phase2 < 10 or phase3 < 10:
                # Проверяем если ip адреса нет в dict_alarms
                if ip not in dict_alarms['phase_alarm']:
                    # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                    params = self._parse_message(line)
                    # Если тип значения params - кортеж
                    if isinstance(params, tuple):
                        # Распаковываем кортеж params на дату и строку с параметрами
                        date, ups_parameters = params
                        if phase1 < 10:
                            # Выделяем значение переменной phase1 жирным ширифтом 
                            ups_parameters = ups_parameters.replace(f'Phase_B: {phase2} V', f'<b>Phase_B: {phase2} V</b>') 
                        if phase2 < 10:
                            # Выделяем значение переменной phase1 жирным ширифтом
                            ups_parameters = ups_parameters.replace(f'Phase_B: {phase2} V', f'<b>Phase_B: {phase2} V</b>')
                        if phase3 < 10:
                            # Выделяем значение переменной phase1 жирным ширифтом
                            ups_parameters = ups_parameters.replace(f'Phase_C: {phase3} V', f'<b>Phase_B: {phase3} V</b>')
                        # Формируем случайным образом ID сообщения
                        id = random.randint(1, 1000)
                        # Формируем сообщение для отправки, выделяем значение жирным шрифтом, параметр которого ...
                        message = f"{date} <b>{name}: Пропадание фазы:</b> {ups_parameters} ID:{id}"
                        if isinstance(ip, str):
                            # Добавляем данные об аварии в dict_alarms
                            dict_alarms['phase_alarm'][ip] = message
                        # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                        return message
            else:
                # Если ip адрес есть в словаре dict_alarms
                if dict_alarms['phase_alarm'].get(ip):
                    # Удаляем значение из словаря аварий
                    del dict_alarms['phase_alarm'][ip]
            
        # ПРОВЕРКА ВЫСОКОЙ И НИЗКОЙ ТЕМПЕРАТУРЫ
        # Если тип значения температуры число И значение выше порога И ip адреса нет в словаре
        #if isinstance(temp_value, int) and temp_value >= self.hight_temp and ip not in self.dict_interim_alarms['hight_temp']:
            # Если тип значения ip адрес - строка
            #if isinstance(ip, str):
                # Добавляем в словарь dict_interim_alarms индекс сообщения 1 - это значит мы получили
                # сообщение об аврии первый раз, а так же количество итераций цикла.
                #self.dict_interim_alarms['hight_temp'][ip] = [1, counter] 
        # Если тип значения температуры число И значение выше порога И значение IP строка И индекс сообщения равен 1 И 
        # разность итераций цикла равно num ИЛИ num+1
        #elif isinstance(temp_value, int) and temp_value >= self.hight_temp  and isinstance(ip, str)\
            #and self.dict_interim_alarms['hight_temp'][ip][0] == 1 \
            #and ((counter - self.dict_interim_alarms['hight_temp'][ip][1]) == self.num \
            #or (counter - self.dict_interim_alarms['hight_temp'][ip][1]) == self.num + 1):
            # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
            #params = self._parse_message(line)
            #if isinstance(params, tuple):
                # Распаковываем кортеж params на дату и строку с параметрами
                #date, ups_parameters = params
                # Формируем случайным образом ID сообщения
                #id = random.randint(1, 1000)
                # Формируем сообщение для отправки
                #message = f"{date} {name}: Высокая температура: {ups_parameters.replace('*C: {}'.format(temp_value), '<b>*C: {}</b>'.format(temp_value))} ID:{id}"
                # Добавляем данные об аварии в dict_alarms
                #self.dict_alarms['hight_temp'][ip] = message
                # Добавляем в dict_interim_alarms идекс сообщения 2, который говорит, что мы второй раз
                # получили одну и туже аврию в течении нескольких итераций цикла
                #self.dict_interim_alarms['hight_temp'][ip][0] = 2
                # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                #return message
        # Если тип значения ip-адрес строка И значение есть в словаре, иначе функция get вернет None
        #elif isinstance(ip, str) and self.dict_interim_alarms['hight_temp'].get(ip):
            # Если индекс сообщения равен 1 И количество итераций цикла больше num+2, значит авария не подтвердилась и мы второй раз не получили одну и туже аварию
            #if self.dict_interim_alarms['hight_temp'][ip][0] == 1 \
            #and (counter - self.dict_interim_alarms['hight_temp'][ip][1]) > self.num + 2:
                # Удаляем значение не подтвержденной аварии из словаря промежуточных аварий
                #del self.dict_interim_alarms['hight_temp'][ip]
        # Если тип значения температуры число И значение больше нижнего порога на 2 градуса и меньше верхнего порога на 2 И ip есть в словаре
        #if isinstance(temp_value, int) and (self.low_temp + 2) < temp_value < (self.hight_temp - 2) and ip in self.dict_alarms['hight_temp']:
            # Удаляем значение из словаря аварий
            #del self.dict_alarms['hight_temp'][ip]
            # Удаляем значение из словаря промежуточных аварий
            #del self.dict_interim_alarms['hight_temp'][ip]

        # Если тип значения температуры число И значение ниже порога И значение IP строка И IP нет в словаре
        #if isinstance(temp_value, int) and temp_value <= self.low_temp and isinstance(ip, str) and ip not in self.dict_interim_alarms['low_temp']:
            # Добавляем в словарь dict_interim_messages индекс сообщения 1 - это значит мы получили
            # сообщение об аврии первый раз, а так же количество итераций цикла.
            #self.dict_interim_alarms['low_temp'][ip] = [1, counter]
        # Если тип значения температуры число И значение меньше порога И тип значения IP строка  
        # И индекс сообщения равен 1 И количество итераций цикла равно num ИЛИ num+1
        #elif isinstance(temp_value, int) and temp_value <= self.low_temp and isinstance(ip, str)\
            #and self.dict_interim_alarms['low_temp'][ip][0] == 1 \
            #and ((counter - self.dict_interim_alarms['low_temp'][ip][1]) == self.num \
                #or (counter - self.dict_interim_alarms['low_temp'][ip][1]) == self.num + 1):
            # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
            #params = self._parse_message(line)
            #if isinstance(params, tuple):
                # Распаковываем кортеж params на дату и строку с параметрами
                #date, ups_parameters = params
                # Формируем случайным образом ID сообщения
                #id = random.randint(1, 1000)
                # Формируем сообщение для отправки
                #message = f"{date} {name}: Низкая температура: {ups_parameters.replace('*C: {}'.format(temp_value), '<b>*C: {}</b>'.format(temp_value))} ID:{id}"
                # Добавляем в словарь dict_alarms сообщение
                #self.dict_alarms['low_temp'][ip] = message
                # Добавляем в dict_alarms идекс сообщения 2, который говорит, что мы второй раз
                # получили одну и туже аврию в течении нескольких итераций цикла
                #self.dict_interim_alarms['low_temp'][ip][0] = 2
                # ВОЗРАЩАЕМ СООБЩЕНИЕ ДЛЯ ОТПРАВКИ 
                #return message
        # Если тип значения Ip строка И ip есть в словаре, иначе функция get вернет None
        #if isinstance(ip, str) and self.dict_interim_alarms['low_temp'].get(ip):
            # Если индекс сообщения равен 1 И количество итераций цикла больше num+2, значит авария не подтвердилась и 
            # мы второй раз не получили одну и туже аварию
            #if self.dict_interim_alarms['low_temp'][ip][0]== 1 \
                #and (counter - self.dict_interim_alarms['low_temp'][ip][1]) > self.num + 2:
                # Удаляем значение не подтвержденной аварии из словаря промежуточных аварий
                #del self.dict_interim_alarms['low_temp'][ip]
        
        # Если тип значения температуры число И значение больше нижнего порога на +2 градуса
        # И меньше верхнего порога на 2 градуса И ip адрес есть в словаре
        #if isinstance(temp_value, int) and (self.low_temp + 2) < temp_value < (self.hight_temp - 2) and ip in self.dict_alarms['low_temp']:
            # Удаляем значение из словаря аварий
            #del self.dict_alarms['low_temp'][ip]
            # Удаляем значение из словаря промежуточных аварий
            #del self.dict_interim_alarms['low_temp'][ip]
        return None

if __name__ == "__main__":
   
    handler = ThreePhaseUPSAlarmHandler()
    print(handler.dict_alarms)




