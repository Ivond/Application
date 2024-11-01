#
import logging
from typing import Union, Tuple
import time
from pathlib import Path
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_wind_alarms

class WindowThreePhaseUPSAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Создаем переменные в которых записываем путь к файлам
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_critical = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        # Переменная в которой будем хранить дефолтное значение порога "Высокого напряжения"
        self.hight_voltage = 250
        # Переменная в которой будем хранить дефолтное значение порога "Низкого напряжения"
        self.low_voltage = 48.0
        # Номер окна
        self.num_window = 4
        # Название аварии
        self.name_alarm = ''
        # Название хоста
        self.host_name = ''
        # Строка для формирования сообщения
        self.row = ''
        # IP адрес устройства
        self.ip_addr = ''

    # Метод устанавливает пороговые значения      
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
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
            # Получаем номер окна
            num_window = self._get_num_window(self.ip_addr)
            if isinstance(num_window, int):
                self.num_window = num_window
            else:
                self.num_window = 4
            # Вызываем метод, передаем числовое значение номера окна, возвращает числовое значение размера шрифта
            font_size_image = self._get_font_size_frame(self.num_window)
            if isinstance(font_size_image, int):
                pass
            else:
                font_size_image = 12
            # Получаем параметры ИБЭП
            ups_parametrs = self._parse_message(line)
            # Формируем строку подставив название  и параметры 
            self.row = f'{self.host_name} {ups_parametrs[1]}'
        # Если попали в исключение то пропускаем все что ниже по коду
        except (TypeError, IndexError):
            return None
        # Вызываем метод _parse_voltage_out получаем значение выходного напряжения
        voltage_out = self._parse_voltage_out(line)
        # Вызываем метод _parse_phase который возращает значение трех фаз
        three_phase = self._parse_phase(line)
        phase1, phase2, phase3 = three_phase
        
        if isinstance(phase1, float) and isinstance(phase2, float) and isinstance(phase3, float) and isinstance(voltage_out, float):
            #print(line)
            # Устанавливаем стили нашей строке с данными
            text = '''<img src="{}" width="{}" height="{}">  <span>{}</span>'''.format(self.path_icon_inf, font_size_image, font_size_image, self.row)
            # Если напряжение на всех трех фазах меньше 10 (АВАРИЯ ОТКЛЮЧЕНИЕ ЭЛЕКТРОЭНЕРГИИ)
            if phase1 < 100 and phase2 < 100 and phase3 < 100:
                self.name_alarm = 'power_alarm'
                # Меняем стиль значения voltege_in на жирный шрифт 
                self.row = self.row.replace('Phase_A: {} V Phase_B: {} V Phase_C: {} V'.format(phase1, phase2, phase3), '<b>Phase_A: {} V Phase_B: {} V Phase_C: {} V</b>'.format(phase1, phase2, phase3))
                # Подсвечиваем строку темно оранжевым цветом, цвет текста белый подставляем строку
                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии  
                text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color: #ff4500; 
                color: rgb(255, 255, 255); ">{}</span>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)  
                # Если выходное напряжение меньше или равно порогу низкого напряжения (АВАРИЯ ПО НИЗКОМУ НАПРЯЖЕНИЮ)
                if voltage_out <= self.low_voltage:
                    self.name_alarm = 'low_voltage'
                    # Меняем стиль значения voltege_out на жирный шрифт
                    self.row = self.row.replace('OUT: {} V'.format(voltage_out), '<b>OUT: {} V</b>'.format(voltage_out))
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

            # Если напряжения на одной из фаз отсутствует (АВАРИЯ ПРОПАДАНИЕ ОДНОЙ ФАЗЫ) 
            if phase1 < 100 or phase2 < 100 or phase3 < 100:
                self.name_alarm = 'phase_alarm'
                if phase1 < 10:
                    # Выделяем значение переменной phase1 жирным ширифтом 
                    self.row = self.row.replace(f'Phase_B: {phase2} V', f'<b>Phase_B: {phase2} V</b>') 
                if phase2 < 10:
                    # Выделяем значение переменной phase1 жирным ширифтом
                    self.row = self.row.replace(f'Phase_B: {phase2} V', f'<b>Phase_B: {phase2} V</b>')
                if phase3 < 10:
                    # Выделяем значение переменной phase1 жирным ширифтом
                    self.row = self.row.replace(f'Phase_C: {phase3} V', f'<b>Phase_B: {phase3} V</b>')
                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                # подставляем строку с параметрами аварии без даты возникновения и длительности аварии
                text_alarm = '''<img src="{}" width="{}" height="{}">  <span style="background-color: #FFC300; 
                color: rgb(254, 0, 0);">{}</span>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                return text_alarm
            # Если нет аварии по фазе
            elif dict_wind_alarms['phase_alarm'].get(self.ip_addr) != None: # Метод get верент None если нет ip  
                # Удаляем запись из словаря date_alarm
                del dict_wind_alarms['phase_alarm'][self.ip_addr]

            # Проверяем если значение на одной из фаз превышает пороговое
            if phase1 >= self.hight_voltage or phase2 >= self.hight_voltage or phase3 >= self.hight_voltage :
                self.name_alarm = 'hight_voltage'
                if phase1 >= self.hight_voltage:
                    # Выделяем значение переменной phase1 жирным ширифтом 
                    self.row = self.row.replace(f'Phase_B: {phase2} V', f'<b>Phase_B: {phase2} V</b>') 
                if phase2 >= self.hight_voltage:
                    # Выделяем значение переменной phase2 жирным ширифтом
                    self.row = self.row.replace(f'Phase_B: {phase2} V', f'<b>Phase_B: {phase2} V</b>')
                if phase3 >= self.hight_voltage:
                    # Выделяем значение переменной phase3 жирным ширифтом
                    self.row = self.row.replace(f'Phase_C: {phase3} V', f'<b>Phase_B: {phase3} V</b>')
                # Подсвечиваем строку оранжевым цветом и цвет текста белый подставляем строку
                text_alarm = '''<img src="{}" width="{}" height="{}"> <span style="background-color: #ffa500; 
                color: rgb(255, 255, 255);">{}</span>'''.format(self.path_icon_warn, font_size_image, font_size_image, self.row)
                return text_alarm
            # Иначе, если аварии нет 
            else:
                self.name_alarm = "None"
                # Вызываем метод который проверяет есть ли запись в словаре об аварии, если запись есть, то удаляем
                self._remove_ip_from_dict_alarms(self.ip_addr, 'hight_voltage')
                #print(text)
                return text
        return None

    # Метод возвращает сообщение для вывода в окно "Текущие аварии"       
    def window_alarm_handler(self) -> Union[str, None]:
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
        elif self.name_alarm == 'phase_alarm':
            # Подсвечиваем строку желтым цветом и цвет текста красный подставляем  дату и время возникновения аварии,
            #  строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color: #FFC300; 
            color: rgb(254, 0, 0);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        elif self.name_alarm == 'hight_phase_voltage':
            # Подсвечиваем строку оранжевым цветом и цвет текста белый, подставляем  дату и время возникновения аварии,
            #  строку с параметрами авриии и длительность аварии
            text_alarm = '''<p><img src="{}" width="{}" height="{}"> <span style="background-color: #ffa500; 
            color: rgb(255, 255, 255);">{} {}</span> <strong>{} </strong></p>'''.format(self.path_icon_warn, font_size_image, font_size_image, start_date_time, self.row, duration_alarm)
            return text_alarm
        return None
               
    
if __name__ == "__main__":
   
    handler = WindowThreePhaseUPSAlarmHandler()
    print(handler.dict_alarms)




