import time
from utils import AirPumpPins, EndEffectorType
from dashboard import Dashboard
from recorder import RobotRecorder


if __name__ == "__main__":
    recorder = RobotRecorder(
        end_effector=EndEffectorType.SUCTION_CUP,
        end_effector_pins=AirPumpPins(13, 12),
        end_effector_state=0,
    )
    time.sleep(1)
    recorder.start()

    dashboard = Dashboard(
        lambda: recorder.displayed_pose,  # lambda is necessary to update address of variable
        lambda: recorder.displayed_angles,
        lambda: recorder.memory,
        lambda: recorder.feed,
        recorder.clear_error,
        recorder.reconnect,
        recorder.dump_memory,
        recorder.load_memory,
        recorder.stop,
        recorder.optimize_relative_movement,
        recorder.replay,
        recorder.set_joint_speed,
        recorder.set_linear_speed,
        recorder.set_joint_acceleration,
        recorder.set_linear_acceleration,
        recorder.is_alive,
        recorder.robot_is_alive,
        recorder.controller_is_alive,
        recorder.set_end_effector,
        recorder.set_end_effector_pins,
        recorder.set_end_effector_state,
    )
    dashboard.run()
