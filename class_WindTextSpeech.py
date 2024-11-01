#
from __future__ import annotations 
from typing import List, Optional, Dict, Union, Any
import time
from pyttsx3.voice import Voice
import pyttsx3

from pathlib import Path
from PyQt5.QtCore import QThread
#import espeakng

class WindTextSpeech(QThread):
    def __init__(self) -> None:
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
        # Инициализация Tex-to-Speech движка
        self.engine = pyttsx3.init()
        # Переменная в которую будем записывать текст длят воспроизведения
        self.text = "Вы слушаете тестовое сообщение"
        # Получаем список голосов 
        voices: List[pyttsx3.voice.Voice] = self.engine.getProperty("voices")
        # Вызываем метод, передаем список объектов, получаем словарь {name_voice:Id_voice} голосов
        self.dic_voices = self._get_param_voice(voices)
        # Значение голоса по умолчанию
        self.voice_id = voices[0].id
        # Дефолтное значение скорости воспроизведение речи
        self.speed_speech = 200
    
    # Метод получает параметры голосов 
    def _get_param_voice(self, voices: List[Voice]) -> Dict[str, str]:
        voices_param={}
        for voice in voices:
            voices_param[voice.name] = voice.id
        return voices_param
        
    # Метод запускает голосовое воспроизведение текста в отдельном потоке 
    def run(self) -> None:
        # Инициализация Tex-to-Speech движка
        #if not self.engine._inLoop:
            #self.engine = pyttsx3.init()
        # Устанавливаем скорость воспроизведения речи
        self.engine.setProperty("rate", self.speed_speech)
        #
        self.engine.setProperty('voice', self.voice_id)
        #
        self.engine.say(self.text)
        #
        self.engine.runAndWait()
        self.engine.stop()

    def stop_speech(self) -> None:
        self.engine.stop()
    
    # Метод проверяет 
    def isbusy_speech(self) -> Union[bool, Any]:
        #
        return self.engine._inLoop

if __name__ == "__main__":
    text = "Hello World"
    speech = WindTextSpeech()
    #print(speech.isbusy_speech())
    #speech.add_text(text)
    speech.run()
    time.sleep(1)
    speech.stop_speech()
    #speech.speak(text)
    #time.sleep(5)
    #print(speech.isbusy_speech())

