#
from typing import Tuple, Optional
import logging
import time
from pathlib import Path
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_wind_alarms

class WindowMACCAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Переменная в которой будем хранить путь к файлу с иконкой IFO 
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_critical = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        # Переменная в которой будем хранить название аварии
        self.name_alarm = ''
        # Дефолтное значение низкого уровня сигнала SFP модуля MAC&C
        self.signal_level_fiber = -22
        # Дефолтное значение низкой температуры SFP модуля MAC&C
        self.low_temp_fiber = 1
        # Дефолтное значение высокой температуры SFP модуля MAC&C
        self.hight_temp_fiber = 50
        # Номер окна во вкладке "Общая информация"
        self.num_window = 4
        # Название устройства
        self.host_name = ''
        # IP-адрес устройства
        self.ip_addr = ''
        # Строка сообщения
        self.row = ''

    # Метод устанавливает пороговые значения аврий полученные из БД      
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение порогового значения "Низкий уровень сигнала"
            signal_level = sql.get_db('num', alarms='window_signal_level', table='Settings')[0]
            if isinstance(signal_level, int):
                self.signal_level_fiber = signal_level
            # Делаем запрос к БД, на получение порога значения "Низкая температура SFP модуля"
            low_temp_fiber = sql.get_db('num', alarms='window_low_temp_fiber', table='Settings')[0]
            if isinstance(low_temp_fiber, int):
                self.low_temp_fiber = low_temp_fiber
            # Делаем запрос к БД, на получение порога значения "Высокая температура SFP модуля"
            hight_temp_fiber = sql.get_db('num', alarms='window_hight_temp_fiber', table='Settings')[0]
            if isinstance(hight_temp_fiber, int):
                self.hight_temp_fiber = hight_temp_fiber
        return None
    
    # Метод обрабатывает значения параметров оборудования 
    def alarm_handler(self, line: str) -> Optional[str]:
        # Вызываем метод, который устанавливает пороговые значения появления аварии
        self._set_threshold_value_alarms()
        # Ловим исключение на случай удаления ip адреса из списка БД при открытом Окне мониторинга
        try:
            # Получаем IP адрес вызвав метод _parse_ip
            ip = self._parse_ip(line)
            if isinstance(ip, str):
                self.ip_addr = ip
                # Получаем имя которое соответствует ip адресу
                host_name = self._get_name(ip)
                if isinstance(host_name, str):
                    self.host_name = host_name
                else:
                    self.host_name = ip
                # Вызываем метод, который получает номер окна в которое будет выводится сообщение
                num_window = self._get_num_window(ip)
                if isinstance(num_window, int):
                    self.num_window = num_window
                else:
                    self.num_window = 4
            else:
                self.logger = logging.getLogger('WindowERRORAlarmHandler')
                self.logger.setLevel(logging.DEBUG)
                self.logger.debug(f'Не получил ip-адрес: {line}')
                return None
            # Вызываем метод, который возвращает значение размера шрифта текста установленного во вкладке "Общая информация"
            font_size_image = self._get_font_size_frame(self.num_window)
            if isinstance(font_size_image, int):
                pass
            else:
                font_size_image = 12 
            # Получаем параметры ИБЭП
            macc_parametrs = self._parse_message(line)
            # Формируем строку подставив название  и параметры 
            self.row = f'{self.host_name} {macc_parametrs[1]}' 
        # Если попали в исключение то возвращаем None
        except (TypeError, IndexError):
            return None
        
        # Устанавливаем стили нашей строке с данными
        text = '''<img src="{}" width="{}" height="{}">  <span>{}</span>'''.format(self.path_icon_inf, font_size_image, font_size_image, self.row)
       
        if 'TxFiber2' in line and 'TxFiber3' in line:
            # Вызываем метод parse_tx_fiber2 получаем значение уровня передающего сигнала SFP_2 модуля
            tx_fiber2 = self._parse_tx_fiber2(line)
            # Вызываем метод parse_rx_fiber2 получаем значение приемного уровня сигнала SFP_2 модуля
            rx_fiber2 = self._parse_rx_fiber2(line)
            # Вызываем метод parse_temp_fiber2 получаем значение температуры SFP_2 модуля
            temp_fiber2 = self._parse_temp_fiber2(line)
            # Вызываем метод parse_tx_fiber3 получаем значение уровня передающего сигнала SFP_3 модуля
            tx_fiber3 = self._parse_tx_fiber3(line)
            # Вызываем метод parse_rx_fiber3 получаем значение приемного уровня сигнала SFP_3 модуля
            rx_fiber3 = self._parse_rx_fiber3(line)
            # Вызываем метод parse_temp_fiber3 получаем значение температуры SFP_3 модуля
            temp_fiber3 = self._parse_temp_fiber3(line)
            # Если типы всех переменных строки
            if isinstance(rx_fiber2, str) and isinstance(rx_fiber3, str) and isinstance(tx_fiber3, str)\
                and isinstance(tx_fiber2, str) and isinstance(temp_fiber2, str) and isinstance(temp_fiber3, str):
                
                # НИЗКИЙ УРОВЕНЬ СИГНАЛА
                # Если значение уровня приемного и передающего сигналов меньше порогового значения
                if int(rx_fiber2) <= self.signal_level_fiber or int(tx_fiber2) <= self.signal_level_fiber or \
                    int(rx_fiber3) <= self.signal_level_fiber or int(tx_fiber3) <= self.signal_level_fiber:
                    # Присваиваем название аварии переменной 
                    self.name_alarm = 'low_signal_level'
                    if int(rx_fiber2) <= self.signal_level_fiber:
                        # Меняем стиль значения rx_fiber2 на жирный шрифт 
                        self.row = self.row.replace(f'RxFiber2: {rx_fiber2} dBm', f'<b style = "font-weight: 900;">RxFiber2: {rx_fiber2} dBm</b>')
                    if int(rx_fiber3) <= self.signal_level_fiber:
                        # Меняем стиль значения rx_fiber3 на жирный шрифт 
                        self.row = self.row.replace(f'RxFiber3: {rx_fiber3} dBm', f'<b style = "font-weight: 900;">RxFiber3: {rx_fiber3} dBm</b>')
                    # Подсвечиваем строку темно красным цветом, цвет текста белый  
                    text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color: #B22222; 
                    color: rgb(255, 255, 255);">{}</span>'''.format(self.path_icon_critical, font_size_image, font_size_image, self.row)
                    return text_alarm
                    
                # ОТСУТСТВИЕ АВАРИИ НИЗКОГО СИГНАЛА
                elif dict_wind_alarms['low_signal_level'].get(self.ip_addr):
                    # Вызываем метод который удаляет ip адрес из словарей аврий
                    self._remove_ip_from_dict_alarms(self.ip_addr, 'low_signal_level')

                # Если значение температуры выше порогового значения 
                if (int(temp_fiber2) >= self.hight_temp_fiber or int(temp_fiber3) >= self.hight_temp_fiber):
                    self.name_alarm = 'hight_temp_macc'
                    if int(temp_fiber2) >= self.hight_temp_fiber:
                        # Меняем стиль значения temp_fiber3 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber2: {temp_fiber2} *C', f'<b style = "font-weight: 900;">TempFiber2: {temp_fiber2} *C</b>')
                    if int(temp_fiber3) >= self.hight_temp_fiber:
                        # Меняем стиль значения temp_fiber3 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber3: {temp_fiber3} *C', f'<b style = "font-weight: 900;">TempFiber3: {temp_fiber3} *C</b>')
                    # Подсвечиваем строку желтым цветом и цвет текста красный 
                    text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #ffff00; 
                    color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                    return text_alarm
                # ОТСУТСТВИЕ АВАРИИ ПО ВЫСОКОЙ ТЕМПЕРАТУРЕ
                elif dict_wind_alarms['hight_temp_macc'].get(self.ip_addr):
                    # Вызываем метод который удаляет ip адрес из словарей аврий
                    self._remove_ip_from_dict_alarms(self.ip_addr, 'hight_temp_macc')

                # Если значение температуры ниже порогового значения 
                elif (int(temp_fiber2) <= self.low_temp_fiber or int(temp_fiber3) <= self.low_temp_fiber):
                    # Присваиваем название аварии переменной
                    self.name_alarm = 'low_temp_macc'
                    if int(temp_fiber2) < self.low_temp_fiber:
                    # Меняем стиль значения temp_fiber2 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber2: {temp_fiber2} *C', f'<b style = "font-weight: 900;">TempFiber2: {temp_fiber2} *C</b>')
                    if int(temp_fiber3) < self.low_temp_fiber:
                        # Меняем стиль значенияtemp_fiber2 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber3: {temp_fiber3} *C', f'<b style = "font-weight: 900;">TempFiber3: {temp_fiber3} *C</b>')
                    # Подсвечиваем строку желтым цветом и цвет текста красный
                    text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #ffff00; 
                    color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                    return text_alarm
                # Иначе если нет аварии 
                else:
                    self.name_alarm = "None"
                    # Вызываем метод который удаляет ip адрес из словаря аврий dict_alarms
                    self._remove_ip_from_dict_alarms(self.ip_addr, 'low_temp_macc')
                    return text
        if 'TxFiber1' in line and 'TxFiber3' in line:
            # Вызываем метод parse_tx_fiber1 получаем значение уровня передающего сигнала SFP_1 модуля
            tx_fiber1 = self._parse_tx_fiber1(line)
            # Вызываем метод parse_rx_fiber1 получаем значение приемного уровня сигнала SFP_1 модуля
            rx_fiber1 = self._parse_rx_fiber1(line)
            # Вызываем метод parse_temp_fiber1 получаем значение температуры SFP_1 модуля
            temp_fiber1 = self._parse_temp_fiber1(line)
            # Вызываем метод parse_tx_fiber3 получаем значение уровня передающего сигнала SFP_3 модуля
            tx_fiber3 = self._parse_tx_fiber3(line)
            # Вызываем метод parse_rx_fiber3 получаем значение приемного уровня сигнала SFP_3 модуля
            rx_fiber3 = self._parse_rx_fiber3(line)
            # Вызываем метод parse_temp_fiber3 получаем значение температуры SFP_3 модуля
            temp_fiber3 = self._parse_temp_fiber3(line)
            # Если типы всех переменных строки
            if isinstance(rx_fiber1, str) and isinstance(rx_fiber3, str) and isinstance(tx_fiber3, str)\
                and isinstance(tx_fiber1, str) and isinstance(temp_fiber1, str) and isinstance(temp_fiber3, str):
                # НИЗКИЙ УРОВЕНЬ СИГНАЛА
                # Если значение уровня приемного и передающего сигналов меньше порогового значения
                if int(rx_fiber1) <= self.signal_level_fiber or int(tx_fiber1) <= self.signal_level_fiber or \
                    int(rx_fiber3) <= self.signal_level_fiber or int(tx_fiber3) <= self.signal_level_fiber:
                    # Присваиваем название аварии переменной 
                    self.name_alarm = 'low_signal_level'
                    if int(rx_fiber1) <= self.signal_level_fiber:
                        # Меняем стиль значения rx_fiber2 на жирный шрифт 
                        self.row = self.row.replace(f'RxFiber1: {rx_fiber1} dBm', f'<b style = "font-weight: 900;">RxFiber1: {rx_fiber1} dBm</b>')
                    if int(rx_fiber3) <= self.signal_level_fiber:
                        # Меняем стиль значения rx_fiber3 на жирный шрифт 
                        self.row = self.row.replace(f'RxFiber3: {rx_fiber3} dBm', f'<b style = "font-weight: 900;">RxFiber3: {rx_fiber3} dBm</b>')
                    # Подсвечиваем строку темно красным цветом, цвет текста белый  
                    text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color: #B22222; 
                    color: rgb(255, 255, 255);">{}</span>'''.format(self.path_icon_critical, font_size_image, font_size_image, self.row)
                    return text_alarm
                    
                # ОТСУТСТВИЕ АВАРИИ НИЗКОГО СИГНАЛА
                elif dict_wind_alarms['low_signal_level'].get(self.ip_addr):
                    # Вызываем метод который удаляет ip адрес из словарей аврий
                    self._remove_ip_from_dict_alarms(self.ip_addr, 'low_signal_level')

                # Если значение температуры выше порогового значения 
                if (int(temp_fiber1) >= self.hight_temp_fiber or int(temp_fiber3) >= self.hight_temp_fiber):
                    self.name_alarm = 'hight_temp_macc'
                    if int(temp_fiber1) >= self.hight_temp_fiber:
                        # Меняем стиль значения temp_fiber3 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber1: {temp_fiber1} *C', f'<b style = "font-weight: 900;">TempFiber1: {temp_fiber1} *C</b>')
                    if int(temp_fiber3) >= self.hight_temp_fiber:
                        # Меняем стиль значения temp_fiber3 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber3: {temp_fiber3} *C', f'<b style = "font-weight: 900;">TempFiber3: {temp_fiber3} *C</b>')
                    # Подсвечиваем строку желтым цветом и цвет текста красный 
                    text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #ffff00; 
                    color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                    return text_alarm

                # ОТСУТСТВИЕ АВАРИИ ПО ВЫСОКОЙ ТЕМПЕРАТУРЕ
                elif dict_wind_alarms['hight_temp_macc'].get(self.ip_addr):
                    # Вызываем метод который удаляет ip адрес из словарей аврий
                    self._remove_ip_from_dict_alarms(self.ip_addr, 'hight_temp_macc')

                # Если значение температуры ниже порогового значения 
                elif (int(temp_fiber1) <= self.low_temp_fiber or int(temp_fiber3) <= self.low_temp_fiber):
                    # Присваиваем название аварии переменной
                    self.name_alarm = 'low_temp_macc'
                    if int(temp_fiber1) < self.low_temp_fiber:
                    # Меняем стиль значения temp_fiber2 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber1: {temp_fiber1} *C', f'<b style = "font-weight: 900;">TempFiber1: {temp_fiber1} *C</b>')
                    if int(temp_fiber3) < self.low_temp_fiber:
                        # Меняем стиль значенияtemp_fiber2 на жирный шрифт 
                        self.row = self.row.replace(f'TempFiber3: {temp_fiber3} *C', f'<b style = "font-weight: 900;">TempFiber3: {temp_fiber3} *C</b>')
                    # Подсвечиваем строку желтым цветом и цвет текста красный
                    text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #ffff00; 
                    color: rgb(254, 0, 0);">{}</span></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                    return text_alarm
                # Иначе если нет аварии 
                else:
                    self.name_alarm = "None"
                    # Вызываем метод который удаляет ip адрес из словаря аврий dict_alarms
                    self._remove_ip_from_dict_alarms(self.ip_addr, 'low_temp_macc')
                    return text
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
        # Вызываем метод, который возвращает значение размера шрифта во вкладке "Текущие аварии"
        font_size_image = self._get_font_size_frame_alarm()
        if isinstance(font_size_image, int):
            pass
        else:
           font_size_image = 12 
        # Если название аварии low_signal_level 
        if self.name_alarm == 'low_signal_level':
            # Подсвечиваем строку темно красным цветом, цвет текста белый подставляем 
            # дату и время возникновения аварии, строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #B22222; 
            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_critical, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        # Если название аварии hight_temp_macc или low_temp_macc
        elif (self.name_alarm is 'hight_temp_macc' or self.name_alarm == 'low_temp_macc'):
            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
            # строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #ffff00; 
            color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        return None
