#
import socket
import struct
import re 
import time
import logging
from pathlib import Path

class ClientModbus():
    def __init__(self) -> None:
        # Настройка логирования
        self.path_logs = Path(Path.cwd(), "logs", "logs_snmp_ask.txt")
        self.logger = logging.getLogger('snm_ask')
        self.logger.setLevel(logging.INFO)
        fh_logs = logging.FileHandler(self.path_logs, 'w')
        formatter_logs = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_logs.setFormatter(formatter_logs)
        self.logger.addHandler(fh_logs)
        
        self.tcp_port = 502
        self.buffer_size = 4096
        # Индентификатор устройства
        self.unit_id = 1
        # Код функции Modbus
        self.function_code = 4

        #self.function_code_bit = 1
        
        self.fuel = None # уровень топлива, коэф = 1
        self.af_tmp = None # температура охлождающей жидкости, коэф = 0,01
        self.bat_V = None # напряжение батареи, коэф = 0,01
        self.ao_tmp = None # температура в АО, коэф = 1
        self.do_tmp = None # температура в ДО, коэф = 0,01
        self.ao_ops = None  # ОПС АО, коэф = 1
        self.do_ops = None  # ОПС ДО, коэф = 1
        self.stop_motor = 0 # Аварийная остановка двигателя 0 или 1 (BIT)
        self.hight_temp_water = 0 # Высокая температура охлаждающей жидкости
        self.low_temp_water = 0 # Низкая температура охлаждающей жидкости
        self.low_oil_pressure = 0 # Низкое давление масла
        self.low_level_water = 0 # Низкий уровень охлаждающей жидкости
        self.low_level_oil = 0 # Низкий уровень топлива
        self.switch_state_motor = 0 # Переключатель управления двигателем не в автоматическом состоянии 
        self.low_batt_charge = 0 # Низкий уровень заряда батареи.

    # Метод конвертирует 
    #def convert_hex(self, coil_id):
        #item = hex(coil_id)
        #if len(item) == 6:
            #hi_bite = int(item[:4], 16)
            #low_bite = int(('0x' + item[-2:]), 16)
            #return hi_bite, low_bite

    '''
    Modbus для считывания данных используем код функции 04 (чтение дискретные входы).
    Структура пакета Modbus TCP:
    MBAP Header состоит из следующих байт:
    MBAP Header: (Индентификатор транзакции(0x01,0x02...0xN)[2 байта]), (Индентификатор протокола(0x00)[2 байта]), 
                 (длина, количество байт идущие далее(0x06)[2 байта]), (Адрес устройства(0x1)[1 байт])
    PDU состоит из следующих байтов:
    PDU: (код функции(0x04)[1 байт]), (Адрес первого регистра(24587)[2 байта]), (количество регистров(4)[2 байта])
    Запрос:
    MBAP Header + PDU

    Ответ:
    00010000000b010408003500070f930532

    (Индентификатор транзакции(0001)[2 байта]), (Индентификатор протокола(0000)[2 байта]), 
    (Длина сообщения ответа(000b)[11 байт], (Адрес устройства(01)[1 байт]), 
    (Код функции(04)[1 байт]),(Количество байт идущие далее(может быть разное)(0008)[8 байт], 
    (Значение 4-х регистров по 2 байта каждый, которые мы запросили) 

    '''
    
    # Метод отправляет запрос на оборудование по протоколу Modbus
    def modbus(self, ip, time_out=10) -> str:
        # Упаковываем данные в байты для отправки на устройство (Н-2байта, В-1байт)
        req1 = struct.pack('>HHHBBHH', 0x01, 0x00, 0x06, self.unit_id, self.function_code, 24587, 0x04)
        req2 = struct.pack('>HHHBBHH', 0x02, 0x00, 0x06, self.unit_id, self.function_code, 24714, 0x02)
        req3 = struct.pack('>HHHBBHH', 0x03, 0x00, 0x06, self.unit_id, self.function_code, 24723, 0x03)
        req4 = struct.pack('>HHHBBHH', 0x04, 0x00, 0x06, self.unit_id, self.function_code, 24598, 0x01)
        #req5 = struct.pack('>HHHBBHH', 0x05, 0x00, 0x06, self.unit_id, 4, 3, 0x01)
        try:
            # Создаем соккет для подключения к устройству
            self.client = socket.socket()
            # Устанавливаем время ожидания при подключении
            self.client.settimeout(time_out)
            # Создаем подключение к устройству
            self.client.connect((ip, self.tcp_port))

            # Отправляем запрос на устройство
            self.client.send(req1)
            #time.sleep(0.5)
            # Зпрашиваем ответ 
            self._recieve_responce()
            # Отправляем запрос на устройство 
            self.client.send(req2)
            #time.sleep(0.5)
            # Запрашиваем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            self.client.send(req3)
            #time.sleep(0.5)
            # Запрашиваем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            self.client.send(req4)
            # Запрашиваем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            #self.client.send(req5)
            # Запрашиваем ответ
            #self._recieve_responce()
            # Формируем строку с результатом
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ОПС:[{self.ao_ops}][{self.do_ops}]; Топл.:{self.fuel}%; Bat:{self.bat_V}V; АО:{self.ao_tmp}*C; ДО:{self.do_tmp}*C; О/Ж:{self.af_tmp}*C; Двиг.:{self.stop_motor}"
            motor = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Работа двигателя: [{self.stop_motor}]"
            hight_temp_water = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Высокая температура О/Ж: [{self.hight_temp_water}]"
            low_temp_water = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Низкая температура О/Ж: [{self.low_temp_water}]"
            low_level_oil = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Уровень топлтва: [{self.low_level_oil}]"
            low_oil_pressure = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Низкое давление масла: [{self.low_oil_pressure}]" 
            low_water = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Низкий уровень О/Ж: [{self.low_level_water}]"
            switch_motor = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Переключатель управления двигателем не в автоматическом состоянии: [{self.switch_state_motor}]"
            low_batt_charge = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} ДГУ: Низкий заряд АКБ: [{self.low_batt_charge}]"
            return result,motor,hight_temp_water,low_temp_water,low_level_oil,low_oil_pressure,low_water,switch_motor,low_batt_charge
        except socket.timeout:
            # Формируем строку ответа в случаи ошибки
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger.error('ClientModbus: Ошибка подключения отправки TCP')
            return error
    
    # Метод получает данные с устройства и обрабатывает их в зависимости от условий
    def _recieve_responce(self):
        # Запрашиваем данные и переводим их в 16-ти ричную систему
        responce = self.client.recv(self.buffer_size).hex()
        #print(responce)
        # Если в запросе есть данные
        if responce:
            # Если длина полученных данных равна 34
            if len(responce) == 34:
                # Получаем значение Уровень топлива, Температура охлаждающей жидкости, Напряжение батареи. 
                match = re.match(r'[\d a-z]{20}(?P<fuel>[\d a-z]{2})[\d a-z]{4}(?P<af_tmp>[\d a-z]{4})(?P<bat_v>[\d a-z]{4})', responce)
                if match:
                    self.fuel = int(match.group('fuel'), 16)
                    self.af_tmp = round(int(match.group('af_tmp'), 16)*0.01, 2)
                    self.bat_V = round(int(match.group('bat_v'), 16)*0.01, 2)
                else:
                    self.fuel = None
                    self.af_tmp = None
                    self.bat_V = None
            # Если длинна полученных данных равна 26
            elif len(responce) == 26:
                # Получаем значения Температуры в АО и Температуры в ДО. . 
                match = re.match(r'[\d a-z]{18}(?P<ao_tmp>[\d a-z]{4})(?P<do_tmp>[\d a-z]{4})', responce)
                if match:
                    self.ao_tmp = int(match.group('ao_tmp'), 16)
                    self.do_tmp = int(match.group('do_tmp'), 16)*0.01
                else:
                    self.ao_tmp = None
                    self.do_tmp = None
            # Если длинна полученных данных равна 30
            elif len(responce) == 30:
                # Получаем значения Охрано Пожарная Сигнализация АО и ОПС ДО
                match = re.match(r'[\d a-z]{18}(?P<ao_ops>[\d a-z]{4})(?P<do_ops>[\d a-z]{4})', responce)
                if match:
                    self.ao_ops = int(match.group('ao_ops'), 16) 
                    self.do_ops = int(match.group('do_ops'), 16)
                else:
                    self.ao_ops = None
                    self.do_ops = None
            # Если длинна полученных данных равна 30
            elif len(responce) == 22:
                # Парсим полученный ответ и достаем последних четыре значенния это два байта в 16-тиричной форме 
                match = re.match(r'[\d]{18}(?P<registr_value>[\d a-z]{4})', responce)
                # Проверяем если мы распарсили данные
                if match:
                    # Преобразуем полученное значение из 16-тиричной формы в двоичную форму, получаем строковое значение (биты)
                    self.value_bit = bin(int(match.group('registr_value'), 16)).lstrip('0b')
                    # Если получили значение не равное нулю
                    if self.value_bit:
                        # Вызываем метод 
                        self._get_signals_controller(self.value_bit)
                else:
                   self.alarm_stop_motor = None 

    def _get_signals_controller(self, register_value):
        #
        for num, bit in enumerate(register_value, start=1):
            if bit == '1':
                # Аварийная остановка двигателя, бит=0
                if len(register_value)-num == 0:
                    self.stop_motor = 1
                # Высокая температура охлаждающей жидкости, бит=2
                if len(register_value)-num == 2:
                    self.hight_temp_water = 1
                # Низкая температура охлаждающей жидкости, бит=3
                if len(register_value)-num == 3:
                    self.low_temp_water = 1  
                # Низкое давление масла, бит=4
                if len(register_value)-num == 4:
                    self.low_oil_pressure = 1
                # Низкий уровень охлаждающей жидкости, бит=6
                if len(register_value)-num == 6:
                    self.low_level_water = 1
                # Низкий уровень топлива, бит=7
                if len(register_value)-num == 7:
                    self.low_level_oil = 1
                # Переключатель управления двигателем не в автоматическом состоянии, бит=8
                if len(register_value)-num == 8:
                   self.switch_not_auto_state = 1
                # Низкий уровень заряда батареи, бит=10
                if len(register_value)-num == 10:
                   self.low_batt_charge = 1


if __name__ == '__main__':
    client = ClientModbus()
    print(client.modbus('10.19.178.2'))
    #time.sleep(30)
    #print(client.modbus_alm_stop_motor('10.184.50.200'))
        
