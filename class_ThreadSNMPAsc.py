#
from __future__ import annotations
from typing import List, Union, Optional, Any
import time
import logging
from snmp import Manager
from snmp.exceptions import Timeout
from snmp.v1.exceptions import NoSuchName
# Импортируем классс QThread отвечающий за многопоточность в PYQT
from PyQt5.QtCore import QThread
from class_ClientModbus import ClientModbus
from class_SqlLiteMain import ConnectSqlDB

class ThreadSNMPAsk(QThread, ClientModbus):
    def __init__(self) -> None:
        # Запускаем у класса QThread метод init
        #QThread.__init__(self)
        super().__init__()
        # Переменная определяет время между запросами цикла while
        self.interval_time = 5
        # Сптсок для хранения результата snmp опроса 
        self.snmp_trap: List[str] = []
        # Счетчик записываем количество итераций сделанных циклом while
        self.counter = 1
        ''' 
        self.queue.put(sys.exc_info())
        Вызываем у экземпляра класса queue метод put, который помещает элемен в очередь.
        Этот метод никогда не блокируется и всегда завершается успешно.
        В качестве элемента передаем метод exc_info модуль sys, который возвращает информацию 
        о самом последнем исключении, перехваченном в текущем фрейме стека или в более раннем фрейме стека.

        '''
        # Создание переменных OID
        # Forpost_2 ШПТ-ИНК-2 для двух групп АКБ
        self.load_A = '1.3.6.1.4.1.33183.14.3.2.0'
        self.temp = '1.3.6.1.4.1.33183.14.5.1.4.2'
        self.load_V = '1.3.6.1.4.1.33183.14.3.1.0'
        self.out_V = '1.3.6.1.4.1.33183.14.5.1.2.1'
        self.in_st = '1.3.6.1.4.1.33183.14.2.3.0'
        self.batt = '1.3.6.1.4.1.33183.14.5.1.6.1'
        self.inp_V = '1.3.6.1.4.1.33183.14.2.1.0'
        # Forpost
        self.load_Amp ='1.3.6.1.4.1.33183.10.3.2.0'
        self.tmp = '1.3.6.1.4.1.33183.10.4.1.4.1'
        self.load_Vol = '1.3.6.1.4.1.33183.10.3.1.0'
        self.in_stat = '1.3.6.1.4.1.33183.10.2.3.0'
        self.betery = '1.3.6.1.4.1.33183.10.5.1.6.1'
        self.inp_Volt = '1.3.6.1.4.1.33183.10.2.1.0'
        # EATON + Legrand
        self.power = '1.3.6.1.2.1.33.1.4.4.1.4.1'
        self.load = '1.3.6.1.2.1.33.1.4.4.1.5.1'
        self.out = '1.3.6.1.2.1.33.1.4.4.1.2.1'
        self.inp = '1.3.6.1.2.1.33.1.3.3.1.3.1'
        self.battery = '1.3.6.1.2.1.33.1.2.4.0'
        self.in_status = '1.3.6.1.2.1.33.1.4.1.0'
        self.temperature = '1.3.6.1.4.1.534.1.6.1.0'
        # SC200
        self.load_Am = '1.3.6.1.4.1.1918.2.13.10.50.10.0'
        self.out_Vol = '1.3.6.1.4.1.1918.2.13.10.70.10.20.0'
        self.inp_Vol = '1.3.6.1.4.1.1918.2.13.10.40.10.0'
        self.temper = '1.3.6.1.4.1.1918.2.13.10.100.30.0'
        # Legrand
        self.tmprt = '1.3.6.1.2.1.33.1.2.7.0'
        # APC 
        self.output_load = '1.3.6.1.4.1.318.1.1.1.4.2.3.0'
        self.output_voltage = '1.3.6.1.4.1.318.1.1.1.4.2.1.0'
        self.inpu_Voltage = '1.3.6.1.4.1.318.1.1.1.3.2.1.0'
        self.input_st = '1.3.6.1.4.1.318.1.1.1.4.1.1.0'
        self.batt_temp = '1.3.6.1.4.1.318.1.1.1.2.2.2.0'
        self.batt_capacity = '1.3.6.1.4.1.318.1.1.1.2.2.1.0'
        # Eltek OIDs
        self.rect_stat_temp = '1.3.6.1.4.1.12148.9.5.5.2.1.5'
        self.batt_out_volt = '1.3.6.1.4.1.12148.9.3.2'
        self.rect_total_curr = '1.3.6.1.4.1.12148.9.5.3'
        self.ac_volt1 = '1.3.6.1.4.1.12148.9.6.1'
        # MC2600
        self.phase1 = '1.3.6.1.4.1.40211.8.1.1.2.1'
        self.phase2 = '1.3.6.1.4.1.40211.8.1.1.2.2'
        self.phase3 = '1.3.6.1.4.1.40211.8.1.1.2.3'
        self.sys_voltage = '1.3.6.1.4.1.40211.2.1.1.2.0'
        self.sys_load = '1.3.6.1.4.1.40211.2.1.1.3.0'
        self.module_temp = '1.3.6.1.4.1.40211.8.1.1.6.1' 
        # MAC&C OIDs
        self.f10GFx1DDTemp = '1.3.6.1.4.1.40844.100.270.20.1.46'
        self.f10GFx1DDTxPWR = '1.3.6.1.4.1.40844.100.270.20.1.44'
        self.f10GFx1DDRxPWR = '1.3.6.1.4.1.40844.100.270.20.1.45'
        self.f10GFx2DDTemp = '1.3.6.1.4.1.40844.100.270.20.1.60'
        self.f10GFx2DDTxPWR = '1.3.6.1.4.1.40844.100.270.20.1.58'
        self.f10GFx2DDRxPWR = '1.3.6.1.4.1.40844.100.270.20.1.59'
        self.f10GFx3DDTemp = '1.3.6.1.4.1.40844.100.270.20.1.74'
        self.f10GFx3DDRxPWR = '1.3.6.1.4.1.40844.100.270.20.1.73'
        self.f10GFx3DDTxPWR = '1.3.6.1.4.1.40844.100.270.20.1.72'
        # Cisco
        self.ifOperStatus = '1.3.6.1.2.1.2.2.1.8.' # (up(1), down(2), testing(3))
        self.ifOutOctets = '1.3.6.1.2.1.2.2.1.16.' # ifOutOctets

    ''' 
    GetRequest - запрос к агенту от менеджера, используемый для получения значения одной или нескольких переменных.
    GetNextRequest - запрос к агенту от менеджера, используемый для получения следующего в иерархии значения переменной.
    '''
    
    # Метод делает запрос по протоколу SNMP, принимает на вход ip и набор oid для определенного устройства.
    def get_request(
        self, 
        ip: str, 
        oids: List[str], 
        block: bool, 
        timeout: int, 
        next: bool
    ) -> Union[List[Any], str]:
        
        if block:
            self.manager = Manager(b'public', version=1, port=161)
        try:
            # Значение block=False, говорит что мы не дожидаемся результата, а получим его при следующем запросе
            out: List[Any] = self.manager.get(ip, *oids, next=next, timeout=timeout, block=block)
            if block:
                self.manager.close()
            return out
        except Timeout as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            # Логирование, записывает в файл logs_snmp_ask.txt
            self.logger = logging.getLogger('class_ThreadSNMPAsc')
            self.logger.debug(f'Ошибка Timeout - не получен ответ от устройства {ip}')
           # Если block истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
                return None
            return error
        except NoSuchName as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            self.logger = logging.getLogger('class_ThreadSNMPAsc')
            self.logger.info(f'Ошибка NoSuchName - не существующая переменная {err}: {ip}')
            # Если block истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
                return None
            return error
        except AttributeError as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            self.logger = logging.getLogger('class_ThreadSNMPAsc')
            self.logger.info(f'Ошибка AttributeError - SNMP Manager не запущен, в запросе не передан block=True: {ip}')
            # Если block истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
                return None
            return error
        except OSError as err:
            # Если block истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
                return None
            return str(err)

    # Метод   
    def macc(self, ip: str, timeout: int =10, next: bool = True, block: bool = False) -> Optional[str]:
        #
        oids = [self.f10GFx1DDTemp, self.f10GFx1DDTxPWR, self.f10GFx1DDRxPWR, self.f10GFx2DDTemp, self.f10GFx2DDTxPWR, self.f10GFx2DDRxPWR, self.f10GFx3DDTemp, self.f10GFx3DDTxPWR, self.f10GFx3DDRxPWR]
        # Делаем запрос GETNEX получаем список данных типа snmp.types.VarBind
        out = self.get_request(ip, oids, block, timeout, next)
        # Если тип переменной out список И список не содержит значения None 
        if isinstance(out, list) and None not in out:
            # Распаковываем список 
            temp_fiber1, tx_fiber1, rx_fiber1, temp_fiber2, tx_fiber2, rx_fiber2, temp_fiber3, tx_fiber3, rx_fiber3 = out
            #
            temp_fiber1 = temp_fiber1.values[-1].value.decode()
            tx_fiber1 = tx_fiber1.values[-1].value.decode()
            rx_fiber1 = rx_fiber1.values[-1].value.decode()
            temp_fiber2 = temp_fiber2.values[-1].value.decode()
            tx_fiber2 = tx_fiber2.values[-1].value.decode()
            rx_fiber2 = rx_fiber2.values[-1].value.decode()
            temp_fiber3 = temp_fiber3.values[-1].value.decode()
            tx_fiber3 = tx_fiber3.values[-1].value.decode()
            rx_fiber3 = rx_fiber3.values[-1].value.decode()
            if not temp_fiber1.endswith('-') and not tx_fiber1.endswith('-') and not rx_fiber1.endswith('-') and \
                not temp_fiber2.endswith('-') and not tx_fiber2.endswith('-') and not rx_fiber2.endswith('-'):
                # Формируем строку вывода с параметрами устройства
                result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; TxFiber1: {tx_fiber1} dBm; RxFiber1: {rx_fiber1} dBm; TempFiber1: {temp_fiber1} *C; TxFiber2: {tx_fiber2} dBm; RxFiber2: {rx_fiber2} dBm; TempFiber2: {temp_fiber2} *C" 
            elif not temp_fiber1.endswith('-') and not tx_fiber1.endswith('-') and not rx_fiber1.endswith('-') and \
                not temp_fiber3.endswith('-') and not tx_fiber3.endswith('-') and not rx_fiber3.endswith('-'):
                # Формируем строку вывода с параметрами устройства
                result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; TxFiber1: {tx_fiber1} dBm; RxFiber1: {rx_fiber1} dBm; TempFiber1: {temp_fiber1} *C; TxFiber3: {tx_fiber3} dBm; RxFiber3: {rx_fiber3} dBm; TempFiber3: {temp_fiber3} *C" 
            elif not temp_fiber2.endswith('-') and not tx_fiber2.endswith('-') and not rx_fiber2.endswith('-') and \
                not temp_fiber3.endswith('-') and not tx_fiber3.endswith('-') and not rx_fiber3.endswith('-'):
                # Формируем строку вывода с параметрами устройства
                result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; TxFiber2: {tx_fiber2} dBm; RxFiber2: {rx_fiber2} dBm; TempFiber2: {temp_fiber2} *C; TxFiber3: {tx_fiber3} dBm; RxFiber3: {rx_fiber3} dBm; TempFiber3: {temp_fiber3} *C" 
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error
        return None
    
    # Метод делает запрос к Системе питания TG.PS.3.9-A5D21 12KW с контроллером управления MC2600 по протоколу SNMP
    def mc2600(self, ip, timeout =10, next = False, block =False):
        # Формируем список oid для запроса
        oids = [self.phase1, self.phase2, self.phase3, self.sys_voltage, self.sys_load]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распоковываем полученный список
            varbind_pahase1, varbind_pahase2, varbind_pahase3, varbind_out_volt, varbind_load = out
            # Преобразуем полученные данные, получаем значения переменных
            pahase1 = (varbind_pahase1.values[-1].value)/10
            pahase2 = (varbind_pahase2.values[-1].value)/10
            pahase3 = (varbind_pahase3.values[-1].value)/10
            out_volt = round((varbind_out_volt.values[-1].value)/1000, 1)
            load =  round((varbind_load.values[-1].value)/1000, 1)
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; Phase_A: {pahase1} V Phase_B: {pahase2} V Phase_C: {pahase3} V; OUT: {out_volt} V ({load} А)"  
            # Возвращаем результат
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        return None
    
    # Метод делает запрос к ИБП Eltek по протоколу SNMP
    def eltek(self, ip: str, timeout: int =10, next: bool = True, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.ac_volt1, self.batt_out_volt, self.rect_total_curr, self.rect_stat_temp]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распоковываем полученный список
            inp_volt, out_volt, load, temp = out
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/100} V ({load.values[-1].value} А); *C: {temp.values[-1].value}"  
            # Возвращаем результат
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error

    def forpost_2(self, ip: str, timeout: int =10, next: bool = False, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.load_A, self.temp, self.load_V, self.out_V, self.batt, self.inp_V]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распоковываем полученный список 
            load, temp, _, out_volt, batt, inp_volt = out 
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/10} V ({(load.values[-1].value)/10} А). Batt: {batt.values[-1].value}%. *C: {temp.values[-1].value}"  
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        
    def forpost(self, ip: str, timeout: int =10, next: bool = False, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.load_Amp, self.tmp, self.load_Vol, self.betery, self.inp_Volt]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распаковываем список с полученными данными
            load, temp, out_volt, batt, inp_volt = out 
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/10} V ({(load.values[-1].value)/10} А); Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        return None

    def forpost_3(self, ip: str, timeout: int =10, next: bool = False, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.load_Amp, self.tmp, self.load_Vol, self.inp_Volt]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распаковываем список с полученными данными
            load, temp, out_volt, inp_volt = out 
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/10} V ({(load.values[-1].value)/10} А); *C: {temp.values[-1].value}" 
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        return None

    def eaton(self, ip: str, timeout: int =10, next: bool = False, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.power, self.load, self.out, self.inp, self.battery, self.temperature]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распоковываем полученный список
            power, load, out_volt, inp_volt, batt, temp = out
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {out_volt.values[-1].value} V; Load: {load.values[-1].value}% ({power.values[-1].value} WT); Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        return None

    def sc200(self, ip: str, timeout: int =10, next: bool = False, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.load_Am, self.out_Vol, self.inp_Vol, self.temper]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распоковываем полученный список
            load, out_volt, inp_volt, temp = out
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/100} V Load: ({load.values[-1].value}A); *C: {temp.values[-1].value}" 
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        return None

    def legrand(self, ip: str, timeout: int =10, next: bool = False, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.out, self.inp, self.tmprt, self.battery]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распоковываем полученный список 
            out_volt, inp_volt, temp, batt = out
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {out_volt.values[-1].value} V Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        return None

    def apc(self, ip: str, timeout: int =10, next: bool = False, block: bool = False) -> Optional[str]:
        # Формируем список oid для запроса
        oids = [self.output_load, self.output_voltage, self.inpu_Voltage, self.batt_temp, self.batt_capacity]
        # Делаем GET запрос, получаем список данных типа VarBind и записываем в перенменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if isinstance(out, list) and None not in out:
            # Распоковываем полученный список 
            load, out_volt, inp_volt, temp, batt = out
            # Формируем строку результата
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {out_volt.values[-1].value} V; Load: {load.values[-1].value}%; Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если значение None, это условие нам нужно при проверке модели устройства в приложении 
        elif isinstance(out, type(None)):
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter} SNMP:REQEST_ERROR"
            return error
        return None
    
    # Метод запускает SNMP опрощик
    def run(self) -> None:
        # Счетчик записываем количество итераций сделанных циклом while
        self.counter = 1
        # Количество SNMP запрсов 
        self.count = 1
        # Запускаем SNMP Менеджер
        self.manager = Manager(b'public', version=1)
        self.logger = logging.getLogger('class_ThreadSNMPAsc')
        self.logger.debug('Запускаю')
        while True:
            # Создаем переменную в которую будем сохранять результаты snmp
            self.snmp_trap = []
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                # Делаем запрос к БД, получить список значений oid и ip из таблицы Devices
                data_base = sql.get_values_list_db('model', 'ip', table='Devices')
            if data_base:
                # Перебираем список и распаковываем кортеж
                for model, ip in data_base:
                    # Делаем проверку если ключ словаря сопал с названием метода
                    if model == 'forpost' and isinstance(ip, str):
                        # Вызываем метод forpost передавая ему ip адрес устройства
                        result = self.forpost(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'forpost_2' and isinstance(ip, str):
                        # Вызываем метод forpost_2 передавая ему ip адрес устройства
                        result = self.forpost_2(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'forpost_3' and isinstance(ip, str):
                        # Вызываем метод forpost_3 передавая ему ip адрес устройства
                        result = self.forpost_3(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'eaton' and isinstance(ip, str):
                        # Вызываем метод eaton передавая ему ip адрес устройства
                        result = self.eaton(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'sc200' and isinstance(ip, str):
                        # Вызываем метод sc200 передавая ему ip адрес устройства
                        result = self.sc200(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'legrand' and isinstance(ip, str):
                        # Вызываем метод legrand передавая ему ip адрес устройства
                        result = self.legrand(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'apc' and isinstance(ip, str):
                        # Вызываем метод apc передавая ему ip адрес устройства
                        result = self.apc(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'eltek' and isinstance(ip, str):
                        # Вызываем метод eltek передавая ему ip адрес устройства
                        result = self.eltek(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'mc2600' and isinstance(ip, str):
                        # Вызываем метод eltek передавая ему ip адрес устройства
                        result = self.mc2600(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'macc' and isinstance(ip, str):
                        # Вызываем метод macc передавая ему ip адрес устройства
                        result = self.macc(ip)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'modbus' and isinstance(ip, str):
                        # Вызываем метод modbus передавая ему ip адрес устройства  и значение счетчика итераций
                        result = self.modbus(ip, count = self.counter)
                        if isinstance(result, str):
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
            # Если число итераций цикла рано двум
            if self.count == 2:
                # Обнуляем счетчик
                self.count = 0
                # Закрываем SNMP Manager
                self.manager.close()
                # Запускаем SNMP Manager
                self.manager = Manager(b'public', version=1)
                # Увеличиваем счетчик на 1
                self.counter += 1
            self.sleep(self.interval_time)
            # Увеличиваем счетчик на 1
            self.count += 1
    
    # Метод останавливает работу SNMP Manager-а
    def snmp_stop(self) -> None:
        try:
            self.manager.close()
        except AttributeError:
            pass


if __name__ == '__main__':
    snmp = ThreadSNMPAsk()
    print(snmp.forpost_2('10.204.50.4', block=True))
    #ls = []
    #for i in range(10):
        #print(snmp.forpost('10.192.50.114', flag=True))
        #time.sleep(10)
    #print('Total:', ls[1] - ls[0])
    
    

