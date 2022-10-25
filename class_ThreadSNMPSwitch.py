#
import time
import logging
import sqlite3
from pathlib import Path
from snmp import Manager
from snmp.exceptions import Timeout
from snmp.v1.exceptions import NoSuchName
from datetime import datetime
# Импортируем классс QThread отвечающий за многопоточность в PYQT
from PyQt5.QtCore import QThread
from class_SqlLiteMain import ConnectSqlDB
from class_MashineLearning import MashineLearning
from class_MashineLearningLoadLow import MashineLearningLoadLow

class ThreadSNMPSwitch(QThread):
    def __init__(self):
        # Запускаем у класса QThread метод init
        QThread.__init__(self)

         # Настройка логирования
        self.path_logs = Path(Path.cwd(), "logs", "logs_snmp_switch.txt")
        self.logger_snmp = logging.getLogger('snm_switch')
        self.logger_snmp.setLevel(logging.INFO)
        fh_logs = logging.FileHandler(self.path_logs, 'w')
        formatter_logs = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        fh_logs.setFormatter(formatter_logs)
        self.logger_snmp.addHandler(fh_logs)

        # Создаем экземпляр класса MashineLearning
        self.ml = MashineLearning()
        #
        self.ml_low_load = MashineLearningLoadLow()

        # Переменная определяет время между запросами цикла while
        self.interval_time = 30
        #
        self.snmp_switch_trap = []
        # Cisco
        self.ifOperStatus = '1.3.6.1.2.1.2.2.1.8.' # (up(1), down(2), testing(3))
        self.ifOutOctets = '1.3.6.1.2.1.2.2.1.16.' # ifOutOctets
        self.ifInOctets = '1.3.6.1.2.1.2.2.1.10.' # ifInOctets

    ''' 
    GetRequest - запрос к агенту от менеджера, используемый для получения значения одной или нескольких переменных.
    GetNextRequest - запрос к агенту от менеджера, используемый для получения следующего в иерархии значения переменной.
    '''
    # Метод делает запрос по протоколу SNMP, принимает на вход ip и набор oids для определенного типа устройства.
    def get_request(self, ip, oids, flag, timeout, next):
        if flag:
            self.manager = Manager(b'public', version=1, port=161)
        try:
            out = self.manager.get(ip, *oids, next=next, timeout=timeout)
            if flag:
                self.manager.close()
            return out
        except Timeout:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; CISCO_SNMP:REQEST_ERROR"
            # Логирование, записывает в файл logs_snmp_ask.txt
            self.logger_snmp.info(f'Ошибка Timeout - не получен ответ от устройства {ip}')
           # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except NoSuchName as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger_snmp.info(f'Ошибка NoSuchName - не существующая переменная {err}: {ip}')
            # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except AttributeError as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} SNMP:REQEST_ERROR"
            self.logger_snmp.info(f'Ошибка AttributeError - SNMP Manager не запущен, в запросе не передан flag=True: {ip}')
            # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except OSError as err:
            # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return str(err)
    # Метод приимает на вход ip-адрес и порт устройства, флаг load (0 или 1) возвращает строку с параметрами
    def cisco(self, ip, port, load, timeout=10, next = True, flag = False):
        # Формируем словрь списков в который будем подставлять полученные значения трафика
        sample = {'inbound': [0], 
                  'outbound': [0]}
        # Т.к. значение index которое необходимо передать для запроса на один меньше значения порта проводим корректировку 
        index =str(int(port)-1)
        # Формируем список запроса из OID
        oids = [self.ifOutOctets+index, self.ifInOctets+index, self.ifOperStatus+index]
        # Делаем запрос GETNEX получаем список данных типа snmp.types.VarBind
        out = self.get_request(ip, oids, flag, timeout, next)
        # Проверяем, что тип переменной out список и что он не пустой
        if out and type(out) is list:
            for var_bind in out:
                # Используем метод values, получаем из VarBind данные типа snmp.types.OCTET_STRING, значение в байтах
                snmp_octet_string = var_bind.values
                # Если получили значение рано 1, значит статус порта UP
                if snmp_octet_string[-1].value == 1:
                    status = 'Up'
                # Если получили значение 2, значит статус порта DWN
                elif snmp_octet_string[-1].value == 2:
                    status = 'Down'
                # 
                elif self.ifInOctets+str(port) == snmp_octet_string[0]:
                    # Преобразуем полученное байтовое значение snmp_octet_string в строковое
                    in_octets = snmp_octet_string[-1].value
                    # Вызываем метод in_traffic_count, метод принимает на вход ip-адрес, номер порта и количество InOctets
                    # возвращает текущее количество входящего трафика на порту
                    in_bit_sec = abs(self.in_traffic_count(ip, port, in_octets))
                    sample['inbound']=[in_bit_sec]
                    #
                    pretty_in_bit_sec = self.pretty_counters(in_bit_sec)
                #
                elif self.ifOutOctets+str(port) == snmp_octet_string[0]:
                    # Преобразуем полученное байтовое значение snmp_octet_string в строковое
                    out_octets = snmp_octet_string[-1].value
                    # Вызываем метод out_traffic_count, метод принимает на вход ip-адрес, номер порта и количество OutOctets 
                    # метод возвращает текущее количество исходящего трафика на порту
                    out_bit_sec = abs(self.out_traffic_count(ip, port, out_octets))
                    # Добавляем значеие в словарь списков
                    sample['outbound']=[out_bit_sec]
                    #
                    pretty_out_bit_sec = self.pretty_counters(out_bit_sec)
            #dt = datetime.now()
            #hour = dt.hour
            # Добавляем значеие в словарь списков
            #sample['hour']=[hour]
            #minute = dt.minute
            # Добавляем значеие в словарь списков
            #sample['minute']=minute]
            # Если Истино
            if load:
                # Просим нашу модель предсказать статус канала принимает на вход словарь списков
                channel_status = self.ml_low_load.predict(sample)
            else:
                # Просим нашу модель предсказать статус канала принимает на вход словарь списков
                channel_status = self.ml.predict(sample)
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Port: {port}; Count {self.counter}; ChannelStatus: {channel_status}; OperStatus: {status}; InOctets: {pretty_in_bit_sec}; OutOctets: {pretty_out_bit_sec}" 
            return result
        else:
            return out
    
    # Метод вычисляет количество трафика на порту
    def in_traffic_count(self, ip_addr, port, in_octets):
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД получаем список кортежа из которого получаем количество входящего трафика 
            in_octets_before = sql.get_db('traffic_in', ip=ip_addr, port=port, table='Ports')[0][0]
            if in_octets_before:
                # Вычисляем количества трафика на порту отняв текущее значение от предыдущего
                in_bit_sec = in_octets - in_octets_before
                # Делаем запрос к БД таблица Ports обновляем значение количества входящего трафика
                sql.add_traffic('traffic_in', ip=ip_addr, port=port, traffic=in_octets)
                # Возвращаем значение количества трафика
                return in_bit_sec
            else:
                # Делаем запрос к БД таблица Ports добавляем значение количества трафика
                sql.add_traffic('traffic_in', ip=ip_addr, port=port, traffic=in_octets)
                # Возращаем то значение которое функция приняла на вход
                return in_octets
        
    # Метод вычисляет количество исходящего трафика на порту
    def out_traffic_count(self, ip_addr, port, out_octets):
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД получаем количество исходящего трафика 
            out_octets_before = sql.get_db('traffic_out', ip=ip_addr, port=port, table='Ports')[0][0]
            if out_octets_before:
                # Вычисляем количества исходящего трафика на порту отняв текущее значение от предыдущего
                out_bit_sec = out_octets - out_octets_before
                # Делаем запрос к БД таблица Ports обновляем значение количества входящего трафика
                sql.add_traffic('traffic_out', ip=ip_addr, port=port, traffic=out_octets)
                # Возвращаем значение количества трафика
                return out_bit_sec
            else:
                # Делаем запрос к БД таблица Ports добавляем значение количества трафика
                sql.add_traffic('traffic_out', ip=ip_addr, port=port, traffic=out_octets)
                # Возращаем то значение которое функция приняла на вход
                return out_octets

    # Метод преобразует значение из бит/c в Кбит/c или Мбит/c 
    def pretty_counters(self, bit_sec):
        mbs = bit_sec // 10**6
        if mbs >=1:
            return f'{mbs} Mbs'
        kbs = bit_sec // 10**3
        if kbs >=1:
            return f'{kbs} Kbs'
        else:
            return f'{bit_sec} bs'

    # Метод запускает SNMP опрощик
    def run(self):
        # Счетчик записываем количество итераций сделанных циклом while
        self.counter = 1
        while True:
            with Manager(b'public', version=1) as self.manager:
                # Создаем переменную в которую будем сохранять результаты snmp
                self.snmp_switch_trap = []
                try:
                    # Создаем экземпляр класса
                    with ConnectSqlDB() as sql:
                        # Делаем запрос к БД, получить список значений ip_addr и port из таблицы Ports
                        data_base = sql.get_values_list_db('ip_addr', 'port', 'loading', table='Ports')
                    if data_base:
                        # Перебираем данные словаря по ключам
                        for ip, port, load in data_base:
                            # Вызываем метод forpost передавая ему ip адрес устройства
                            result = self.cisco(ip, port, load)
                            # Добавляем результат в список snmp_switch_trap
                            self.snmp_switch_trap.append(result)
                #
                except (sqlite3.IntegrityError, sqlite3.OperationalError):
                    self.logger_snmp.error("Ошибка запроса из БД: sql.get_values_list_db('ip_addr', 'port', table='Ports')" )
            #
            self.sleep(self.interval_time)
            # Увеличиваем счетчик на 1
            self.counter += 1

    # Метод останавливает работу SNMP Manager-а
    def snmp_stop(self):
        try:
            self.manager.close()
        except AttributeError:
            pass

if __name__ == '__main__':
    snmp = ThreadSNMPSwitch()
    print(snmp.cisco('10.0.28.3', 42, flag=True))
    #snmp.start()
