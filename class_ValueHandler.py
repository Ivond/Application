#
from typing import Union, Optional, Tuple
import sqlite3
import re
import time
import logging
from datetime import datetime
from class_SqlLiteMain import ConnectSqlDB
from dictionaryAlarms import dict_interim_alarms, dict_wind_alarms

class ValueHandler:
    def __init__(self) -> None:
        # Настройка логирования
        self.logger = logging.getLogger('base_value_handler')
        logging.basicConfig(#filename=Path(Path.cwd(),"GGS", "logs_v640.txt"), 
        #filemode='w', 
        format = '%(asctime)s %(name)s: %(lineno)d: %(message)s', 
        datefmt='%d-%m-%y',
        level=logging.DEBUG)
        #self.logger.setLevel(logging.DEBUG)
          
    # Метод нимает на вход ip адрес устройства, возвращает строку с название места установки или None
    def _get_name(self, ip: str) -> Union[str, None]:
        try:
            # Создаем экземпляр класса sql
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД, получаем описание устройства соответствующее Ip адресу
                hostname = sql.get_db('description', ip=ip, table='Devices')[0]
        except (sqlite3.IntegrityError, IndexError) as err:
            return None
        else:
            return hostname
        
    # Метод принимает на вход строку с параметрами, возвращает строку с ip адресом устройства или None 
    def _parse_ip(self, line: str) -> Optional[str]:
        match = re.match(r'.*?(?P<ip>\d*\.\d*\.\d*\.\d*).+', line)
        if match:
            ip_addr = match.group('ip')
            return ip_addr
        return None
        
    # Метод принимает на вход ip адрес устройсва, возвращает числовое значение номера окна
    def _get_num_window(self, ip: str) -> Optional[int]:
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, получаем номер окна куда выводить аврию
            window_number = sql.get_db('num_window', ip=ip, table='Devices')[0]
        return window_number
    
    # Метод принимает на вход строку с параметрами, возвращает числовое значение "Количество итераций цикла" или None
    def _parse_count(self, line: str) -> Union[int, None]:
        # Получаем количество итераций цикла из строки полученной от ThreadSNMPAsc
        match = re.match(r'.+Count: (?P<count>\d*)', line)
        if match:
            count = match.group('count')
            return int(count)
        return None
        
    # Метод преобразует дату модуля time и возвращает строковое представление
    def _date_to_str(self) -> str:
        # Получаем кортеж с датой, временем и т.д.
        date_tuple = time.localtime()
        # Преобразуем дату и время в нужный нам формат
        date = time.strftime('%d-%m-%Y %H:%M:%S', date_tuple)
        return date
        
    # Метод преобразует принимает на вход числовое значние времени и возвращает строковое представление 
    # в виде День, Часы:Минуты:Секунды
    def _convert_time(self, sec: float) -> str:
        # Вычисляем количество дней
        day = int(sec // (24 * 3600))
        # Если количество дней не равно 0
        if day:
            # Вычисляем остаток от количества дней(часы)
            sec %= (24 * 3600)
            # Вычисляем количество часов, преобразуем в строку, удаляем ноль сточкой после числа (11.0)
            hour = str(round(sec /3600))
            if len(hour) == 1:
                hour = f'0{hour}'
            # Вычисляем остаток от количества часов, т.е. минуты
            sec %= 3600
            # Вычисляем количество минут, округляем и преобразуем в строку
            minu = str(round(sec//60))
            if len(minu) == 1:
                minu = f'0{minu}'
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'{day}д. {hour}:{minu}:{int(sec)}'
        # Вычисляем количество часов
        hour = str(round(sec // 3600))
        # Если количество часов не равно 0
        if hour:
            if len(hour) == 1:
                hour = f'0{hour}'
            # Вычисляем остаток от количества часов(мин)
            sec %= 3600
            # Вычисляем количество минут, округляем до целого числа (без нуля после точки 11.0) преобразуем в строку
            minu = str(round(sec//60))
            if len(minu) == 1:
                minu = f'0{minu}'
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'{hour}:{minu}:{int(sec)}'
        # Вычисляем количество минут, округляем до целого числа (без нуля после точки 11.0) преобразуем в строку
        minu = str(round(sec//60))
        if minu:
            if len(minu) == 1:
                minu = f'0{minu}'
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'00:{minu}:{int(sec)}'
        else:
            # Вычисляем остаток от количества минут(сек)
            sec %= 60
            return f'00:00:{int(sec)}'
    
    # Метод принимает на вход ip-адрес устройства и дату окончания аварии, возвращает время работы оборудования на АКБ 
    def _battery_operating_time(self, ip: str, time_end: str) -> Optional[str]:
        # Создаем экземпляр класса sql
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД и получаем словарь с текущими авариями
            dic_data = sql.get_values_dict_db('json_extract(data, "$.date")', table='Alarms')
        #
        if ip in dic_data:
            # Изменяем формат даты и времени начала возникновения аварии
            start_time = datetime.strptime((dic_data[ip]).strip(), "%d-%m-%Y  %H:%M:%S")
            # Изменяем формат даты и времени окончании аварии
            end_time = datetime.strptime((time_end).strip(), "%d-%m-%Y  %H:%M:%S")
            # Вычисляем разницу между конечным и начальным временем начала аварии
            delta = (end_time - start_time)
            # Получаем количество дней
            day = delta.days # -> int
            # Получаем количчество секунд
            sec = delta.seconds # -> int
            if day:
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
            return None
        
    # Метод подтвержадет, что аврия активна в течении нескольких циклах опроса   
    def _confirme_alarm(self, name_alarm, ip, counter):
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Получаем количество проверок 
            number_of_checks = sql.get_db('num', alarms = 'monitor_count', table = 'Settings')[0]
        # Если ip адреса нет в словаре
        if ip not in dict_interim_alarms[name_alarm]:
            # Добавляем в словарь dict_interim_alarms индекс сообщения 1 - это значит мы получили
            # сообщение об аврии первый раз, а так же количество итераций цикла.
            dict_interim_alarms[name_alarm][ip] = [1, counter]
            return False
        # Если индекс сообщения равен 1 И разность итераций цикла равно num ИЛИ num+1
        elif dict_interim_alarms[name_alarm][ip][0] == 1 and ((counter - dict_interim_alarms[name_alarm][ip][1]) == number_of_checks \
            or (counter - dict_interim_alarms[name_alarm][ip][1]) == number_of_checks + 1):
            # Добавляем в dict_interim_alarms идекс сообщения 2, который говорит, что мы второй раз
            # получили одну и туже аврию в течении нескольких итераций цикла
            dict_interim_alarms[name_alarm][ip][0] = 2
            return True
        # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num+2, 
        # значит мы второй раз не получили одну и туже аварию в течение нескольких итераций цикла
        elif dict_interim_alarms[name_alarm][ip][0] == 1 \
        and (counter - dict_interim_alarms[name_alarm][ip][1]) > number_of_checks + 2:
            # Удаляем значение не подтвержденной аварии из словаря промежуточных аварий
            del dict_interim_alarms[name_alarm][ip]
            return False
        else:
            return False
    
    # Метод разбирает строку на дату и описание параметров устройства
    def _parse_message(self, line: str) -> Optional[Tuple[str, str]]:
        match_ups = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>IN.+)', line)
        match_dgu = re.match(r'^(?P<date>[\d+\-*]+ [\d+\:*]+).+(?P<description>ОПС.+) Двиг', line)
        match_macc_fiber2 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>TxFiber2.+)', line)
        match_macc_fiber1 = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>TxFiber1.+)', line)
        match_power_system = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>Phase_A:.+)', line)
        match_sla = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>SlaStatus.+)', line)
        match_port = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>OperStatus.+)', line)
        match_error_sw = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>CISCO.+)', line)
        match_error_ups = re.match(r'^(?P<date>[\d+\-*]+ +[\d+\:*]+) .+(?P<description>SNMP.+)', line)
        # Это условие для ИБЭП
        if match_ups:
            date = match_ups.group('date').strip()
            description = match_ups.group('description').strip()
            return date, description
        # Это условия для сообщения приходящего по протоколу ModBus
        elif match_dgu:
            date = match_dgu.group('date').strip()
            description = match_dgu.group('description').strip()
            return date, description
        # Это условие для MAC&C
        elif match_macc_fiber2:
            date = match_macc_fiber2.group('date').strip()
            description = match_macc_fiber2.group('description').strip()
            return date, description
        # Это условие для MAC&C
        elif match_macc_fiber1:
            date = match_macc_fiber1.group('date').strip()
            description = match_macc_fiber1.group('description').strip()
            return date, description
        # Это условие для ИБП с контроллером MC-2600
        elif match_power_system:
            date = match_power_system.group('date').strip()
            description = match_power_system.group('description').strip()
            return date, description
        # Это условие для Cisco IP SLA
        elif match_sla:
            date = match_sla.group('date').strip()
            description = match_sla.group('description').strip()
            return date, description
        # Это условие для Cisco Port
        elif match_port:
            date = match_port.group('date').strip()
            description = match_port.group('description').strip()
            return date, description
        #
        elif match_error_sw:
            date = match_error_sw.group('date').strip()
            description = match_error_sw.group('description').strip()
            return date, description
        elif match_error_ups:
            date = match_error_ups.group('date').strip()
            description = match_error_ups.group('description').strip()
            return date, description
        return None

    # Метод возвращает числовое значение размера шрифта текста во вкладке "Общая информация"
    def _get_font_size_frame(self, number_window: int) -> Union[int, None]:
        with ConnectSqlDB() as sql:
            if number_window == 1:
                font_size = sql.get_db('value', description='font_size_frame1', table = 'Styles')[0] 
            elif number_window == 2:
                font_size = sql.get_db('value', description='font_size_frame2', table = 'Styles')[0]
            elif number_window == 3:
                font_size = sql.get_db('value', description='font_size_frame3', table = 'Styles')[0]
            elif number_window == 4:
                font_size = sql.get_db('value', description='font_size_frame4', table = 'Styles')[0]
        # Если тип значения число
        if isinstance(font_size, int):
            return font_size
        return None

    # Метод возвращает числовое значение размера шрифта текста во вкладке "Текущие аварии"
    def _get_font_size_frame_alarm(self) -> Optional[int]:
        with ConnectSqlDB() as sql:
            font_size = sql.get_db('value', description='font_size_current_alarm', table = 'Styles')[0]
        if isinstance(font_size, int):
            return font_size
        return None

    # Метод получает значение размера шрифта текста который установлен во вкладке "Каналы"
    def _get_font_size_frame_channel(self) -> Optional[int]:
        with ConnectSqlDB() as sql:
            font_size = sql.get_db('value', description='font_size_channel', table = 'Styles')[0] 
        if isinstance(font_size, int):
            return font_size
        return None

    # Метод принимает на вход ip-адрес, название аварии и добавляет дату и время возникновения аварии в словарь аварий
    def _add_date_time_alarm(self, ip: str, key: str) -> None:
        # Вызываем метод, кторый вернет дату и время начала аврии в строковом представлении   
        date_time = self._date_to_str()
        # Если метод get вернет None для ключа ip
        if dict_wind_alarms[key].get(ip) is None:
            # Добавляем дату и время возниконовения аварии и начла аврии в словарь dict_alarms
            dict_wind_alarms[key][ip]= {'date_time': date_time, 'start_time': time.time()}
        return None

    # Метод принмает на вход ip-адрес и название аварии, удаляет запись об аврии из словарей
    def _remove_ip_from_dict_alarms(self, ip: str, *key_alarms: str) -> None:
        for alarm in key_alarms:
            # Если есть запись в словаре аврий
            if dict_wind_alarms[alarm].get(ip):
                # Удаляем запись из словаря аварий
                del dict_wind_alarms[alarm][ip]
            try:
                # Если есть запись в словаре промежуточных аварий
                if dict_interim_alarms[alarm].get(ip):
                    # Удаляем запись из словаря промежуточных аварий
                    del dict_interim_alarms[alarm][ip]
            except KeyError:
                pass
        
    # ИБЭП
        
    # Метод принимает на вход строку с параметрами ИБЭП, возвращает числовое значение "Входного напряжения" или None
    def _parse_voltage_in(self, line: str) -> Union[int, None]:
        match = re.match(r'.+IN: *(?P<voltage>\d+)', line)
        if match:
            voltage = match.group('voltage').strip()
            return int(voltage)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_voltage_in вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами ИБЭП, возвращает числовое значение "Выходного напряжения" или None
    def _parse_voltage_out(self, line: str) -> Optional[float]:
        match = re.match(r'.+OUT: *(?P<voltage>\d+\.*\d*)', line)
        if match:
            voltage = match.group('voltage').strip()
            return float(voltage)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_voltage_out вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами ИБЭП, возвращает числовое значение "Температуры" или None
    def _parse_temperature(self, line: str) -> Union[int, None]:
        match = re.match(r'.+\*C: +(?P<temp_value>-*\d+)', line)
        if match:
            temperature_value = match.group('temp_value').strip()
            return int(temperature_value)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_temperature вернул None: {line}")
        return None
    
    def _parse_phase(self, line: str) ->Union[Tuple[float, float, float], None]:
        match = re.match(r'.+Phase_A: +(?P<phase1>\d+\.\d*) V Phase_B: +(?P<phase2>\d+\.\d*) V Phase_C: +(?P<phase3>\d+\.\d*) V', line)
        if match:
            phase1 = match.group('phase1').strip()
            phase2 = match.group('phase2').strip()
            phase3 = match.group('phase3').strip()
            return float(phase1), float(phase2), float(phase3)
        return None
        
    # MAC$C

    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Температуры SFP_1 модуля" или None
    def _parse_temp_fiber1(self, line: str) -> Optional[str]:
        match = re.match(r'.+TempFiber1: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber1 = match.group('temp_value').strip()
            return temp_fiber1
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_temp_fiber1 вернул None: {line}")
        return None
    
    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Температуры SFP_2 модуля" или None
    def _parse_temp_fiber2(self, line: str) -> Optional[str]:
        match = re.match(r'.+TempFiber2: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber2 = match.group('temp_value').strip()
            return temp_fiber2
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_temp_fiber2 вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Температуры SFP_3 модуля" или None
    def _parse_temp_fiber3(self, line: str) -> Optional[str]:
        match = re.match(r'.+TempFiber3: +(?P<temp_value>[-+]*\d+)', line)
        if match:
            temp_fiber3 = match.group('temp_value').strip()
            return temp_fiber3
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_temp_fiber3 вернул None: {line}")
        return None
    
    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Tx SFP_1 модуля" или None
    def _parse_tx_fiber1(self, line: str) -> Optional[str]:
        match = re.match(r'.+TxFiber1: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber1 = match.group('tx_value').strip()
            return tx_fiber1
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_tx_fiber1 вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Tx SFP_2 модуля" или None
    def _parse_tx_fiber2(self, line: str) -> Optional[str]:
        match = re.match(r'.+TxFiber2: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber2 = match.group('tx_value').strip()
            return tx_fiber2
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_tx_fiber2 вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение " Tx SFP_3 модуля" или None
    def _parse_tx_fiber3(self, line: str) -> Optional[str]:
        match = re.match(r'.+TxFiber3: +(?P<tx_value>[-+]*\d+)', line)
        if match:
            tx_fiber3 = match.group('tx_value').strip()
            return tx_fiber3
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_tx_fiber3 вернул None: {line}")
        return None
    
    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Rx SFP_1 модуля" или None
    def _parse_rx_fiber1(self, line: str) -> Optional[str]:
        match = re.match(r'.+RxFiber1: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber1 = match.group('rx_value').strip()
            return rx_fiber1
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_rx_fiber2 вернул None: {line}")
        return None
    
    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Rx SFP_2 модуля" или None
    def _parse_rx_fiber2(self, line: str) -> Optional[str]:
        match = re.match(r'.+RxFiber2: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber2 = match.group('rx_value').strip()
            return rx_fiber2
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_rx_fiber2 вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами MAC&C, возвращает числовое значение "Rx SFP_3 модуля" или None
    def _parse_rx_fiber3(self, line: str) -> Optional[str]:
        match = re.match(r'.+RxFiber3: +(?P<rx_value>[-+]*\d+)', line)
        if match:
            rx_fiber3 = match.group('rx_value').strip()
            return rx_fiber3
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_rx_fiber3 вернул None: {line}")
        return None
        
    # ДГУ 

    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Количества топлива" или None
    def _parse_level_oil(self, line: str) -> Union[int, None]:
        match = re.match(r'.+Топл\.:(?P<level_oil>\d+)%', line)
        if match:
            level_oil = match.group('level_oil').strip()
            return int(level_oil)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_level_oil вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Состояния работы двигателя" или None
    def _parse_motor_work(self, line: str) -> Optional[int]:
        bit_0 = re.match(r'.+Двиг\.:\[(?P<motor>\d*)\];', line)
        if bit_0:
            motor_work = bit_0.group('motor').strip()
            return int(motor_work)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_motor_work вернул None: {line}")
        return None
    
    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Высокой температуры О/Ж" или None
    def _parse_hight_temp_water(self, line: str) -> Union[int, None]:
        bit_2 = re.match(r'.+Выс\.Темп_О/Ж:\[(?P<hight_water>\d*)\];', line)
        if bit_2:
            hight_temp_water = bit_2.group('hight_water').strip()
            return int(hight_temp_water)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_hight_temp_water вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Низкой температуры О/Ж" или None    
    def _parse_low_temp_water(self, line: str) -> Union[int, None]:
        bit_3 = re.match(r'.+Низ\.Темп_О/Ж:\[(?P<low_water>\d*)\]', line)
        if bit_3:
            low_water = bit_3.group('low_water').strip()
            return int(low_water)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_low_temp_water вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Давления масла в двигателе" или None
    def _parse_low_pressure_oil(self, line: str) -> Union[int, None]:
        bit_4 = re.match(r'.+ДМ:\[(?P<low_oil>\d*)\];', line)
        if bit_4:
            low_oil = bit_4.group('low_oil').strip()
            return int(low_oil)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_low_pressure_oil вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Уровня О/Ж" или None
    def _parse_level_water(self, line: str) -> Optional[int]:
        bit_6 = re.match(r'.+Уров\.О/Ж:\[(?P<level_water>\d*)\];', line)
        if bit_6:
            level_water = bit_6.group('level_water').strip()
            return int(level_water)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_level_water вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Уровня топлива" или None
    def _parse_low_level_oil(self, line: str) -> Union[int, None]:
        bit_7 = re.match(r'.+Топл\.:\[(?P<level_oil>\d*)\];', line)
        if bit_7:
            level_oil = bit_7.group('level_oil').strip()
            return int(level_oil)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_low_level_oil вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Режима работы ДГУ" или ТNone
    def _parse_switch_motor(self, line: str) -> Union[int, None]:
        bit_8 = re.match(r'.+ПУД:\[(?P<switch_motor>\d*)\];', line)
        if bit_8:
            switch_motor = bit_8.group('switch_motor').strip()
            return int(switch_motor)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_switch_motor вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами ДГУ, возвращает числовое значение "Низкого заряда АКБ" или None
    def _parse_low_batt(self, line: str) -> Union[int, None]:
        bit_10 = re.match(r'.+Бат\.:\[(?P<low_batt>\d*)\]', line)
        if bit_10:
            low_batt = bit_10.group('low_batt').strip()
            return int(low_batt)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_low_batt вернул None: {line}")
        return None
        
    # SWITCH

    # Метод принимает на вход ip-адрес, номер порта и SLA коммутатора Cisco, возращает строковое значение название канала или None
    def _parse_channel_name(self, ip: str, port: Optional[int] = None, sla: Optional[int] = None) -> Union[str, None]:
        try:
            # Создаем экземпляр класса sql
            with ConnectSqlDB() as sql:
                if port:
                    # Делаем запрос к БД, получаем кортеж со значением с "Описанием канала"
                    channel_name = sql.get_db('description', ip_addr=ip, port=port, table='Ports')[0]
                elif sla:
                    # Делаем запрос к БД, получаем кортеж со значением с "Описанием канала"
                    channel_name = sql.get_db('description', ip_addr=ip, sla=sla, table='Ports')[0]  
        except (sqlite3.IntegrityError, IndexError) as err:
            # Выводим сообщение 
            self.logger.info(f"Ошибка запроса  _parse_channel_name: {err}")
            return None
        # Иначе, если код выполнен без ошибок
        else:
            if isinstance(channel_name, str):
                return channel_name
        return None
        
    # Метод принимает на вход строку с параметрами Коммутатора, возвращает числовое значение "Номер порта" или None
    def _parse_port_number(self, line: str) -> Optional[str]:
        # Получаем значение порта коммутатора из строки полученной от ThreadSNMPSWitch
        match = re.match(r'.+Port: (?P<port>\d*)', line)
        if match:
            port = match.group('port')
            return port
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_port_number вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами Коммутатора, возвращает числовое значение порта или Sla или None
    def _parse_value(self, line: str) -> Union[int, None]:
        # Получаем значение порта коммутатора из строки полученной от ThreadSNMPSWitch
        match = re.match(r'.+Port: (?P<port>\d*)', line)
        # Получаем значение порта коммутатора из строки полученной от ThreadSNMPSWitch
        match1 = re.match(r'.+Number: (?P<number>\d*)', line)
        # Получаем значение порта коммутатора из строки полученной от ThreadSNMPSWitch
        match2 = re.match(r'.+Sla: (?P<sla>\d*);', line)
        # 
        if match:
            port = match.group('port')
            return int(port) 
        # ОШИБКА ПО ДОСТУПНОСТИ КОММУТАТОРА CISCO SNMP REQESTERR
        if match1:
            port = match1.group('number')
            return int(port)
        # SLA 
        if match2:
            sla = match2.group('sla')
            return int(sla)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_value вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами Коммутатора, возвращает строковое значение "Статус порта" или None
    def _parse_status_port(self, line: str) -> Union[str, None]:
        match = re.match(r'.+OperStatus: (?P<status_port>\w+)', line)
        if match:
            oper_status = match.group('status_port').strip()
            return oper_status
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_status_port вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами Коммутатора, возвращает строковое значение "Статус канала" или None
    def _parse_status_channel(self, line: str) -> Union[str, None]:
        match = re.match(r'.+ChannelStatus: (?P<channel>\S+);', line)
        if match:
            chanel = match.group('channel').strip()
            return chanel
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_status_channel вернул None: {line}")
        return None

    # Метод принимает на вход строку с параметрами Коммутатора, возвращает числовое значение "Номер SLA"
    def _parse_sla(self, line: str) -> Union[int, None]:
        # Получаем значение порта коммутатора из строки полученной от ThreadSNMPSWitch
        match = re.match(r'.+Sla: (?P<sla>\d*);', line)
        if match:
            sla = match.group('sla')
            return int(sla)
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_sla вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами Коммутатора, возвращает строковое значение "Статус SLA (Up или Down)" или None
    def _parse_sla_status(self, line: str) -> Union[str, None]:
        match = re.match(r'.+SlaStatus: (?P<sla>\S+)', line)
        if match:
            sla = match.group('sla').strip()
            return sla
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_sla_status вернул None: {line}")
        return None
        
    # Метод принимает на вход строку с параметрами Коммутатора, возвращает строковое значение "icmp_echo" или None
    def _parse_icmp_echo(self, line: str) -> Union[str, None]:
        # Получаем значение порта коммутатора из строки полученной от ThreadSNMPSWitch
        match = re.match(r'.+ICMP_ECHO: (?P<icmp_echo>\d*);', line)
        if match:
            icmp_echo = match.group('icmp_echo')
            return icmp_echo
        # Выводим сообщение 
        self.logger.info(f"Метод _parse_icmp_echo вернул None: {line}")
        return None
        
if __name__ == "__main__":
    
    #line = '10.31.31.2 Port: 52; Count 22; ChannelStatus: Up; OperStatus: Up; InOctets: 365 Mbs; OutOctets: 90 Mbs'
    #line1 = '05-05-2023 12:33:35 10.25.31.3 Port: 52; Count 3; ChannelStatus: Up; OperStatus: Up; InOctets: 86 Mbs; OutOctets: 274 Mbs'
    line2 = '21-10-2023 19:03:11 10.184.50.8 Count: 1; Phase_A: 240.4 V Phase_B: 242.8 V Phase_C: 241.4 V; OUT: 53.7 V (28.1 А)'
    handler = ValueHandler()
    #value = handler._date_to_str()
    #port = handler._parse_port_number('dgdgfgf')
    #in_voltage = handler._parse_voltage_in()
    phase = handler._parse_phase(line2)
    #time = handler._convert_time(1683544397.5458345)
    print(phase)

        
    
            
    


                
             
        
    
    