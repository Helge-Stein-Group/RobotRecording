import time

import pydualsense

from utils import Keymap


class ControllerInterface:
    _id_counter = 0  # Class variable (static counter)

    def __init__(self, keymap: Keymap, print_function: callable = print):
        self.controller = None
        self.keymap = keymap
        self._id = ControllerInterface._id_counter
        ControllerInterface._id_counter += 1
        self.print_function = print_function

        self.connect_controller()

    def controller_is_alive(self):
        try:
            self.controller.device._check_device_status()
            return True
        except:
            return False

    def log_controller(self, msg: str):
        self.print_function(msg, f"Controller {self._id}")

    def connect_controller(self):
        self.controller = pydualsense.pydualsense()
        self.controller.init()
        while self.controller.states is None:
            self.log_controller("Connecting")
            time.sleep(1)
        self.log_controller("Connection successful")

    def set_controls(self):
        for key, func in self.keymap.__dict__.items():
            self.controller.__setattr__(key, func)
