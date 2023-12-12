import json
import time
import re

import numpy as np

from include.dobot_api import (
    DobotApiDashboard,
    DobotApi,
    DobotApiMove,
)
from utils import MemoryType, MotionType
import threading


class RobotInterface:
    def __init__(
        self,
        robot_ip: str = "192.168.1.6",
        dashboard_port: int = 29999,
        move_port: int = 30003,
        feed_port: int = 30004,
        number_of_joints: int = 4,
        print_function: callable = print,
    ):
        self._dashboard = None
        self._move = None
        self.feed = None  # unused

        self.dashboard_lock = threading.Lock()

        self.robot_ip = robot_ip
        self.identifier = robot_ip.split(".")[1]
        self.dashboard_port = dashboard_port
        self.move_port = move_port
        self.feed_port = feed_port
        self.error_translation = json.load(open("../data/translation.json", "r"))

        self.number_of_joints = number_of_joints

        self.start_pose = np.array([0, 0, 220, 0])

        self.print_function = print_function

        self.connect_robot()
        self.init_robot()

    def connect_robot(self):
        try:
            self.log_robot("Connecting")
            self._dashboard = DobotApiDashboard(
                self.robot_ip, self.dashboard_port, False
            )
            self._move = DobotApiMove(self.robot_ip, self.move_port, False)
            self.feed = DobotApi(self.robot_ip, self.feed_port)
            self.log_robot("Connection successful")
        except Exception as e:
            self.log_robot("Connection failure")
            raise e

    def init_robot(self):
        with self.dashboard_lock:
            self._dashboard.ClearError()
            time.sleep(0.5)
            self._dashboard.EnableRobot()
            self._dashboard.SpeedJ(100)

        self.move_joint(self.start_pose)

    def reconnect(self):
        self.log_robot("Connection lost")
        self.log_robot("Trying to reconnect")
        self.close_robot()
        time.sleep(0.5)
        self.connect_robot()
        self.init_robot()

    def close_robot(self):
        with self.dashboard_lock:
            self._dashboard.close()
        self._move.close()
        self.feed.close()

    def move_joint(self, cartesian_coordinates):
        self._move.MovJ(*cartesian_coordinates)
        self._move.Sync()

    def move_linear(self, cartesian_coordinates):
        self._move.MovL(*cartesian_coordinates)
        self._move.Sync()

    def move_joint_relative(self, movement):
        self._move.RelMovJ(*movement)
        self._move.Sync()

    def move_linear_relative(self, movement):
        self._move.RelMovL(*movement)
        self._move.Sync()

    def robot_is_alive(self):
        try:
            with self.dashboard_lock:
                self._dashboard.GetPose()
            return True
        except:
            return False

    def set_joint_speed(self, speed):
        self.log_robot(f"Setting joint speed to {speed}")
        with self.dashboard_lock:
            self._dashboard.SpeedJ(int(speed))

    def set_linear_speed(self, speed):
        self.log_robot(f"Setting linear speed to {speed}")
        with self.dashboard_lock:
            self._dashboard.SpeedL(int(speed))

    def set_joint_acceleration(self, acceleration):
        self.log_robot(f"Setting joint acceleration to {acceleration}")
        with self.dashboard_lock:
            self._dashboard.AccJ(int(acceleration))

    def set_linear_acceleration(self, acceleration):
        self.log_robot(f"Setting linear acceleration to {acceleration}")
        with self.dashboard_lock:
            self._dashboard.AccL(int(acceleration))

    def log_robot(self, msg: str):
        self.print_function(msg, f"Robot {self.identifier}")

    def clear_error(self):
        self.log_robot("Clearing error (" + str(self.error_id) + ")")
        with self.dashboard_lock:
            self._dashboard.ClearError()
            time.sleep(0.5)
            self._dashboard.EnableRobot()

    def nonblocking_move(self, func, params) -> bool:
        func(params)
        if self.error_id:
            self.log_robot(f"Invalid movement [{self.error_id}]")
            self.clear_error()
            return False
        return True

    @property
    def pose(self):
        """
        return pose in [x, y, z, r] format
        """
        try:
            with self.dashboard_lock:
                result = self._dashboard.GetPose()

            pose = np.fromstring(
                result[result.find("{") + 1 : result.find("}")], sep=","
            )[: self.number_of_joints]
            if pose.size:
                return pose
            else:
                raise Exception("No pose available")
        except Exception as e:
            self.log_robot(f"Error getting pose {e}")
            return np.array([0, 0, 0, 0])

    @property
    def angles(self):
        """
        return angles in [j1, j2, j3, j4] format
        """
        try:
            with self.dashboard_lock:
                result = self._dashboard.GetAngle()
            angles = np.fromstring(
                result[result.find("{") + 1 : result.find("}")], sep=","
            )[: self.number_of_joints]
            if angles.size:
                return angles
            else:
                raise Exception("No angles available")
        except Exception as e:
            self.log_robot(f"Error getting angles {e}")
            return np.array([0, 0, 0, 0])

    @property
    def error_id(self):
        try:
            with self.dashboard_lock:
                result = self._dashboard.GetErrorID()

            string = result[result.find("{") + 1 : result.find("}")]
            data = json.loads(string)
            error_ids = [
                str(item) if int(item) >= 0 else 0
                for sublist in data
                for item in sublist
            ]
            translations = []
            for error_id in error_ids:
                if error_id in self.error_translation:
                    translations.append(self.error_translation[error_id])
                else:
                    translations.append(f"Unknown error {error_id}")

            if len(translations) > 0:
                translations = translations[0]
            return translations
        except Exception as e:
            self.log_robot(f"Error getting error id {e}")
            print("Result", result)
        except json.decoder.JSONDecodeError:
            self.log_robot(f"Error in JSON parsing")
            return []

    def replay(self, memory):
        self.log_robot("Replaying")
        for entry in memory:
            if entry.type == MemoryType.POINT:
                if entry.motion_type == MotionType.LINEAR:
                    func = self.move_linear
                elif entry.motion_type == MotionType.JOINT:
                    func = self.move_joint
            elif entry.type == MemoryType.MOVEMENT:
                if entry.motion_type == MotionType.LINEAR:
                    func = self.move_linear_relative
                elif entry.motion_type == MotionType.JOINT:
                    func = self.move_joint_relative

            result = self.nonblocking_move(func, *entry.value)
            if not result:
                self.log_robot(
                    f"Error replaying from {self.pose if entry.motion_type == MemoryType.POINT else self.angles} "
                )
                self.log_robot(f"Error replaying to {entry.value}")
                break
            self._move.Sync()
        self.log_robot("Done Replaying")
