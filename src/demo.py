import keyboard

from recorder import RobotRecorder
from   player import RobotPlayer

if __name__ == "__main__":
    recorder = RobotRecorder()
    recorder.start()
  
    print("Press the spacebar to stop the recorder...")
    keyboard.wait('space')

    recorder.stop()

    player = RobotPlayer()
    player.read_memory("memory.json")
    print("Read memory:")  
    player.print_memory()  
  
    print("Press the spacebar to replay...")
    keyboard.wait('space')       

    player.replay()
          