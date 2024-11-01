#
from msilib.schema import tables
from typing import Optional, Dict, Any
import logging
import re
import time
import sqlite3
from pathlib import Path
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_wind_alarms, dict_interim_alarms

class WindowERRORAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
       # Переменная в которой будем хранить путь к файлу с иконкой IFO 
        self.path_icon_error = str(Path(Path.cwd(), "Resources", "Icons", "icn23.ico"))
        # Значение количества проверок перед отправкой сообщения
        #self.number_of_checks = 3
        # Будем записывать тип ошибки
        self.is_error = ''
        # Флаг подтверждения аварии
        self.is_alarm = False 
        # Номер окна 
        self.num_window = 4
        # IP адрес
        self.ip_addr = ''
        # Название аварии
        self.name_alarm = ''
        # Строка сообщения
        self.row_error = ''
        # Имя канала
        self.host_name = ''


    # Метод принимает на вход строку с данными, возвращает строковое описание ошибки
    #def _parse_erro(self, line: str) -> Optional[str]:
        #match = re.match(r'.+(?P<description>CISCO.+)', line)
        #match1 = re.match(r'.+(?P<error>SNMP.+)', line)
        # Это условие для Cisco ERROR
        #if match:
            #self.is_error = 'cisco'
            #cisco_error = match.group('description').strip()
            #return cisco_error
        # Ошибка UPS, MAC&C ERROR
        #elif match1:
            #self.is_error = 'ups'
            #error = match1.group('error').strip()
            #return error
        #return None

    # Метод подтвержадет, что аврия активна в течении нескольких циклах опроса   
    def _confirme_battery_disconnect(self, name_alarm, ip, counter):
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
            # Флаг, который активирует выполнение следующих действий в классе SecondWindow
            self.is_alarm = True
            return True
        # Проверяем если индекс сообщения равен 1 И количество итераций цикла больше num+2, 
        # значит мы второй раз не получили одну и туже аварию в течение нескольких итераций цикла
        elif dict_interim_alarms[name_alarm][ip][0] == 1 \
        and (counter - dict_interim_alarms[name_alarm][ip][1]) > number_of_checks + 2:
            # Удаляем значение не подтвержденной аварии из словаря промежуточных аварий
            del dict_interim_alarms[name_alarm][ip]
            return False
        elif dict_interim_alarms[name_alarm][ip][0] == 2:
            # Флаг, который активирует выполнение следующих действий в классе SecondWindow
            self.is_alarm = False
            return True
        else:
            return False

    # Метод принимает на вход строку с данными возвращает строку собщения
    def alarm_handler(self, line: str) -> Optional[str]:
        # Ловим исключение на случай удаления ip адреса из списка БД при открытом Окне мониторинга
        try:
            # Получаем IP адрес вызвав метод _parse_ip
            ip = self._parse_ip(line)
            if isinstance(ip, str):
                self.ip_addr = ip
                # Вызываем метод, который получает номер окна в которое будет выводится сообщение
                self.num_window = self._get_num_window(ip)
                # Получаем имя которое соответствует ip адресу
                host_name = self._get_name(ip)
                if isinstance(host_name, str):
                    self.host_name = host_name
                else:
                    # Присваиваем ip-адрес устройства вместо названия хоста
                    self.host_name = ip
            else:
                self.logger = logging.getLogger('WindowERRORAlarmHandler')
                self.logger.setLevel(logging.DEBUG)
                self.logger.debug(f'Не получил ip-адрес: {line}')
                return None
            # Вызываем метод, который распарсивает строку сообщения об ошибке
            data = self._parse_message(line)
            if isinstance(data, tuple):
                error = data[1]
                # Формируем строку подставив название  и параметры  
                self.row_error = f'{self.host_name} {error}'
            else:
                return None
        # Если попали в исключение то пропускаем все что ниже по коду
        except TypeError:
            return None
        # Вызываем метод _parse_count, получаем количество итераций цикла
        counter = self._parse_count(line)
        # Если тип ошибки равен 
        if error == 'CISCO_SNMP:REQEST_ERROR1':
            # Получаем размер шрифта установленного во вкладке "Каналы"
            font_size_image = self._get_font_size_frame_channel()
            # Присваиваем перемнной название аварии
            self.name_alarm = 'cisco_error'
            # Флаг, который активирует выполнение следующих действий в классе SecondWindow
            self.is_alarm = False
            # Вызываем метод, который возращает True если авария подтвердилась
            if self._confirme_alarm('request_err', ip, counter):
                # Флаг, который активирует выполнение следующих действий в классе SecondWindow
                self.is_alarm = True
            # Добавляем дату возникновения аварии
            self._add_date_time_alarm(ip, 'request_err')
            # Получаем дату и время начала аварии в определенном формате для подстановки ее в сообщение
            start_date_time = dict_wind_alarms['request_err'][ip].get('date_time')
            # Получаем время начала аварии в секундах из словаря dict_wind_alarms
            start_time = dict_wind_alarms['request_err'][ip].get('start_time')
            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
            duration_alarm = self._convert_time(time.time() - start_time)
            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}"> <span style="background-color: #FF0000; color: rgb(255, 255, 255);">{} {}</span> 
            <strong>{} </strong></p>'''.format(self.path_icon_error, font_size_image, font_size_image, start_date_time, self.row_error, duration_alarm)
            return text_alarm
        # Иначе мы получили аварию SNMP:REQEST_ERROR
        else:
            self.name_alarm = 'snmp_error' 
            # Вызываем метод, который получает значение размера шрифта устанволенного в окнах во вкладки Общая информация
            font_size_image = self._get_font_size_frame(self.num_window)
            # Подсвечиваем строку красным цветом и цвет текста белый
            text_alarm = '''<img src="{}" width="{}" height="{}"> <span style="background-color: #FF0000;
            color: rgb(255, 255, 255);">{}</span>'''.format(self.path_icon_error, font_size_image, font_size_image, self.row_error)
            # Подключаемся к БД
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД и получаем словарь с текущими авариями
                dic_power_alarm = sql.get_values_dict_db('json_extract(data, "$.power_alarm")', table='Duration')
                # Если ip адрес есть в словаре dic_power_alarm
                if self.ip_addr in dic_power_alarm:
                    # Вызываем метод, который возращает True если авария подтвердилась
                    if self._confirme_battery_disconnect('battery_disconnect', self.ip_addr, counter):
                        self.name_alarm = 'battery_disconnect'
                        # Формируем строку подставив название  и параметры  
                        #self.row_error = f'{self.host_name} <b>АКУМУЛЯТОРНЫЕ БАТАРЕИИ ОТКЛЮЧЕНЫ!!!</b>'
                        self.row_error = f'{self.host_name} <b>Батарейная группа отключена</b>'
                        # Подсвечиваем строку красным цветом и цвет текста белый
                        text_alarm = '''<img src="{}" width="{}" height="{}"> <span style="background-color: #FF0000;
                        color: rgb(255, 255, 255);">{}</span>'''.format(self.path_icon_error, font_size_image, font_size_image, self.row_error)
                        return text_alarm
                    else: 
                        return text_alarm
                else:
                    return text_alarm
                
    # Метод обрабатывает возвращает строку сообщения для вывода в окно "Текущие аварии" 
    def window_alarm_handler(self) -> str:
        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
        # на всем протяжении длительности аварии. Для этого добавляем в словарь dict_wind_alarms дату и время     
        # Добавляем дату возникновения аварии
        self._add_date_time_alarm(self.ip_addr, 'request_err')
        # Получаем дату и время начала аварии в определенном формате для подстановки ее в сообщение
        start_date_time = dict_wind_alarms['request_err'][self.ip_addr].get('date_time')
        # Получаем время начала аварии в секундах из словаря dict_alarm
        start_time = dict_wind_alarms['request_err'][self.ip_addr].get('start_time')
        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
        duration_alarm = self._convert_time(time.time() - start_time)
        # Вызываем метод, который получает значение размера шрифта устанволенного в окнах во вкладки Общая информация
        font_size_image = self._get_font_size_frame(self.num_window)
        # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
        # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
        text_alarm = '''<img src="{}" width="{}" height="{}"> <span style="background-color: #FF0000; color: rgb(255, 255, 255);">{} {}</span> 
        <strong>{} </strong>'''.format(self.path_icon_error, font_size_image, font_size_image, start_date_time, self.row_error, duration_alarm)
        return text_alarm
            
            