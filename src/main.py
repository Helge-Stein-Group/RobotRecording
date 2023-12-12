from dashboard import Dashboard
from recorder import RobotRecorder
from threading import Event
import time

if __name__ == "__main__":
    recorder = RobotRecorder()
    time.sleep(1)
    recorder.start()

    shutdown_event = Event()

    dashboard = Dashboard(
        lambda: recorder.current_pose,  # lambda is necessary to update address of variable
        lambda: recorder.current_angles,
        lambda: recorder.memory,
        lambda: recorder.feed_log,
        recorder.clear_error,
        recorder.reconnect,
        recorder.dump_memory,
        recorder.stop,
        recorder.optimize_linear_movement,
        shutdown_event,
        recorder.set_joint_speed,
        recorder.set_linear_speed,
        recorder.set_joint_acceleration,
        recorder.set_linear_acceleration,
        recorder.is_alive,
        recorder.robot_is_alive,
        recorder.controller_is_alive,
    )
    dashboard.run()

    shutdown_event.wait()
