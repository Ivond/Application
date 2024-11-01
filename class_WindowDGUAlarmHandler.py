#
from typing import Optional, Dict, Any
import logging
import time
from pathlib import Path
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_wind_alarms

class WindowDGUAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Переменные в которых будем хранить путь к файлам с иконками
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_critical = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        # Переменная в которой будем хранить пороговое значение "Низкого уровня топлива"
        self.low_oil_limit = 35
        # Переменная в которой будем хранить название аварии
        self.name_alarm = ''
        # Переменная в которой будем хранить Название устройства
        self.host_name = ''
        # Переменная в которой будем хранить ip-адрес устройства
        self.ip_addr = ''
        # Номер окна
        self.num_window = 4
        #
        self.is_alarm = False 

    # Метод устанавливает пороговые значения полученные из БД      
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение порогового значения Низкий уровень топлива
            low_oil_level = sql.get_db('num', alarms='window_low_oil', table='Settings')[0]
            if isinstance(low_oil_level, int):
                self.low_oil_limit = low_oil_level
        return None
    
    # Метод обрабатывет значение по Низкому уровню топлива и возвращает текст сообщения
    def alarm_handler(self, line: str) -> Optional[str]:
        # Вызываем метод, который устанавливает пороговые значения аварий
        self._set_threshold_value_alarms()
        # Ловим исключение на случай удаления ip адреса из списка БД при открытом Окне мониторинга
        try:
            # Вызвав метод, который возвращает ip-адрес
            ip = self._parse_ip(line)
            if isinstance(ip, str):
                self.ip_addr = ip
                # Получаем название хоста
                host_name = self._get_name(ip)
                if isinstance(host_name, str):
                   self.host_name = host_name
                else:
                    self.host_name = ip
                # Вызываем метод, который получает номер окна в которое будет выводится сообщение
                num_window = self._get_num_window(ip)
                if isinstance(self.num_window, int):
                    self.num_window = num_window
                else:
                    self.num_window = 4
            else:
                self.logger = logging.getLogger('WindowERRORAlarmHandler')
                self.logger.setLevel(logging.DEBUG)
                self.logger.debug(f'Не получил ip-адрес: {line}')
                return None
            # Получаем параметры ДГУ
            dgu_parametrs = self._parse_message(line)
            # Формируем строку подставив название  и параметры 
            self.row = f'{self.host_name} {dgu_parametrs[1]}'
            # Вызываем метод, получаем размер шрифта
            font_size_image = self._get_font_size_frame(self.num_window)
            if isinstance(font_size_image, int):
                self.font_size_image = font_size_image
            else:
                self.font_size_image = 12
        # Если попали в исключение возвращаем None
        except (TypeError, IndexError):
            return None
        # Низкий уровень топлива
        low_oil = self._parse_level_oil(line)
        # Вызываем метод _parse_count, получаем количество итераций цикла
        counter = self._parse_count(line)

        # Если тип переменной low_oil число И значение больше порогового значения
        if isinstance(low_oil, int) and low_oil > self.low_oil_limit:
            self.name_alarm = "None"
            # Подсвечиваем строку зеленым цветом
            text = '''<img src="{}" width="{}" height="{}"> <span style="background-color:#00ff00;">{}
            </span>'''.format(self.path_icon_inf, self.font_size_image, self.font_size_image, self.row)
            # Вызываем метод который удаляет запись из словарей dict_alarm 
            self._remove_ip_from_dict_alarms(ip, 'low_level_oil')
            return text 
        # Если тип переменной low_oil число И значение меньше порогового
        elif isinstance(low_oil, int) and low_oil <= self.low_oil_limit:
            # Присваиваем перемнной название аварии
            self.name_alarm = 'low_level_oil'
            # Флаг подтверждения аварии
            self.is_alarm = False
            # Вызываем метод, который возращает True если авария подтвердилась
            if self._confirme_alarm('low_level_oil', ip, counter):
                # Флаг подтверждения аварии
                self.is_alarm = True
            # Подсвечиваем строку бордовым цветом, цвет текста белый
            text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{}</span>'''.format(self.path_icon_warn, self.font_size_image, self.font_size_image, self.row)
            return text_alarm
        return None

    # Метод обрабатывет значение по Аварийной остановке двигателя и возвращает текст сообщения
    def motor_stop_handler(self, line: str) -> Optional[str]:
        # Вызываем метод, который возвращает значение 0 или 1
        motor = self._parse_motor_work(line)
        # Получаем IP адрес вызвав метод _parse_ip
        ip = self._parse_ip(line)
        # Аварийная остановка двигателя
        if motor == 0:
            self.name_alarm = "None"
            # Подсвечиваем строку зеленым цветом
            text = '''<img src="{}" width="{}" height="{}"> <span style="background-color:#00ff00;">{} Экстренная остановка двигателя
            </span>'''.format(self.path_icon_inf, self.font_size_image, self.font_size_image, self.host_name)
            # Вызываем метод который удаляет дату и время начала аврии из словаря dict_alarm 
            self._remove_ip_from_dict_alarms(ip, 'motor')
            return text
        elif motor == 1:
            self.name_alarm = 'motor'
            self.description = 'Экстренная остановка двигателя'
            # Подсвечиваем строку бордовым цветом и цвет текста белый
            text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{} Экстренная остановка двигателя</span>'''.format(self.path_icon_critical, self.font_size_image, self.font_size_image, self.host_name)
            return text_alarm
        return None
    
    # Метод обрабатывет значение по Низкому давлению масла и возвращает текст сообщения
    def low_pressure_oil_handler(self, line: str) -> Optional[str]:
        # Низкое давление масла в двигателе
        low_pressure_oil = self._parse_low_pressure_oil(line)
        # Получаем IP адрес вызвав метод _parse_ip
        ip = self._parse_ip(line)
        # Вызываем метод _parse_count, получаем количество итераций цикла
        counter = self._parse_count(line)
        self.description = 'Низкое давление масла'
        # Если значение равно 0
        if low_pressure_oil == 0:
            # Присваиваем переменной название аврии None
            self.name_alarm = "None"
            # Подсвечиваем строку зеленым цветом
            text = '''<img src="{}" width="{}" height="{}"> <span style="background-color:#00ff00;">{}: Низкое давление масла
            </span>'''.format(self.path_icon_inf, self.font_size_image, self.font_size_image, self.host_name)
            # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
            self._remove_ip_from_dict_alarms(ip, 'low_pressure_oil')
            return text
        # Проверяем если значение равно 1 
        elif low_pressure_oil == 1:
            # Присваиваем переменной название аврии 
            self.name_alarm = 'low_pressure_oil'
            # Флаг подтверждения аварии
            self.is_alarm = False
            # Если ip адрес строка вызываем метод, который возращает True если авария подтвердилась
            if isinstance(ip, str) and self._confirme_alarm('low_pressure_oil', ip, counter):
                # Флаг подтверждения аварии
                self.is_alarm = True
            # Подсвечиваем строку бордовым цветом и цвет текста белый
            text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{} Низкое давление масла</span>'''.format(self.path_icon_critical, self.font_size_image, self.font_size_image, self.host_name)
            return text_alarm
        return None
    
    # Метод обрабатывет значение по Низкому уровню О/Ж и возвращает текст сообщения
    def low_level_water_handler(self, line: str) -> Optional[str]:
        # Низкий уровень О/Ж
        level_water = self._parse_level_water(line)
        # Получаем IP адрес вызвав метод _parse_ip
        ip = self._parse_ip(line)
        # Низкий уровень О/Ж
        if level_water == 0:
            self.name_alarm = "None"
            # Подсвечиваем строку зеленым цветом
            text = '''<img src="{}" width="{}" height="{}"> <span style="background-color:#00ff00;">{}: Низкий уровень О/Ж
            </span>'''.format(self.path_icon_inf, self.font_size_image, self.font_size_image, self.host_name)
            # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
            self._remove_ip_from_dict_alarms(ip, 'low_level_water')
            return text
        elif level_water == 1:
            self.name_alarm = 'low_level_water'
            # Флаг подтверждения аварии
            self.is_alarm = True
            #name = 'Низкий уровень О/Ж'
            self.description = 'Низкий уровень О/Ж'
            # Подсвечиваем строку бордовым цветом и цвет текста белый
            text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{} Низкий уровень О/Ж</span>'''.format(self.path_icon_critical, self.font_size_image, self.font_size_image, self.host_name)
            return text_alarm
        return None
    
    # Метод обрабатывет значение по Низкой температуре О/Ж и возвращает текст сообщения
    def low_temp_water_handler(self, line: str) -> Optional[str]:
        # Низкая температура О/Ж
        low_temp_water = self._parse_low_temp_water(line)
        # Получаем IP адрес вызвав метод _parse_ip
        ip = self._parse_ip(line)
        # Низкая температура О/Ж
        if low_temp_water == 0:
            self.name_alarm = "None"
            # Подсвечиваем строку зеленым цветом
            text = '''<img src="{}" width="{}" height="{}"> <span style="background-color:#00ff00;">{}: Низкая температура О/Ж
            </span>'''.format(self.path_icon_inf, self.font_size_image, self.font_size_image, self.host_name)
            # Вызываем метод который удаляет запись об аварии из словарей date_alarm и dic_alarm_sound 
            self._remove_ip_from_dict_alarms(ip, 'low_temp_water')
            return text
        elif low_temp_water == 1:
            self.name_alarm = 'low_temp_water'
            # Флаг подтверждения аварии
            self.is_alarm = True
            #name = 'Низкая температура О/Ж'
            self.description = 'Низкая температура О/Ж'
            # Подсвечиваем строку бордовым цветом и цвет текста белый
            text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{} Низкая температура О/Ж</span>'''.format(self.path_icon_critical, self.font_size_image, self.font_size_image, self.host_name)
            return text_alarm
        return None
    
    # Метод обрабатывет значение по Высокой температуре О/Ж и возвращает текст сообщения
    def hight_temp_water_handler(self, line: str) -> Optional[str]:
        # Высокая температура О/Ж
        hi_temp_water = self._parse_hight_temp_water(line)
        # Получаем IP адрес вызвав метод _parse_ip
        ip = self._parse_ip(line)
        # Высокая температура О/Ж
        if hi_temp_water == 0:
            self.name_alarm = "None"
            # Подсвечиваем строку зеленым цветом
            text = '''<img src="{}" width="{}" height="{}"> <span style="background-color:#00ff00;">{} Высокая температура О/Ж
            </span>'''.format(self.path_icon_inf, self.font_size_image, self.font_size_image, self.host_name)
            # Вызываем метод который удаляет запись из словарей date_alarm и dic_alarm_sound 
            self._remove_ip_from_dict_alarms(ip, 'hight_temp_water')
            return text
        elif hi_temp_water == 1:
            self.name_alarm = 'hight_temp_water'
            # Флаг подтверждения аварии
            self.is_alarm = True
            #name = 'Высокая температура О/Ж'
            self.description = 'Высокая температура О/Ж'
            # Подсвечиваем строку бордовым цветом и цвет текста белый
            text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{}: Высокая температура О/Ж</span>'''.format(self.path_icon_critical, self.font_size_image, self.font_size_image, self.host_name)
            return text_alarm
        return None
            
    # Метод обрабатывает возвращает строку сообщения для вывода в окно "Текущие аварии" 
    def window_alarm_handler(self) -> Optional[str]:
        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
        # на всем протяжении длительности аварии. Для этого добавляем в словарь dict_alarms дату и время     
        # Добавляем дату возникновения аварии
        self._add_date_time_alarm(self.ip_addr, self.name_alarm)
        # Получаем дату и время начала аварии в определенном формате для подстановки ее в сообщение
        start_date_time = dict_wind_alarms[self.name_alarm][self.ip_addr].get('date_time')
        # Получаем время начала аварии в секундах из словаря dict_alarm
        start_time = dict_wind_alarms[self.name_alarm][self.ip_addr].get('start_time')
        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
        duration_alarm = self._convert_time(time.time() - start_time)
        #
        font_size_image = self._get_font_size_frame_alarm()
        if self.name_alarm == 'low_level_oil':
            # Подсвечиваем строку бордовым, цвет текста белый подставляем 
            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{} {}</span>  <strong>  {}</strong></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        else:
            # Подсвечиваем строку бордовым, цвет текста белый подставляем 
            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
            text_alarm  = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
            ">{} {} {}</span> <strong>  {}</strong></p>'''.format(self.path_icon_critical, font_size_image, font_size_image, start_date_time, self.host_name, self.description, duration_alarm)
            return text_alarm

        
