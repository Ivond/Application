#
from typing import Tuple, Optional, Union
import random
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_alarms

class SLASwitchHandler(ValueHandler):
    def __init__(self) -> None:
        ValueHandler().__init__()

    # 
    def alarm_handler(self, line: str) -> Union[str, None]:
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Вызываем метод который возвращает ip адреса коммутатора
            ip = self._parse_ip(line)
            # Вызываем метод который возвращает номер sla коммутатора
            sla = self._parse_sla(line)
            if isinstance(ip, str) and isinstance(sla, int):
                # Вызываем метод который возвращает название канала
                channel_name = self._parse_channel_name(ip, sla)
        # Попали в исключение, значит ip адрес или sla коммутатора удален из БД, останавливаем метод
        except TypeError:
            return None
        # Вызываем метод, который возвращает Статус SLA (Up или Down)
        sla_status = self._parse_sla_status(line)
        # Вызываем метод, который возвращает значение icmp_echo
        icmp_echo = self._parse_icmp_echo(line)
        # Если значение переменной равно Down И тип переменной ip строка И IP нет в словаре аварий
        if sla_status == 'Down' and isinstance(ip, str) and ip not in dict_alarms['sla']:
            # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж params на дату и строку с параметрами
                date, sla_parametrs = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(5001, 6000)
                # Если значение icmp_echo True
                if icmp_echo:
                    # Формируем сообщение для отправки
                    message = f'{date} <b>Потеря icmp-пакетов по каналу "{channel_name}":</b> {sla_parametrs} ID:{id}'
                else:
                    # Формируем сообщение для отправки
                    message = f'{date} <b>Пропадание канала "{channel_name}":</b> {sla_parametrs} ID:{id}'
                # Добавляем данные об аварии в dict_messages
                dict_alarms['sla'][ip] = {sla:message}
                return message
        # Если значение переменной равно Down И тип переменной ip строка И номера sla нет в словаре аварий
        elif sla_status == 'Down' and isinstance(ip, str) and sla not in dict_alarms['sla'][ip]:
            # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
            params = self._parse_message(line)
            if isinstance(params, tuple):
                # Распаковываем кортеж params на дату и строку с параметрами
                date, sla_parametrs = params
                # Формируем случайным образом номер ID сообщения
                id = random.randint(5001, 6000)
                # Если значение icmp_echo True
                if icmp_echo:
                    # Формируем сообщение для отправки
                    message = f'{date} <b>Потеря icmp-пакетов по каналу "{channel_name}":</b> {sla_parametrs} ID:{id}'
                else:
                    # Формируем сообщение для отправки
                    message = f'{date} <b>Пропадание канала "{channel_name}":</b> {sla_parametrs} ID:{id}'
                # Добавляем данные об аварии в dict_messages
                dict_alarms['sla'][ip][sla] = message
                return message
        # Проверяем если ip sla статсу Up и сообщение с таким ip есть в словаре
        elif sla_status == 'Up' and ip in dict_alarms['sla']:
            #
            if dict_alarms['sla'][ip].get(sla):
                if icmp_echo:
                    # Удаляем сообщение об аварии из dict_messages
                    del dict_alarms['sla'][ip][sla]
                else:
                    # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
                    params = self._parse_message(line)
                    if isinstance(params, tuple):
                        # Распаковываем кортеж params на дату и строку с параметрами
                        date, sla_parametrs = params
                        message = f'{date} <b>Работа канала "{channel_name}" восстановлена:</b> {sla_parametrs}'
                        # Удаляем сообщение об аварии из dict_messages
                        del dict_alarms['sla'][ip][sla]
                        return message
        return None

if __name__ == "__main__":

    sla_handler = SLASwitchHandler()

