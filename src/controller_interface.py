import colorsys
import time

import numpy as np
import pydualsense

from utils import Keymap


class ControllerInterface:
    def __init__(self, keymap: Keymap, print_function: callable = print):
        self.controller = None
        self.serial_number = None
        self.keymap = keymap
        self.print_function = print_function

        self.connect_controller()

    def controller_is_alive(self):
        return self.controller.states is not None

    def log_controller(self, msg: str):
        self.print_function(msg, f"Controller {self.serial_number}")

    def connect_controller(self):
        self.controller = pydualsense.pydualsense()
        self.controller.init()
        self.serial_number = self.controller.device.get_serial_number_string()
        while self.controller.states is None:
            self.log_controller("Connecting")
            time.sleep(1)
        self.log_controller("Connection successful")

    def set_controls(self):
        for key, func in self.keymap.__dict__.items():
            self.controller.__setattr__(key, func)


if __name__ == "__main__":
    interface = ControllerInterface(None)
    interface.controller.audio.setMicrophoneLED(True)
    time.sleep(1)
    interface.controller.audio.setMicrophoneLED(False)
    color = np.array(colorsys.hsv_to_rgb(0 / 4, 1, 1)) * 255
    color = [int(c) for c in color]
    interface.controller.light.setColorI(*color)

    time.sleep(5)
    interface.controller.close()
