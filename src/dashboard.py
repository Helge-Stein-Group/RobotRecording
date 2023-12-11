import dash
import dash_bootstrap_components as dbc
import plotly.io as pio
from dash import html, dcc
from dash.dash_table import DataTable
from dash.dependencies import Input, Output
import logging
from flask import request

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
        func_save,
        func_stop,
        func_bundle,
        shutdown_event,
    ):
        self.get_pose = get_pose
        self.get_angles = get_angles
        self.get_memory = get_memory
        self.get_feed = get_feed
        self.func_clear_error = func_clear_error
        self.func_save = func_save
        self.func_stop = func_stop
        self.func_bundle = func_bundle
        self.shutdown_event = shutdown_event

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
                                        for i in ["Type", "Value", "Motion Type"]
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
                            dbc.Button(
                                "Clear Error",
                                id="clear-error-button",
                                color="danger",
                                className="mr-1",
                            )
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Save Memory",
                                id="save-memory-button",
                                color="primary",
                                className="mr-1",
                            )
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Bundle",
                                id="bundle-button",
                                color="primary",
                                className="mr-1",
                            )
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Stop",
                                id="stop-button",
                                color="secondary",
                                className="mr-1",
                            )
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
                el["Value"] = str(el["Value"])
            return data

        @self.app.callback(
            Output("feed-table", "data"),
            [Input("interval", "n_intervals")],
            prevent_initial_callback=True,
        )
        def update_feed(_):
            data = [el.serialize() for el in self.get_feed()]
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
            Output("memory-table", "data", allow_duplicate=True),
            Input("bundle-button", "n_clicks"),
            prevent_initial_call=True,
        )
        def bundle_callback(n_clicks):
            if n_clicks is not None:
                self.func_bundle()
                data = [el.serialize() for el in self.get_memory]
                for el in data:
                    el["Value"] = str(el["Value"])
                return data
            else:
                return dash.no_update

    def run(self):
        self.app.run()
