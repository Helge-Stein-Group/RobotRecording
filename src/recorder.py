import colorsys
import json
import operator
import threading
import time

from controller_interface import ControllerInterface
from robot_interface import RobotInterface
from utils import *
from display_interface import DisplayInterface


class RobotRecorder(threading.Thread, RobotInterface, ControllerInterface):
    def __init__(
        self,
        robot_ip: str = "192.168.1.6",
        dashboard_port: int = 29999,
        move_port: int = 30003,
        feed_port: int = 30004,
        number_of_joints: int = 4,
        return_to_start: bool = True,
        max_speed: np.ndarray = np.array([5, 5, 5, 15]),
        linear_speed: float = 5,
        keymap: Keymap = None,
        left_joystick_joint: int = 0,
        right_joystick_joint: int = 1,
        joint_bounds: np.ndarray = np.array(
            [[-80, 80], [-125, 125], [80, 245], [-355, 355]]
        ),
        save_path: str = "memory.json",
    ):
        self.robot_ip = robot_ip
        self.dashboard_port = dashboard_port
        self.move_port = move_port
        self.feed_port = feed_port
        self.number_of_joints = number_of_joints

        self.feed_log = []
        self.memory = []
        self.display_pose = [0, 0, 0, 0]
        self.display_angles = [0, 0, 0, 0]
        threading.Thread.__init__(self)
        self.init_robot_connection()
        ControllerInterface.__init__(self, keymap, self.add_feed)
        self.display_interface = DisplayInterface(
            lambda: self.display_pose,
            lambda: self.display_angles,
            lambda: self.memory,
            lambda: self.feed_log,
            self.clear_error,
            self.dump_memory,
            self.stop,
        )

        self.current_joint_pos = 0
        self.current_joint_neg = 0
        self.left_joystick = 0
        self.right_joystick = 0

        self.return_to_start = return_to_start
        self.max_speed = max_speed
        self.linear_speed = linear_speed
        if self.keymap is None:
            self.default_keymap()
        self.left_joystick_joint = left_joystick_joint
        self.right_joystick_joint = right_joystick_joint
        self.joint_bounds = joint_bounds
        self.save_path = save_path

        self.active_joint = number_of_joints // 2

        self.mode = MemoryType.POINT
        self.running = False

        if return_to_start:
            entry = MemoryEntry(MemoryType.POINT, self.start_angles, MotionType.JOINT)
            self.memory.append(entry)
            self.memory.append(entry)

        self.indicate_active_joint()

        self.set_controls()

    def init_robot_connection(self):
        RobotInterface.__init__(
            self,
            self.robot_ip,
            self.dashboard_port,
            self.move_port,
            self.feed_port,
            self.number_of_joints,
            self.add_feed,
        )

    def add_feed(self, msg: str, source: str):
        self.feed_log.append(FeedEntry(datetime.now(), msg, source))

    def save(self, memory_type, value, motion_type):
        entry = MemoryEntry(memory_type, value, motion_type)
        if self.return_to_start:
            self.memory.insert(-1, entry)
        else:
            self.memory.append(entry)

    def indicate_active_joint(self):
        color = (
            np.array(
                colorsys.hsv_to_rgb(self.active_joint / self.number_of_joints, 1, 1)
            )
            * 255
        )
        color = [int(c) for c in color]
        self.controller.light.setColorI(*color)

    def indicate_mode(self):
        if self.mode == MemoryType.POINT:
            self.controller.audio.setMicrophoneLED(False)
        else:
            self.controller.audio.setMicrophoneLED(True)

    def default_keymap(self):
        def save_func(state):
            if state:
                self.save(MemoryType.POINT, self.pose, MotionType.JOINT)

        def mode_func(state):
            if state:
                if self.mode == MemoryType.POINT:
                    self.mode = MemoryType.MOVEMENT
                    # QOL
                    self.save(MemoryType.POINT, self.pose, MotionType.JOINT)
                else:
                    self.mode = MemoryType.POINT
                self.indicate_mode()

        def delete_func(state):
            if state and self.memory:
                del self.memory[-2 if self.return_to_start else -1]

        def replay_func(state):
            if state:
                self.replay(self.memory)

        def generate_cycle_joint_func(op):
            def cycle_joint_func(state):
                if state:
                    self.active_joint = op(self.active_joint, 1) % self.number_of_joints
                    self.indicate_active_joint()

            return cycle_joint_func

        def generate_button2_recording_func(attr_str):
            def button2_recording_func(state):
                if state > 5:
                    self.__setattr__(attr_str, state / 255)
                else:
                    self.__setattr__(attr_str, 0)

            return button2_recording_func

        def generate_joystick_recording_func(attr_str):
            def joystick_recording_func(stateX, stateY):
                if np.abs(stateX) > 5:
                    self.__setattr__(attr_str, stateX / 128)
                else:
                    self.__setattr__(attr_str, 0)

            return joystick_recording_func

        def generate_linear_move_func(movement):
            def linear_move_func(state):
                if state:
                    result = self.nonblocking_move(self.move.RelMovL, *movement)
                    if self.mode == MemoryType.MOVEMENT and result:
                        self.save(MemoryType.MOVEMENT, movement, MotionType.LINEAR)

            return linear_move_func

        self.keymap = Keymap(
            cross_pressed=save_func,
            square_pressed=mode_func,
            triangle_pressed=delete_func,
            circle_pressed=replay_func,
            r1_changed=generate_cycle_joint_func(operator.add),
            l1_changed=generate_cycle_joint_func(operator.sub),
            r2_changed=generate_button2_recording_func("current_joint_pos"),
            l2_changed=generate_button2_recording_func("current_joint_neg"),
            left_joystick_changed=generate_joystick_recording_func("left_joystick"),
            right_joystick_changed=generate_joystick_recording_func("right_joystick"),
            dpad_up=generate_linear_move_func([-self.linear_speed, 0, 0, 0]),
            dpad_down=generate_linear_move_func([self.linear_speed, 0, 0, 0]),
            dpad_left=generate_linear_move_func([0, -self.linear_speed, 0, 0]),
            dpad_right=generate_linear_move_func([0, self.linear_speed, 0, 0]),
        )

    def dump_memory(self):
        with open(self.save_path, "w") as f:
            json.dump([entry.serialize() for entry in self.memory], f, indent=4)
            self.add_feed(f"Dumped memory to {self.save_path}", "Recorder")

    def start(self):
        self.running = True
        self.add_feed("Started recording", "Recorder")
        super().start()
        self.display_interface.start()

    def stop(self):
        self.add_feed("Shutting down", "Recorder")
        self.running = False
        self.join()

        self.dump_memory()

        self.close_robot()
        self.controller.close()
        time.sleep(1)

    def bound_movement(self, movement: list):
        current_angles = self.angles
        if np.any(self.angles):
            attempted_angles = current_angles + movement
            attempted_angles = np.clip(
                attempted_angles, self.joint_bounds[:, 0], self.joint_bounds[:, 1]
            )
            return attempted_angles - current_angles
        else:
            raise Exception("No angles available")

    def move_robot(self):
        current_joint = self.current_joint_pos - self.current_joint_neg
        movement = [0] * self.number_of_joints
        movement[self.active_joint] = current_joint * self.max_speed[self.active_joint]
        movement[self.left_joystick_joint] += (
            self.left_joystick * self.max_speed[self.left_joystick_joint]
        )
        movement[self.right_joystick_joint] += (
            self.right_joystick * self.max_speed[self.right_joystick_joint]
        )

        bounded_movement = self.bound_movement(movement)
        bounded_movement = np.where(np.abs(bounded_movement) < 0.5, 0, bounded_movement)
        if np.any(bounded_movement):
            try:
                self.move.RelMovJ(*bounded_movement)
                self.move.Sync()
                if self.mode == MemoryType.MOVEMENT:
                    self.save(MemoryType.MOVEMENT, movement, MotionType.JOINT)
            except ConnectionAbortedError:
                self.add_feed("Robot connection aborted", "Recorder")
                self.init_robot_connection()

    def run(self):
        while self.running:
            for _ in range(10):
                self.move_robot()
            self.display_pose = self.pose
            self.display_angles = self.angles


if __name__ == "__main__":
    recorder = RobotRecorder()
    recorder.start()

    import keyboard

    while True:
        if keyboard.is_pressed("q"):
            recorder.stop()
            break
        time.sleep(0.1)
