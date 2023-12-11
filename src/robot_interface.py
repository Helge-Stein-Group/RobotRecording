import json
import time

import numpy as np

from include.dobot_api import (
    DobotApiDashboard,
    DobotApi,
    DobotApiMove,
)
from utils import MemoryType, MotionType


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
        self.dashboard = None
        self.move = None
        self.feed = None

        self.robot_ip = robot_ip
        self.identifier = robot_ip.split(".")[1]
        self.dashboard_port = dashboard_port
        self.move_port = move_port
        self.feed_port = feed_port
        self.error_translation = json.load(open("../data/translation.json", "r"))

        self.number_of_joints = number_of_joints

        self.start_angles = np.array([0, 0, 220, 0])

        self.print_function = print_function

        self.connect_robot()
        self.init_robot()

    def connect_robot(self):
        try:
            self.log_robot("Connecting")
            self.dashboard = DobotApiDashboard(
                self.robot_ip, self.dashboard_port, False
            )
            self.move = DobotApiMove(self.robot_ip, self.move_port, False)
            self.feed = DobotApi(self.robot_ip, self.feed_port)
            self.log_robot("Connection successful")
        except Exception as e:
            self.log_robot("Connection failure")
            raise e

    def init_robot(self):
        self.dashboard.ClearError()
        time.sleep(0.5)
        self.dashboard.EnableRobot()
        self.dashboard.SpeedJ(100)

        self.move.MovJ(*self.start_angles)

    def reconnect(self):
        self.log_robot("Connection lost")
        self.log_robot("Trying to reconnect")
        self.close_robot()
        self.connect_robot()
        self.init_robot()

    def close_robot(self):
        self.dashboard.close()
        self.move.close()
        self.feed.close()

    def log_robot(self, msg: str):
        self.print_function(msg, f"Robot {self.identifier}")

    def clear_error(self):
        self.log_robot("Clearing error (" + str(self.error_id) + ")")
        self.dashboard.ClearError()
        time.sleep(0.5)
        self.dashboard.EnableRobot()

    def nonblocking_move(self, func, *params) -> bool:
        func(*params)
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
            result = self.dashboard.GetPose()

            pose = np.fromstring(
                result[result.find("{") + 1 : result.find("}")], sep=","
            )
            return pose[: self.number_of_joints]
        except Exception as e:
            self.log_robot(f"Error getting pose {e}")
            self.reconnect()

    @property
    def angles(self):
        """
        return angles in [j1, j2, j3, j4] format
        """
        try:
            result = self.dashboard.GetAngle()
            angles = np.fromstring(
                result[result.find("{") + 1 : result.find("}")], sep=","
            )[: self.number_of_joints]
            if angles.size:
                return angles
            else:
                raise Exception("No angles available")
        except Exception as e:
            self.log_robot(f"Error getting angles {e}")
            self.reconnect()

    @property
    def error_id(self):
        try:
            result = self.dashboard.GetErrorID()

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
            print(e)
            self.log_robot(f"Error getting error id {e}")
            self.reconnect()

    def replay(self, memory):
        self.log_robot("Replaying")
        for entry in memory:
            if entry.type == MemoryType.POINT:
                if entry.motion_type == MotionType.LINEAR:
                    func = self.move.MovL
                elif entry.motion_type == MotionType.JOINT:
                    func = self.move.MovJ
            elif entry.type == MemoryType.MOVEMENT:
                if entry.motion_type == MotionType.LINEAR:
                    func = self.move.RelMovL
                elif entry.motion_type == MotionType.JOINT:
                    func = self.move.RelMovJ

            result = self.nonblocking_move(func, *entry.value)
            if not result:
                self.log_robot(
                    f"Error replaying from {self.pose if entry.motion_type == MemoryType.POINT else self.angles} "
                )
                self.log_robot(f"Error replaying to {entry.value}")
                break
            self.move.Sync()
        self.log_robot("Done Replaying")
