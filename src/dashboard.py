import logging

import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.io as pio
from dash import html, dcc, ctx
from dash.dash_table import DataTable
from dash.dependencies import Input, Output, State

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
        func_load,
        func_stop,
        func_bundle,
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
        self.func_load = func_load
        self.func_stop = func_stop
        self.func_bundle = func_bundle
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
                # IMPORTANT updates the page every 200ms
                dcc.Interval(
                    id="interval",
                    interval=200,
                    n_intervals=0,
                ),
                self.memory_modal("save"),
                self.memory_modal("load"),
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
                            dbc.Stack(
                                [
                                    dbc.Button(
                                        "Save Memory",
                                        id="save-memory-button",
                                        color="success",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Load Memory",
                                        id="load-memory-button",
                                        color="success",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Bundle",
                                        id="bundle-button",
                                        color="success",
                                        className="mr-1",
                                    ),
                                ],
                                gap=3,
                            ),
                            width=1,
                        ),
                        dbc.Col(
                            dbc.Stack(
                                [
                                    dbc.Button(
                                        "Clear Error",
                                        id="clear-error-button",
                                        color="warning",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Reconnect",
                                        id="reconnect-button",
                                        color="warning",
                                        className="mr-1",
                                    ),
                                    dbc.Button(
                                        "Stop",
                                        id="stop-button",
                                        color="danger",
                                        className="mr-1",
                                    ),
                                ],
                                gap=3,
                            ),
                            width=1,
                        ),
                        dbc.Col(
                            dbc.Stack(
                                [
                                    self.slider(
                                        "Speed Joint",
                                        "speed-joint-slider",
                                        set_speed_joint,
                                    ),
                                    self.slider(
                                        "Speed Linear",
                                        "speed-linear-slider",
                                        set_speed_linear,
                                    ),
                                ],
                                gap=3,
                            ),
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Stack(
                                [
                                    self.slider(
                                        "Acceleration Joint",
                                        "acc-joint-slider",
                                        self.set_acc_joint,
                                    ),
                                    self.slider(
                                        "Acceleration Linear",
                                        "acc-linear-slider",
                                        self.set_acc_linear,
                                    ),
                                ],
                                gap=3,
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            self.indicator(
                                "Recorder", "recorder-status", self.status_recorder
                            ),
                            width=1,
                        ),
                        dbc.Col(
                            self.indicator("Robot", "robot-status", self.status_robot),
                            width=1,
                        ),
                        dbc.Col(
                            self.indicator(
                                "Controller",
                                "controller-status",
                                self.status_controller,
                            ),
                            width=1,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            self.input_group(
                                "Pose",
                                ["X", "Y", "Z", "R"],
                                [f"pose-{i}-input" for i in ["x", "y", "z", "r"]],
                            ),
                            width=6,
                        ),
                        dbc.Col(
                            self.input_group(
                                "Angles",
                                [f"J{i}" for i in range(1, 5)],
                                [f"angles-j{i}-input" for i in range(1, 5)],
                            ),
                            width=6,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            self.table(
                                "Memory",
                                "memory-table",
                                [
                                    "Type",
                                    "X/J1",
                                    "Y/J2",
                                    "Z/J3",
                                    "R/J4",
                                    "Motion Type",
                                ],
                            ),
                            width=6,
                        ),
                        dbc.Col(
                            self.table(
                                "Feed Log",
                                "feed-table",
                                ["Timestamp", "Message", "Source"],
                            ),
                            width=6,
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
            [
                Output("memory-table", "data"),
                Output("memory-table", "style_data_conditional"),
            ],
            [Input("interval", "n_intervals")],
            prevent_initial_callback=True,
        )
        def update_memory(_):
            data = [el.serialize() for el in self.get_memory()]
            data_conditional = []
            for i, el in enumerate(data):
                el["X/J1"] = np.round(el["Value"][0], 1)
                el["Y/J2"] = np.round(el["Value"][1], 1)
                el["Z/J3"] = np.round(el["Value"][2], 1)
                el["R/J4"] = np.round(el["Value"][3], 1)
                if not el["Valid"]:
                    data_conditional.append(
                        {
                            "if": {"row_index": i},
                            "backgroundColor": "red",
                            "color": "white",
                        }
                    )
            return data, data_conditional

        @self.app.callback(
            Output("feed-table", "data"),
            [Input("interval", "n_intervals")],
            prevent_initial_callback=True,
        )
        def update_feed(_):
            data = [el.serialize() for el in reversed(self.get_feed())]
            return data

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
            if n_save_outer or n_save_inner or n_cancel:
                if n_save_inner and ctx.triggered_id == "save-modal-save-button":
                    self.func_save(filename)
                return not is_open

            return dash.no_update

        @self.app.callback(
            [
                Output("load-modal", "is_open"),
                Output("load-modal-filename-alert", "is_open"),
            ],
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
            if n_load_outer or n_load_inner or n_cancel:
                if n_load_inner and ctx.triggered_id == "load-modal-load-button":
                    result = self.func_load(filename)
                    return not result, not result
                else:
                    return not is_open, False

            return dash.no_update

        self.button_callback("clear-error-button", self.func_clear_error)
        self.button_callback("stop-button", self.func_stop)
        self.button_callback("bundle-button", self.func_bundle)
        self.button_callback("reconnect-button", self.func_reconnect)

    def input_group(self, title, labels, ids):
        def generator(labels, ids):
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

    def table(self, label, idx, columns, data_conditional=None, hidden_columns=None):
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
        @self.app.callback(
            Output(idx, "disabled"),
            Input(idx, "n_clicks"),
        )
        def button_callback(n_clicks):
            if n_clicks is not None:
                func()
            return dash.no_update

    def indicator(self, label, idx, func):
        @self.app.callback(
            Output(idx, "value"),
            Output(idx, "color"),
            Input("interval", "n_intervals"),
            prevent_initial_callback=True,
        )
        def indicator_callback(n_intervals):
            if n_intervals % 5 == 0:
                value = func()
                return value, "green" if value else "red"
            return dash.no_update

        return daq.Indicator(
            id=idx,
            label=label,
            labelPosition="bottom",
            value=True,
        )

    def slider(self, label, idx, func):
        @self.app.callback(
            Output(idx, "value"),
            Input(idx, "value"),
            prevent_initial_callback=True,
        )
        def slider_callback(value):
            func(value)
            return value

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

    def memory_modal(self, prefix: str):
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

    def run(self):
        self.app.run()
