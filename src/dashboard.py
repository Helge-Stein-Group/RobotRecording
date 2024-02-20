import typing

import dash
import logging
import numpy as np
import dash_daq as daq
import plotly.io as pio
import dash_bootstrap_components as dbc

from dash import html, dcc, ctx
from dash.dash_table import DataTable
from dash.dependencies import Input, Output, State

# Ensure dash is not spamming the console
log = logging.getLogger("werkzeug")
log.setLevel(logging.CRITICAL)

pio.templates.default = "plotly_white"


class Dashboard:
    """
    Dashboard class to record a robot sequence and display some monitoring.

    Attributes:
        get_pose (callable): Function to get the current pose of the robot.
        get_angles (callable): Function to get the current angles of the robot.
        get_memory (callable): Function to get the current memory of the robot.
        get_feed (callable): Function to get the current feed of the robot.
        func_clear_error (callable): Function to clear the error of the robot.
        func_reconnect (callable): Function to reconnect the robot.
        func_save (callable): Function to save the memory of the robot.
        func_load (callable): Function to load the memory of the robot.
        func_stop (callable): Function to stop the robot.
        func_bundle (callable): Function to bundle the memory of the robot.
        func_replay (callable): Function to replay the memory of the robot.
        set_speed_joint (callable): Function to set the joint speed of the robot.
        set_speed_linear (callable): Function to set the linear speed of the robot.
        set_acc_joint (callable): Function to set the joint acceleration of the robot.
        set_acc_linear (callable): Function to set the linear acceleration of the robot.
        status_recorder (callable): Function to check the status of the recorder.
        status_robot (callable): Function to check the status of the robot.
        status_controller (callable): Function to check the status of the controller.
        app (dash.Dash): The dash app.

    Methods:
        modals: Returns the modals for the dashboard.
        title: Returns the title for the dashboard.
        save_button: Returns the save button for the dashboard.
        save_button_callback: Registers the save button callback.
        load_button: Returns the load button for the dashboard.
        load_button_callback: Registers the load button callback.
        bundle_button: Returns the bundle button for the dashboard.
        bundle_button_callback: Registers the bundle button callback.
        clear_error_button: Returns the clear error button for the dashboard.
        clear_error_button_callback: Registers the clear error button callback.
        reconnect_button: Returns the reconnect button for the dashboard.
        reconnect_button_callback: Registers the reconnect button callback.
        stop_button: Returns the stop button for the dashboard.
        stop_button_callback: Registers the stop button callback.
        keymap_button: Returns the keymap button for the dashboard.
        keymap_button_callback: Registers the keymap button callback.
        replay_button: Returns the replay button for the dashboard.
        replay_button_callback: Registers the replay button callback.
        control_buttons: Returns the control buttons for the dashboard.
        joint_speed_slider: Returns the joint speed slider for the dashboard.
        joint_speed_slider_callback: Registers the joint speed slider callback.
        linear_speed_slider: Returns the linear speed slider for the dashboard.
        linear_speed_slider_callback: Registers the linear speed slider callback.
        joint_acceleration_slider: Returns the joint acceleration slider for the dashboard.
        joint_acceleration_slider_callback: Registers the joint acceleration slider callback.
        linear_acceleration_slider: Returns the linear acceleration slider for the dashboard.
        linear_acceleration_slider_callback: Registers the linear acceleration slider callback.
        movement_sliders: Returns the movement sliders for the dashboard.
        recorder_status: Returns the recorder status for the dashboard.
        recorder_status_callback: Registers the recorder status callback.
        robot_status: Returns the robot status for the dashboard.
        robot_status_callback: Registers the robot status callback.
        controller_status: Returns the controller status for the dashboard.
        controller_status_callback: Registers the controller status callback.
        indicators: Returns the indicators for the dashboard.
        pose_display: Returns the pose display for the dashboard.
        pose_display_callback: Registers the pose display callback.
        angles_display: Returns the angles display for the dashboard.
        angles_display_callback: Registers the angles display callback.
        memory_table: Returns the memory table for the dashboard.
        memory_table_callback: Registers the memory table callback.
    """

    def __init__(
        self,
        get_pose,
        get_angles,
        get_memory,
        get_feed,
        func_clear_error,
        func_reconnect,
        func_save,
        func_load,
        func_stop,
        func_bundle,
        func_replay,
        set_speed_joint,
        set_speed_linear,
        set_acc_joint,
        set_acc_linear,
        status_recorder,
        status_robot,
        status_controller,
    ):
        """
        Initializes the Dashboard class.

        Args:
            get_pose (callable): Function to get the current pose of the robot.
            get_angles (callable): Function to get the current angles of the robot.
            get_memory (callable): Function to get the current memory of the robot.
            get_feed (callable): Function to get the current feed of the robot.
            func_clear_error (callable): Function to clear the error of the robot.
            func_reconnect (callable): Function to reconnect the robot.
            func_save (callable): Function to save the memory of the robot.
            func_load (callable): Function to load the memory of the robot.
            func_stop (callable): Function to stop the robot.
            func_bundle (callable): Function to bundle the memory of the robot.
            func_replay (callable): Function to replay the memory of the robot.
            set_speed_joint (callable): Function to set the joint speed of the robot.
            set_speed_linear (callable): Function to set the linear speed of the robot.
            set_acc_joint (callable): Function to set the joint acceleration of the robot.
            set_acc_linear (callable): Function to set the linear acceleration of the robot.
            status_recorder (callable): Function to check the status of the recorder.
            status_robot (callable): Function to check the status of the robot.
            status_controller (callable): Function to check the status of the controller.
        """
        self.get_pose = get_pose
        self.get_angles = get_angles
        self.get_memory = get_memory
        self.get_feed = get_feed
        self.func_clear_error = func_clear_error
        self.func_reconnect = func_reconnect
        self.func_save = func_save
        self.func_load = func_load
        self.func_stop = func_stop
        self.func_bundle = func_bundle
        self.func_replay = func_replay
        self.set_speed_joint = set_speed_joint
        self.set_speed_linear = set_speed_linear
        self.set_acc_joint = set_acc_joint
        self.set_acc_linear = set_acc_linear
        self.status_recorder = status_recorder
        self.status_robot = status_robot
        self.status_controller = status_controller

        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
        )

        self.app.layout = dbc.Container(
            [
                # IMPORTANT updates the page every 200ms
                dcc.Interval(
                    id="interval",
                    interval=200,
                    n_intervals=0,
                ),
                *self.modals(),
                self.title(),
                dbc.Row(
                    [
                        *self.control_buttons(),
                        *self.movement_sliders(),
                        *self.indicators(),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(self.pose_display(), width=6),
                        dbc.Col(self.angles_display(), width=6),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(self.memory_table(), width=6),
                        dbc.Col(self.feed_table(), width=6),
                    ]
                ),
            ],
            fluid=True,
            style={"padding": "5vh"},
        )

        self.register_callbacks()

    def modals(self) -> typing.List[dbc.Modal]:
        """
        Returns the modals for the dashboard.
        """
        return [
            self.memory_modal("save"),
            self.memory_modal("load"),
            self.keymap_modal(),
        ]

    @staticmethod
    def title() -> dbc.Row:
        """
        Returns the title for the dashboard.
        """
        return dbc.Row(
            dbc.Col(
                html.H1("Robot Recorder Dashboard", style={"text-align": "center"})
            ),
            justify="center",
        )

    @staticmethod
    def save_button() -> dbc.Button:
        """
        Returns the save button for the dashboard.
        """
        return dbc.Button(
            "Save Memory",
            id="save-memory-button",
            color="success",
            className="mr-1",
        )

    def save_button_callback(self):
        """
        Registers the save button callback.
        """

        @self.app.callback(
            Output("save-modal", "is_open"),
            [
                Input("save-memory-button", "n_clicks"),
                Input("save-modal-cancel-button", "n_clicks"),
                Input("save-modal-save-button", "n_clicks"),
            ],
            [
                State("save-modal", "is_open"),
                State("save-modal-filename-input", "value"),
            ],
            prevent_initial_callback=True,
        )
        def save_memory(n_save_outer, n_cancel, n_save_inner, is_open, filename):
            """
            Callback to save the memory to a file.
            """
            if n_save_outer or n_save_inner or n_cancel:
                if n_save_inner and ctx.triggered_id == "save-modal-save-button":
                    self.func_save(filename)
                return not is_open

            return dash.no_update

    @staticmethod
    def load_button() -> dbc.Button:
        """
        Returns the load button for the dashboard.
        """
        return dbc.Button(
            "Load Memory",
            id="load-memory-button",
            color="success",
            className="mr-1",
        )

    def load_button_callback(self):
        """
        Registers the load button callback.
        """

        @self.app.callback(
            Output("load-modal", "is_open"),
            [
                Input("load-memory-button", "n_clicks"),
                Input("load-modal-cancel-button", "n_clicks"),
                Input("load-modal-load-button", "n_clicks"),
            ],
            [
                State("load-modal", "is_open"),
                State("load-modal-filename-input", "value"),
            ],
            prevent_initial_callback=True,
        )
        def load_memory(n_load_outer, n_cancel, n_load_inner, is_open, filename):
            """
            Callback to load the memory from a file.
            """
            if n_load_outer or n_load_inner or n_cancel:
                if n_load_inner and ctx.triggered_id == "load-modal-load-button":
                    result = self.func_load(filename)
                    return not result, not result
                else:
                    return not is_open, False

            return dash.no_update

    @staticmethod
    def bundle_button() -> dbc.Button:
        """
        Returns the bundle button for the dashboard.
        """
        return dbc.Button(
            "Bundle",
            id="bundle-button",
            color="success",
            className="mr-1",
        )

    def bundle_button_callback(self):
        """
        Registers the bundle button callback.
        """
        self.button_callback("bundle-button", self.func_bundle)

    @staticmethod
    def clear_error_button() -> dbc.Button:
        """
        Returns the clear error button for the dashboard.
        """
        return dbc.Button(
            "Clear Error",
            id="clear-error-button",
            color="warning",
            className="mr-1",
        )

    def clear_error_button_callback(self):
        """
        Registers the clear error button callback.
        """
        self.button_callback("clear-error-button", self.func_clear_error)

    @staticmethod
    def reconnect_button() -> dbc.Button:
        """
        Returns the reconnect button for the dashboard.
        """
        return dbc.Button(
            "Reconnect",
            id="reconnect-button",
            color="warning",
            className="mr-1",
        )

    def reconnect_button_callback(self):
        """
        Registers the reconnect button callback.
        """
        self.button_callback("reconnect-button", self.func_reconnect)

    @staticmethod
    def stop_button() -> dbc.Button:
        """
        Returns the stop button for the dashboard.
        """
        return dbc.Button(
            "Stop",
            id="stop-button",
            color="danger",
            className="mr-1",
        )

    def stop_button_callback(self):
        """
        Registers the stop button callback.
        """
        self.button_callback("stop-button", self.func_stop)

    @staticmethod
    def keymap_button() -> dbc.Button:
        """
        Returns the keymap button for the dashboard.
        """
        return dbc.Button(
            "Keymap",
            id="keymap-button",
            className="mr-1",
        )

    def keymap_button_callback(self):
        """
        Registers the keymap button callback.
        """

        @self.app.callback(
            Output("keymap-modal", "is_open"),
            [Input("keymap-button", "n_clicks")],
            [State("keymap-modal", "is_open")],
            prevent_initial_callback=True,
        )
        def keymap(n_clicks, is_open):
            """
            Callback to open the keymap modal.
            """
            if n_clicks:
                return not is_open
            return dash.no_update

    @staticmethod
    def replay_button() -> dbc.Button:
        """
        Returns the replay button for the dashboard.
        """
        return dbc.Button(
            "Replay",
            id="replay-button",
            color="success",
            className="mr-1",
        )

    def replay_button_callback(self):
        """
        Registers the replay button callback.
        """

        @self.app.callback(
            Output("replay-button", "disabled"),
            Input("replay-button", "n_clicks"),
        )
        def button_callback(n_clicks):
            """
            Callback to replay the memory.
            """
            if n_clicks is not None:
                self.func_replay(self.get_memory())
            return dash.no_update

    def control_buttons(self) -> typing.List[dbc.Col]:
        """
        Returns the control buttons for the dashboard.
        """
        return [
            dbc.Col(
                dbc.Stack(
                    [
                        self.save_button(),
                        self.load_button(),
                        self.bundle_button(),
                    ],
                    gap=3,
                ),
                width=1,
            ),
            dbc.Col(
                dbc.Stack(
                    [
                        self.clear_error_button(),
                        self.reconnect_button(),
                        self.stop_button(),
                    ],
                    gap=3,
                ),
                width=1,
            ),
            dbc.Col(
                dbc.Stack(
                    [
                        self.keymap_button(),
                        self.replay_button(),
                    ],
                    gap=3,
                ),
                width=1,
            ),
        ]

    def joint_speed_slider(self) -> dbc.Row:
        """
        Returns the joint speed slider for the dashboard.
        """
        return self.slider(
            "Speed Joint",
            "speed-joint-slider",
        )

    def joint_speed_slider_callback(self):
        """
        Registers the joint speed slider callback.
        """
        self.slider_callback("speed-joint-slider", self.set_acc_joint)

    def linear_speed_slider(self) -> dbc.Row:
        """
        Returns the linear speed slider for the dashboard.
        """
        return self.slider(
            "Speed Linear",
            "speed-linear-slider",
        )

    def linear_speed_slider_callback(self):
        """
        Registers the linear speed slider callback.
        """
        self.slider_callback("speed-linear-slider", self.set_speed_linear)

    def joint_acceleration_slider(self) -> dbc.Row:
        """
        Returns the joint acceleration slider for the dashboard.
        """
        return self.slider(
            "Acceleration Joint",
            "acc-joint-slider",
        )

    def joint_acceleration_slider_callback(self):
        """
        Registers the joint acceleration slider callback.
        """
        self.slider_callback("acc-joint-slider", self.set_acc_joint)

    def linear_acceleration_slider(self) -> dbc.Row:
        """
        Returns the linear acceleration slider for the dashboard.
        """
        return self.slider(
            "Acceleration Linear",
            "acc-linear-slider",
        )

    def linear_acceleration_slider_callback(self):
        """
        Registers the linear acceleration slider callback.
        """
        self.slider_callback("acc-linear-slider", self.set_acc_linear)

    def movement_sliders(self) -> typing.List[dbc.Col]:
        """
        Returns the movement sliders for the dashboard.
        """
        return [
            dbc.Col(
                dbc.Stack(
                    [
                        self.joint_speed_slider(),
                        self.linear_speed_slider(),
                    ],
                    gap=3,
                ),
                width=3,
            ),
            dbc.Col(
                dbc.Stack(
                    [
                        self.joint_acceleration_slider(),
                        self.linear_acceleration_slider(),
                    ],
                    gap=3,
                ),
                width=3,
            ),
        ]

    def recorder_status(self) -> daq.Indicator:
        """
        Returns the recorder status for the dashboard.
        """
        return self.indicator("Recorder", "recorder-status")

    def recorder_status_callback(self):
        """
        Registers the recorder status callback.
        """
        self.indicator_callback("recorder-status", self.status_recorder)

    def robot_status(self) -> daq.Indicator:
        """
        Returns the robot status for the dashboard.
        """
        return self.indicator("Robot", "robot-status")

    def robot_status_callback(self):
        """
        Registers the robot status callback.
        """
        self.indicator_callback("robot-status", self.status_robot)

    def controller_status(self) -> daq.Indicator:
        """
        Returns the controller status for the dashboard.
        """
        return self.indicator("Controller", "controller-status")

    def controller_status_callback(self):
        """
        Registers the controller status callback.
        """
        self.indicator_callback("controller-status", self.status_controller)

    def indicators(self) -> typing.List[dbc.Col]:
        """
        Returns the indicators for the dashboard.
        """
        return [
            dbc.Col(
                self.recorder_status(),
                width=1,
            ),
            dbc.Col(
                self.robot_status(),
                width=1,
            ),
            dbc.Col(
                self.controller_status(),
                width=1,
            ),
        ]

    def pose_display(self) -> dbc.Container:
        """
        Returns the pose display for the dashboard.
        """
        return self.input_group(
            "Pose",
            ["X", "Y", "Z", "R"],
            [f"pose-{i}-input" for i in ["x", "y", "z", "r"]],
        )

    def pose_display_callback(self):
        """
        Registers the pose display callback.
        """

        @self.app.callback(
            [
                Output("pose-x-input", "value"),
                Output("pose-y-input", "value"),
                Output("pose-z-input", "value"),
                Output("pose-r-input", "value"),
            ],
            [Input("interval", "n_intervals")],
            prevent_initial_call=True,
        )
        def update_pose(_):
            """
            Callback to update the pose display.
            """
            return self.get_pose().tolist()

    def angles_display(self) -> dbc.Container:
        """
        Returns the angles display for the dashboard.
        """
        return self.input_group(
            "Angles",
            [f"J{i}" for i in range(1, 5)],
            [f"angles-j{i}-input" for i in range(1, 5)],
        )

    def angles_display_callback(self):
        @self.app.callback(
            [
                Output("angles-j1-input", "value"),
                Output("angles-j2-input", "value"),
                Output("angles-j3-input", "value"),
                Output("angles-j4-input", "value"),
            ],
            [Input("interval", "n_intervals")],
            prevent_initial_call=True,
        )
        def update_angles(_):
            """
            Callback to update the angles display.
            """
            return self.get_angles().tolist()

    def memory_table(self) -> dbc.Container:
        """
        Returns the memory table for the dashboard.
        """
        return self.table(
            "Memory",
            "memory-table",
            [
                "Type",
                "Motion Type",
                "X/J1",
                "Y/J2",
                "Z/J3",
                "R/J4",
                "End Effector",
            ],
        )

    def memory_table_callback(self):
        @self.app.callback(
            [
                Output("memory-table", "data"),
                Output("memory-table", "style_data_conditional"),
            ],
            [Input("interval", "n_intervals")],
            prevent_initial_call=True,
        )
        def update_memory(_):
            """
            Callback to update the memory table.
            """
            data = [el.serialize() for el in self.get_memory()]
            data_conditional = []
            for i, el in enumerate(data):
                if el["Type"] != "END_EFFECTOR":
                    el["X/J1"] = np.round(el["Value"][0], 1)
                    el["Y/J2"] = np.round(el["Value"][1], 1)
                    el["Z/J3"] = np.round(el["Value"][2], 1)
                    el["R/J4"] = np.round(el["Value"][3], 1)
                    el["End Effector"] = ["-"]
                elif el[("Motion Type")] == "GRIPPER":
                    el["X/J1"] = ["-"]
                    el["Y/J2"] = ["-"]
                    el["Z/J3"] = ["-"]
                    el["R/J4"] = ["-"]
                    el["End Effector"] = "Open" if el["Value"][1][1] == 1 else "Close"

                if not el["Valid"]:
                    data_conditional.append(
                        {
                            "if": {"row_index": i},
                            "backgroundColor": "red",
                            "color": "white",
                        }
                    )
            return data, data_conditional

    def feed_table(self) -> dbc.Container:
        """
        Returns the feed table for the dashboard.
        """
        return self.table(
            "Feed Log",
            "feed-table",
            ["Timestamp", "Message", "Source"],
        )

    def feed_table_callback(self):
        """
        Registers the feed table callback.
        """

        @self.app.callback(
            Output("feed-table", "data"),
            [Input("interval", "n_intervals")],
            prevent_initial_call=True,
        )
        def update_feed(_):
            """
            Callback to update the feed table.
            """
            data = [el.serialize() for el in reversed(self.get_feed())]
            return data

    @staticmethod
    def input_group(title, labels, ids):
        """
        Returns an input group for the dashboard. (Used for pose and angles)
        """

        def generator(labels, ids):
            """
            Generator to create the input group.
            """
            for label, idx in zip(labels, ids):
                yield dbc.InputGroupText(label)
                yield dbc.Input(
                    id=idx,
                    type="number",
                    disabled=True,
                    value=0,
                )

        return dbc.Container(
            [
                html.H4(title),
                dbc.InputGroup(
                    list(generator(labels, ids)),
                    className="mb-3",
                ),
            ],
            fluid=True,
        )

    @staticmethod
    def table(label, idx, columns, data_conditional=None, hidden_columns=None):
        """
        Returns a table for the dashboard. (Used for memory and feed)
        """
        return dbc.Container(
            [
                html.H4(label),
                DataTable(
                    id=idx,
                    columns=[{"name": i, "id": i} for i in columns],
                    data=[],
                    style_table={
                        "maxHeight": "55vh",
                        "overflowY": "scroll",
                    },
                    style_cell={
                        "textAlign": "left",
                        "whiteSpace": "pre-line",
                        "font-family": "sans-serif",
                    },
                    style_cell_conditional=[
                        {"if": {"column_id": ""}, "textAlign": "left"}
                    ],
                    style_as_list_view=True,
                    style_header={
                        "border-top": "none",
                        "font-family": "sans-serif",
                        "background-color": "white",
                    },
                    style_data_conditional=data_conditional,
                    hidden_columns=hidden_columns,
                ),
            ],
            fluid=True,
        )

    def button_callback(self, idx, func):
        """
        Registers a generic button callback that just calls a function on click.
        """

        @self.app.callback(
            Output(idx, "disabled"),
            Input(idx, "n_clicks"),
        )
        def button_callback(n_clicks):
            """
            Generic button callback to call a function on button click.
            """
            if n_clicks is not None:
                func()
            return dash.no_update

    @staticmethod
    def indicator(label, idx):
        """
        Returns a generic indicator for the dashboard.
        """
        return daq.Indicator(
            id=idx,
            label=label,
            labelPosition="bottom",
            value=True,
        )

    def indicator_callback(self, idx, func):
        """
        Registers a generic indicator callback that updates the value and color of the indicator.
        """

        @self.app.callback(
            Output(idx, "value"),
            Output(idx, "color"),
            Input("interval", "n_intervals"),
            prevent_initial_callback=True,
        )
        def indicator_callback(n_intervals):
            """
            Generic indicator callback to update the value and color of the indicator.
            """
            if n_intervals % 5 == 0:
                value = func()
                return value, "green" if value else "red"
            return dash.no_update

    @staticmethod
    def slider(label, idx):
        """
        Returns a generic slider for the dashboard.
        """
        return dbc.Row(
            [
                dbc.Col(dbc.Label(label), width=5),
                dbc.Col(
                    dcc.Slider(
                        id=idx,
                        min=1,
                        max=100,
                        step=1,
                        value=100,
                        marks={1: "1", 100: "100"},
                    ),
                    width=7,
                ),
            ],
        )

    def slider_callback(self, idx, func):
        """
        Registers a generic slider callback that calls a function on slider change.
        """

        @self.app.callback(
            Output(idx, "value"),
            Input(idx, "value"),
            prevent_initial_callback=True,
        )
        def slider_callback(value):
            """
            Generic slider callback to call a function on slider change.
            """
            func(value)
            return value

    @staticmethod
    def memory_modal(prefix: str) -> dbc.Modal:
        """
        Returns a generic memory modal for the dashboard.
        """
        return dbc.Modal(
            [
                dbc.ModalHeader(f"{prefix.capitalize()} Memory"),
                dbc.ModalBody(
                    [
                        dbc.Input(
                            id=f"{prefix}-modal-filename-input",
                            placeholder="Enter filename",
                            type="text",
                        ),
                        dbc.Alert(
                            "File not found",
                            color="danger",
                            is_open=False,
                            id=f"{prefix}-modal-filename-alert",
                        )
                        if prefix == "load"
                        else None,
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            prefix.capitalize(),
                            id=f"{prefix}-modal-{prefix}-button",
                            className="ml-auto",
                        ),
                        dbc.Button(
                            "Cancel",
                            id=f"{prefix}-modal-cancel-button",
                            className="ml-auto",
                        ),
                    ]
                ),
            ],
            id=f"{prefix}-modal",
            is_open=False,
        )

    def keymap_modal(self):
        """
        Returns a keymap modal for the dashboard.
        """
        return dbc.Modal(
            dbc.ModalBody(
                html.Img(
                    src=self.app.get_asset_url("keymap.png"),
                    style={"height": "100%", "width": "100%"},
                )
            ),
            id="keymap-modal",
            is_open=False,
            size="xl",
        )

    def control_buttons_callbacks(self):
        """
        Registers the control buttons callbacks.
        """
        self.save_button_callback()
        self.load_button_callback()
        self.bundle_button_callback()

        self.clear_error_button_callback()
        self.reconnect_button_callback()
        self.stop_button_callback()

        self.keymap_button_callback()
        self.replay_button_callback()

    def slider_callbacks(self):
        """
        Registers the slider callbacks.
        """
        self.joint_speed_slider_callback()
        self.linear_speed_slider_callback()

        self.joint_acceleration_slider_callback()
        self.linear_acceleration_slider_callback()

    def indicator_callbacks(self):
        """
        Registers the indicator callbacks.
        """
        self.recorder_status_callback()
        self.robot_status_callback()
        self.controller_status_callback()

    def register_callbacks(self):
        """
        Registers all callbacks.
        """
        self.control_buttons_callbacks()
        self.slider_callbacks()
        self.indicator_callbacks()

        self.pose_display_callback()
        self.angles_display_callback()

        self.memory_table_callback()
        self.feed_table_callback()

    def run(self):
        """
        Runs dash app for the dashboard.
        """
        self.app.run()
