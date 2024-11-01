#
from typing import Optional
import socket
from socket import AF_INET, SOCK_DGRAM
import struct
import re 
import time
import logging
from PyQt5 import QtCore

class ClientModbus:
    # Сигнал для сигнализации отсутствия сетевого доступа
    signa_network_error = QtCore.pyqtSignal()


    def __init__(self) -> None:
        # Настройка логирования
        #self.path_logs = Path(Path.cwd(), "logs", "logs_snmp_ask.txt")
        self.logger = logging.getLogger('class_ClientModbus')
        logging.basicConfig(#filename=Path(Path.cwd(),"GGS", "logs_v640.txt"), 
            #filemode='w', 
            format = '%(asctime)s %(name)s: %(lineno)d: %(message)s' , 
            datefmt='%d-%m-%y',
            level=logging.INFO)
        #self.logger.setLevel(logging.INFO)
        #fh_logs = logging.FileHandler(self.path_logs, 'w')
        #formatter_logs = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        #fh_logs.setFormatter(formatter_logs)
        #self.logger.addHandler(fh_logs)

        # Номер порта
        self.tcp_port = 502
        # Размер буфера
        self.buffer_size = 4096
        # Индентификатор устройства
        self.unit_id = 1
        # Код функции Modbus
        self.function_code = 4

        #self.function_code_bit = 1
        
        self.oil_level: Optional[int] = None # уровень топлива, коэф = 1
        self.af_tmp: Optional[float] = None # температура охлождающей жидкости, коэф = 0,01
        self.bat_V: Optional[float] = None # напряжение батареи, коэф = 0,01
        self.ao_tmp: Optional[int] = None # температура в Аппаратной , коэф = 1
        self.do_tmp: Optional[float] = None # температура в Дизельной, коэф = 0,01
        self.air_temp:Optional[float] = None # температура наружного воздуха

        
        self.ao_ops: Optional[int] = None  # ОПС АО, коэф = 1
        self.do_ops: Optional[int] = None  # ОПС ДО, коэф = 1
        self.stop_motor = 0 # Аварийная остановка двигателя 0 или 1 (BIT)
        self.hight_temp_water = 0 # Высокая температура охлаждающей жидкости
        self.low_temp_water = 0 # Низкая температура охлаждающей жидкости
        self.low_oil_pressure = 0 # Низкое давление масла
        self.low_level_water = 0 # Низкий уровень охлаждающей жидкости
        self.low_level_oil = 0 # Низкий уровень топлива
        self.switch_state_motor = 0 # Переключатель управления двигателем не в автоматическом состоянии 
        self.low_batt_charge = 0 # Низкий уровень заряда батареи.

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

    0007 0000 000b 01 04 0800 2e00 0a 06df  052d

    0006 0000 0005 01 04 02 00fb

    0006 0000 0007 01 04 04 f5b6 00fb

    (Индентификатор транзакции(0001)[2 байта]), (Индентификатор протокола(0000)[2 байта]), 
    (Длина сообщения ответа(000b)[11 байт], (Адрес устройства(01)[1 байт]), 
    (Код функции(04)[1 байт]),(Количество байт идущие далее(может быть разное)(0800)[8 байт], 
    (Значение 4-х регистров по 2 байта каждый, которые мы запросили) 

    '''

    def get_params(self, ip: str, time_out: int =10, count: int = 1):
        # Упаковываем данные в байты для отправки на устройство (Н-2байта, В-1байт), тип регистра DWORD 16-тиричный
        req1 = struct.pack('>HHHBBHH', 0x01, 0x00, 0x06, self.unit_id, self.function_code, 24587, 0x04)
        # Тип регистра DWORD 16-тиричный
        req2 = struct.pack('>HHHBBHH', 0x02, 0x00, 0x06, self.unit_id, self.function_code, 24714, 0x02)
        # 
        req3 = struct.pack('>HHHBBHH', 0x06, 0x00, 0x06, self.unit_id, self.function_code, 24720, 0x01)
        try:
            # Создаем соккет для подключения к устройству
            self.client = socket.socket()
            # Устанавливаем время ожидания при подключении
            self.client.settimeout(time_out)
            # Создаем подключение к устройству
            self.client.connect((ip, self.tcp_port))
            # Отправляем запрос на устройство
            self.client.send(req1)
            # Получаем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            self.client.send(req2)
            # Получаем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            self.client.send(req3)
            # Получаем ответ
            self._recieve_responce()
            responce = f''' 
<b>Температура в АО:</b> {self.ao_tmp} *C
<b>Температура в ДО:</b> {self.do_tmp} *C
<b>Температура О/Ж:</b> {self.af_tmp} *C
<b>Уровень топлива:</b> {self.oil_level} %
<b>Напряжение батареи:</b> {self.bat_V} V
'''
            return responce
        except:
            pass
    
    # Метод отправляет запрос на оборудование по протоколу Modbus
    def modbus(self, ip: str, time_out: int =10, count: int = 1) -> Optional[str]:
        # Упаковываем данные в байты для отправки на устройство (Н-2байта, В-1байт), тип регистра DWORD 16-тиричный
        req1 = struct.pack('>HHHBBHH', 0x01, 0x00, 0x06, self.unit_id, self.function_code, 24587, 0x04)
        # Тип регистра DWORD 16-тиричный
        req2 = struct.pack('>HHHBBHH', 0x02, 0x00, 0x06, self.unit_id, self.function_code, 24714, 0x02)
        # Тип регистра DWORD 16-тиричный
        req3 = struct.pack('>HHHBBHH', 0x03, 0x00, 0x06, self.unit_id, self.function_code, 24723, 0x02)
        # Тип регистра BIT 2-ый
        req4 = struct.pack('>HHHBBHH', 0x04, 0x00, 0x06, self.unit_id, self.function_code, 24598, 0x01)
        # Экстренная остановка двигателя тип регистра BIT 2-ый
        req5 = struct.pack('>HHHBBHH', 0x05, 0x00, 0x06, self.unit_id, self.function_code, 24597, 0x01)
        try:
            # Создаем соккет для подключения к устройству
            self.client = socket.socket()
            # Устанавливаем время ожидания при подключении
            self.client.settimeout(time_out)
            # Создаем подключение к устройству
            self.client.connect((ip, self.tcp_port))

            # Отправляем запрос на устройство
            self.client.send(req1)
            # Зпрашиваем ответ 
            self._recieve_responce()
            # Отправляем запрос на устройство 
            self.client.send(req2)
            # Запрашиваем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            self.client.send(req3)
            # Запрашиваем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            self.client.send(req4)
            # Запрашиваем ответ
            self._recieve_responce()
            # Отправляем запрос на устройство
            self.client.send(req5)
            # Запрашиваем ответ
            self._recieve_responce()
            # Формируем строку с результатом
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {count}; ДГУ: ОПС:[{self.ao_ops}][{self.do_ops}]; Топл.:{self.oil_level}%; Bat:{self.bat_V}V; АО:{self.ao_tmp}*C; ДО:{self.do_tmp}*C; О/Ж:{self.af_tmp}*C; Двиг.:[{self.stop_motor}]; Выс.Темп_О/Ж:[{self.hight_temp_water}]; Низ.Темп_О/Ж:[{self.low_temp_water}]; Топл.:[{self.low_level_oil}]; ДМ:[{self.low_oil_pressure}]; Уров.О/Ж:[{self.low_level_water}]; ПУД:[{self.switch_state_motor}]; Бат.:[{self.low_batt_charge}]" 
            return result
        except socket.timeout:
            # Формируем строку ответа в случаи ошибки
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger.error('ClientModbus: Ошибка подключения отправки TCP')
            return error
        except (ConnectionAbortedError, OSError):
            self.signa_network_error.emit()
            return None
    
    # Метод получает данные с устройства и обрабатывает их в зависимости от условий
    def _recieve_responce(self) -> None:
        # Запрашиваем данные и переводим их в 16-ти ричную систему
        responce = self.client.recv(self.buffer_size).hex()
        #print(responce)
        # Если в запросе есть данные
        if responce:
            # Если третий индекс в ответе равен 1, это номер запроса
            if responce[3] == '1':
                # Получаем значение Уровень топлива, Температура охлаждающей жидкости, Напряжение батареи. 
                match = re.match(r'[\d a-z]{20}(?P<oil_level>[\d a-z]{2})[\d a-z]{4}(?P<af_tmp>[\d a-z]{4})(?P<bat_v>[\d a-z]{4})', responce)
                if match:
                    # Преобразуем полученные значения в 16-тиричной форме в десятичную
                    self.oil_level = int(match.group('oil_level'), 16)
                    # Преобразуем полученные значения в 16-тиричной форме в десятичную и домножаем полученое значение на 
                    # коэф-т и округляем значение до двух чисел после запятой 
                    self.af_tmp = round(int(match.group('af_tmp'), 16)*0.01, 2)
                    self.bat_V = round(int(match.group('bat_v'), 16)*0.01, 2)
                else:
                    self.oil_level = None
                    self.af_tmp = None
                    self.bat_V = None
            # Если третий индекс в ответе равен 2, это номер запроса
            elif responce[3] == '2':
                # Получаем значения Температуры в АО и Температуры в ДО. . 
                match = re.match(r'[\d a-z]{18}(?P<ao_tmp>[\d a-z]{4})(?P<do_tmp>[\d a-z]{4})', responce)
                if match:
                    # Преобразуем полученные значения в 16-тиричной форме в десятичную
                    self.ao_tmp = int(match.group('ao_tmp'), 16)
                    # Преобразуем полученные значения в 16-тиричной форме в десятичную и домножаем полученое значение на коэф-т
                    self.do_tmp = int(match.group('do_tmp'), 16)*0.01
                else:
                    self.ao_tmp = None
                    self.do_tmp = None
            # Если третий индекс в ответе равен 3, это номер запроса
            elif responce[3] == '3':
                # Получаем значения Охрано Пожарная Сигнализация АО и ОПС ДО
                match = re.match(r'[\d a-z]{18}(?P<ao_ops>[\d a-z]{4})(?P<do_ops>[\d a-z]{4})', responce)
                if match:
                    # Преобразуем полученные значения в 16-тиричной форме в десятичную
                    self.ao_ops = int(match.group('ao_ops'), 16) 
                    self.do_ops = int(match.group('do_ops'), 16)
                else:
                    self.ao_ops = None
                    self.do_ops = None

            # Если третий индекс в ответе равен 4, это номер запроса
            elif responce[3] == '4':
                # Парсим полученный ответ, достаем последние четыре значенния это два байта в 16-тиричной форме 
                match = re.match(r'[\d]{18}(?P<registr_value>[\d a-z]{4})', responce)
                # Проверяем если мы распарсили данные
                if match:
                    # Преобразуем значение(2 байта) из 16-тиричной формы в десятичную, получаем целое число
                    value_decimal = int(match.group('registr_value'), 16)
                    # Преобразуем целое число в двоичную последовательсть бит 
                    sequence_bit = f'{value_decimal:b}'
                    # Если значение не равно 0
                    if sequence_bit != '0':
                        # Вызываем метод, передаем последовательность бит  
                        self._get_signals_controller(sequence_bit)
                    else:
                        self.hight_temp_water = 0
                        self.low_temp_water = 0
                        self.low_oil_pressure = 0
                        self.low_level_water = 0
                        self.low_level_oil = 0
                        self.switch_state_motor = 0 
                        self.low_batt_charge = 0

            # Если третий индекс в ответе равен 5, это номер запроса.
            elif responce[3] == '5':
                # Парсим полученный ответ, достаем последние четыре значенния это два байта в 16-тиричной форме 
                match = re.match(r'[\d]{18}(?P<registr_value>[\d a-z]{4})', responce)
                # Проверяем если мы распарсили данные
                if match:
                    # Преобразуем байты из 16-тиричной формы в десятичную, получаем целое число
                    value_decimal = int(match.group('registr_value'), 16)
                    # Преобразуем целое число в битовую строку
                    value_bit = f'{value_decimal:b}'
                    # Если значение равно 1
                    if value_bit == '1':
                        # Экстренная остановка двигателя - бит=0
                        self.stop_motor = 1
                    else:
                        self.stop_motor = 0
            

    # Метод принимает на вход битовую строку, присваивает значение переменным 0 или 1
    def _get_signals_controller(self, sequence_bit: str) -> None:
        # Получаем количество старших бит значения которых равны нулю
        hight_bit = (11 - len(sequence_bit)) * '0' # Пример: (11- 6) * '0' = '00000'
        # Получаем полную полседовательность бит регистра сложив старшие биты и полученную полседовательность бит
        full_sequence_bit = hight_bit + sequence_bit # Пример: '00000' + '100000' = '00000100000' и тому подобное
        #
        for num, bit in enumerate(full_sequence_bit, start=1):
            # Высокая температура охлаждающей жидкости, бит=2
            if len(full_sequence_bit)-num == 2:
                self.hight_temp_water = int(bit)
            # Низкая температура охлаждающей жидкости, бит=3
            elif len(full_sequence_bit)-num == 3:
                self.low_temp_water = int(bit) 
            # Низкое давление масла, бит=4
            elif len(full_sequence_bit)-num == 4:
                self.low_oil_pressure = int(bit)
            # Низкий уровень охлаждающей жидкости, бит=6
            elif len(full_sequence_bit)-num == 6:
                self.low_level_water = int(bit)
            # Низкий уровень топлива, бит=7
            elif len(full_sequence_bit)-num == 7:
                self.low_level_oil = int(bit)
            # Переключатель управления двигателем не в автоматическом состоянии, бит=8
            elif len(full_sequence_bit)-num == 8:
                self.switch_state_motor = int(bit)
            # Низкий уровень заряда батареи, бит=10
            elif len(full_sequence_bit)-num == 10:
                self.low_batt_charge = int(bit)
        return None
    

if __name__ == '__main__':
    client = ClientModbus()
    #print(client.orion('10.31.58.51'))
    #time.sleep(30)
    #client.modbus('10.184.50.200', time_out =10, count = 1)
    client.get_params('10.184.50.200')
    #print(client.modbus_alm_stop_motor('10.184.50.200'))
        
