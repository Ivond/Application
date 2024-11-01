#
from class_SqlLiteMain import ConnectSqlDB
import sqlite3
# Словарь для хранения записей аварий (Telegram Чат бот)
dict_alarms = {}
# Словарь для хранения промежуточных значений аварий (Telegram Чат бот)
dict_interim_alarms = {}
# Словарь для хранения записей аварий (Second window)
dict_wind_alarms = {}

# Подключаемся к БД
with ConnectSqlDB() as sql:
    try:
        # Делаем запрос к БД и получаем словарь с текущими авариями
        #dict_alarms = sql.get_values_dict_db('data', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['power_alarm'] = sql.get_values_dict_db('json_extract(data, "$.power_alarm")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_voltage'] = sql.get_values_dict_db('json_extract(data, "$.low_voltage")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['hight_temp'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['batt_disconnect'] = sql.get_values_dict_db('json_extract(data, "$.batt_disconnect")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms ['date'] = sql.get_values_dict_db('json_extract(data, "$.date")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_temp'] = sql.get_values_dict_db('json_extract(data, "$.low_temp")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['phase_alarm'] = sql.get_values_dict_db('json_extract(data, "$.phase_alarm")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_signal_power'] = sql.get_values_dict_db('json_extract(data, "$.low_signal_power")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['hight_temp_macc'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp_macc")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_temp_macc'] = sql.get_values_dict_db('json_extract(data, "$.low_temp_macc")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['error'] = sql.get_values_dict_db('json_extract(data, "$.error")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_level_oil'] = sql.get_values_dict_db('json_extract(data, "$.low_level_oil")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['channel'] = sql.get_values_dict_db('json_extract(data, "$.channel")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['sla'] = sql.get_values_dict_db('json_extract(data, "$.sla")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_batt'] = sql.get_values_dict_db('json_extract(data, "$.low_batt")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['switch_motor'] = sql.get_values_dict_db('json_extract(data, "$.switch_motor")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_level_water'] = sql.get_values_dict_db('json_extract(data, "$.low_level_water")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['hight_temp_water'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp_water")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_temp_water'] = sql.get_values_dict_db('json_extract(data, "$.low_temp_water")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['low_pressure_oil'] = sql.get_values_dict_db('json_extract(data, "$.low_pressure_oil")', table='Alarms')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_alarms['motor'] = sql.get_values_dict_db('json_extract(data, "$.motor")', table='Alarms')
    except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
        # Записываем значения аврий в словарь
        dict_alarms = {'power_alarm':{},
                        'low_voltage':{},
                        'hight_temp':{},
                        'low_temp':{},
                        'batt_disconnect':{},
                        'phase_alarm':{},
                        'date':{},
                        'low_signal_power':{},
                        'hight_temp_macc':{},
                        'low_temp_macc':{},
                        'error': {},
                        'low_level_oil':{},
                        'motor': {},
                        'low_pressure_oil': {},
                        'low_temp_water': {},
                        'hight_temp_water': {},
                        'low_level_water': {},
                        'switch_motor': {},
                        'low_batt': {},
                        'channel': {},
                        'sla': {},
                        }
        
    # ПРОМЕЖУТОЧНЫЕ ЗНАЧЕНИЯ АВАРИЙ
