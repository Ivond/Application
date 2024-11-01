#
from __future__ import annotations
from typing import List, Dict, Any, Optional
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from SecondWindow import Ui_MainWindow
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtCore import QThread, Qt 
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QLabel, QMessageBox
from class_SqlLiteMain import ConnectSqlDB
from class_WindPlaySound import WindPlaySound
from class_ApplicationWidget import AplicationWidget
from class_WindTextSpeech import WindTextSpeech
from class_WindowUPSAlarmHandler import WindowUPSAlarmHandler
from class_WindowDGUAlarmHandler import WindowDGUAlarmHandler
from class_WindowMACCAlarmHandler import WindowMACCAlarmHandler
from class_WindowERRORAlarmHandler import WindowERRORAlarmHandler
from class_WindowPortSwitchHandler import WindowPortSwitchHandler
from class_WindowSLASwitchHandler import WindowSLASwitchHandler
from class_WindowThreePhaseUPSAlarmHandler import WindowThreePhaseUPSAlarmHandler
from class_ValueHandler import ValueHandler
from dictionaryAlarms import dict_interim_alarms, dict_wind_alarms

class SecondWindowBrowser(QtWidgets.QMainWindow, Ui_MainWindow, QThread, AplicationWidget, ValueHandler):
    def __init__(self) -> None:
        super().__init__()
        #QThread.__init__(self)
        # Вызываем метод setupUi, в котором настроены все наши виджеты (кнопки, поля и т.д.)
        self.setupUi(self)
        # Создаем переменные в которых записываем путь к файлам
        self.path_icon_second_window = str(Path(Path.cwd(), "Resources", "Icons", "icn61.ico"))
        self.path_icon_load = str(Path(Path.cwd(), "Resources", "Icons", "icn8.ico"))
        self.path_icon_time = str(Path(Path.cwd(), "Resources", "Icons", "icn18.ico"))
        self.path_icon_done = str(Path(Path.cwd(), "Resources", "Icons", "icn15.ico"))
        self.path_icon_progress = str(Path(Path.cwd(), "Resources", "Icons", "icn16.ico"))
        
        # Переменная определяет интервал между запросами
        self.interval_time = 1
        # Обзащаемся к странице стиля textBrowser из которой получаем значение размера текста сообщения 
        self.font_size_frame1 = int(self.textBrowser_4.styleSheet().split()[-2].rstrip('pt'))
        # Получаем стили ширифта примененные для окна textBrowser_2, получаем значение размера ширифта и записываем в переменную
        self.font_size_frame2 = int(self.textBrowser_2.styleSheet().split()[-2].rstrip('pt'))
        # Получаем стили ширифта примененные для окна textBrowser_3, получаем значение размера ширифта и записываем в переменную
        self.font_size_frame3 = int(self.textBrowser.styleSheet().split()[-2].rstrip('pt'))
        # Получаем стили ширифта примененные для окна textBrowser_4, получаем значение размера ширифта и записываем в переменную
        self.font_size_frame4 = int(self.textBrowser_3.styleSheet().split()[-2].rstrip('pt'))
        # Получаем стили ширифта примененные для окна textBrowser_6, получаем значение размера ширифта и записываем в переменную
        self.font_size_current_alarm = int(self.textBrowser_6.styleSheet().split()[-2].rstrip('pt'))
        # Получаем стили ширифта примененные для окна textBrowser_7, получаем значение размера ширифта и записываем в переменную
        self.font_size_channel_frame = int(self.textBrowser_7.styleSheet().split()[-2].rstrip('pt'))
        # Создаем переменную в которую записываем значение размера текста аварийных сообщении в диалоговом окне 
        self.font_size_dialog_box = 64
        
        # Создаем экзепляр класса WindPlaySound
        self.play_sound = WindPlaySound()
        # Создаем экземпляр класса WindTextSpeech
        self.speech_text = WindTextSpeech()
        # Создаем экземпляр класса WindowUPSAlarmHandler
        self.ups_handler = WindowUPSAlarmHandler()
        self.macc_handler = WindowMACCAlarmHandler()
        self.dgu_handler = WindowDGUAlarmHandler()
        self.error_handler = WindowERRORAlarmHandler()
        self.port_handler = WindowPortSwitchHandler()
        self.sla_handler = WindowSLASwitchHandler()
        self.phase_ups_handler = WindowThreePhaseUPSAlarmHandler()
        
        # Подключаемся к БД
        with ConnectSqlDB() as sql:
            # Делаем запрос на получение значения имени речи
            name = sql.get_db('value', description='speech_name', table='Styles')[0]
        # Если кортеж не пустой
        if isinstance(name, str):
            # Обращаемся к словарю получаем id голоса по имени
            voice_id = self.speech_text.dic_voices.get(name)
            if isinstance(voice_id, str):
                # Устанавливаем голос речи
                self.speech_text.voice_id = voice_id

        # Создаем экземпляр классса Таймер запуска метода run
        self.timer = QtCore.QTimer(self)
        # Таймер запуска часов
        self.timer_clock = QtCore.QTimer(self)
        # Задаем интервал запуска timer(обновления)
        self.timer.setInterval(self.interval_time*1000)
        self.timer_clock.setInterval(1000)
        # Определяем какую функцию будет запускать Таймер через указанный промежуток времени
        self.timer.timeout.connect(self.run)
        self.timer_clock.timeout.connect(self.show_clock)

        # Флаг определяет закрыто или открыто второе окно
        self.isClose_window = False
        # Флаг определяет состояние воспроизведения мелодии
        self.isPlaySoundOff = True
        # Создаем переменную в котрую добавляем ключ IP адрес и значение строка с параметрами устройства
        self.dict_set = OrderedDict()
        # Словарь для хранения ip адресов устройств для которых воспроизводилась мелодия. 
        self.dic_alarm_sound: Dict[str, Dict[str, str]] = {'power_alarm': {},
                                                            'low_voltage': {},
                                                            'low_signal_level': {},
                                                            'battery_disconnect': {},
                                                            'hight_temp_macc': {},
                                                            #'power_system':{},
                                                            #'low_sys_voltage':{},
                                                            'motor': {},
                                                            'low_level_water': {},
                                                            'low_pressure_oil': {},
                                                            'low_temp_water': {},
                                                            'hight_temp_water': {},
                                                            'low_level_oil': {},
                                                            'request_err': {},
                                                            'hight_voltage':{},
                                                            'low_temp':{},
                                                            'loss_channel':{},
                                                            'icmp_echo': {},
                                                            'loss_sla': {},
                                                            }
        # Словарь для хранения информации ip адресов устройств для которых выводилось диалоговое окно.
        self.dic_massege_box: Dict[str, Dict[str, Any]] = {'power_alarm': {},
                                                            'low_voltage': {},
                                                            'low_signal_level': {},
                                                            'hight_temp_macc': {},
                                                            'battery_disconnect': {},
                                                            #'power_system':{},
                                                            #'low_sys_voltage':{},
                                                            'motor': {},
                                                            'low_level_water': {},
                                                            'low_pressure_oil': {},
                                                            'low_temp_water': {},
                                                            'hight_temp_water': {},
                                                            'low_level_oil': {},
                                                            'request_err': {},
                                                            'hight_voltage':{},
                                                            'low_temp':{},
                                                            'loss_channel':{},
                                                            'icmp_echo': {},
                                                            'loss_sla': {},
                                                            }
        # Переменная список куда записываем результат опроса snmp
        self.snmp_traps: List[str] = []

     # СОЗДАЕМ ЭКЗЕМПЛЯР КЛАССА QIcon, ДОБАВЛЕНИЕ ИЗОБРАЖЕНИЯ ДЛЯ MAIN WINDOW
        # Создаем экземпляр класса icon_second_window, класс QIcon - отвечает за добавления иконки с изображением для основного окна программы
        icon_second_window = QtGui.QIcon()
        # Вызываем у экземпляра класса icon_second_window метод addFile, указываем путь где находится изображение
        icon_second_window.addFile(self.path_icon_second_window)
        # У QMainWindow вызываем метод setWindowIcon, которому передаем экземпляр класса нашего второго окна self и экземпляр класса icon_second_window в котором содержится изображение
        QtWidgets.QMainWindow.setWindowIcon(self, icon_second_window)

        # Создаем экземпляр класса  QLable Выводим сообщение в статус бар со статусом загрузки
        self.lbl = QLabel()
        # Добавляем стиль к экземпляру класса
        self.lbl.setStyleSheet("text-align: center")
        # Делаем выравнивание по левому краю нашей иконки с изображением
        #self.lbl.setAlignment(QtCore.Qt.AlignLeft)
        # Создаем экземпляр класса QLable Выводим сообщение в статус бар с датой и временем
        self.lbl_clock = QLabel()
        # Получаем дату и время в нужной нам форме
        date = datetime.today().strftime('%H:%M:%S %d-%m-%Y')
        # Добавляем изображение и дату и время в экземпляр класса lbl_clock
        self.lbl_clock.setText('<img src="{}" width="45" height="45"> <strong>{}</strong>'.format(self.path_icon_time, date))

        # СТАТУС БАР
        # Выводим Надпись с изображением в статус Бар
        self.statusbar.insertWidget(0, self.lbl, stretch = 0)
        self.statusbar.insertWidget(1, self.checkSound, stretch = 0)
        self.statusbar.insertWidget(2, self.Hidden_message_check_box, stretch = 0)
        self.statusbar.insertWidget(3, self.speech_message, stretch = 0)
        #
        self.statusbar.insertWidget(4, self.sound_message, stretch = 0)
        # Добавляем в статус бар наш экземпляр класса lbl_clock
        self.statusbar.addPermanentWidget(self.lbl_clock, stretch = 0)
       
        # Создаем экземпляр класса QScrollBar, который позволит обратиться к  вертикальной полосе прокрутки Окна №1,2,3,4 textBrowser
        self.vertScrollBarWind2 = self.textBrowser.verticalScrollBar()
        self.vertScrollBarWind1 = self.textBrowser_3.verticalScrollBar()
        self.vertScrollBarWind3 = self.textBrowser_2.verticalScrollBar()
        self.vertScrollBarWind4 = self.textBrowser_4.verticalScrollBar()
        self.vertScrollBarWind5 = self.textBrowser_5.verticalScrollBar()
        self.vertScrollBarWind6 = self.textBrowser_6.verticalScrollBar()
        # При наведении курсора мыши на полосу прокрутки будет появляться значек руки
        self.vertScrollBarWind2.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind1.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind3.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind4.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind5.setCursor(Qt.OpenHandCursor)
        self.vertScrollBarWind6.setCursor(Qt.OpenHandCursor)
        # actionTriggered вызывается когда полоса прокрутки изменяется в результате взаимодействия с пользователем
        # прикрепляем к нему метод scroll, который будет вызываться при каждой сработке триггера. 
        self.vertScrollBarWind1.actionTriggered.connect(self.scroll_wind_1)
        self.vertScrollBarWind2.actionTriggered.connect(self.scroll_wind_2)
        self.vertScrollBarWind3.actionTriggered.connect(self.scroll_wind_3)
        self.vertScrollBarWind4.actionTriggered.connect(self.scroll_wind_4)
        self.vertScrollBarWind5.actionTriggered.connect(self.scroll_wind_5)
        self.vertScrollBarWind6.actionTriggered.connect(self.scroll_wind_6)
        # Устанавливаем первоначальное положение ползунка в верхнее положение для всех окон
        self.position_scroll_wind1 = 0
        self.position_scroll_wind2 = 0
        self.position_scroll_wind3 = 0
        self.position_scroll_wind4 = 0
        self.position_scroll_wind5 = 0
        self.position_scroll_wind6 = 0
        # Словарь для хранения промежуточных значений ключа(ip) и значения(value)
        self.dict_interim_set: Dict[str, str] = {}
        # Список для хранения ip адресов, индекс которых нужно поменять в словаре
        self.ip_list: List[str] = []
        # Список ip адресов без аварии
        self.ip_list_not_alarm = []
        #
        self.ip_list_alarm = []
        # Флаг говорит, что нужно изменить позицию ключа ip в словаре dict_set  
        self._change_index_key: bool = False
        
    # Метод обрабатывает нажатие кнопок "ОК" в диалоговом окне, останавливает воспроизведение мелодии
    def click_btn(self, btn: Any) -> None:
        # Удаление пользователя
        if btn.text() == 'OK':
            # Вызываем метод который подтверждает аврию.
            self._press_button_confirm_alarm()
    
    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №1
    def scroll_wind_1(self) -> None:
        # Метод изменяет положение полосы прокрутки (вверх или вниз) с шагом, когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind1.setSingleStep(25)
        # Определяем значение положение полосы прокрутки scroll
        self.position_scroll_wind1 = self.vertScrollBarWind1.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind1.setSliderPosition(self.position_scroll_wind1)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №2
    def scroll_wind_2(self) -> None:
        # Метод изменяет положение полосы прокрутки (вверх или вниз) с шагом, когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind2.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind2 = self.vertScrollBarWind2.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind2.setSliderPosition(self.position_scroll_wind2)
    
    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №3
    def scroll_wind_3(self) -> None:
        # Метод изменяет положение полосы прокрутки (вверх или вниз) с шагом, когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind3.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind3 = self.vertScrollBarWind3.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind3.setSliderPosition(self.position_scroll_wind3)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем в Окне №4
    def scroll_wind_4(self) -> None:
        # Метод изменяет положение полосы прокрутки (вверх или вниз) с шагом, когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind4.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind4 = self.vertScrollBarWind4.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind4.setSliderPosition(self.position_scroll_wind4)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем во вкладке "Текущие аварии"
    def scroll_wind_5(self) -> None:
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind5.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind5 = self.vertScrollBarWind5.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind5.setSliderPosition(self.position_scroll_wind5)

    # Метод фиксирует положение ползунка полосы прокрутки после изменения его положения пользователем во вкладке "Текущие аварии"
    def scroll_wind_6(self) -> None:
        # Метод изменяет положение полосы прокрутки (вверх или вниз), когда пользователь прокручивает scroll мыши
        self.vertScrollBarWind6.setSingleStep(25)
        # Определяем значение положения полосы прокрутки
        self.position_scroll_wind6 = self.vertScrollBarWind6.sliderPosition()
        # Устанавливаем положение ползунка полосы прокрутки
        self.vertScrollBarWind6.setSliderPosition(self.position_scroll_wind6)
    
    # Метод переносит запись в конец словаря
    def _move_to_end(self, ip: str) -> None:
        #
        if ip in self.ip_list_alarm:
            self.ip_list_not_alarm.append(ip)
            #self.dict_set.move_to_end(ip, last=True)
            #
            #self.ip_list_not_alarm.remove(ip)
    
    # Метод проверяет количество строк в одном из окон textBrowser
    def _check_index_line_in_textBrowser(self, num_window: int) -> bool:
        if num_window == 1:
            # Получаем количество записей в textBrowser3
            count_line = self.textBrowser_3.document().size().toSize().height() # -> int
            # Получаем высоту окна textBrowser
            height = self.textBrowser_3.geometry().height() # -> int
            # Если количество строк в окне превышает высоту экрана
            if (count_line + 10) > height:
                return True
        elif num_window == 2:
            # Получаем количество записей в textBrowser
            count_line = self.textBrowser.document().size().toSize().height() # -> int
            # Получаем высоту окна textBrowser
            height = self.textBrowser.geometry().height() # -> int
            # Если количество строк в окне превышает высоту экрана
            if (count_line + 10) > height:
                return True
        elif num_window == 3:
            # Получаем количество записей в textBrowser2
            count_line = self.textBrowser_2.document().size().toSize().height() # -> int
            # Получаем высоту окна textBrowser2
            height = self.textBrowser_2.geometry().height() # -> int
            # Если количество строк в окне превышает высоту экрана
            if (count_line + 10) > height:
                return True
        elif num_window == 4:
            # Получаем количество записей в textBrowser4
            count_line = self.textBrowser_4.document().size().toSize().height() # -> int
            # Получаем высоту окна textBrowser4
            height = self.textBrowser_4.geometry().height() # -> int
            # Если количество строк в окне превышает высоту экрана
            if (count_line + 10) > height:
                return True
        return False

    #@QtCore.pyqtSlot(int)
    # Метод выводит строки сообщения в одно из окон во вкладке "Общая информация" 
    def _show_message_on_window(self, num_window: int, message: str) -> None:
        if num_window == 1:
            # Выводим аварийное сообщение во вкладку "Общая информация" 
            self.textBrowser_3.append(message)
            '''
            Поскольку метод append добавляет строки одну под другой и когда количество строк 
            превышает размеры окна, метод append добавляет scroll(ползунок) и чтобы положение 
            ползунка оставалось не изменным при обновлении даных в окне, вызываем метод
            setSliderPosition, который устанавливает положение ползунка не давая изменить
            его положение
            '''
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind1.setSliderPosition(self.position_scroll_wind1)
        elif num_window == 2:
            # Выводим аварийное сообщение во вкладку "Общая информация" 
            self.textBrowser.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind2.setSliderPosition(self.position_scroll_wind2)
        elif num_window == 3:
            # Выводим аварийное сообщение во вкладку "Общая информация"
            self.textBrowser_2.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind3.setSliderPosition(self.position_scroll_wind3)
        elif num_window == 4:
            # Выводим аварийное сообщение во вкладку "Общая информация"
            self.textBrowser_4.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind4.setSliderPosition(self.position_scroll_wind4)
        else:
            # Выводим аварийное сообщение во вкладку "Общая информация"
            self.textBrowser_4.append(message) 
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind4.setSliderPosition(self.position_scroll_wind4)
    
    # Метод выводит строки сообщения в окно во вкладке Текущие аварии
    def _show_message_in_window_current_alarm(self, message: str) -> None:
        # Получаем количество записей в textBrowser_6
        size = self.textBrowser_6.document().size().toSize().height() # -> int
        # Получаем высоту окна textBrowser_6
        geometry = self.textBrowser_6.geometry().height() # -> int
        # Проверяем если количество аварий во вкладке Curent Alarm не превышает высоту экрана
        if (size + 40) < geometry:
            # Выводим значение на экран в первый столбец
            self.textBrowser_6.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind6.setSliderPosition(self.position_scroll_wind6)
        else:
            # Иначе, если количество аварий привышает высоту экрана, то выводим значение на экран во второй столбец
            self.textBrowser_5.append(message)
            # Устанавливаем положение ползунка полосы прокрутки
            self.vertScrollBarWind5.setSliderPosition(self.position_scroll_wind5)
    
    # Метод преобразует дату и время в строку и подставляет ее значение в меню Статус Бар
    def show_clock(self) -> None:
        # Получаем дату и время
        date = datetime.today().strftime('%H:%M:%S %d-%m-%Y')
        # Выравниваем по правому краю
        #self.lbl.setAlignment(QtCore.Qt.AlignCenter)
        # В экземпляр класса QLable подставляем изображение и полученную дату и время
        self.lbl_clock.setText('<img src="{}" width="20" height="20"> <strong>{}</strong>'.format(self.path_icon_time, date))
    
    # Метод запускает мелодию при возникновении аварии
    def _run_play_sound(self) -> None:
        # Проверяем если галочка "Без звука" не установлена, то воспроизводим мелодию
        if not self.checkSound.isChecked():
            # Проверяем если мелодия не запущена
            if not self.play_sound.is_play():
                # Воспроизвести мелодию один раз
                self.play_sound.single_sound()

    # Метод воспроизводит речевое сообщение
    def _speech_message(self, host_name: str, description: str) -> bool:
        # Проверяем если галочка "Без звука" не установлена, то воспроизводим текст
        if not self.checkSound.isChecked():
            # Формируем текст который буде озвучен
            text = f'{host_name} {description}'
            # Проверяем, что в данный момент не произносится речь
            if not self.speech_text.isbusy_speech():
                # Обращаемся к переменной, присваиваем ей текст
                self.speech_text.text = text
                # Запускаем в отдельном потоке метод, который воспроизводит текст.
                self.speech_text.start()
                return True
            else:
                return False 
        else:
            return True 
                
    # Метод проверяет воспроизводилась ли мелодия для аварии
    def _isplay_sound(self, key_alarm: str, ip: str) -> bool:
        # Если в словаре нет ключа с ip адресом
        if self.dic_alarm_sound[key_alarm].get(ip) == None:
            # Добавляем в словарь ключ ip адрес и значение Alarm
            self.dic_alarm_sound[key_alarm][ip] = 'Alarm'
            return True
        else:
            return False

    # Метод проверяет воспроизводилась ли речевое оповещение для аварии
    def _isplay_voice(self, key_alarm: str, ip: str) -> bool:
        # Если в словаре нет ключа с ip адресом
        if self.dic_alarm_sound[key_alarm].get(ip) == None:
            return True
        else:
            return False

    # Метод проверяет выводилось Диалоговое окно с сообщением для аварии 
    def _is_display_dialog(self, key_alarm: str, ip: str) -> bool:
        # Если в словаре нет ключа с ip адресом
        if self.dic_massege_box[key_alarm].get(ip) == None:
            # Добавляем ip адрес в словарь со значением Add
            self.dic_massege_box[key_alarm][ip] = 'Add'
            return True
        else:
            return False
    
    # Метод выводит Диалоговое окно с сообщением об аварии
    def _display_dialog(self, host_name: str,  description: str) -> QMessageBox:
        # Создаем экземпляр класса
        critical_alarm = QMessageBox()
        critical_alarm.setWindowTitle('Авария')
        critical_alarm.setText('Авария')
        critical_alarm.setIcon(QMessageBox.Critical)
        critical_alarm.setWindowIcon(self.icon_err)
        # Добавляем текст сообщения который будет выводится с вызовом Диалогово окна
        critical_alarm.setText(f'<b style="font-size:{self.font_size_dialog_box}px">{host_name}: {description}</b>')
        critical_alarm.open()
        critical_alarm.buttonClicked.connect(self.click_btn)
        # Возвращаем экземпляр класса
        return critical_alarm
    
    # Метод проверяет все ли аварии были потверждены пользователем
    def _is_confirm_alarms(self) -> bool:
        # Создаем генератор списка, обращаемся к словарю dic_alarm_sound по значениям (values) полученные 
        # данные преобразуем в список перебираем в цикле список словарей, если словарь не пустой
        #  добавлеям в созданный список ls проверяем если этот список пустой.
        ls = [list(dic.values()) for dic in list(self.dic_alarm_sound.values()) if dic]
        for num, alarms in enumerate(ls, start=1):
            # Если в словаре есть значение  Alarm, значит есть не подтвержденная авария
            if 'Alarm' in alarms:
                # Возвращаем False
                return False
            # Если число итераций равно длине списка, значит мы дошли до конца списка, т.е. все аварии потверждены
            elif num == len(ls):
                return True 
        return True

    # Метод останавливает воспроизведение мелодии
    def _stop_play_sound(self) -> None:
        # Проверяем если мелодия запущена
        if self.play_sound.is_play():
            # Останавливаем мелодию
            self.play_sound.stop()
            self.play_sound.terminate()
    
    # Метод обрабатывает  воспроизведение речевого сообщения
    def _audio_message_handler(self, ip: str, host_name: str, name_alarm: str, text: str) -> None:
        # Проверяем, если установлена галочка "Голосовое оповещение"
        if self.speech_message.isChecked():
            # Вызываем метод, который проверяет, воспроизводилась ли мелодия/голос для текущего ip, верни True
            if self._isplay_voice(name_alarm, ip):
                # Вызываем метод, который воспроизводит речь, если метод возвращает True
                if self._speech_message(host_name, text):
                    # Добавляем в словарь ключ ip адрес и значение Alarm
                    self.dic_alarm_sound[name_alarm][ip] = 'Alarm'
        # Проверяем, если установлена галочка "Звуковое оповещение"
        elif self.sound_message.isChecked():
            # Вызываем метод, который проверяет, воспроизводилась ли мелодия/речь для текущего ip, если нет, верни True
            if self._isplay_sound(name_alarm, ip):
                # Вызываем метод который запускает мелодию
                self._run_play_sound()
                # Добавляем в словарь ключ ip адрес и значение Alarm
                self.dic_alarm_sound[name_alarm][ip] = 'Alarm'

    # Метод выводит диалоговое окно и речевое/звуковое оповещение
    def _dialog_box_handler(self, ip: str, host_name: str, name_alarm: str, description: str) -> None:
        # Проверяет выводилось Диалоговое окно для этой аварии путем проверки в словаре записи с этим ip адресом
        if self._is_display_dialog(name_alarm, ip):
            # Если не установлена галочка "Не выводить Диалоговое окно с сообщением"
            if not self.Hidden_message_check_box.isChecked():
                # Вызываем метод который выводит диалоговое окно с сообщением об аварии
                critical_alarm = self._display_dialog(host_name, description)
                # Добавляем в словарь ключ ip адрес и экземпляр класса
                self.dic_massege_box[name_alarm][ip] = critical_alarm

    # Метод вызывается при нажатии кнопки "Ок" в Диалоговом окне, меняем занчение в словаре с Alarm на Confirm,
    # тем самым подтверждаем наличие аварии
    def _press_button_confirm_alarm(self) -> None:
        # Обращаетмя к словарю dic_alarm_sound получаем список ключей
        keys = list(self.dic_alarm_sound.keys())
        # Проходимся по списку ключей
        for num, key in enumerate(keys):
            # Обращаемся к словарю по ключу key, получаем словарь проверяем что если в словаре есть запись
            if self.dic_alarm_sound[key]:
                # Обращаемся к словарю и проходимся по его ключам ip 
                for ip in self.dic_alarm_sound[key]:
                    # Если значение равно 'Alarm'
                    if self.dic_alarm_sound[key][ip] == 'Alarm':
                        # Меняем значение с Alarm на Confirm, т.е. мы подтверждаем наличие аварий
                        self.dic_alarm_sound[key][ip] = 'Confirm'
                        return None 
    
    # Метод удаляет запись об аврии из словарей dic_alarm_sound, dic_massege_box
    def _remove_ip_from_dict_alarms(self, ip: str, *key_alarms: str) -> None:
        for alarm in key_alarms:
            # Если есть запись в словаре с ключом ip
            if self.dic_alarm_sound[alarm].get(ip):
                # Удаляем запись из словаря alarm_sound
                del self.dic_alarm_sound[alarm][ip] 
            # Если в словаре есть запись с этим ip
            if self.dic_massege_box[alarm].get(ip):
                # Удаляем запись из словаря
                del self.dic_massege_box[alarm][ip] 
            
    # Метод запускает 
    def run(self) -> None:    
        # Задаем интервал запуска timer(обновления метода run)
        self.timer.setInterval(self.interval_time*1000)
        # В экземпляр класса QLable подставляем изображение и текст 
        self.lbl.setText('<img src="{}">  Выполняется'.format(self.path_icon_progress))
        # Еслисписок snmp_traps не пустой
        if self.snmp_traps:
            for line in self.snmp_traps:
                # Получаем IP адрес вызвав метод _parse_ip
                ip_addr = self._parse_ip(line)
                # Если тип переменной ip строка И в строке есть значение Port ИЛИ SLA И 
                if isinstance(ip_addr, str) and ('Port' in line or 'Sla' in line):
                        # Получаем значение порта или sla 
                        item = self._parse_value(line)
                        # Проверяем есть ли в словаре ключ с именем ip_addr
                        if self.dict_set.get(ip_addr):
                            # Добавляем в словарь ключ ip/item И значение это вывод строки с текущими значениями 
                            self.dict_set[f'{ip_addr}/{item}'] = line
                            # Удаляем старое имя ключа из словаря
                            del self.dict_set[ip_addr]
                        else:
                            # Добавляем в словарь ключ ip/item И значение это вывод строки с текущими значениями
                            self.dict_set[f'{ip_addr}/{item}'] = line
                # Если тип переменной ip строка И в строке есть значение Number, т.е. оборудование не доступно
                elif isinstance(ip_addr, str) and 'Number' in line:
                    # Получаем значение number
                    item = self._parse_value(line)
                    # Проверяем есть ли в словаре ключ с таким именем
                    if self.dict_set.get(f'{ip_addr}/{item}'):
                        # Добаляем имя ключа "ip_addr" и значение
                        self.dict_set[ip_addr] = line
                        # Удаляем старое имя ключа из словаря
                        del self.dict_set[f'{ip_addr}/{item}']
                    else:
                        # Добавляем ключ с именем ip_addr И текущее значение
                        self.dict_set[ip_addr] = line
                
                # УСЛОВИЕ ДЛЯ ИБЭП Если тип переменной ip строка
                elif isinstance(ip_addr, str):
                    # Добавляем в словарь ключ ip_addr И значение это вывод строки с текущими значениями
                    self.dict_set[ip_addr] = line
            # Очищаем окна от данных
            self.textBrowser.clear()
            self.textBrowser_2.clear()
            self.textBrowser_3.clear()
            self.textBrowser_4.clear()
            self.textBrowser_5.clear()
            self.textBrowser_6.clear()
            self.textBrowser_7.clear()
            # Перебираем данные из словаря dict_set по ключу ip и значению value 
            for ip, value in self.dict_set.items():
            # CISCO
                if 'Sla' in value:
                    # Получаем сообщение в HTML формате
                    message = self.sla_handler.alarm_handler(value)
                    ip_address = self.sla_handler.ip
                    # Если тип переменной message строка И название аврии icmp_echo
                    if isinstance(message, str) and self.sla_handler.name_alarm == 'icmp_echo':
                        channel_name = self.sla_handler.channel_name
                        alarm_name = self.sla_handler.name_alarm
                        description = self.sla_handler.description
                        # Вызываем метод обработчик аудио сообщений 
                        self._audio_message_handler(ip, channel_name, alarm_name, description)
                        # Вызываем метод обработчик сообщений диалогового окна
                        self._dialog_box_handler(ip, channel_name, alarm_name, description)
                        # Вызываем метод, который выводит сообщение во вкладке "Каналы"
                        self.textBrowser_7.append(message)
                    # Если тип переменной message строка И название аварии None
                    elif isinstance(message, str) and self.sla_handler.name_alarm == "None":
                        # Вызываем метод, который выводит сообщение во вкладку "Каналы"
                        self.textBrowser_7.append(message)
                        # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'icmp_echo')
                    # Проверяем есть ли запись в словаре dict_alarms с ключом request_err класс WindowERRORAlarmHandler
                    if dict_wind_alarms['request_err'].get(ip_address):
                        # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip_address, 'request_err')
                        # Удаляем запись из словаря
                        del dict_wind_alarms['request_err'][ip_address]
                        # Удаляем запись из словаря
                        if dict_interim_alarms['request_err'].get(ip_address):
                            # Удаляем запись из словаря
                            del dict_interim_alarms['request_err'][ip_address]
                    
                # Если в строке сообщения есть занчение 'Port'
                elif 'Port' in value:
                    message = self.port_handler.alarm_handler(value)
                    ip_address = self.port_handler.ip
                    alarm_name = self.port_handler.name_alarm
                    # Если тип переменной message строка И название аварии loss_channel 
                    if isinstance(message, str) and self.port_handler.name_alarm == 'loss_channel':
                        channel_name = self.port_handler.channel_name
                        description = self.port_handler.description
                        # Вызываем метод обработчик аудио сообщений 
                        self._audio_message_handler(ip, channel_name, alarm_name, description)
                        # Вызываем метод обработчик сообщений диалогового окна
                        self._dialog_box_handler(ip, channel_name, alarm_name, description)
                        # Вызываем метод, который выводит сообщение во вкладке "Каналы"
                        self.textBrowser_7.append(message)
                    # # Если тип переменной message строка И название аварии "None"
                    elif isinstance(message, str) and self.port_handler.name_alarm == "None":
                        # Вызываем метод, который выводит сообщение во вкладке "Каналы"
                        self.textBrowser_7.append(message)
                        # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'loss_channel')
                    # Проверяем есть ли запись в словаре с ключом request_err класс WindowERRORAlarmHandler
                    if dict_wind_alarms['request_err'].get(ip_address):
                        # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip_address, 'request_err')
                        # Удаляем запись из словаря
                        del dict_wind_alarms['request_err'][ip_address]
                        if dict_interim_alarms['request_err'].get(ip_address):
                            # Удаляем запись из словаря
                            del dict_interim_alarms['request_err'][ip_address]

                elif 'ДГУ' in value:
                    # НИЗКИЙ УРОВЕНЬ ТОПЛИВА
                    # Вызываем метод, который возвращает сообщение в формате HTML
                    message = self.dgu_handler.alarm_handler(value)
                    #
                    num_window = self.dgu_handler.num_window
                    # Если сообщение не пустое И имя аварии low_level_oil
                    if message and self.dgu_handler.name_alarm == 'low_level_oil':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.dgu_handler.window_alarm_handler()
                        # Если авария подтверждена
                        if self.dgu_handler.is_alarm:
                            host_name = self.dgu_handler.host_name
                            description = 'Низкий уровень топлива'
                            # Вызываем метод обработчик аудио сообщений 
                            self._audio_message_handler(ip, host_name, 'low_level_oil', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'low_level_oil', description)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        if isinstance(message_window2, str):
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(message_window2)
                    # Если тип переменной message строка И название аварии None
                    elif isinstance(message, str) and self.dgu_handler.name_alarm == "None":
                        # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'low_level_oil')
                        #
                        self._move_to_end(ip)
                        # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)

                    # ЭКСТРЕННАЯ ОСТАНОВКА ДВИГАТЕЛЯ
                    # Вызываем метод который возвращает строку сообщения в формате HTML
                    message = self.dgu_handler.motor_stop_handler(value)
                    # Если сообщение не пустое И имя аварии motor
                    if message and self.dgu_handler.name_alarm is 'motor':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        host_name = self.dgu_handler.host_name
                        description = 'Экстренная остановка двигателя'
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.dgu_handler.window_alarm_handler()
                        # Вызываем метод обработчик аудио сообщений 
                        self._audio_message_handler(ip, host_name, 'motor', description)
                        # Вызываем метод обработчик сообщений диалогового окна
                        self._dialog_box_handler(ip, host_name, 'motor', description)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        if isinstance(message_window2, str):
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(message_window2)
                    # Если тип переменной message строка И название аврий None
                    elif isinstance(message, str) and self.dgu_handler.name_alarm == "None":
                        # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'motor')
                        #
                        self._move_to_end(ip)
                        # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)

                    # НИЗКИЙ УРОВЕНЬ О/Ж
                    # Вызываем метод который возвращает строку с данными в формате HTML
                    message = self.dgu_handler.low_level_water_handler(value)
                    # Если сообщение не пустое И имя аварии level_water
                    if message and self.dgu_handler.name_alarm == 'low_level_water':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        description_box = 'Низкий уровень О/Ж'
                        description_speech = 'Низкий уровень охлаждающей жидкости'
                        host_name = self.dgu_handler.host_name
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.dgu_handler.window_alarm_handler()
                        # Вызываем метод обработчик аудио сообщений 
                        self._audio_message_handler(ip, host_name, 'low_level_water', description_speech)
                        # Вызываем метод обработчик сообщений диалогового окна
                        self._dialog_box_handler(ip, host_name, 'low_level_water', description_box)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        if isinstance(message_window2, str):
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(message_window2)
                    # Если аварии нет
                    elif message and self.dgu_handler.name_alarm == "None":
                        # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'low_level_water')
                        #
                        self._move_to_end(ip)
                        # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)

                    # НИЗКОЕ ДАВЛЕНИЕ МАСЛА
                    # Вызываем метод который возвращает строку с данными в формате HTML
                    message = self.dgu_handler.low_pressure_oil_handler(value)
                    # Если сообщение не пустое И имя аварии low_pressure_oil
                    if message and self.dgu_handler.name_alarm == 'low_pressure_oil':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        description = 'Низкое давление масла'
                        host_name = self.dgu_handler.host_name
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.dgu_handler.window_alarm_handler()
                        # Если авария подтверждена
                        if self.dgu_handler.is_alarm:
                            # Вызываем метод обработчик аудио сообщений 
                            self._audio_message_handler(ip, host_name, 'low_pressure_oil', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'low_pressure_oil', description)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        if isinstance(message_window2, str):
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(message_window2)
                    # Если тип переменной message строка И название аварии None
                    elif isinstance(message, str) and self.dgu_handler.name_alarm == "None":
                        # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'low_pressure_oil')
                        #
                        self._move_to_end(ip)
                        # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)

                    # НИЗКАЯ ТЕМПЕРАТУРА О/Ж
                    # Вызываем метод который возвращает строку с данными в формате HTML
                    message = self.dgu_handler.low_temp_water_handler(value)
                    # Если сообщение не пустое И имя аврий low_temp_water
                    if message and self.dgu_handler.name_alarm == 'low_temp_water':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        description_box = 'Низкая температура О/Ж'
                        description_speech = 'Низкая температура охлаждающей жидкости'
                        host_name = self.dgu_handler.host_name
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.dgu_handler.window_alarm_handler()
                        # Вызываем метод обработчик аудио сообщений 
                        self._audio_message_handler(ip, host_name, 'low_temp_water', description_speech)
                        # Вызываем метод обработчик сообщений диалогового окна
                        self._dialog_box_handler(ip, host_name, 'low_temp_water', description_box)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        if isinstance(message_window2, str):
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(message_window2)
                    # Если тип переменной message строка И название аварии None
                    elif isinstance(message, str) and self.dgu_handler.name_alarm == "None":
                        # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'low_temp_water')
                        #
                        self._move_to_end(ip)
                        # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)

                    # ВЫСОКАЯ ТЕМПЕРАТУРА О/Ж
                    # Вызываем метод который возвращает строку с данными в формате HTML
                    message = self.dgu_handler.hight_temp_water_handler(value)
                    # Если сообщение не пустое И имя аврии hi_temp_water
                    if message and self.dgu_handler.name_alarm == 'hight_temp_water':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        description_box = 'Высокая температура О/Ж'
                        description_speech = 'Высокая температура охлаждающей жидкости'
                        host_name = self.dgu_handler.host_name
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.dgu_handler.window_alarm_handler()
                        # Вызываем метод обработчик аудио сообщений 
                        self._audio_message_handler(ip, host_name, 'hight_temp_water', description_speech)
                        # Вызываем метод обработчик сообщений диалогового окна
                        self._dialog_box_handler(ip, host_name, 'hight_temp_water', description_box)
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        if isinstance(message_window2, str):
                            # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                            self._show_message_in_window_current_alarm(message_window2)
                    # Если тип переменной message строка И название None
                    elif isinstance(message, str) and self.dgu_handler.name_alarm == "None":
                        # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                        self._remove_ip_from_dict_alarms(ip, 'hight_temp_water')
                        #
                        self._move_to_end(ip)
                        # Вызываем метод, который выводит сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)

                elif 'TxFiber2' in value or 'TxFiber3' in value:
                    # Вызываем метод который возвращает строку с данными в формате HTML
                    message = self.macc_handler.alarm_handler(value)
                    num_window = self.macc_handler.num_window
                    host_name = self.macc_handler.host_name
                    # Если сообщение не пустое
                    if message:
                        # Если имя аварии low_signal_level
                        if self.macc_handler.name_alarm == 'low_signal_level':
                            # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                            # и если количество строк превышает пороговое значение, возвращает True  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            description = 'Низкие приемные уровни транспондера'
                            # Вызываем метод обработчик аудио сообщений 
                            self._audio_message_handler(ip, host_name, 'low_signal_level', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'low_signal_level', description)
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.macc_handler.window_alarm_handler()
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку "Текущие аварии"
                                self._show_message_in_window_current_alarm( message_window2)
                        # Если имя аварии hight_temp_macc
                        elif self.macc_handler.name_alarm == 'hight_temp_macc':
                            # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                            # и если количество строк превышает пороговое значение, возвращает True  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            description = 'Высокая температура транспондера'
                            # Вызываем метод обработчик аудио сообщений 
                            self._audio_message_handler(ip, host_name, 'hight_temp_macc', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'hight_temp_macc', description)
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.macc_handler.window_alarm_handler()
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку "Текущие аварии"
                                self._show_message_in_window_current_alarm( message_window2)
                        # Если название аварии low_temp_macc
                        elif self.macc_handler.name_alarm == 'low_temp_macc':
                            # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                            # и если количество строк превышает пороговое значение, возвращает True  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.macc_handler.window_alarm_handler()
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку "Текущие аварии"
                                self._show_message_in_window_current_alarm( message_window2)
                                # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                                self._remove_ip_from_dict_alarms(ip, 'low_signal_level', 'hight_temp_macc')
                        # Если аварии нет
                        elif self.macc_handler.name_alarm == "None":
                            # Удаляем из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'low_signal_level', 'hight_temp_macc')
                            #
                            self._move_to_end(ip)
                        # Проверяем есть ли запись в словаре с ключом request_err класс WindowERRORAlarmHandler
                        if dict_wind_alarms['request_err'].get(ip):
                            # Удаляем запись из словаря
                            del dict_wind_alarms['request_err'][ip]
                        # Вызываем метод который выводит сообщение в одно из окон во вкладке "Общая информация"
                        self._show_message_on_window(num_window, message)
                
                # Если мы получили сообщение с ошибкой, то 
                elif 'SNMP:REQEST_ERROR' in value:
                    # Вызываем метод который возвращает строку с данными в формате HTML
                    message = self.error_handler.alarm_handler(value)
                    # Вызываем метод, возвращает номер окна
                    num_window = self.error_handler.num_window
                    # Если тип переменной строка И название аварии snmp_error
                    if isinstance(message, str) and self.error_handler.name_alarm == 'snmp_error':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.error_handler.window_alarm_handler()
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(message_window2)
                    elif isinstance(message, str) and self.error_handler.name_alarm == 'battery_disconnect':
                        # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                        # и если количество строк превышает пороговое значение, возвращает True  
                        if self._check_index_line_in_textBrowser(num_window):
                            # Добавляем ip адрес в список ip_list
                            self.ip_list.append(ip)
                            # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                            self._change_index_key = True
                            continue
                        # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                        message_window2 = self.error_handler.window_alarm_handler()
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                        # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                        self._show_message_in_window_current_alarm(message_window2)
                        # Если авария подтверждена
                        if self.error_handler.is_alarm:
                            host_name = self.error_handler.host_name
                            ip = self.error_handler.ip_addr
                            #
                            description = 'АКУМУЛЯТОРНЫЕ БАТАРЕИИ ОТКЛЮЧЕНЫ!!!'
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'battery_disconnect', description)
                            # Вызываем метод обработчик аудио сообщений 
                            self._audio_message_handler(ip, host_name, 'battery_disconnect', description)
                    # Если тип переменной строка И название аварии cisco_error
                    elif isinstance(message, str) and self.error_handler.name_alarm == 'cisco_error':
                        # Выводим сообщение во вкладку "Каналы"
                        self.textBrowser_7.append(message)
                       # Если авария подтверждена
                        if self.error_handler.is_alarm:
                            host_name = self.error_handler.host_name
                            ip = self.error_handler.ip_addr
                            #
                            description = 'Оборудование не доступно'
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'request_err', description)
                            # Вызываем метод обработчик аудио сообщений 
                            self._audio_message_handler(ip, host_name, 'request_err', description)
                
                # ПРОВЕРКА ПАРАМЕТРОВ ТРЕХФАЗНОГО ИБП
                elif 'Phase_A' in value:
                    # Вызываем метод который возвращает сообщение в формате HTML
                    message = self.phase_ups_handler.alarm_handler(value)
                    host_name = self.phase_ups_handler.host_name
                    num_window = self.phase_ups_handler.num_window
                    # Если тип переменной строка
                    if isinstance(message, str):
                        # Если название аварии power_alarm 
                        if self.phase_ups_handler.name_alarm == 'power_alarm':
                            # Вызываем метод, проверяет количество строк во фрейме, возвращает True или False
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            description = 'Отключение электроэнергии'
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            #message_window2 = self.phase_ups_handler.window_alarm_handler()
                            # Вызываем метод обработчик аудио сообщений
                            #self._audio_message_handler(ip, host_name, 'power_alarm', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            #self._dialog_box_handler(ip, host_name, 'power_alarm', description)
                            #if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                #self._show_message_in_window_current_alarm(message_window2)
                                
                        # Если название аварии low_voltage
                        elif self.phase_ups_handler.name_alarm == 'low_voltage':
                            # Вызываем метод, метод определяет количество строк в одном из окон, возвращает True или False  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            description = 'Низкое напряжение АКБ'
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.phase_ups_handler.window_alarm_handler()
                            # Вызываем метод обработчик аудио сообщений
                            self._audio_message_handler(ip, host_name, 'low_voltage', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'low_voltage', description)
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                self._show_message_in_window_current_alarm(message_window2)
                        # Если имя аварии phase_alarm
                        elif self.phase_ups_handler.name_alarm == 'phase_alarm':
                            # Вызываем метод, метод определяет количество строк в одном из окон, возвращает True или False  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.phase_ups_handler.window_alarm_handler()
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                self._show_message_in_window_current_alarm(message_window2)
                        # Если имя аварии hight_phase_voltage
                        elif self.phase_ups_handler.name_alarm == 'hight_voltage':
                            # Вызываем метод, метод определяет количество строк в одном из окон, возвращает True или False 
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.phase_ups_handler.window_alarm_handler()
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                self._show_message_in_window_current_alarm(message_window2)
                        # Если нет аварии
                        elif self.phase_ups_handler.name_alarm == "None":
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')
                            #
                            #self._move_to_end(ip)
                        # Проверяем есть ли запись в словаре с ключом request_err класс WindowERRORAlarmHandler
                        if dict_wind_alarms['request_err'].get(ip):
                            # Удаляем запись из словаря
                            del dict_wind_alarms['request_err'][ip]
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)

                else: 
                    # Вызываем метод который возвращает сообщение в формате HTML
                    message = self.ups_handler.alarm_handler(value)
                    host_name = self.ups_handler.host_name
                    num_window = self.ups_handler.num_window
                    # Если тип переменной строка
                    if isinstance(message, str):
                        # Если название аварии power_alarm 
                        if self.ups_handler.name_alarm == 'power_alarm':
                            # Вызываем метод, передаем номер окна, метод проверяет количество строк во фрейме 
                            # и если количество строк превышает пороговое значение, возвращает True  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            description = 'Отключение электроэнергии'
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.ups_handler.window_alarm_handler()
                            # Вызываем метод обработчик аудио сообщений
                            self._audio_message_handler(ip, host_name, 'power_alarm', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'power_alarm', description)
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                self._show_message_in_window_current_alarm(message_window2)
                        # Если название аварии low_voltage
                        elif self.ups_handler.name_alarm == 'low_voltage':
                            # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                            # и если количество строк превышает пороговое значение, возвращает True  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            description = 'Низкое напряжение АКБ'
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.ups_handler.window_alarm_handler()
                            # Вызываем метод обработчик аудио сообщений
                            self._audio_message_handler(ip, host_name, 'low_voltage', description)
                            # Вызываем метод обработчик сообщений диалогового окна
                            self._dialog_box_handler(ip, host_name, 'low_voltage', description)
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                self._show_message_in_window_current_alarm(message_window2)
                        # Если имя аварии hight_temp
                        elif self.ups_handler.name_alarm == 'hight_temp':
                            # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                            # и если количество строк превышает пороговое значение, возвращает True  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.ups_handler.window_alarm_handler()
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                self._show_message_in_window_current_alarm(message_window2)
                        # Если имя аварии hight_temp
                        elif self.ups_handler.name_alarm == 'hight_voltage':
                            # Вызываем метод, передаем номер окна, метод определяет количество строк в одном из окон 
                            # и если количество строк превышает пороговое значение, возвращает True  
                            if self._check_index_line_in_textBrowser(num_window):
                                # Добавляем ip адрес в список ip_list
                                self.ip_list.append(ip)
                                # Меняем значение флага на True, говорим, что нужно изменить позицию ключа(ip) в словаре dict_set  
                                self._change_index_key = True
                                continue
                            # Вызываем метод который возвращает сообщение для вывода в окно "Текущие аварии"
                            message_window2 = self.ups_handler.window_alarm_handler()
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')
                            if isinstance(message_window2, str):
                                # Вызываем метод, который выводит аварийное сообщение во вкладку Текущие аварии
                                self._show_message_in_window_current_alarm(message_window2)
                        # Если нет аварии
                        elif self.ups_handler.name_alarm == "None":
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'power_alarm', 'low_voltage')
                            #
                            #self._move_to_end(ip)
                        # Проверяем есть ли запись в словаре с ключом request_err класс WindowERRORAlarmHandler
                        if dict_wind_alarms['request_err'].get(ip):
                            # Удаляем запись из словаря
                            del dict_wind_alarms['request_err'][ip]
                        if dict_interim_alarms['battery_disconnect'].get(ip):
                            del dict_interim_alarms['battery_disconnect'][ip]
                            # Удаляя из словаря запись мы удаляем ссылку на экземпляр класса QMassegeBox тем самым закрываем Диалоговое окно 
                            self._remove_ip_from_dict_alarms(ip, 'battery_disconnect')
                        # Вызываем метод, который выводит аварийное сообщение в одно из окон во вкладке Общая информация
                        self._show_message_on_window(num_window, message)
                
                # Вызываем метод который проверяет, что все аварии потверждены пользователем перед тем как остановить мелодию
                if self._is_confirm_alarms():
                    # Вызываем метод который останавливает воспроизведение мелодии
                    self._stop_play_sound()

            # Проверяем если флаг True
            if self._change_index_key:
                # Перебираем список ip-адресов
                for ip in self.ip_list:
                    # Вызываем метод передаем ip адрес  
                    self.dict_set.move_to_end(ip, last=False)
                #
                self.ip_list_alarm += self.ip_list
                # Очищаем список 
                self.ip_list.clear()
                # Меняем значение флага False
                self._change_index_key = False
            #
            #if self.ip_list_not_alarm:
                #for ip in self.ip_list_not_alarm:
                    #print(ip)
                    #if ip in self.ip_list_alarm:
                    # Вызываем метод передаем ip адрес  
                    #self.dict_set.move_to_end(ip, last=True) 
                    #self.ip_list_alarm.remove(ip)
                #self.ip_list_not_alarm.clear()

            # Подключаемся к БД
            with ConnectSqlDB() as sql:
                # Делаем запрс к БД, Добавляем словарь date_alarm в таблицу Duration
                sql.add_data_json_db(dict_wind_alarms, table='Duration')
            # Выводим сообщение в статус бар с изображением и текстом "Готово"
            self.lbl.setText('<img src="{}">  <span style="font-size:12pt;">Готово</span>'.format(self.path_icon_done))
            
    # Запускаем таймер, который будет запускать метод run
    def start(self) -> None:
        # Переводим флаг в False, что второе окно не закрыто
        self.isClose_window = False
        # Запускаем timer, который запускает метод run
        self.timer.start(5000)
        # Запускаем timer_clock, который запускает метод show_clock
        self.timer_clock.start()
        # Добавляем в статус бар наш экземпляр класса lbl
        self.lbl.setText('<img src="{}">  <span style="font-size: 12pt;">Выполняется загрузка...</span>'.format(self.path_icon_load))
        # Выводим Надпись с изображением в статус Бар
        self.statusbar.insertWidget(0, self.lbl, stretch = 0)
        
    # Метод срабатывает при закрытии второго окна и останавливает работу Таймеров и переводи флаг в True
    def closeEvent(self, event: QCloseEvent) -> None:
        # Переводим флаг в True, что второе окно действительно закрыто
        self.isClose_window = True
        # Останавливаем экземпляр класса timer, класса QTimer
        self.timer.stop()
        # Останавливаем экземпляр класса timer_clock, класса QTimer
        self.timer_clock.stop()
        # Проверяем если мелодия запущена
        if self.play_sound.is_play():
            # Останавливаем play_sound
            self.play_sound.stop()
            self.play_sound.terminate()
        # Очищаем окна от данных
        self.textBrowser.clear()
        self.textBrowser_2.clear()
        self.textBrowser_3.clear()
        self.textBrowser_4.clear()
        self.textBrowser_5.clear()
        self.textBrowser_6.clear()
        event.accept()

if __name__ == '__main__':
    app = SecondWindowBrowser()
    #app._create_massege_box(1)
    #app._show_massege_box()
    #s = SecondWindowBrowser()
    #s._play_sound()
    print()

