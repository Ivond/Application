#
from typing import Union, Tuple, Optional
import random
from class_SqlLiteMain import ConnectSqlDB
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_alarms

class MACCAlarmHandler(ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        # Записываем дефолтное(начальное) значение уровня сигнала Fiber транспондера MAC&C
        self.signal_level_fiber = -22
        # Записываем дефолтное(начальное) значение низкой температуры Fiber транспондера MAC&C
        self.low_temp_fiber = 0
        # Записываем дефолтное(начальное) значение высокой температуры Fiber транспондера MAC&C
        self.hight_temp_fiber = 50 
        
    # Метод устанавливает пороговые значения сработки аврии      
    def _set_threshold_value_alarms(self) -> None:
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос к БД, на получение порогового значения низкой температуры SFP-модуля
            low_temp_fiber = sql.get_db('num', alarms='monitor_low_temp_fiber', table='Settings')[0]
            if isinstance(low_temp_fiber, int):
                self.low_temp_fiber =low_temp_fiber
            # Делаем запрос к БД, на получение порога значения высокой температуры SFP-модуля
            hight_temp_fiber = sql.get_db('num', alarms='monitor_hight_temp_fiber', table='Settings')[0]
            if isinstance(hight_temp_fiber, int):
                self.hight_temp_fiber = hight_temp_fiber
            # Делаем запрос к БД, на получение порога значения низкого уровня сигнала SFP-модуля
            signal_level_fiber = sql.get_db('num', alarms='monitor_signal_level', table='Settings')[0]
            if isinstance(signal_level_fiber, int):
                self.signal_level_fiber = signal_level_fiber
    
    # ПРОВЕРКА ПАРАМЕТРОВ MAC&C
    def alarm_handler(self, line: str) -> Union[str, None]:
        # Вызываем метод, который устанавливает пороговые значения возниконовения аварии
        self._set_threshold_value_alarms()
        # Вылавливаем исключение, когда при запущенном приложение мы удаляем устройство из БД
        try:
            # Получаем значение ip адреса вызвав метод _parse_ip
            ip = self._parse_ip(line)
            # Если тип переменной ip строка
            if isinstance(ip, str):
                # Вызываем метод, передаем на вход ip адрес устройства, метод возращает строковое значение места установки
                name = self._get_name(ip)
        # Попали в исключение, значит ip адрес устройство уже удален, пропускаем все действия ниже
        except TypeError:
            return None
        # Вызываем метод передаем строку, метод возвращает кортеж из строковых значений(дата и параметры устройства)
        params = self._parse_message(line)
        if isinstance(params, tuple):
            # Распаковываем кортеж params на дату и строку с параметрами
            date, macc_parametrs = params
        # Формируем случайным образом номер ID сообщения
        id = random.randint(3001, 4000)

    # ПРОВЕРКА УРОВНЯ СИГНАЛА FIBER2 И FIBER3
        if 'TxFiber2' in line and 'TxFiber3' in line and isinstance(date, str) and isinstance(macc_parametrs, str):
            # Вызываем метод получаем значение TX сигнала SFP_2 модуля
            tx_fiber2 = self._parse_tx_fiber2(line)
            # Вызываем метод получаем значение Tx сигнала SFP_3 модуля
            tx_fiber3 = self._parse_tx_fiber3(line)
            # Вызываем метод получаем значение Rx сигнала SFP_2 модуля
            rx_fiber2 = self._parse_rx_fiber2(line)
            # Вызываем метод получаем значение Rx сигнала SFP_3 модуля
            rx_fiber3 = self._parse_rx_fiber3(line)
            # Вызываем метод получаем значение температуры SFP_2 модуля
            temp_fiber2 = self._parse_temp_fiber2(line)
            # Вызываем метод получаем значение температуры SFP_3 модуля
            temp_fiber3 = self._parse_temp_fiber3(line)
            #
            if isinstance(rx_fiber2, str) and isinstance(rx_fiber3, str) and isinstance(tx_fiber3, str) and isinstance(tx_fiber2, str) and isinstance(ip, str):
                # Если значения уровня приемного и передающего сигналов меньше порога И тип переменной ip строка И IP нет в словаре аварий                           
                if (int(rx_fiber2) < self.signal_level_fiber or int(rx_fiber3) < self.signal_level_fiber or int(tx_fiber2) < self.signal_level_fiber \
                    or int(tx_fiber3) < self.signal_level_fiber) and ip not in dict_alarms['low_signal_power']:
                    #
                    if int(rx_fiber2) < self.signal_level_fiber:
                        # Меняем стиль на жирный шрифт значения переменной RxFiber2 
                        macc_parametrs = macc_parametrs.replace('RxFiber2: {} dBm'.format(rx_fiber2), '<b>RxFiber2: {} dBm</b>'.format(rx_fiber2))
                        # Формируем сообщение которое отпавим пользователю
                        message = f"{date} {name}: <b>Низкий уровень сигнала транспондера MAC&C</b> {macc_parametrs} ID:{id}"
                    if int(rx_fiber3) < self.signal_level_fiber:
                        # Формируем сообщение которое отпавим пользователю и меняем стиль на жирный шрифт значения переменной RxFiber3 
                        message = f"{date} {name}: <b>Низкий уровень сигнала транспондера MAC&C</b> {macc_parametrs.replace('RxFiber3: {} dBm'.format(rx_fiber3), '<b>RxFiber3: {} dBm</b>'.format(rx_fiber3))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['low_signal_power'][ip] = message
                    return message
                
                # Если значения уровня приемного и передающего сигналов выше порога И IP адрес есть в словаре аварий
                elif (int(rx_fiber2) > self.signal_level_fiber and int(rx_fiber3) > self.signal_level_fiber and \
                    int(tx_fiber2) > self.signal_level_fiber and int(tx_fiber3) > self.signal_level_fiber) and ip in dict_alarms['low_signal_power']:
                    #             
                    message = f"{date} {name}: <b>Уровень сигнала транспондера MAC&C восстановлен</b>: {macc_parametrs}."
                    # Удаляем сообщение об аварии из dict_alarms
                    del dict_alarms['low_signal_power'][ip]
                    return message
        
        # ПРОВЕРКА ВЫСОКОЙ ТЕМПЕРАТУРЫ FIBER2 И FIBER3
            # Если тип переменных число И значение выше порога И тип переменной ip число И IP нет в словаре аварий
            if isinstance(temp_fiber2, str) and isinstance(temp_fiber3, str) and isinstance(ip, str):
                #
                if (int(temp_fiber2) > self.hight_temp_fiber or int(temp_fiber3) > self.hight_temp_fiber) and ip not in dict_alarms['hight_temp_macc']:
                    #
                    if int(temp_fiber2) > self.hight_temp_fiber:
                        # Меняем стиль на жирный шрифт значения переменной TempFiber2 
                        macc_parametrs = macc_parametrs.replace('TempFiber2: {} *C'.format(temp_fiber2), '<b>TempFiber2: {} *C</b>'.format(temp_fiber2))
                        # Формируем сообщение которое отправим пользователю
                        message = f"{date} {name}: <b>Высокая температура транспондера MAC&C</b> {macc_parametrs} ID:{id}"
                    if int(temp_fiber3) > self.hight_temp_fiber:
                        # Формируем сообщение которое отправим пользователю изменив стиль на жирный шрифт значения переменной TempFiber3 
                        message = f"{date} {name}: <b>Высокая температура транспондера MAC&C</b> {macc_parametrs.replace('TempFiber3: {} *C'.format(temp_fiber3), '<b>TempFiber3: {} *C</b>'.format(temp_fiber3))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['hight_temp_macc'][ip] = message
                    return message
                # Если значение меньше порога на 3 И ip есть в словаре аварий
                elif int(temp_fiber2) < (self.hight_temp_fiber - 3) and int(temp_fiber3) < (self.hight_temp_fiber - 3) and ip in dict_alarms['hight_temp_macc']:
                    # Удаляем аврию из словаря dict_alarms
                    del dict_alarms['hight_temp_macc'][ip]

            # ПРОВЕРКА НИЗКОЙ ТЕМПЕРАТУРЫ FIBER2 И FIBER3
                if (int(temp_fiber2) < self.low_temp_fiber or int(temp_fiber3) < self.low_temp_fiber) and ip not in dict_alarms['low_temp_macc']:
                    #
                    if int(temp_fiber2) < self.low_temp_fiber:
                        # Выделяем жирным шрифтом значение переменной TempFiber2 
                        macc_parametrs = macc_parametrs.replace('TempFiber2: {} *C'.format(temp_fiber2), '<b>TempFiber2: {} *C</b>'.format(temp_fiber2))
                        # Формируем сообщение которое отпавим пользователю
                        message = f"{date} {name}: Низкая температура транспондера MAC&C: {macc_parametrs} ID:{id}"
                    if int(temp_fiber3) < self.low_temp_fiber:
                        # Формируем сообщение которое отпавим пользователю, изменив стиль на жирный шрифт значения переменной TempFiber2 
                        message = f"{date} {name}: Низкая температура транспондера MAC&C: {macc_parametrs.replace('TempFiber3: {} *C'.format(temp_fiber3), '<b>TempFiber3: {} *C</b>'.format(temp_fiber3))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['low_temp_macc'][ip] = message
                    return message
                # Если тип переменых число И значение выше порога на 3 И ip-адрес есть в словаре аварий
                elif int(temp_fiber2) > (self.low_temp_fiber + 3) and int(temp_fiber3) > (self.low_temp_fiber + 3) and ip in dict_alarms['low_temp_macc']:
                    # Удаляем аврию из словаря dict_alarms
                    del dict_alarms['low_temp_macc'][ip]

        if 'TxFiber1' in line and 'TxFiber3' in line and isinstance(date, str) and isinstance(macc_parametrs, str):
            # Вызываем метод получаем значение TX сигнала SFP_2 модуля
            tx_fiber1 = self._parse_tx_fiber1(line)
            # Вызываем метод получаем значение Tx сигнала SFP_3 модуля
            tx_fiber3 = self._parse_tx_fiber3(line)
            # Вызываем метод получаем значение Rx сигнала SFP_2 модуля
            rx_fiber1 = self._parse_rx_fiber1(line)
            # Вызываем метод получаем значение Rx сигнала SFP_3 модуля
            rx_fiber3 = self._parse_rx_fiber3(line)
            # Вызываем метод получаем значение температуры SFP_2 модуля
            temp_fiber1 = self._parse_temp_fiber1(line)
            # Вызываем метод получаем значение температуры SFP_3 модуля
            temp_fiber3 = self._parse_temp_fiber3(line)
            #
            if isinstance(rx_fiber1, str) and isinstance(rx_fiber3, str) and isinstance(tx_fiber3, str) and isinstance(tx_fiber1, str) and isinstance(ip, str):
                # Если значения уровня приемного и передающего сигналов меньше порога И тип переменной ip строка И IP нет в словаре аварий                           
                if (int(rx_fiber1) < self.signal_level_fiber or int(rx_fiber3) < self.signal_level_fiber or int(tx_fiber1) < self.signal_level_fiber \
                    or int(tx_fiber3) < self.signal_level_fiber) and ip not in dict_alarms['low_signal_power']:
                    # 
                    if int(rx_fiber1) < self.signal_level_fiber:
                        # Меняем стиль на жирный шрифт значения переменной RxFiber2 
                        macc_parametrs = macc_parametrs.replace('RxFiber1: {} dBm'.format(rx_fiber1), '<b>RxFiber1: {} dBm</b>'.format(rx_fiber1))
                        # Формируем сообщение которое отпавим пользователю
                        message = f"{date} {name}: <b>Низкий уровень сигнала транспондера MAC&C</b> {macc_parametrs} ID:{id}"
                    if int(rx_fiber3) < self.signal_level_fiber:
                        # Формируем сообщение которое отпавим пользователю и меняем стиль на жирный шрифт значения переменной RxFiber3 
                        message = f"{date} {name}: <b>Низкий уровень сигнала транспондера MAC&C</b> {macc_parametrs.replace('RxFiber3: {} dBm'.format(rx_fiber3), '<b>RxFiber3: {} dBm</b>'.format(rx_fiber3))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['low_signal_power'][ip] = message
                    return message
                
                # Если значения уровня приемного и передающего сигналов выше порога И IP адрес есть в словаре аварий
                if (int(rx_fiber1) > self.signal_level_fiber and int(rx_fiber3) > self.signal_level_fiber and \
                    int(tx_fiber1) > self.signal_level_fiber and int(tx_fiber3) > self.signal_level_fiber) and ip in dict_alarms['low_signal_power']:
                    #            
                    message = f"{date} {name}: <b>Уровень сигнала транспондера MAC&C восстановлен</b>: {macc_parametrs}."
                    # Удаляем сообщение об аварии из dict_alarms
                    del dict_alarms['low_signal_power'][ip]
                    return message
        
        # ПРОВЕРКА ВЫСОКОЙ НИЗКОЙ ТЕМПЕРАТУРЫ FIBER2 И FIBER3

            # Если тип переменных число И значение выше порога И тип переменной ip число И IP нет в словаре аварий
            if isinstance(temp_fiber1, str) and isinstance(temp_fiber3, str) and isinstance(ip, str):
                if (int(temp_fiber1) > self.hight_temp_fiber or int(temp_fiber3) > self.hight_temp_fiber) and ip not in dict_alarms['hight_temp_macc']:
                    #
                    if int(temp_fiber1) > self.hight_temp_fiber:
                        # Меняем стиль на жирный шрифт значения переменной TempFiber2 
                        macc_parametrs = macc_parametrs.replace('TempFiber1: {} *C'.format(temp_fiber1), '<b>TempFiber1: {} *C</b>'.format(temp_fiber1))
                        # Формируем сообщение которое отправим пользователю
                        message = f"{date} {name}: <b>Высокая температура транспондера MAC&C</b> {macc_parametrs} ID:{id}"
                    if int(temp_fiber3) > self.hight_temp_fiber:
                        # Формируем сообщение которое отправим пользователю изменив стиль на жирный шрифт значения переменной TempFiber3 
                        message = f"{date} {name}: <b>Высокая температура транспондера MAC&C</b> {macc_parametrs.replace('TempFiber3: {} *C'.format(temp_fiber3), '<b>TempFiber3: {} *C</b>'.format(temp_fiber3))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['hight_temp_macc'][ip] = message
                    return message
                # Если тип переменных число И значение меньше порога на 3 И ip есть в словаре аварий
                elif int(temp_fiber1) < (self.hight_temp_fiber - 3) and int(temp_fiber3) < (self.hight_temp_fiber - 3) and ip in dict_alarms['hight_temp_macc']:
                    # Удаляем аврию из словаря dict_alarms
                    del dict_alarms['hight_temp_macc'][ip]

            # ПРОВЕРКА НИЗКОЙ ТЕМПЕРАТУРЫ FIBER2 И FIBER3
                # Если значение меньше порогового И ip-адреса нет в словаре
                if (int(temp_fiber1) < self.low_temp_fiber or int(temp_fiber3) < self.low_temp_fiber) and ip not in dict_alarms['low_temp_macc']:
                    #
                    if int(temp_fiber1) < self.low_temp_fiber:
                        # Выделяем значение переменной TempFiber2 жирным шрифтом
                        macc_parametrs = macc_parametrs.replace('TempFiber1: {} *C'.format(temp_fiber1), '<b>TempFiber1: {} *C</b>'.format(temp_fiber1))
                        # Формируем сообщение которое отправим пользователю
                        message = f"{date} {name}: Низкая температура транспондера MAC&C: {macc_parametrs} ID:{id}"
                    if int(temp_fiber3) < self.low_temp_fiber:
                        # Формируем сообщение которое отпавим пользователю, выделяем значение переменной TempFiber3 жирным шрифтом 
                        message = f"{date} {name}: Низкая температура транспондера MAC&C: {macc_parametrs.replace('TempFiber3: {} *C'.format(temp_fiber3), '<b>TempFiber3: {} *C</b>'.format(temp_fiber3))} ID:{id}"
                    # Добавляем данные об аварии в dict_alarms
                    dict_alarms['low_temp_macc'][ip] = message
                    return message
                # Если тип переменых число И значение выше порога на 3 И ip-адрес есть в словаре аварий
                elif int(temp_fiber1) > (self.low_temp_fiber + 3) and int(temp_fiber3) > (self.low_temp_fiber + 3) and ip in dict_alarms['low_temp_macc']:
                    # Удаляем аврию из словаря dict_alarms
                    del dict_alarms['low_temp_macc'][ip]
        return None
        
if __name__ == "__main__":

    macc_handler = MACCAlarmHandler()
