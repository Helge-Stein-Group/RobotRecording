import time
import json
import colorsys
import operator
import threading

from typing import override
from controller_interface import ControllerInterface
from robot_interface import RobotInterface
from utils import *


class RobotRecorder(threading.Thread, RobotInterface, ControllerInterface):
    """
    RobotRecorder class to program a dobot m4 pro robot with a playstation controller.

    Attributes:
        number_of_joints (int): The number of joints of the robot.
        feed (list): A list of feed entries.
        memory (list): A list of memory entries.
        displayed_pose (np.ndarray): The displayed pose of the robot.
        displayed_angles (np.ndarray): The displayed angles of the robot.
        controller_buffer (dict): A dictionary containing the controller buffer values.
        max_speed (np.ndarray): The maximum speed for each joint of the robot.
        linear_speed (float): The linear speed for the robot.
        joystick_mapping (dict): A dictionary mapping joystick names to joint indices.
        joint_bounds (np.ndarray): The bounds for each joint of the robot.
        active_joint (int): The index of the active joint.
        end_effector (EndEffectorType): The end effector of the robot.
        end_effector_state (int): The state of the end effector.
        mode (MemoryType): The memory mode of the robot.
        running (bool): A flag indicating if the robot is running.

    Methods:
        reconnect(): Reconnects the robot.
        add_feed(msg: str, source: str): Adds a feed entry.
        set_end_effector(end_effector: EndEffectorType): Sets the end effector of the robot.
        save(memory_type, value, motion_type): Saves a memory entry.
        indicate_active_joint(): Indicates the active joint.
        indicate_mode(): Indicates the memory mode.
        default_keymap(): Sets the default keymap.
        load_memory(filename="memory.json"): Loads the memory from a file.
        dump_memory(filename="memory.json"): Dumps the memory to a file.
        start(): Starts the robot recording.
        stop(): Stops the robot recording.
        bound_movement(movement: list): Bounds the movement of the robot.
        move_robot(): Moves the robot.
    """

    def __init__(
        self,
        robot_ip: str = "192.168.1.6",
        dashboard_port: int = 29999,
        move_port: int = 30003,
        number_of_joints: int = 4,
        max_speed: np.ndarray = np.array([5, 5, 5, 15]),
        linear_speed: float = 5,
        keymap: Keymap = None,
        left_joystick_joint: int = 0,
        right_joystick_joint: int = 1,
        joint_bounds: np.ndarray = np.array(
            [[-80, 80], [-125, 125], [85, 245], [-355, 355]]
        ),
        end_effector: EndEffectorType = EndEffectorType.NO_END_EFFECTOR,
        end_effector_pins: EndEffectorPins = None,
        end_effector_state: int = 0,
    ):
        """
        Initialize the Recorder object.

        Args:
            robot_ip (str, optional): The IP address of the robot. Defaults to "192.168.1.6".
            dashboard_port (int, optional): The port number for the robot's dashboard server. Defaults to 29999.
            move_port (int, optional): The port number for the robot's motion server. Defaults to 30003.
            number_of_joints (int, optional): The number of joints in the robot. Defaults to 4.
            max_speed (np.ndarray, optional): The maximum speed for each joint. Defaults to np.array([5, 5, 5, 15]).
            linear_speed (float, optional): The linear speed of the robot. Defaults to 5.
            keymap (Keymap, optional): The keymap for controlling the robot. Defaults to None.
            left_joystick_joint (int, optional): The joint index controlled by the left joystick. Defaults to 0.
            right_joystick_joint (int, optional): The joint index controlled by the right joystick. Defaults to 1.
            joint_bounds (np.ndarray, optional): The bounds for each joint angle. Defaults to np.array([[-80, 80], [-125, 125], [85, 245], [-355, 355]]).
            end_effector (EndEffectorType, optional): The end effector of the robot. Defaults to EndEffectorType.NO_END_EFFECTOR.
            end_effector_pins (EndEffectorPins, optional): The pins for the end effector. Defaults to None.
            end_effector_state (int, optional): The initial state of the end effector. Defaults to 0.
        """

        self.number_of_joints = number_of_joints

        self.feed = []
        self.memory = []

        self.displayed_pose = np.array([0, 0, 0, 0])
        self.displayed_angles = np.array([0, 0, 0, 0])

        self.controller_buffer = {
            "joint_pos": 0,
            "joint_neg": 0,
            "left_joystick": 0,
            "right_joystick": 0,
        }

        self.max_speed = max_speed
        self.linear_speed = linear_speed
        self.joystick_mapping = {
            "left": left_joystick_joint,
            "right": right_joystick_joint,
        }
        self.joint_bounds = joint_bounds

        self.active_joint = number_of_joints // 2

        self.mode = MemoryType.ABSOLUTE
        self.running = False

        RobotInterface.__init__(
            self,
            robot_ip,
            dashboard_port,
            move_port,
            self.number_of_joints,
            self.add_feed,
            end_effector,
            end_effector_pins,
            end_effector_state,
        )
        ControllerInterface.__init__(self, keymap, self.add_feed)
        if self.keymap is None:
            self.default_keymap()

        self.set_controls()
        self.indicate_active_joint()

        threading.Thread.__init__(self)

    def reconnect(self):
        """
        Reconnects the robot interface and controller.

        This method is responsible for reconnecting the robot interface and controller after a disconnection.
        It performs the following steps:
        1. Sets the 'running' flag to False, which leads to the thread dying.
        2. Sleeps for 0.5 seconds to allow time for the thread to terminate.
        3. Calls the 'default_keymap' method to reinitialize the keymap, as 'self.dashboard' and other attributes may have changed.
        4. Closes the controller if it is still alive.
        5. Calls the 'reconnect' method of the 'RobotInterface' class to reconnect the robot interface.
        6. Calls the 'connect_controller' method to reconnect the controller.
        7. Calls the 'set_controls' method to set the controls.
        8. Sets the 'running' flag to True.
        9. Re-initializes the thread.
        10. Starts the thread.

        """
        self.running = False
        time.sleep(0.5)
        self.default_keymap()
        if self.controller_is_alive():
            self.controller.close()
        RobotInterface.reconnect(self)
        self.connect_controller()
        self.set_controls()
        self.running = True
        threading.Thread.__init__(self)
        self.start()

    def add_feed(self, msg: str, source: str):
        """
        Add a feed entry to the recorder.

        Args:
            msg (str): The message to be added to the feed.
            source (str): The source of the feed entry.

        Notes:
            This is the main print method of the application.
        """
        self.feed.append(FeedEntry(datetime.now(), msg, source))

    @override
    def set_end_effector(self, end_effector: EndEffectorType):
        """
        Set the end effector of the robot.

        Args:
            end_effector (EndEffectorType): The end effector to be set.
        """
        RobotInterface.set_end_effector(self, end_effector)
        self.default_keymap()
        self.set_controls()

    def save(self, memory_type: MemoryType, motion_type: MotionType, value: np.ndarray):
        """
        Create a memory entry.

        Args:
            memory_type (MemoryType): The memory type of the memory entry.
            motion_type (MotionType): The motion type of the memory entry.
            value (np.ndarray): The value of the memory entry.
        """
        entry = MemoryEntry(memory_type, motion_type, value)
        self.memory.append(entry)

    def indicate_active_joint(self):
        """
        Indicate the active joint with the controller LEDs.
        """
        color = (
            np.array(
                colorsys.hsv_to_rgb(self.active_joint / self.number_of_joints, 1, 1)
            )
            * 255
        )
        color = [int(c) for c in color]
        self.controller.light.setColorI(*color)

    def indicate_mode(self):
        """
        Indicate the memory mode with the microphone LED.
        """
        if self.mode == MemoryType.ABSOLUTE:
            self.controller.audio.setMicrophoneLED(False)
        else:
            self.controller.audio.setMicrophoneLED(True)

    def default_keymap(self):
        """
        Set the default keymap for the robot.

        The default keymap is as follows:
        - Cross: Save the current pose.
        - Square: Change the memory mode.
        - Triangle: Delete the last memory entry or control the end effector.
        - Circle: Replay the memory.
        - R1: Cycle through the joints.
        - L1: Cycle through the joints.
        - R2: Positive joint movement.
        - L2: Negative joint movement.
        - Left Joystick: Control joint 1.
        - Right Joystick: Control joint 2.
        - Dpad Up: Move the robot linearly.
        - Dpad Down: Move the robot linearly.
        - Dpad Left: Move the robot linearly.
        - Dpad Right: Move the robot linearly.
        """

        def save_func(state):
            if state:
                self.save(MemoryType.ABSOLUTE, MotionType.JOINT, self.pose)

        def mode_func(state):
            if state:
                if self.mode == MemoryType.ABSOLUTE:
                    self.mode = MemoryType.RELATIVE
                    # QOL
                    self.save(MemoryType.ABSOLUTE, MotionType.JOINT, self.pose)
                else:
                    self.mode = MemoryType.ABSOLUTE
                self.indicate_mode()

        def delete_func(state):
            if state and self.memory:
                del self.memory[-1]

        def replay_func(state):
            if state:
                self.replay(self.memory)

        def gripper_func(state):
            if state:
                if self.end_effector_state == 0:  # Opened Gripper
                    self.end_effector_state = 1
                    self.close_gripper()
                    self.save(
                        MemoryType.END_EFFECTOR,
                        MotionType.GRIPPER,
                        np.array(
                            [
                                [self.end_effector_pins.power, 0],
                                [self.end_effector_pins.direction, 0],
                                [self.end_effector_pins.power, 1],
                            ]
                        ),
                    )
                elif self.end_effector_state == 1:  # Closed Gripper
                    self.end_effector_state = 0
                    self.open_gripper()
                    self.save(
                        MemoryType.END_EFFECTOR,
                        MotionType.GRIPPER,
                        np.array(
                            [
                                [self.end_effector_pins.power, 0],
                                [self.end_effector_pins.direction, 1],
                                [self.end_effector_pins.power, 1],
                            ]
                        ),
                    )

        def suction_cup_func(state):
            if state:
                if self.end_effector_state == 0:  # Not sucking
                    self.end_effector_state = 1
                    self.suck()
                    self.save(
                        MemoryType.END_EFFECTOR,
                        MotionType.SUCTION_CUP,
                        np.array(
                            [
                                [self.end_effector_pins.direction, 0],
                                [self.end_effector_pins.power, 0],
                            ]
                        ),
                    )
                elif self.end_effector_state == 1:  # Sucking
                    self.end_effector_state = 0
                    self.unsuck()
                    self.save(
                        MemoryType.END_EFFECTOR,
                        MotionType.SUCTION_CUP,
                        np.array(
                            [
                                [self.end_effector_pins.direction, 0],
                                [self.end_effector_pins.power, 1],
                            ]
                        ),
                    )

        def generate_cycle_joint_func(op):
            def cycle_joint_func(state):
                if state:
                    self.active_joint = op(self.active_joint, 1) % self.number_of_joints
                    self.indicate_active_joint()

            return cycle_joint_func

        def generate_button2_recording_func(key):
            def button2_recording_func(state):
                if state > 5:
                    self.controller_buffer[key] = state / 255
                else:
                    self.controller_buffer[key] = 0

            return button2_recording_func

        def generate_joystick_recording_func(key):
            def joystick_recording_func(stateX, stateY):
                if np.abs(stateX) > 5:
                    self.controller_buffer[key] = stateX / 128
                else:
                    self.controller_buffer[key] = 0

            return joystick_recording_func

        def generate_linear_move_func(movement):
            def linear_move_func(state):
                if state:
                    result = self.nonblocking_move(self.move_linear_relative, movement)
                    if self.mode == MemoryType.RELATIVE and result:
                        self.save(MemoryType.RELATIVE, MotionType.LINEAR, movement)

            return linear_move_func

        end_effector_func = {
            EndEffectorType.NO_END_EFFECTOR: replay_func,
            EndEffectorType.GRIPPER: gripper_func,
            EndEffectorType.SUCTION_CUP: suction_cup_func,
        }

        self.keymap = Keymap(
            cross_pressed=save_func,
            square_pressed=mode_func,
            triangle_pressed=delete_func,
            circle_pressed=end_effector_func[self.end_effector],
            r1_changed=generate_cycle_joint_func(operator.add),
            l1_changed=generate_cycle_joint_func(operator.sub),
            r2_changed=generate_button2_recording_func(
                list(self.controller_buffer.keys())[0]
            ),
            l2_changed=generate_button2_recording_func(
                list(self.controller_buffer.keys())[1]
            ),
            left_joystick_changed=generate_joystick_recording_func(
                list(self.controller_buffer.keys())[2]
            ),
            right_joystick_changed=generate_joystick_recording_func(
                list(self.controller_buffer.keys())[3]
            ),
            dpad_up=generate_linear_move_func([-self.linear_speed, 0, 0, 0]),
            dpad_down=generate_linear_move_func([self.linear_speed, 0, 0, 0]),
            dpad_left=generate_linear_move_func([0, -self.linear_speed, 0, 0]),
            dpad_right=generate_linear_move_func([0, self.linear_speed, 0, 0]),
        )

    def load_memory(self, filename: str = "memory.json") -> bool:
        """
        Load the memory from a file under ./recordings/

        Args:
            filename (str, optional): The name of the file to load the memory from. Defaults to "memory.json".

        Returns:
            bool: True if the memory was loaded successfully, False otherwise.
        """
        if not filename.endswith(".json"):
            filename += ".json"
        try:
            with open("./recordings/" + filename, "r") as f:
                self.memory = [MemoryEntry.from_dict(entry) for entry in json.load(f)]
                self.add_feed(f"Loaded memory from {filename}", "Recorder")
        except FileNotFoundError:
            return False
        return True

    def dump_memory(self, filename: str = "memory.json"):
        """
        Dump the memory to a file under ./recordings/

        Args:
            filename (str, optional): The name of the file to dump the memory to. Defaults to "memory.json".
        """
        if not filename.endswith(".json"):
            filename += ".json"
        with open("./recordings/" + filename, "w") as f:
            json.dump([entry.serialize() for entry in self.memory], f, indent=4)
            self.add_feed(f"Dumped memory to {filename}", "Recorder")

    def start(self):
        """
        Start the recording.
        """
        self.running = True
        self.add_feed("Started recording", "Recorder")
        super().start()

    def stop(self):
        """
        Stop the recording and dump the memory to a file.
        """
        self.add_feed("Shutting down", "Recorder")
        self.running = False
        self.join()

        self.dump_memory()

        self.close_robot()
        self.controller.close()
        time.sleep(1)

    def bound_movement(self, movement: list) -> list:
        """
        Bound the movement of the robot in an attempt to prevent invalid movements.

        Args:
            movement (list): The movement to be bounded.

        Returns:
            list: The bounded movement.

        Raises:
            Exception: If no angles are available.
        """

        current_angles = self.angles.copy()

        if current_angles.size:
            attempted_angles = current_angles + movement
            attempted_angles = np.clip(
                attempted_angles, self.joint_bounds[:, 0], self.joint_bounds[:, 1]
            )
            return attempted_angles - current_angles
        else:
            raise Exception("No angles available")

    def move_robot(self):
        """
        Move the robot according to the controller buffer values.
        """
        movement = [0] * self.number_of_joints
        movement[self.active_joint] = (
            self.controller_buffer["joint_pos"] - self.controller_buffer["joint_neg"]
        ) * self.max_speed[self.active_joint]
        movement[self.joystick_mapping["left"]] += (
            self.controller_buffer["left_joystick"]
            * self.max_speed[self.joystick_mapping["left"]]
        )
        movement[self.joystick_mapping["right"]] += (
            self.controller_buffer["right_joystick"]
            * self.max_speed[self.joystick_mapping["right"]]
        )
        movement = self.bound_movement(movement)
        movement = np.where(np.abs(movement) < 0.5, 0, movement)
        if np.any(movement):
            try:
                self.move_joint_relative(movement)
                if self.mode == MemoryType.RELATIVE and np.abs(np.sum(movement)) > 0:
                    self.save(MemoryType.RELATIVE, MotionType.JOINT, movement)
            except ConnectionAbortedError:
                self.add_feed("Connection aborted", "Recorder")

    def optimize_relative_movement(self):
        """
        Optimize the relative movement in the memory by grouping consecutive relative movements in the same directions.
        """
        optimized_memory = [self.memory[0]]
        for entry in self.memory[1:]:
            if (
                entry.type == optimized_memory[-1].type == MemoryType.RELATIVE
                and entry.motion_type == optimized_memory[-1].motion_type
                and np.array_equal(
                    np.sign(entry.value), np.sign(optimized_memory[-1].value)
                )
            ):
                optimized_memory[-1].value = np.array(
                    optimized_memory[-1].value
                ) + np.array(entry.value)
                if not entry.valid:
                    optimized_memory[-1].valid = False
            else:
                optimized_memory.append(entry)
        self.memory = optimized_memory

    def run(self):
        """
        Main loop for the robot recording. Moving the robot and updating the displayed pose and angles.
        """
        while self.running:
            for _ in range(10):
                self.move_robot()
            self.displayed_pose[:] = self.pose
            self.displayed_angles[:] = self.angles
