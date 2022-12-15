#
import time
#import os
#import sys
import sqlite3
from pathlib import Path
from snmp import Manager
#from snmp import exceptions
from snmp.exceptions import Timeout
from snmp.v1.exceptions import NoSuchName
# Импортируем классс QThread отвечающий за многопоточность в PYQT
from PyQt5.QtCore import QThread
from class_ClientModbus import ClientModbus
from class_SqlLiteMain import ConnectSqlDB

class ThreadSNMPAsk(QThread, ClientModbus):
    def __init__(self):
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
    
        # Переменная определяет время между запросами цикла while
        self.interval_time = 5
        #
        self.snmp_trap = []
        #
        self.counter = 1
        # Переменная queue, которой присваиваем значение экземпляр класса queue ( обработчик очередей) полученной
        # при вызове данного класса
        #self.queue = queue
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
        # MAC&C OIDs
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
    def get_request(self, ip, oids, block, timeout, next):
        if block:
            self.manager = Manager(b'public', version=1, port=161)
        try:
            # Значение block=False, говорит что мы не дожидаемся результата, а получим его при следующем запросе
            out = self.manager.get(ip, *oids, next=next, timeout=timeout, block=block)
            if block:
                self.manager.close()
            return out
        except Timeout as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            # Логирование, записывает в файл logs_snmp_ask.txt
            self.logger.info(f'Ошибка Timeout - не получен ответ от устройства {ip}')
           # Если flag истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
            return error
        except NoSuchName as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger.info(f'Ошибка NoSuchName - не существующая переменная {err}: {ip}')
            # Если flag истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
            return error
        except AttributeError as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger.info(f'Ошибка AttributeError - SNMP Manager не запущен, в запросе не передан flag=True: {ip}')
            # Если flag истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
            return error
        except OSError as err:
            # Если flag истина, то закрываем SNMP поток. 
            if block:
                self.manager.close()
            return str(err)
        
    def macc(self, ip, timeout=10, next = True, block = False):
        #
        values = []
        oids = [self.f10GFx2DDTemp, self.f10GFx2DDTxPWR, self.f10GFx2DDRxPWR, self.f10GFx3DDTemp, self.f10GFx3DDTxPWR, self.f10GFx3DDRxPWR]
        # Делаем запрос GETNEX получаем список данных типа snmp.types.VarBind
        out = self.get_request(ip, oids, block, timeout, next)
        #
        if type(out) is list and None not in out:
            # Перебираем список по переменной типа VarBind
            for var_bind in out:
                # Используем метод values, получаем из VarBind данные типа snmp.types.OCTET_STRING, значение в которой в байтах
                snmp_octet_string = var_bind.values
                # Используем метод value получаем из OCTET_STRING значение в байтах преобразуем его в строку и добавляем в список values
                values.append(snmp_octet_string[-1].value.decode())
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; TxFiber2: {values[1]} dBm; RxFiber2: {values[2]} dBm; TempFiber2: {values[0]} *C; TxFiber3: {values[4]} dBm; RxFiber3: {values[5]} dBm; TempFiber3: {values[3]} *C" 
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    def eltek(self, ip, timeout=10, next = True, block = False):
        # Формируем список oid для запроса
        oids = [self.ac_volt1, self.batt_out_volt, self.rect_total_curr, self.rect_stat_temp]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распоковываем полученный список
            inp_volt, out_volt, load, temp = out
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/100} V ({load.values[-1].value} А); *C: {temp.values[-1].value}"  
            # Возвращаем результат
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    def forpost_2(self, ip, timeout=10, next = False, block = False):
        # Формируем список oid для запроса
        oids = [self.load_A, self.temp, self.load_V, self.out_V, self.batt, self.inp_V]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распоковываем полученный список 
            load, temp, _, out_volt, batt, inp_volt = out 
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/10} V ({(load.values[-1].value)/10} А). Batt: {batt.values[-1].value}%. *C: {temp.values[-1].value}"  
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error
        
    def forpost(self, ip, timeout=10, next = False, block = False):
        # Формируем список oid для запроса
        oids = [self.load_Amp, self.tmp, self.load_Vol, self.betery, self.inp_Volt]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распаковываем список с полученными данными
            load, temp, out_volt, batt, inp_volt = out 
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/10} V ({(load.values[-1].value)/10} А); Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    def forpost_3(self, ip, timeout=10, next = False, block = False):
        # Формируем список oid для запроса
        oids = [self.load_Amp, self.tmp, self.load_Vol, self.inp_Volt]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распаковываем список с полученными данными
            load, temp, out_volt, inp_volt = out 
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/10} V ({(load.values[-1].value)/10} А); *C: {temp.values[-1].value}" 
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    def eaton(self, ip, timeout=10, next = False, block = False):
        # Формируем список oid для запроса
        oids = [self.power, self.load, self.out, self.inp, self.battery, self.temperature]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распоковываем полученный список
            power, load, out_volt, inp_volt, batt, temp = out
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {out_volt.values[-1].value} V; Load: {load.values[-1].value}% ({power.values[-1].value} WT); Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    def sc200(self, ip, timeout=10, next = False, block = False):
        # Формируем список oid для запроса
        oids = [self.load_Am, self.out_Vol, self.inp_Vol, self.temper]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распоковываем полученный список
            load, out_volt, inp_volt, temp = out
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {(out_volt.values[-1].value)/100} V Load: ({load.values[-1].value}A); *C: {temp.values[-1].value}" 
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    def legrand(self, ip, timeout=10, next = False, block = False):
        # Формируем список oid для запроса
        oids = [self.out, self.inp, self.tmprt, self.battery]
        # Делаем запрос, вызвав метод get_request результат записываем в переменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распоковываем полученный список 
            out_volt, inp_volt, temp, batt = out
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {out_volt.values[-1].value} V Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    def apc(self, ip, timeout=10, next = False, block = False):
        # Формируем список oid для запроса
        oids = [self.output_load, self.output_voltage, self.inpu_Voltage, self.batt_temp, self.batt_capacity]
        # Делаем GET запрос, получаем список данных типа VarBind и записываем в перенменную out
        out = self.get_request(ip, oids, block, timeout, next)
        # Если полученный результат список И полученный список не содержит None
        if type(out) is list and None not in out:
            # Распоковываем полученный список 
            load, out_volt, inp_volt, temp, batt = out
            # Формируем строку результата
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; IN: {inp_volt.values[-1].value} V; OUT: {out_volt.values[-1].value} V; Load: {load.values[-1].value}%; Batt: {batt.values[-1].value}%; *C: {temp.values[-1].value}" 
            return result
        # Если тип ответа строка 
        elif type(out) is str:
            return out
        # Если количество запросов одного и тогоже устройства равно 2
        elif self.count == 2:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            return error

    # Метод запускает SNMP опрощик
    def run(self):
        # Счетчик записываем количество итераций сделанных циклом while
        self.counter = 1
        # Количество SNMP запрсов 
        self.count = 1
        # Запускаем SNMP Менеджер
        self.manager = Manager(b'public', version=1)
        while True:
            # Создаем переменную в которую будем сохранять результаты snmp
            self.snmp_trap = []
            # Создаем экземпляр класса
            with ConnectSqlDB() as sql:
                try:
                    # Делаем запрос к БД, получить список значений oid и ip из таблицы Devices
                    data_base = sql.get_values_list_db('model', 'ip', table='Devices')
                except (sqlite3.IntegrityError, sqlite3.OperationalError):
                    self.logger.error("Ошибка запроса из БД: sql.get_values_list_db('model', 'ip', table='Devices')" )
            if data_base:
                # Перебираем данные словаря по ключам
                for model, ip in data_base:
                    # Делаем проверку если ключ словаря сопал с названием метода
                    if model == 'forpost':
                        # Вызываем метод forpost передавая ему ip адрес устройства
                        result = self.forpost(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'forpost_2':
                        # Вызываем метод forpost_2 передавая ему ip адрес устройства
                        result = self.forpost_2(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'forpost_3':
                        # Вызываем метод forpost_3 передавая ему ip адрес устройства
                        result = self.forpost_3(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'eaton':
                        # Вызываем метод eaton передавая ему ip адрес устройства
                        result = self.eaton(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'sc200':
                        # Вызываем метод sc200 передавая ему ip адрес устройства
                        result = self.sc200(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'legrand':
                        # Вызываем метод legrand передавая ему ip адрес устройства
                        result = self.legrand(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'apc':
                        # Вызываем метод apc передавая ему ip адрес устройства
                        result = self.apc(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'eltek':
                        # Вызываем метод eltek передавая ему ip адрес устройства
                        result = self.eltek(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'macc':
                        # Вызываем метод macc передавая ему ip адрес устройства
                        result = self.macc(ip)
                        if result:
                            # Добавляем результат в список snmp_trap
                            self.snmp_trap.append(result)
                    elif model == 'modbus':
                        # Вызываем метод modbus передавая ему ip адрес устройства  и значение счетчика итераций
                        result = self.modbus(ip, count = self.counter)
                        if type(result) is tuple:
                            # Преобразуем кортеж в список и объеденяем со списком snmp_trap
                            self.snmp_trap += list(result)
                        else:
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
    def snmp_stop(self):
        try:
            self.manager.close()
        except AttributeError:
            pass


if __name__ == '__main__':
    snmp = ThreadSNMPAsk()
    snmp.run()
    #ls = []
    #for i in range(10):
        #print(snmp.forpost('10.192.50.114', flag=True))
        #time.sleep(10)
    #print('Total:', ls[1] - ls[0])
    
    