with ConnectSqlDB() as sql:
    try:
        # Делаем запрос к БД и получаем словарь с текущими авариями
        #dict_interim_alarms = sql.get_values_dict_db('data', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['power_alarm'] = sql.get_values_dict_db('json_extract(data, "$.power_alarm")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['low_voltage'] = sql.get_values_dict_db('json_extract(data, "$.low_voltage")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['hight_temp'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['low_temp'] = sql.get_values_dict_db('json_extract(data, "$.low_temp")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['hight_voltage'] = sql.get_values_dict_db('json_extract(data, "$.hight_voltage")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['battery_disconnect'] = sql.get_values_dict_db('json_extract(data, "$.battery_disconnect")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['batt_disconnect'] = sql.get_values_dict_db('json_extract(data, "$.batt_disconnect")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['low_signal_level'] = sql.get_values_dict_db('json_extract(data, "$.low_signal_level")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['hight_temp_macc'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp_macc")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['low_temp_macc'] = sql.get_values_dict_db('json_extract(data, "$.low_temp_macc")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['phase_alarm'] = sql.get_values_dict_db('json_extract(data, "$.phase_alarm")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['error'] = sql.get_values_dict_db('json_extract(data, "$.error")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями (количества топлива)
        dict_interim_alarms['low_level_oil'] = sql.get_values_dict_db('json_extract(data, "$.low_level_oil")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями (Низкое давление масла в ДГУ)
        dict_interim_alarms['low_pressure_oil'] = sql.get_values_dict_db('json_extract(data, "$.low_pressure_oil")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями (Экстренная остановка двигателя ДГУ)
        dict_interim_alarms['motor'] = sql.get_values_dict_db('json_extract(data, "$.motor")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями (Низкая температура О/Ж в ДГУ)
        dict_interim_alarms['low_temp_water'] = sql.get_values_dict_db('json_extract(data, "$.low_temp_water")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями ()
        dict_interim_alarms['low_batt'] = sql.get_values_dict_db('json_extract(data, "$.low_batt")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['low_level_water'] = sql.get_values_dict_db('json_extract(data, "$.low_level_water")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['hight_temp_water'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp_water")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['switch_motor'] = sql.get_values_dict_db('json_extract(data, "$.switch_motor")', table='Interim')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_interim_alarms['request_err'] = sql.get_values_dict_db('json_extract(data, "$.request_err")', table='Interim')
    except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
        # Если попали в исключение значит не смогли получить данные из БД, тогда подставляем словарь   
        dict_interim_alarms = { 'power_alarm':{},
                                'low_voltage':{},
                                'hight_temp':{},
                                'low_temp':{},
                                'hight_voltage':{},
                                'battery_disconnect':{},
                                'batt_disconnect':{},
                                'low_signal_level':{},
                                'hight_temp_macc':{},
                                'low_temp_macc':{},
                                'phase_alarm':{},
                                'error':{},
                                'low_level_oil':{},
                                'request_err':{},
                                'low_pressure_oil': {},
                                'motor': {},
                                'low_temp_water': {},
                                'low_level_water': {},
                                'hight_temp_water': {},
                                'switch_motor': {},
                                'low_batt': {},
                                }

with ConnectSqlDB() as sql:
    try:
        # Делаем запрос к БД и получаем словарь с текущими авариями
        #dict_wind_alarms = sql.get_values_dict_db('data', table='Duration')
        dict_wind_alarms['power_alarm'] = sql.get_values_dict_db('json_extract(data, "$.power_alarm")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_voltage'] = sql.get_values_dict_db('json_extract(data, "$.low_voltage")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['phase_alarm'] = sql.get_values_dict_db('json_extract(data, "$.phase_alarm")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['hight_temp'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['hight_voltage'] = sql.get_values_dict_db('json_extract(data, "$.hight_voltage")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_level_oil'] = sql.get_values_dict_db('json_extract(data, "$.low_level_oil")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['motor'] = sql.get_values_dict_db('json_extract(data, "$.motor")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_level_water'] = sql.get_values_dict_db('json_extract(data, "$.low_level_water")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_pressure_oil'] = sql.get_values_dict_db('json_extract(data, "$.low_pressure_oil")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_temp_water'] = sql.get_values_dict_db('json_extract(data, "$.low_temp_water")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['hight_temp_water'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp_water")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_batt'] = sql.get_values_dict_db('json_extract(data, "$.low_batt")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['switch_motor'] = sql.get_values_dict_db('json_extract(data, "$.switch_motor")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['request_err'] = sql.get_values_dict_db('json_extract(data, "$.request_err")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['channel'] = sql.get_values_dict_db('json_extract(data, "$.channel")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['sla'] = sql.get_values_dict_db('json_extract(data, "$.sla")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_signal_level'] = sql.get_values_dict_db('json_extract(data, "$.low_signal_level")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['low_temp_macc'] = sql.get_values_dict_db('json_extract(data, "$.low_temp_macc")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['hight_temp_macc'] = sql.get_values_dict_db('json_extract(data, "$.hight_temp_macc")', table='Duration')
        # Делаем запрос к БД и получаем словарь с текущими авариями
        dict_wind_alarms['battery_disconnect'] = sql.get_values_dict_db('json_extract(data, "$.battery_disconnect")', table='Duration')
    except (sqlite3.IntegrityError, sqlite3.OperationalError, TypeError):
        pass
        # Записываем значения аврий в словарь
        dict_wind_alarms = {'power_alarm':{},
                            'low_voltage':{},
                            'hight_temp':{},
                            'hight_voltage':{},
                            'battery_disconnect':{},
                            'phase_alarm':{},
                            'low_level_oil':{},
                            'motor':{},
                            'low_level_water': {},
                            'low_pressure_oil':{},
                            'low_temp_water':{},
                            'hight_temp_water': {},
                            'switch_motor':{},
                            'low_batt':{},
                            'request_err':{},
                            'channel': {},
                            'sla': {},
                            'low_signal_level':{},
                            'low_temp_macc':{},
                            'hight_temp_macc':{}
                            }

   