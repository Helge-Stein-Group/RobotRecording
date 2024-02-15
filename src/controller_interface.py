import time
import pydualsense

from utils import Keymap


class ControllerInterface:
    """
    The interface for the playstation controller.

    Attributes:
        _id_counter (int): A class variable used to assign unique IDs to instances of the class.
        controller (pydualsense.pydualsense): The controller object used for communication.
        keymap (Keymap): The keymap object containing the mapping of keys to functions.
        print_function (callable): The function used for printing log messages.

    Methods:
        __init__(self, keymap: Keymap, print_function: callable = print): Initializes a new instance of the ControllerInterface class.
        controller_is_alive(self) -> bool: Checks if the controller is alive and connected.
        log_controller(self, msg: str): Logs a message with the controller ID.
        connect_controller(self): Connects to the controller.
        set_controls(self): Sets the controls based on the keymap.

    """

    _id_counter = 0  # Class variable (static counter)

    def __init__(self, keymap: Keymap, print_function: callable = print):
        """
        Initializes a new instance of the ControllerInterface class.

        Args:
            keymap (Keymap): The keymap object containing the mapping of keys to functions.
            print_function (callable, optional): The function used for printing log messages. Defaults to print.

        """
        self._id = ControllerInterface._id_counter
        ControllerInterface._id_counter += 1
        self.controller = None
        self.keymap = keymap
        self.print_function = print_function

        self.connect_controller()

    def controller_is_alive(self) -> bool:
        """
        Checks if the controller is alive and connected.

        Returns:
            bool: True if the controller is alive and connected, False otherwise.

        """
        try:
            self.controller.device._check_device_status()
            return True
        except pydualsense.DeviceError:
            return False

    def log_controller(self, msg: str):
        """
        Logs a message with the controller ID.

        Args:
            msg (str): The message to be logged.

        """
        self.print_function(msg, f"Controller {self._id}")

    def connect_controller(self):
        """
        Connects to the controller.

        """
        self.controller = pydualsense.pydualsense()
        self.controller.init()
        retries = 0
        while self.controller.states is None and retries < 10:
            self.log_controller("Connecting")
            time.sleep(1)
            retries += 1
        if retries == 10:
            self.log_controller("Failed to connect to the controller")
            raise ConnectionError("Failed to connect to the controller")
        self.log_controller("Connection successful")

    def set_controls(self):
        """
        Sets the controls based on the keymap.

        """
        for key, func in self.keymap.__dict__.items():
            self.controller.__setattr__(key, func)
