#
from typing import Optional, Union
import time
import logging
from pathlib import Path
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_wind_alarms

class WindowUPSAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Создаем переменные в которых записываем путь к файлам
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_critical = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        # Дефолтное значение порога "Высокой температуры"
        self.hight_temp = 35
        # Дефолтное значение порога "Низкой температуры"
        self.low_temp = 0
        # Дефолтное значение порога "Высокого напряжения"
        self.hight_voltage = 245
        # Дефолтное значение порога "Низкого напряжения"
        self.low_voltage = 48.0
        # Номер окна
        self.num_window = 4
        # Название аварии
        self.name_alarm = ''
        # Название устройства
        self.host_name = ''
        # Строка для формирования сообщения
        self.row = ''
        # IP адрес устройства
        self.ip_addr = ''

    # Метод устанавливает пороговые значения      
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение порогового значения высокой температуры
            hight_temp = sql.get_db('num', alarms='window_hight_temp', table='Settings')[0]
            if isinstance(hight_temp, int):
                self.hight_temp = hight_temp
            # Делаем запрос к БД, на получение порога значения низкой температуры
            low_temp = sql.get_db('num', alarms='window_low_temp', table='Settings')[0]
            if isinstance(low_temp, int):
                self.low_temp = low_temp
            # Делаем запрос к БД, на получение порога значения низкого напряжения
            low_voltage = sql.get_db('num', alarms='window_low_volt', table='Settings')[0]
            if isinstance(low_voltage, float):
                self.low_voltage = low_voltage
            # Делаем запрос к БД, на получение порога значения высокого напряжения
            hight_voltage = sql.get_db('num', alarms='window_hight_voltage', table='Settings')[0]
            if isinstance(hight_voltage, int):
                self.hight_voltage = hight_voltage

    # Метод обрабатывает строку со значениями параметров оборудования 
    def alarm_handler(self, line: str) -> Union[str, None]:
        # Вызываем метод, который устанавливает пороговые значения появления аварии
        self._set_threshold_value_alarms()
        # Ловим исключение на случай удаления ip адреса из списка БД при открытом Окне мониторинга
        try:
            # Получаем IP адрес вызвав метод _parse_ip
            ip = self._parse_ip(line)
            if isinstance(ip, str):
                self.ip_addr = ip
                # Получаем имя которое соответствует ip адресу
                host_name = self._get_name(self.ip_addr)
                if isinstance(host_name, str):
                    self.host_name = host_name
                else:
                    self.host_name = ip
            else:
                self.logger = logging.getLogger('WindowERRORAlarmHandler')
                self.logger.setLevel(logging.DEBUG)
                self.logger.debug(f'Не получил ip-адрес: {line}')
                return None
            # Получаем параметры ИБЭП
            ups_parametrs = self._parse_message(line)
            # Формируем строку подставив название  и параметры 
            self.row = f'{self.host_name} {ups_parametrs[1]}'
            # Получаем номер окна
            num_window = self._get_num_window(self.ip_addr)
            if isinstance(num_window, int):
                self.num_window = num_window
            else:
                self.num_window = 4
            # Вызываем метод, передаем числовое значение номера окна, возвращает числовое значение размера шрифта
            font_size_image = self._get_font_size_frame(num_window)
            if isinstance(font_size_image, int):
                pass
            else:
                font_size_image = 12
        # Если попали в исключение то пропускаем все что ниже по коду
        except (TypeError, IndexError):
            return None
        # Получаем значение температуры
        temperature = self._parse_temperature(line)
        # Получаем знаение входного напряжения
        voltege_in = self._parse_voltage_in(line)
        # Получаем значение выходного напряжения
        voltege_out = self._parse_voltage_out(line)
        
        if isinstance(temperature, int) and isinstance(voltege_in, int) and isinstance(voltege_out, float):
            # Устанавливаем стили нашей строке с данными
            text = '''<img src="{}" width="{}" height="{}">  <span>{}</span>'''.format(self.path_icon_inf, font_size_image, font_size_image, self.row)
            # Если входное напряжение меньше 10 (АВАРИЯ ОТКЛЮЧЕНИЕ ЭЛЕКТРОЭНЕРГИИ)
            if voltege_in < 100:
                self.name_alarm = 'power_alarm'
                # Меняем стиль значения voltege_in на жирный шрифт 
                self.row = self.row.replace(f'IN: {voltege_in} V', f'<b style = "font-weight: 900;">IN: {voltege_in} V</b>')
                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем строку
                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии  
                text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color: #ff4500; 
                color: rgb(255, 255, 255); ">{}</span>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)  
                # Если выходное напряжение меньше или равно порогу низкого напряжения (АВАРИЯ ПО НИЗКОМУ НАПРЯЖЕНИЮ)
                if voltege_out <= self.low_voltage:
                    self.name_alarm = 'low_voltage'
                    # Меняем стиль значения voltege_out на жирный шрифт
                    self.row = self.row.replace(f'OUT: {voltege_out} V', f'<b style = "font-weight: 900;">OUT: {voltege_out} V</b>')
                    # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем строку
                    # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                    text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color: #B22222; 
                    color: rgb(255, 255, 255);">{}</span>'''.format(self.path_icon_critical, font_size_image, font_size_image, self.row)
                return text_alarm
            # ОТСУТСТВИЕ АВАРИИ ПО ЭЛЕКТРОЭНЕРГИИ И НИЗКОМУ НАПРЯЖЕНИЮ
            # Если значение больше 180В И есть запись в словаре с ключом ip
            elif dict_wind_alarms['power_alarm'].get(self.ip_addr) != None: # Метод get вернет None если нет ip
                # Вызываем метод который удаляет запись об авариях из словарей.
                self._remove_ip_from_dict_alarms(self.ip_addr, 'power_alarm', 'low_voltage')

            # Если температура выше порогового значения 
            if temperature >= self.hight_temp or temperature <= self.low_temp:
                self.name_alarm = 'hight_temp'
                # Меняем стиль значения temperature на жирный шрифт
                self.row = self.row.replace(f'*C: {temperature}', f'<b style = "font-weight: 900;">*C: {temperature}</b>')
                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color: #ffff00; 
                color: rgb(254, 0, 0);">{}</span>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                return text_alarm
            # Если нет аварии по температуре
            elif dict_wind_alarms['hight_temp'].get(self.ip_addr) != None: # Метод get верент None если нет ip  
                # Удаляем запись из словаря date_alarm
                del dict_wind_alarms['hight_temp'][self.ip_addr]

            # Проверяем если значение входного напряжения выше порогового
            if voltege_in >= self.hight_voltage:
                self.name_alarm = 'hight_voltage'
                # Меняем стиль значения voltege_in на жирный шрифт
                self.row = self.row.replace(f'IN: {voltege_in} V', f'<b style = "font-weight: 900;">IN: {voltege_in} V</b>')
                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                text_alarm = '''<img src="{}" width="{}" height="{}"> <span style="background-color: #ffa500; 
                color: rgb(255, 255, 255);">{}</span>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                return text_alarm
            # Иначе, если аварии нет 
            else:
                self.name_alarm = "None"
                # Вызываем метод который проверяет есть ли запись в словаре об аварии, если запись есть, то удаляем
                self._remove_ip_from_dict_alarms(self.ip_addr, 'hight_voltage')
                return text
        return None

    # Метод возвращает сообщение для вывода в окно "Текущие аварии"       
    def window_alarm_handler(self) -> Optional[str]:
        # Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
        # на всем протяжении длительности аварии. Для этого добавляем в словарь date_alarm дату и время     
        # Добавляем дату возникновения аварии
        self._add_date_time_alarm(self.ip_addr, self.name_alarm)
        # Получаем дату и время начала аварии в определенном формате для подставления ее в сообщение
        start_date_time = dict_wind_alarms[self.name_alarm][self.ip_addr].get('date_time')
        # Получаем время начала аварии в секундах из словаря dict_alarm
        start_time = dict_wind_alarms[self.name_alarm][self.ip_addr].get('start_time')
        # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
        duration_alarm = self._convert_time(time.time() - start_time)
        #
        font_size_image = self._get_font_size_frame_alarm()
        if isinstance(font_size_image, int):
            pass
        else:
            font_size_image = 12
        #
        if self.name_alarm == 'power_alarm':
            # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем 
            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #ff4500; 
            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        elif self.name_alarm == 'low_voltage':
            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем  дату и время возникновения аварии,
            #  строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #B22222; 
            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_critical, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        elif self.name_alarm == 'hight_temp':
            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
            #  строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #ffff00; 
            color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        elif self.name_alarm == 'hight_voltage':
            # Подсвечиваем строку оранжевым цветом и цвет текста белый, подставляем  дату и время возникновения аварии,
            #  строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}"> <span style="background-color: #ffa500; 
            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        return None
