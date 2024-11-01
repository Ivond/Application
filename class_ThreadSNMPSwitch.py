#
from __future__ import annotations
from typing import Optional, List, Union, Any, Tuple
import time
import logging
from pathlib import Path
from snmp import Manager
from snmp.types import VarBind
from snmp.exceptions import Timeout
from snmp.v1.exceptions import NoSuchName
# Импортируем классс QThread отвечающий за многопоточность в PYQT
from PyQt5.QtCore import QThread
from class_SqlLiteMain import ConnectSqlDB
from class_MashineLearning import MashineLearning
from class_MashineLearningLoadLow import MashineLearningLoadLow

class ThreadSNMPSwitch(QThread):
    def __init__(self) -> None:
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
        # Настройка логирования
        #self.path_logs = Path(Path.cwd(), "logs", "logs_snmp_switch.txt")
        self.logger_snmp = logging.getLogger('class_ThreadSNMPSwitch')
        logging.basicConfig(#filename=Path(Path.cwd(),"GGS", "logs_v640.txt"), 
            #filemode='w', 
            format = '%(asctime)s %(name)s: %(lineno)d: %(message)s', 
            datefmt='%d-%m-%y',
            level=logging.INFO)
        #self.path_logs = Path(Path.cwd(), "logs", "logs_snmp_switch.txt")
        #self.logger_snmp = logging.getLogger('snm_switch')
        #self.logger_snmp.setLevel(logging.INFO)
        #fh_logs = logging.FileHandler(self.path_logs, 'w')
        #formatter_logs = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
        #fh_logs.setFormatter(formatter_logs)
        #self.logger_snmp.addHandler(fh_logs)
        
        # Создаем экземпляр класса MashineLearning
        self.ml = MashineLearning()
        #
        self.ml_low_load = MashineLearningLoadLow()

        # Переменная определяет время между запросами цикла while
        self.interval_time = 30

        # Флаг, сигнализирует если нет подключение к интернету.
        self.is_network_error = False

        self.counter  = 1
        #
        self.snmp_switch_trap: List[str] = []
        # Cisco
        self.ifOperStatus = '1.3.6.1.2.1.2.2.1.8.' # (up(1), down(2), testing(3))
        self.ifOutOctets = '1.3.6.1.2.1.2.2.1.16.' # ifOutOctets
        self.ifInOctets = '1.3.6.1.2.1.2.2.1.10.' # ifInOctets
        self.OperTimeoutSLA = '1.3.6.1.4.1.9.9.42.1.2.9.1.6.'

    ''' 
    GetRequest - запрос к агенту от менеджера, используемый для получения значения одной или нескольких переменных.
    GetNextRequest - запрос к агенту от менеджера, используемый для получения следующего в иерархии значения переменной.
    '''
    # Метод делает запрос по протоколу SNMP, принимает на вход ip и набор oids для определенного типа устройства.
    def get_request(self, ip: str, oids: List[str], flag: bool, timeout: int, next: bool, port: int) -> Union[List[Any], str]:
        if flag:
            self.manager = Manager(b'public', version=1, port=161)
        try:
            out: List[Any] = self.manager.get(ip, *oids, next=next, timeout=timeout)
            if flag:
                self.manager.close()
            return out
        except Timeout:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Count: {self.counter}; Number: {port}; CISCO_SNMP:REQEST_ERROR1"
            # Логирование, записывает в файл logs_snmp_ask.txt
            #self.logger_snmp.info(f'Ошибка Timeout - не получен ответ от устройства {ip}')
           # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except NoSuchName as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} CISCO_SNMP:REQEST_ERROR1"
            self.logger_snmp.info(f'Ошибка NoSuchName - не существующая переменная {err}: {ip}')
            # Если flag истина, то закрываем SNMP поток. 
            if flag:
                self.manager.close()
            return error
        except AttributeError as err:
            # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
            error = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} CISCO_SNMP:REQEST_ERROR1"
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
    def cisco(
        self, 
        ip: str, 
        port: Optional[int], 
        sla: Optional[int], 
        load: Optional[int], 
        icmp_echo: Optional[int], 
        timeout: int =10, 
        next: bool = True, 
        flag: bool = False
    ) -> Optional[str]:
        
        # Формируем словрь списков в который будем подставлять полученные значение количетсва трафика
        sample = {'inbound': [0], 
                  'outbound': [0]}
        # Если тип переменных port и sla числа
        if isinstance(sla, int) and isinstance(port, int):
            # Т.к. значение index которое необходимо передать для запроса на один меньше значения sla проводим корректировку 
            index_sla = str(sla-1)
            # Т.к. значение index которое необходимо передать для запроса на один меньше значения порта проводим корректировку 
            index =str(port-1)
            # Формируем список запроса из OID
            oids = [f"{self.ifOutOctets}{index}", f"{self.ifInOctets}{index}", f"{self.ifOperStatus}{index}", f"{self.OperTimeoutSLA}{index_sla}"]
            # Делаем запрос GETNEX получаем список данных типа snmp.types.VarBind
            out = self.get_request(ip, oids, flag, timeout, next, port)
            # Если тип переменной "out" список И список не пустой
            if isinstance(out, list) and out:
                # Распаковываем список с полученными данными
                out_octet, in_octet, oper_status, ip_sla = out
                # Вызываем метод, передаем ему полученное значение ip_sla, возвращает значение sla status
                sla_status = self._get_sla_status(ip_sla)
                # Вызываем метод который возвращает кортеж с параметрами порта коммутатора
                status, in_octets, out_octets = self._get_port_values(out_octet, in_octet, oper_status)
                # Вызываем метод который возвращает текущее количество входящего трафика на порту (значение берем по модулю)
                in_bit_sec = abs(self.in_traffic_count(ip, port, in_octets))
                # Добавляем полученное значение в словарь
                sample['inbound']=[in_bit_sec]
                # Вызываем метод который возвращает текущее количество входящего трафика в красивом виде
                pretty_in_bit_sec = self.pretty_counters(in_bit_sec)
                # Вызываем метод который возвращает текущее количество исходящего трафика на порту
                out_bit_sec = abs(self.out_traffic_count(ip, port, out_octets))
                # Добавляем полученное значеие в словарь списков
                sample['outbound']=[out_bit_sec]
                # Вызываем метод который возвращает значени количества исходящего трафика в красивом виде
                pretty_out_bit_sec = self.pretty_counters(out_bit_sec)
                # Если значение True
                if load:
                    # Просим нашу модель предсказать статус канала принимает на вход словарь списков
                    channel_status = self.ml_low_load.predict(sample)
                else:
                    # Просим нашу модель предсказать статус канала принимает на вход словарь списков
                    channel_status = self.ml.predict(sample)
                # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
                result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Port: {port}; Count {self.counter}; ChannelStatus: {channel_status}; SlaStatus: {sla_status}; OperStatus: {status}; InOctets: {pretty_in_bit_sec}; OutOctets: {pretty_out_bit_sec}" 
                return result
            elif isinstance(out, str):
                # Если is_network_error True
                if self.is_network_error:
                    return 
                # Возвращаем строку с ошибкой CiscoSNMPError
                return out
        # Если тип переменной port число
        elif isinstance(port, int):
            # Т.к. значение index которое необходимо передать для запроса на один меньше значения порта проводим корректировку 
            index =str(port-1)
            # Формируем список запроса из OID
            oids = [f"{self.ifOutOctets}{index}", f"{self.ifInOctets}{index}", f"{self.ifOperStatus}{index}"]
             # Делаем запрос GETNEX получаем список данных типа snmp.types.VarBind
            out = self.get_request(ip, oids, flag, timeout, next, port)
            # Если тип переменной "out" список И список не пустой
            if isinstance(out, list) and out:
                # Распаковываем список с полученными данными
                out_octet, in_octet, oper_status = out
                # Вызываем метод который возвращает кортеж со значениями параметров порта коммутатора
                status, in_octets, out_octets = self._get_port_values(out_octet, in_octet, oper_status)
                # Вызываем метод который возвращает текущее количество входящего трафика на порту (значение берем по модулю)
                in_bit_sec = abs(self.in_traffic_count(ip, port, in_octets))
                # Добавляем полученное значение в словарь
                sample['inbound']=[in_bit_sec]
                # Вызываем метод который возвращает значени количества входящего трафика в красивом виде
                pretty_in_bit_sec = self.pretty_counters(in_bit_sec)
                # Вызываем метод который возвращает текущее количество исходящего трафика на порту коммутатора
                out_bit_sec = abs(self.out_traffic_count(ip, port, out_octets))
                # Добавляем полученное значеие в словарь списков
                sample['outbound']=[out_bit_sec]
                # Вызываем метод который возвращает значени количества исходящего трафика в красивом виде
                pretty_out_bit_sec = self.pretty_counters(out_bit_sec)
                # Если значение True
                if load:
                    # Просим нашу модель предсказать статус канала принимает на вход словарь списков
                    channel_status = self.ml_low_load.predict(sample)
                else:
                    # Просим нашу модель предсказать статус канала принимает на вход словарь списков
                    channel_status = self.ml.predict(sample)
                # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
                result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Port: {port}; Count {self.counter}; ChannelStatus: {channel_status}; OperStatus: {status}; InOctets: {pretty_in_bit_sec}; OutOctets: {pretty_out_bit_sec}" 
                return result
            elif isinstance(out, str):
                # Возвращаем строку с ошибкой CiscoSNMPError
                return out
        # Если тип переменной число
        elif isinstance(sla, int):
            # Т.к. значение index которое необходимо передать для запроса на один меньше значения sla проводим корректировку 
            index_sla = str(sla-1)
            # Формируем список запроса из OID
            oids = [f"{self.OperTimeoutSLA}{index_sla}"]
            # Делаем запрос GETNEX получаем список данных типа snmp.types.VarBind
            out = self.get_request(ip, oids, flag, timeout, next, sla)
            # Если тип переменной "out" список И список не пустой
            if isinstance(out, list) and out:
                # Распаковываем список с полученными данными
                ip_sla = out[0]
                # Вызываем метод который возвращает значение sla status
                sla_status = self._get_sla_status(ip_sla)
                # Подставляем дату(перепреобразовав в нужный формат) и ip адрес
                result = f"{time.strftime('%d-%m-%Y %H:%M:%S', time.localtime())} {ip} Sla: {sla}; Count {self.counter}; ICMP_ECHO: {icmp_echo}; SlaStatus: {sla_status}" 
                return result
            elif isinstance(out, str):
                # Возвращаем строку с ошибкой CiscoSNMPError
                return out
        return None
    
    # Метод возвращает статус ip sla 
    def _get_sla_status(self, var_bind: Any) -> str:
        # Применяем к классу VarBind метод values, получаем класс snmp.types.OCTET_STRING, значение в байтах
        # применяем к классу OCTET_STRING метод value и получаем значение типа INTEGER
        # Если получили значение рано 1, значит статус порта UP
        if var_bind.values[-1].value == 1:
            sla_status = 'Down'
        # Если получили значение 2, значит статус порта DWN
        elif var_bind.values[-1].value == 2:
            sla_status = 'Up'
        return sla_status
    
    # Метод возвращает значение параметров порта коммутатора
    def _get_port_values(self, out_octet: VarBind, in_octet: VarBind, oper_status: VarBind) -> Tuple[str,int,int]:
        # Применяем к классу VarBind метод values, получаем класс snmp.types.OCTET_STRING, значение в байтах
        # применяем к классу OCTET_STRING метод value и получаем значение типа INTEGER
        if oper_status.values[-1].value == 1:
            status = 'Up'
        elif oper_status.values[-1].value == 2:
            status = 'Down'
        # Получаем значение входящего трафика
        in_octets = in_octet.values[-1].value
        # Получаем значение исходящего трафика
        out_octets = out_octet.values[-1].value
        return status, in_octets, out_octets
    
    # Метод вычисляет количество трафика на порту
    def in_traffic_count(self, ip_addr: str, port: int, in_octets: int) -> int:
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД получаем список кортежа из которого получаем количество входящего трафика 
            in_octets_before = sql.get_db('traffic_in', ip_addr=ip_addr, port=port, table='Ports')[0]
            if isinstance(in_octets_before, int):
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
    def out_traffic_count(self, ip_addr: str, port: int, out_octets: int) -> int:
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД получаем количество исходящего трафика 
            out_octets_before = sql.get_db('traffic_out', ip_addr=ip_addr, port=port, table='Ports')[0]
            if isinstance(out_octets_before, int):
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
    def pretty_counters(self, bit_sec: int) -> str:
        mbs = bit_sec // 10**6
        if mbs >=1:
            return f'{mbs} Mbs'
        kbs = bit_sec // 10**3
        if kbs >=1:
            return f'{kbs} Kbs'
        else:
            return f'{bit_sec} bs'

    # Метод запускает SNMP опрощик
    def run(self) -> None:
        # Счетчик записываем количество итераций сделанных циклом while
        self.counter = 1
        self.logger_snmp.info('Запускаю')
        while True:
            # Создаем соединение 
            with Manager(b'public', version=1) as self.manager:
                # Создаем переменную в которую будем сохранять результаты snmp
                self.snmp_switch_trap = []
                # Подключаемся к БД
                with ConnectSqlDB() as sql:
                    # Делаем запрос к БД, получить список значений ip_addr и port из таблицы Ports
                    data_base = sql.get_values_list_db('ip_addr', 'port', 'sla', 'loading', 'icmp_echo', table='Ports')
                if data_base:
                    # Перебираем данные словаря по ключам
                    for ip, port, sla, load, icmp_echo in data_base:
                        if isinstance(ip, str) and (isinstance(port, int) or port is None) \
                            and (isinstance(sla, int) or sla is None) and (isinstance(load, int) or load is None) \
                            and (isinstance(icmp_echo, int) or icmp_echo is None):
                            # Вызываем метод cisco передавая ему ip адрес устройства
                            result = self.cisco(ip, port, sla, load, icmp_echo)
                            if isinstance(result, str):
                                # Добавляем результат в список snmp_switch_trap
                                self.snmp_switch_trap.append(result)
            #
            self.sleep(self.interval_time)
            # Увеличиваем счетчик на 1
            self.counter += 1
        return None

    # Метод останавливает работу SNMP Manager-а
    def snmp_stop(self) -> None:
        try:
            self.manager.close()
        except AttributeError:
            return None
        else:
            return None

if __name__ == '__main__':
    snmp = ThreadSNMPSwitch()
    #print(snmp.cisco('10.0.129.10', 17, None, 0, 0, flag=True))
    #snmp.start()
