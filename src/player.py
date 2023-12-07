import json
from utils import *
from robot_interface import RobotInterface


class RobotPlayer(RobotInterface):
    def __init__(
            self,
            robot_ip: str = "192.168.1.6",
            dashboard_port: int = 29999,
            move_port: int = 30003,
            feed_port: int = 30004,
            number_of_joints: int = 4,
            optimize_movements: bool = False
    ):
        super().__init__(robot_ip, dashboard_port, move_port, feed_port, number_of_joints)

        self.memory = None
        self.optimize_movements = optimize_movements 

    def read_memory(self, memory_path: str):
        with open(memory_path, "r") as f:
            self.memory = json.load(f)
            self.memory = [MemoryEntry.from_dict(entry) for entry in self.memory]
 
    def replay(self, indices: slice = slice(None)): 
        super().replay(self.memory[indices], self.optimize_movements)
 
    def print_memory(self):  
        print("Memory: \n" + "\n".join(f"[{entry.type.name}][{entry.coordinate_system.name}] {entry.value}" for entry in self.memory))


if __name__ == "__main__":
    import keyboard
 
    player = RobotPlayer(optimize_movements=False)
    player.read_memory("memory.json") 
    print("Read memory:")
    player.print_memory()  
   
    print("Press the spacebar to replay...")
    keyboard.wait('space')

    player.replay()