#
from class_ThreadSNMPAsc import ThreadSNMPAsk
from PyQt5 import QtCore
# Импортируем классс QThread отвечающий за многопоточность в PYQT
from PyQt5.QtCore import QThread

# Класс в отдельном потоке опрашивает разные модели оборудования
class ThreadCheckModelDevice(QThread):
    # Сигнал snmp-запроса 
    signal_snmp_request_done = QtCore.pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        # Создаем экземпляр класса snmp_ask_check
        self.snmp_ask_check = ThreadSNMPAsk()
        #
        self.ip_address = None

    # Метод делает проверку к какому типу принадлежит устройство с веденным ip адресом
    def run(self) -> None:
        # Вызываем метод forpost из класса "class_SNMPAsc" передавая на вход ip адрес устройства, полученный результат записываем в переменную result
        result = self.snmp_ask_check.forpost(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: Forpost')
        # Вызываем метод forpost2 передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.forpost_2(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: Forpost-2')
        # Вызываем метод forpost_3 передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.forpost_3(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: Forpost-3')
        # Вызываем метод eaton передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.eaton(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: Eaton')
        # Вызываем метод legrand передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.legrand(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: Legrand')
        # Вызываем метод apc передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.apc(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: APC')
        # Вызываем метод eltek передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.eltek(self.ip_address, timeout=5, block=True, next=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_donee.emit('Модель устройства: Eltek')
        # Вызываем метод eltek передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.eltek(self.ip_address, timeout=5, block=True, next = True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: MAC&C')
        # Вызываем метод modbus передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.mc2600(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: MC-2600')
        # Вызываем метод sc200 передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        result = self.snmp_ask_check.sc200(self.ip_address, timeout=5, block=True)
        if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            self.signal_snmp_request_done.emit('Модель устройства: SC-200')
        # Вызываем метод modbus передавая на вход ip адрес, время ожидания и флаг(что бы запустить snmp manager)
        #result = self.snmp_ask_check.modbus(self.ip_address, time_out=5)
        #if isinstance(result, str):
            # Испускаем сигнал передав на вход строку с названием модели устройства
            #self.signal_snmp_request_done.emit('Modbus')
        # Испускаем сигнал передав на вход строку с результатом опроса
        self.signal_snmp_request_done.emit('Модели устройства в списке нет')  
