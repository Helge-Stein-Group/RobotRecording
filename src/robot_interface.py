import os
import sys
import time

import numpy as np

sys.path.append(os.path.join(os.getcwd(), "TCP-IP-4Axis-Python-main"))
from dobot_api import (
    DobotApiDashboard,
    DobotApi,
    DobotApiMove,
    MyType,
    alarmAlarmJsonFile,
)

from utils import MemoryType, CoordinateSystem


class RobotInterface:
    def __init__(
            self,
            robot_ip: str = "192.168.1.6",
            dashboard_port: int = 29999,
            move_port: int = 30003,
            feed_port: int = 30004,
            number_of_joints: int = 4,
    ):
        self.dashboard = None
        self.move = None
        self.feed = None

        self.robot_ip = robot_ip
        self.identifier = robot_ip.split(".")[1]
        self.dashboard_port = dashboard_port
        self.move_port = move_port
        self.feed_port = feed_port

        self.number_of_joints = number_of_joints

        self.connect_robot()
        self.init_robot()

    def connect_robot(self):
        try:
            self.log_robot("Connecting")
            self.dashboard = DobotApiDashboard(self.robot_ip, self.dashboard_port, False)
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

    def log_robot(self, msg: str):
        print(f"[ROBOT][{self.identifier}] {msg}")

    @property
    def pose(self):
        """
        return pose in [x, y, z, r] format
        """
        result = self.dashboard.GetPose()
        pose = np.fromstring(result[result.find("{") + 1: result.find("}")], sep=",")
        return pose[:self.number_of_joints]

    @property
    def angles(self):
        """
        return angles in [j1, j2, j3, j4] format
        """
        result = self.dashboard.GetAngle()
        angles = np.fromstring(result[result.find("{") + 1: result.find("}")], sep=",")
        return angles[:self.number_of_joints]

    def replay(self, memory, optimize_movements: bool = False):
        self.log_robot("Replaying")
        if optimize_movements:
            memory = self.optimize_movement(memory)
        for entry in memory:
            if entry.type == MemoryType.POINT:
                if entry.coordinate_system == CoordinateSystem.WORLD:
                    self.move.MovL(*entry.value)
                elif entry.coordinate_system == CoordinateSystem.JOINT:
                    self.move.MovJ(*entry.value)
            elif entry.type == MemoryType.MOVEMENT:
                if entry.coordinate_system == CoordinateSystem.WORLD:
                    self.move.RelMovL(*entry.value)
                elif entry.coordinate_system == CoordinateSystem.JOINT:
                    self.move.RelMovJ(*entry.value)
            self.move.Sync()
    
    def optimize_movement(self, memory):
        optimized_memory = []
        for entry in memory:
            if entry.type == MemoryType.MOVEMENT and optimized_memory[-1].type == MemoryType.MOVEMENT and entry.coordinate_system == optimized_memory[-1].coordinate_system:
                optimized_memory[-1].value += entry.value
            else:
                optimized_memory.append(entry)
        return optimized_memory
