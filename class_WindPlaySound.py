#
import time
from glob import glob
from pathlib import Path
from PyQt5.QtCore import QThread
import simpleaudio as sa

class WindPlaySound(QThread):
    def __init__(self) -> None:
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
        #file_path = glob(str(Path(Path.cwd(), 'Resources', 'Sound', '*.WAV')))
        # Создаем экземпляр класса WaveObject
        #self.sound = sa.WaveObject.from_wave_file(file_path[0])
        # Устанавливае начально значение play_id в None
        self.play_id = None
    
    # Метод воспроизводит мелодию единыжды
    def single_sound(self) -> None:
        # Указываем путь к списку файлов c расширением WAV 
        file_path = glob(str(Path(Path.cwd(), 'Resources', 'Sound', '*.WAV')))
        # Создаем экземпляр класса WaveObject, передав ему путь с первым в списке файлом WAV
        self.sound = sa.WaveObject.from_wave_file(file_path[0])
        try:
            # Вызываем у WaveObject метод play который возвращает PlayObject
            self.play_sound = self.sound.play() # -> PlayObject
            # Вызываем у объекта PlayObject метод play_id, получаем id мелодии
            self.play_id = self.play_sound.play_id
            # Вызываем у WaveObject метод wait_done который говорит доиграть до конца
            #self.play_sound.wait_done() 
        except:
            return None 

        return None

    # Метод запускает поток, который постоянно воспроизводит мелодию
    def run(self) -> None:
        # Указываем путь к списку файлов c расширением WAV 
        file_path = glob(str(Path(Path.cwd(), 'Resources', 'Sound', '*.WAV')))
        # Создаем экземпляр класса WaveObject
        self.sound = sa.WaveObject.from_wave_file(file_path[0])
        while True:
            try:
                self.play_sound = self.sound.play()
                self.play_id = self.play_sound.play_id
                self.play_sound.wait_done() 
            except:
                return None
        return None 
    
    # Метод останавливает воспроизведение мелодии
    def stop(self) -> None:
        self.play_sound.stop()
        return None
    
    # Метод проверяет запущена ли мелодия
    def is_play(self) -> bool:
        if self.play_id or self.play_id == 0:
            play_sound = sa.PlayObject(self.play_id)
            return play_sound.is_playing()
        else:
            return False


if __name__ == "__main__":
    sound = WindPlaySound()
    sound.start()
    time.sleep(10)
    sound.stop()
    sound.terminate()
    time.sleep(2)
    sound.single_sound()
    time.sleep(7)
    sound.terminate()
    sound.stop()
    #print(sound.idealThreadCount())
    #print(sound.isRunning())
    #time.sleep(3)
    #print(sound.is_play())
    #print(sound.is_play())
    #sound.start()
    #print(sound.idealThreadCount())
    #print(sound.isRunning())
    #time.sleep(5)

