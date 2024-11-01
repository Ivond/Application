#
from typing import Optional, Dict
#import re
import time
#import logging
#import sqlite3
from pathlib import Path
#from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_wind_alarms

class WindowSLASwitchHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Создаем переменные в которых записываем путь к файлам
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_critical = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        # Название аварии
        self.name_alarm = ''
        # Название канала
        self.channel_name = ''
        # Описание аварии
        self.description = ''
        # IP адрес
        self.ip = ''
        
    # Метод принимает на вход ip адрес, номер sla, название аварии и добавляет дату и время возникновения аварии
    def _add_date_time_alarm(self, ip: str, sla: int, key: str) -> None:
        # Получаем текущую дату и время   
        date_time = self._date_to_str()
        # Если метод get вернет None для ключа ip
        if dict_wind_alarms[key].get(ip) is None:
            # Добавляем дату и время возниконовения аварии и начла аврии в словарь dict_alarm
            dict_wind_alarms[key][ip] = {sla:{'date_time': date_time, 'start_time': time.time()}}
        elif dict_wind_alarms[key][ip].get(sla) is None:
            # Добавляем дату и время возниконовения аварии и начла аврии в словарь dict_alarm
            dict_wind_alarms[key][ip][sla] = {'date_time': date_time, 'start_time': time.time()}
    
    # Метод принимает на вход строку с данными, возращает сообщение 
    def alarm_handler(self, line: str) -> Optional[str]:
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Вызываем метод который возвращает ip адреса коммутатора
            self.ip = self._parse_ip(line)
            # Вызываем метод который возвращает номер sla коммутатора
            sla = self._parse_sla(line)
            # Вызываем метод который возвращает название канала
            self.channel_name = self._parse_channel_name(self.ip, sla=sla)
            # Вызываем метод _parse_message, получаем строку с параметрами
            sla_parametrs = self._parse_message(line)
            # Формируем строку подставив название канала и параметры коммутатора
            row = f'{self.channel_name}: {sla_parametrs[1]}' 
        # Попали в исключение, значит ip адрес или sla коммутатора удален из БД, останавливаем метод
        except (TypeError, IndexError):
            return None
        # Вызываем метод, который возвращает Статус SLA (Up или Down)
        sla_status = self._parse_sla_status(line)
        # Вызываем метод, который возвращает значение icmp_echo
        icmp_echo = self._parse_icmp_echo(line)
        # Получаем размер шрифта который установлен во вкладке "Каналы"
        font_size = self._get_font_size_frame_channel()
        if isinstance(font_size, int):
            # Устанавливаем стили нашей строке с данными
            text = '''<p><img src="{}" width="{}" height="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, font_size, font_size, row)
        # Если тип переменной строка И значение равно Down И тип переменной sla_parametrs строка
        if isinstance(sla_status, str) and sla_status == 'Down' and isinstance(sla_parametrs, str) and isinstance(sla, int):
            #
            self.name_alarm = 'icmp_echo'
            # Меняем стиль значения sla_status на жирный шрифт 
            sla_parametrs = sla_parametrs.replace(f'SlaStatus: {sla_status}', f'<b style = "font-weight: 900;">SlaStatus: {sla_status}</b>')
            '''Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
            на всем протяжении длительности аварии. Для этого добавляем в словарь dict_alarm дату и время'''     
            # Добавляем дату возникновения аварии
            self._add_date_time_alarm(self.ip, sla, 'sla')
            # Получаем дату и время начала аварии в определенном формате для подставления ее в сообщение
            start_date_time = dict_wind_alarms['sla'][self.ip][sla].get('date_time')
            # Получаем время начала аварии в секундах из словаря dict_alarm
            start_time = dict_wind_alarms['sla'][self.ip][sla].get('start_time')
            # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
            duration_alarm = self._convert_time(time.time() - start_time)
            # Если значение icmp_echo True
            if icmp_echo:
                # Формируем сообщение для отправки
                self.description = 'Потеря icmp-пакетов по каналу'
            else:
                # Формируем сообщение для отправки
                self.description = 'Пропадание канала'
            # Подсвечиваем строку бордовым цветом и цвет текста белый
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{} {} {} {}</span><strong>  {}</strong></p>'''.format(self.path_icon_critical, font_size, font_size, start_date_time, self.channel_name, self.description, sla_parametrs, duration_alarm)
            return text_alarm
        # Если тип переменной sla_status строка И значение переменной равно Up И тип переменной sla число
        elif isinstance(sla_status, str) and sla_status == 'Up' and isinstance(sla, int):
            self.name_alarm = "None"
            # Проверяем если ip адреса есть в словаре аврий
            if dict_wind_alarms['sla'].get(self.ip) is not None:
                # Проверяем если порт есть в словаре аварий
                if dict_wind_alarms['sla'][self.ip].get(sla):
                    # Удаляем сообщение об аварии из dict_alarms
                    del dict_wind_alarms['sla'][self.ip][sla]
            return text
        return None
            
        