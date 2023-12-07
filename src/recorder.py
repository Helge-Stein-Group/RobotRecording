import colorsys
import operator
import os
import time
import threading
import json
import numpy as np
import pydualsense
import curses


from robot_interface import RobotInterface
from controller_interface import ControllerInterface
from utils import *


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
            joint_bounds: np.ndarray = np.array([
                [-80, 80],
                [-125, 125],
                [80, 245],
                [-355, 355]
            ]),
            save_path: str = "memory.json"
    ):
        threading.Thread.__init__(self)
        RobotInterface.__init__(self, robot_ip, dashboard_port, move_port, feed_port, number_of_joints)
        ControllerInterface.__init__(self, keymap)

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

        self.memory = []
        if return_to_start:
            self.memory.append(MemoryEntry(MemoryType.POINT, self.pose, CoordinateSystem.WORLD))

        self.active_joint = number_of_joints // 2
        self.indicate_active_joint()

        self.set_controls()

        self.mode = MemoryType.POINT
        self.running = False

    def save(self, value, mode, coordinate_system):
        entry = MemoryEntry(mode, value, coordinate_system)
        if self.return_to_start:
            self.memory.insert(-1, entry)
        else:
            self.memory.append(entry)

    def indicate_active_joint(self):
        color = np.array(colorsys.hsv_to_rgb(self.active_joint / self.number_of_joints, 1, 1)) * 255
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
                self.save(self.pose, MemoryType.POINT, CoordinateSystem.WORLD)

        def mode_func(state):
            if state:
                if self.mode == MemoryType.POINT:
                    self.mode = MemoryType.MOVEMENT
                else:
                    self.mode = MemoryType.POINT
                self.indicate_mode()

        def delete_func(state):
            if state:
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
                    self.move.RelMovL(*movement) # missing bounds
                    if self.mode == MemoryType.MOVEMENT:
                        self.save(movement, self.mode, CoordinateSystem.WORLD)

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
            print(f"Saved memory to {self.save_path}")

    def start(self):
        self.running = True
        print("Ready")
        super().start()

    def stop(self):
        self.running = False
        self.join()

        self.dump_memory()

        self.dashboard.close()
        self.move.close()
        self.feed.close()
        self.controller.close()
        time.sleep(1)

    def bound_movement(self, movement: list):
        current_angles = self.angles
        attempted_angles = current_angles + movement
        attempted_angles = np.clip(attempted_angles, self.joint_bounds[:, 0], self.joint_bounds[:, 1])
        return attempted_angles - current_angles

    def move_robot(self):
        current_joint = self.current_joint_pos - self.current_joint_neg
        movement = [0] * self.number_of_joints
        movement[self.active_joint] = current_joint * self.max_speed[self.active_joint]
        movement[self.left_joystick_joint] += self.left_joystick * self.max_speed[self.left_joystick_joint]
        movement[self.right_joystick_joint] += self.right_joystick * self.max_speed[self.right_joystick_joint]

        bounded_movement = self.bound_movement(movement)
        bounded_movement = np.where(np.abs(bounded_movement) < 0.5, 0, bounded_movement)
        if np.any(bounded_movement):
            self.move.RelMovJ(*bounded_movement)
            self.move.Sync()
            if self.mode == MemoryType.MOVEMENT:
                self.save(bounded_movement, self.mode, CoordinateSystem.JOINT)


    def run(self):
        stdscr = curses.initscr()  # Initialize curses
        curses.noecho()  # Turn off automatic echoing of keys to the screen
        curses.cbreak()  # React to keys instantly, without requiring the Enter key
        stdscr.keypad(True)  # Interpret special keys like Backspace, Delete, and the four arrow keys

        try:
            while self.running:
                stdscr.clear()  # Clear the screen
                stdscr.addstr(0, 0, "Pose: [" + ", ".join("{:.2f}".format(p) for p in self.pose) + "]")
                stdscr.addstr(1, 0, "Angles: [" + ", ".join("{:.2f}".format(a) for a in self.angles) + "]")
                if self.return_to_start:
                    stdscr.addstr(2, 0, "Return Pose: \n" + str(self.memory[-1]))

                stdscr.addstr(3, 0, "Memory: \n")
                for i, entry in enumerate(self.memory):
                    stdscr.addstr(4 + i, 0, f"[{entry.type.name}][{entry.coordinate_system.name}] {entry.value}")
                stdscr.refresh()  # Refresh the screen
                for _ in range(10):
                    self.move_robot()
        finally:
            curses.echo()
            curses.nocbreak()
            stdscr.keypad(False)
            curses.endwin()  # Restore the terminal to its original operating mode


if __name__ == "__main__":
    import keyboard

    recorder = RobotRecorder()
    recorder.start()

    print("Press the spacebar to stop the recorder...")
    keyboard.wait('space')

    recorder.stop()
      