import dash
import dash_bootstrap_components as dbc
import plotly.io as pio
from dash import html, dcc
from dash.dash_table import DataTable
from dash.dependencies import Input, Output
import dash_daq as daq
import logging
import numpy as np

log = logging.getLogger("werkzeug")
log.setLevel(logging.CRITICAL)

pio.templates.default = "plotly_white"


class Dashboard:
    def __init__(
        self,
        get_pose,
        get_angles,
        get_memory,
        get_feed,
        func_clear_error,
        func_reconnect,
        func_save,
        func_stop,
        func_bundle,
        shutdown_event,
        set_speed_joint,
        set_speed_linear,
        set_acc_joint,
        set_acc_linear,
        status_recorder,
        status_robot,
        status_controller,
    ):
        self.get_pose = get_pose
        self.get_angles = get_angles
        self.get_memory = get_memory
        self.get_feed = get_feed
        self.func_clear_error = func_clear_error
        self.func_reconnect = func_reconnect
        self.func_save = func_save
        self.func_stop = func_stop
        self.func_bundle = func_bundle
        self.shutdown_event = shutdown_event
        self.set_speed_joint = set_speed_joint
        self.set_speed_linear = set_speed_linear
        self.set_acc_joint = set_acc_joint
        self.set_acc_linear = set_acc_linear
        self.status_recorder = status_recorder
        self.status_robot = status_robot
        self.status_controller = status_controller

        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

        self.app.layout = dbc.Container(
            [
                dcc.Interval(
                    id="interval",
                    interval=200,
                    n_intervals=0,
                ),
                dbc.Row(
                    dbc.Col(
                        html.H1(
                            "Robot Recorder Dashboard", style={"text-align": "center"}
                        )
                    ),
                    justify="center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("Pose"),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("X"),
                                        dbc.Input(
                                            id="pose-x-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                        dbc.InputGroupText("Y"),
                                        dbc.Input(
                                            id="pose-y-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                        dbc.InputGroupText("Z"),
                                        dbc.Input(
                                            id="pose-z-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                        dbc.InputGroupText("R"),
                                        dbc.Input(
                                            id="pose-r-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H4("Angles"),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText("J1"),
                                        dbc.Input(
                                            id="angles-j1-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                        dbc.InputGroupText("J2"),
                                        dbc.Input(
                                            id="angles-j2-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                        dbc.InputGroupText("J3"),
                                        dbc.Input(
                                            id="angles-j3-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                        dbc.InputGroupText("J4"),
                                        dbc.Input(
                                            id="angles-j4-input",
                                            type="number",
                                            disabled=True,
                                            value=0,
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                            ],
                            md=6,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H4("Memory"),
                                DataTable(
                                    id="memory-table",
                                    columns=[
                                        {"name": i, "id": i}
                                        for i in [
                                            "Type",
                                            "X/J1",
                                            "Y/J2",
                                            "Z/J3",
                                            "R/J4",
                                            "Motion Type",
                                        ]
                                    ],
                                    data=[],
                                    style_table={
                                        "maxHeight": "60vh",
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
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H4("Feed Log"),
                                DataTable(
                                    id="feed-table",
                                    columns=[
                                        {"name": i, "id": i}
                                        for i in ["Timestamp", "Message", "Source"]
                                    ],
                                    data=[],
                                    style_table={
                                        "maxHeight": "60vh",
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
                                ),
                            ],
                            md=6,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Stack(
                                [
                                    dbc.Button(
                                        "Clear Error",
                                        id="clear-error-button",
                                        color="danger",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Reconnect",
                                        id="reconnect-button",
                                        color="danger",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Save Memory",
                                        id="save-memory-button",
                                        color="primary",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Bundle",
                                        id="bundle-button",
                                        color="primary",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Stop",
                                        id="stop-button",
                                        color="secondary",
                                        className="mr-1",
                                    ),
                                ],
                                gap=3,
                            ),
                            width=2,
                        ),
                        dbc.Col(
                            dbc.Stack(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Label("Speed Joint"), width=2),
                                            dbc.Col(
                                                dcc.Input(
                                                    id="speed-joint-slider",
                                                    type="range",
                                                    min=1,
                                                    max=100,
                                                    step=1,
                                                    value=100,
                                                ),
                                                width=6,
                                            ),
                                        ],
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(dbc.Label("Speed Linear"), width=2),
                                            dbc.Col(
                                                dcc.Input(
                                                    id="speed-linear-slider",
                                                    type="range",
                                                    min=1,
                                                    max=100,
                                                    step=1,
                                                    value=100,
                                                ),
                                                width=6,
                                            ),
                                        ],
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Acceleration Joint"), width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(
                                                    id="acc-joint-slider",
                                                    type="range",
                                                    min=1,
                                                    max=100,
                                                    step=1,
                                                    value=100,
                                                ),
                                                width=6,
                                            ),
                                        ],
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Acceleration Linear"),
                                                width=2,
                                            ),
                                            dbc.Col(
                                                dcc.Input(
                                                    id="acc-linear-slider",
                                                    type="range",
                                                    min=1,
                                                    max=100,
                                                    step=1,
                                                    value=100,
                                                ),
                                                width=6,
                                            ),
                                        ],
                                    ),
                                ],
                                gap=3,
                            ),
                            width=2,
                        ),
                        dbc.Col(
                            dbc.Stack(
                                [
                                    daq.Indicator(
                                        id="recorder-status",
                                        label="RecorderThread",
                                        labelPosition="bottom",
                                        value=True,
                                    ),
                                    daq.Indicator(
                                        id="robot-status",
                                        label="Robot",
                                        labelPosition="bottom",
                                        value=True,
                                    ),
                                    daq.Indicator(
                                        id="controller-status",
                                        label="Controller",
                                        labelPosition="bottom",
                                        value=True,
                                    ),
                                ],
                                gap=3,
                            ),
                            width=2,
                        ),
                    ]
                ),
            ],
            fluid=True,
            style={"padding": "5vh"},
        )

        @self.app.callback(
            [
                Output("pose-x-input", "value"),
                Output("pose-y-input", "value"),
                Output("pose-z-input", "value"),
                Output("pose-r-input", "value"),
                Output("angles-j1-input", "value"),
                Output("angles-j2-input", "value"),
                Output("angles-j3-input", "value"),
                Output("angles-j4-input", "value"),
            ],
            [Input("interval", "n_intervals")],
            prevent_initial_call=True,
        )
        def update_pose(_):
            return *self.get_pose(), *self.get_angles()

        @self.app.callback(
            Output("memory-table", "data"),
            [Input("interval", "n_intervals")],
            prevent_initial_callback=True,
        )
        def update_memory(_):
            data = [el.serialize() for el in self.get_memory()]
            for el in data:
                el["X/J1"] = np.round(el["Value"][0], 1)
                el["Y/J2"] = np.round(el["Value"][1], 1)
                el["Z/J3"] = np.round(el["Value"][2], 1)
                el["R/J4"] = np.round(el["Value"][3], 1)
            return data

        @self.app.callback(
            Output("feed-table", "data"),
            [Input("interval", "n_intervals")],
            prevent_initial_callback=True,
        )
        def update_feed(_):
            data = [el.serialize() for el in reversed(self.get_feed())]
            return data

        @self.app.callback(
            Output("clear-error-button", "disabled"),
            Input("clear-error-button", "n_clicks"),
            prevent_initial_callback=True,
        )
        def clear_error_callback(n_clicks):
            if n_clicks is not None:
                self.func_clear_error()
            return dash.no_update

        @self.app.callback(
            Output("save-memory-button", "disabled"),
            Input("save-memory-button", "n_clicks"),
            prevent_initial_callback=True,
        )
        def save_callback(n_clicks):
            if n_clicks is not None:
                self.func_save()
            return dash.no_update

        @self.app.callback(
            Output("stop-button", "disabled"),
            Input("stop-button", "n_clicks"),
            prevent_initial_callback=True,
        )
        def stop_callback(n_clicks):
            if n_clicks is not None:
                self.func_stop()
                self.shutdown_event.set()
            return dash.no_update

        @self.app.callback(
            Output("bundle-button", "disabled"),
            Input("bundle-button", "n_clicks"),
        )
        def bundle_callback(n_clicks):
            if n_clicks is not None:
                self.func_bundle()
            return dash.no_update

        @self.app.callback(
            Output("reconnect-button", "disabled"),
            Input("reconnect-button", "n_clicks"),
        )
        def bundle_callback(n_clicks):
            if n_clicks is not None:
                self.func_reconnect()
            return dash.no_update

        @self.app.callback(
            Output("speed-joint-slider", "value"),
            Input("speed-joint-slider", "value"),
            prevent_initial_callback=True,
        )
        def speed_joint_callback(value):
            self.set_speed_joint(value)
            return value

        @self.app.callback(
            Output("speed-linear-slider", "value"),
            Input("speed-linear-slider", "value"),
            prevent_initial_callback=True,
        )
        def speed_linear_callback(value):
            self.set_speed_linear(value)
            return value

        @self.app.callback(
            Output("acc-joint-slider", "value"),
            Input("acc-joint-slider", "value"),
            prevent_initial_callback=True,
        )
        def acc_joint_callback(value):
            self.set_acc_joint(value)
            return value

        @self.app.callback(
            Output("acc-linear-slider", "value"),
            Input("acc-linear-slider", "value"),
            prevent_initial_callback=True,
        )
        def acc_linear_callback(value):
            self.set_acc_linear(value)
            return value

        @self.app.callback(
            Output("recorder-status", "value"),
            Output("recorder-status", "color"),
            Input("interval", "n_intervals"),
            prevent_initial_callback=True,
        )
        def recorder_status_callback(n_intervals):
            if n_intervals % 5 == 0:
                value = self.status_recorder()
                return value, "green" if value else "red"
            return dash.no_update

        @self.app.callback(
            Output("robot-status", "value"),
            Output("robot-status", "color"),
            Input("interval", "n_intervals"),
            prevent_initial_callback=True,
        )
        def robot_status_callback(n_intervals):
            if n_intervals % 5 == 0:
                value = self.status_robot()
                return value, "green" if value else "red"
            return dash.no_update

        @self.app.callback(
            Output("controller-status", "value"),
            Output("controller-status", "color"),
            Input("interval", "n_intervals"),
            prevent_initial_callback=True,
        )
        def controller_status_callback(n_intervals):
            if n_intervals % 5 == 0:
                value = self.status_controller()
                return value, "green" if value else "red"
            return dash.no_update

    def run(self):
        self.app.run()
