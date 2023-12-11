from dashboard import Dashboard
from recorder import RobotRecorder
from threading import Event

if __name__ == "__main__":
    recorder = RobotRecorder()
    recorder.start()

    shutdown_event = Event()

    dashboard = Dashboard(
        lambda: recorder.current_pose,  # lambda is necessary to update adress of variable
        lambda: recorder.current_angles,
        lambda: recorder.memory,
        lambda: recorder.feed_log,
        recorder.clear_error,
        recorder.dump_memory,
        recorder.stop,
        recorder.optimize_linear_movement,
        shutdown_event,
    )
    dashboard.run()

    shutdown_event.wait()
