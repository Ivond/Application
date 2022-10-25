#
import time
from pathlib import Path
from PyQt5.QtCore import QThread
import simpleaudio as sa

class WindPlaySound(QThread):
    def __init__(self):
        # Запускаем у класса QThread метод init
        QThread.__init__(self)
        #
        filename = str(Path(Path.cwd(), 'Resources', 'germany-speech.WAV'))
        self.sound = sa.WaveObject.from_wave_file(filename)
        self.play_id = None
        
    def run(self):
        while True:
            try:
                self.play_sound = self.sound.play()
                self.play_id = self.play_sound.play_id
                self.play_sound.wait_done() 
            except:
                pass 

    def stop(self):
        self.play_sound.stop()

    def is_play(self):
        if self.play_id or self.play_id == 0:
            play_sound = sa.PlayObject(self.play_id)
            return play_sound.is_playing()
        else:
            return False


if __name__ == "__main__":
    sound = WindPlaySound()
    sound.start()
    time.sleep(5)
    sound.stop()
    sound.terminate()
    #print(sound.idealThreadCount())
    #print(sound.isRunning())
    time.sleep(3)
    print(sound.is_play())
    #print(sound.is_play())
    #sound.start()
    #print(sound.idealThreadCount())
    #print(sound.isRunning())
    time.sleep(5)

    #sound.terminate()
    #print(sound.isRunning())
    #time.sleep(3)
    #sound.start()
    #print(sound.isRunning())
    #time.sleep(5)
    #sound.terminate()
    #print(sound.idealThreadCount())
   # sound.start()
   # time.sleep(5)
    #print(sound.idealThreadCount())
