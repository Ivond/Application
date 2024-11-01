#
from typing import Optional, Tuple
import time
import logging
from pathlib import Path
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_wind_alarms

class WindowPortSwitchHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Создаем переменные в которых записываем путь к файлам
        self.path_icon_inf = str(Path(Path.cwd(), "Resources", "Icons", "icn25.ico"))
        self.path_icon_warn = str(Path(Path.cwd(), "Resources", "Icons", "icn24.ico"))
        self.path_icon_critical = str(Path(Path.cwd(), "Resources", "Icons", "icn22.ico"))
        # Название аврии
        self.name_alarm = ''
        # Название канала
        self.channel_name = ''
        # Описание аварии
        self.description = ''
        # IP-адрес
        self.ip = ''
        
    # Метод добавляет дату и время возникновения аварии
    def _add_date_time_alarm(self, ip: str, port: str, key: str) -> None:
        # Получаем текущую дату и время   
        date_time = self._date_to_str()
        # Если метод get вернет None для ключа ip
        if dict_wind_alarms[key].get(ip) is None:
            # Добавляем дату и время возниконовения аварии и начла аврии в словарь dict_alarm
            dict_wind_alarms[key][ip] = {port:{'date_time': date_time, 'start_time': time.time()}}
        elif dict_wind_alarms[key][ip].get(port) is None:
            # Добавляем дату и время возниконовения аварии и начла аврии в словарь dict_alarm
            dict_wind_alarms[key][ip][port] = {'date_time': date_time, 'start_time': time.time()}
        return None

    #   
    def alarm_handler(self, line: str) -> Optional[str]:
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Вызываем метод который возвращает ip адреса коммутатора
            ip = self._parse_ip(line)
            if isinstance(ip, str):
                self.ip = ip
                # Вызываем метод который возвращает номер порта коммутатора
                port = self._parse_port_number(line)
                if isinstance(port, str):
                    # Вызываем метод который возвращает название канала
                    channel_name = self._parse_channel_name(ip, port=port)
                    if isinstance(channel_name, str):
                        self.channel_name = channel_name
                    else:
                        self.channel_name = ip
                else:
                    self.logger = logging.getLogger('WindowERRORAlarmHandler')
                    self.logger.setLevel(logging.DEBUG)
                    self.logger.debug(f'Не получил порт: {line}')
                    return None

            else:
                self.logger = logging.getLogger('WindowERRORAlarmHandler')
                self.logger.setLevel(logging.DEBUG)
                self.logger.debug(f'Не получил ip-адрес: {line}')
                return None
            # Вызываем метод, который возвращает параметры коммутатора
            switch_parametrs = self._parse_message(line)
            # Формируем строку подставив название канала и параметры коммутатора
            row = f'{self.channel_name}: {switch_parametrs[1]}'
        # Попали в исключение, значит ip адрес или порт коммутатора удален из БД, останавливаем метод
        except (TypeError, IndexError) as err:
            print(err)
            return None
        channel_status = self._parse_status_channel(line)
        oper_status = self._parse_status_port(line)
        font_size_image = self._get_font_size_frame_channel()
        if isinstance(font_size_image, int):
            pass
        else:
           font_size_image = 12 
        #
        if isinstance(channel_status, str) and isinstance(oper_status, str):
            # Устанавливаем стили нашей строке с данными
            text = '''<p><img src="{}" width="{}" height="{}">  <span>{}</span></p>'''.format(self.path_icon_inf, font_size_image, font_size_image, row)
            #
            if channel_status == 'Down' or oper_status == 'Down':
                self.name_alarm = 'loss_channel'
                if channel_status == 'Down' and isinstance(switch_parametrs, str):
                    # Меняем стиль значения channel_status на жирный шрифт 
                    switch_parametrs = switch_parametrs.replace(f'ChannelStatus: {channel_status}', f'<b style = "font-weight: 900;">ChannelStatus: {channel_status}</b>')
                if oper_status == 'Down' and isinstance(switch_parametrs, str):
                    # Меняем стиль значения oper_status на жирный шрифт 
                    switch_parametrs = switch_parametrs.replace(f'OperStatus: {oper_status}', f'<b style = "font-weight: 900;">OperStatus: {oper_status}</b>')
                '''
                Хотим что бы при выводе строки с данными дата и время возникновения аврии не менялась 
                на всем протяжении длительности аварии. Для этого добавляем в словарь dict_alarm дату и время''' 
                if isinstance(port, str):    
                    # Добавляем дату возникновения аварии
                    self._add_date_time_alarm(self.ip, port, 'channel')
                    # Получаем дату и время начала аварии в определенном формате для подставления ее в сообщение
                    start_date_time = dict_wind_alarms['channel'][self.ip][port].get('date_time')
                    # Получаем время начала аварии в секундах из словаря dict_alarm
                    start_time = dict_wind_alarms['channel'][self.ip][port].get('start_time')
                    # Вычисляем продолжительность аварии вычислив разницу между текущим временем и временем возникновения аварии
                    duration_alarm = self._convert_time(time.time() - start_time)
                    # Описание аварии
                    self.description = 'Пропадание канала'
                    # Подсвечиваем строку бордовым цветом и цвет текста белый
                    text_alarm = '''<p><img src="{}" width="{}" height="{}">  <span style="background-color:#8B0000; color: rgb(255, 255, 255);
                    ">{} {} Пропадание канала {}</span><strong>  {}</strong></p>'''.format(self.path_icon_critical, font_size_image, font_size_image, start_date_time, self.channel_name, switch_parametrs, duration_alarm)
                    return text_alarm
            # Проверяем если количество трафика равно Мбит/c или Кбит/c и статсу порта Up и сообщение с таким ip есть в словаре
            elif channel_status == 'Up' and oper_status == 'Up':
                self.name_alarm = "None"
                # Проверяем если ip адреса есть в словаре аврий
                if dict_wind_alarms['channel'].get(self.ip) is not None:
                    # Проверяем если порт есть в словаре аварий
                    if dict_wind_alarms['channel'][self.ip].get(port):
                        # Удаляем сообщение об аварии из dict_alarms
                        del dict_wind_alarms['channel'][self.ip][port]
                return text
        return None

if __name__ == "__main__":
    
    port_handler = WindowPortSwitchHandler()




