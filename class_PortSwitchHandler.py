#
from typing import Tuple, Union, Optional
import random
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_alarms

class PortSwitchHandler(ValueHandler):
    def __init__(self) -> None:
        ValueHandler.__init__(self)

    #   
    def alarm_handler(self, line: str) -> Optional[str]:
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Вызываем метод передаем строку, метод возвращает строковое значение ip адреса коммутатора
            ip = self._parse_ip(line)
            # Вызываем метод который возвращает номер порта коммутатора
            port = self._parse_port_number(line)
            # Если тип переменной ip строка И тип переменной port строка
            if isinstance(ip, str) and isinstance(port, str):
                # Вызываем метод который возвращает название канала
                channel_name = self._parse_channel_name(ip, port)
            else:
                return None
        # Попали в исключение, значит ip адрес или порт коммутатора удален из БД, останавливаем метод
        except TypeError:
            return None
        channel_status = self._parse_status_channel(line)
        oper_status = self._parse_status_port(line)
        #
        if channel_status and oper_status:
            # Если значение равно Down И ip-адреса нет в словаре аварий
            if (channel_status == 'Down' or oper_status == 'Down') and ip not in dict_alarms['channel']:
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, switch_parametrs = params
                    # Формируем случайным образом номер ID сообщения
                    id = random.randint(4001, 5000)
                    if isinstance(channel_name, str):
                        # Формируем сообщение для отправки
                        message = f'{date} <b>Пропадание канала "{channel_name}":</b> {switch_parametrs} ID:{id}'
                        # Добавляем данные об аварии в dict_alarms
                        dict_alarms['channel'][ip] = {port:message}
                        return message
            # Если значение равно Down И номера порта нет в словаре аварий
            elif (channel_status == 'Down' or oper_status == 'Down') and port not in dict_alarms['channel'][ip]:
                # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                params = self._parse_message(line)
                if isinstance(params, tuple):
                    # Распаковываем кортеж params на дату и строку с параметрами
                    date, switch_parametrs = params
                    # Формируем случайным образом номер ID сообщения
                    id = random.randint(4001, 5000)
                    # Формируем сообщение для отправки
                    message = f'{date} <b>Пропадание канала "{channel_name}":</b> {switch_parametrs} ID:{id}'
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['channel'][ip][port] = message
                    return message
            # Если значение равно Up И ip-адрес есть в словаре аварий
            elif (channel_status == 'Up' and oper_status == 'Up') and ip in dict_alarms['channel']:
                #
                if dict_alarms['channel'][ip].get(port):
                    # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                    params = self._parse_message(line)
                    if isinstance(params, tuple):
                        # Распаковываем кортеж params на дату и строку с параметрами
                        date, switch_parametrs = params
                        message = f'{date} <b>Работа канала "{channel_name}" восстановлена:</b> {switch_parametrs}'
                        # Удаляем сообщение об аварии из dict_alarms
                        del dict_alarms['channel'][ip][port]
                        return message
        
        return None

if __name__ == "__main__":
    
    port_handler = PortSwitchHandler()
