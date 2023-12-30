from dash import Dash, dcc, html, Input, Output, State, callback
from dash.exceptions import PreventUpdate
import plotly.express as px

import base64
import io

import pandas as pd


DATE_COL = "calendarDate"
TIME_COLS = ["calendarDate", "week", "month", "year"]
AGGREGATE_FUNCTIONS = ["median", "mean", "sum", "min", "max", "count"]


def normalise_camel_case(x):
    """Convert a string like 'camelCase' to 'camel case'."""
    result_str = "".join([" " + char if char.isupper() and index != 0 else char for index, char in enumerate(x)])
    return result_str.capitalize()


def _parse_json(json_data):
    if json_data is None:
        return
    return pd.read_json(json_data, convert_dates=TIME_COLS)


def parse_content(content):
    content_type, content_string = content.split(",")

    decoded_content = base64.b64decode(content_string)
    try:
        df = pd.read_json(io.BytesIO(decoded_content), convert_dates=[DATE_COL])
        num_cols = list(df.select_dtypes(include=["int64", "float64"]).columns)
        df = df[[DATE_COL] + num_cols]
    except Exception as e:
        return html.Div(
            [
                f"There was an error processing this file: {e}",
            ]
        )

    return df


@callback(
    Output("display-metric", "options"),
    Output("upload-data-output", "data"),
    Input("upload-data", "contents"),
)
def prepare_data(contents):
    if contents is not None:
        dfs = [parse_content(c) for c in contents]
    else:
        raise PreventUpdate

    df = pd.concat(dfs, ignore_index=True)

    df["week"] = df[DATE_COL] - pd.to_timedelta(df[DATE_COL].dt.dayofweek, unit="D")
    df["month"] = df[DATE_COL] - pd.to_timedelta(df[DATE_COL].dt.day - 1, unit="D")
    df["year"] = df[DATE_COL].dt.year.astype(str)

    for col in df.columns:
        if col.endswith("Meters"):
            df[col.replace("Meters", "Kilometers")] = df[col] / 1000
        if col.endswith("Minutes"):
            df[col.replace("Minutes", "Hours")] = df[col] / 60
        if col.endswith("Seconds"):
            df[col.replace("Seconds", "Hours")] = df[col] / (60 * 60)
        if col.endswith("Milliseconds"):
            df[col.replace("Milliseconds", "Hours")] = df[col] / (60 * 1000)

    df = df.sort_values(DATE_COL)

    cols = list(df.columns)
    cols.sort()
    options = [{"label": normalise_camel_case(col), "value": col} for col in cols if not col in TIME_COLS]

    return options, df.to_json()


@callback(
    Output("plot", "children"),
    Input("upload-data-output", "data"),
    Input("display-metric", "value"),
    Input("group-by", "value"),
    Input("aggregate-function", "value"),
)
def update_plot(json_data, y_col, x_col, agg_func):
    if json_data is None:
        return

    df = _parse_json(json_data)

    if x_col is None or y_col is None or agg_func is None:
        return

    plot_df = df.groupby(x_col).agg({y_col: agg_func}).reset_index()

    fig = px.scatter(
        plot_df,
        x=x_col,
        y=y_col,
        title=f"{agg_func.title()} of {normalise_camel_case(y_col)} by {x_col}",
        labels={
            x_col: normalise_camel_case(x_col),
            y_col: normalise_camel_case(y_col),
        },
    )

    return html.Div(
        [
            dcc.Graph(id="resting-heart-rate-plot", figure=fig),
        ]
    )


@callback(
    Output("download-data-as-csv", "data"),
    Input("download-data", "n_clicks"),
    State("upload-data-output", "data"),
    prevent_initial_call=True,
)
def download_data(n_clicks, json_data):
    if json_data is None:
        return
    df = _parse_json(json_data)
    return dcc.send_data_frame(df.to_csv, "merged-garmin-export-data.csv")


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Garmin data export visualiser"
app.layout = html.Div(
    [
        html.H3("Garmin data export visualiser"),
        html.Div(
            [
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(
                        [
                            "Upload Garmin data export files ",
                            html.B("DI_CONNECT/DI-Connect-Aggregator/USDFile_*.json"),
                            " via drag & drop or ",
                            html.A("select files"),
                            ".",
                        ]
                    ),
                    multiple=True,
                ),
            ],
            style={
                "width": "100%",
                "height": "90px",
                "lineHeight": "90px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
        ),
        dcc.Dropdown(
            # GARMIN_DATA_COLS_LABELS,
            id="display-metric",
            placeholder="Display metric",
        ),
        dcc.Dropdown(
            [{"label": normalise_camel_case(col), "value": col} for col in TIME_COLS],
            id="group-by",
            placeholder="Group by",
        ),
        dcc.Dropdown(
            [{"label": normalise_camel_case(col), "value": col} for col in AGGREGATE_FUNCTIONS],
            id="aggregate-function",
            placeholder="Aggregate via",
        ),
        dcc.Store(id="upload-data-output", storage_type="session"),
        html.Div(id="plot"),
        html.Br(),
        html.Center(
            [
                html.A("Download your uploaded data as a merged CSV.", id="download-data"),
                html.Div(
                    [dcc.Download(id="download-data-as-csv")],
                    style={
                        "textAlign": "right",
                    },
                ),
            ]
        ),
        html.Center(
            dcc.Link(
                "Find more information about this widget.",
                href="https://github.com/stelsemeyer/garmin-export-visualiser",
            )
        ),
        html.Center("Please allow a few seconds of initial loading."),
    ]
)

server = app.server


@app.server.route("/ping")
def ping():
    return "OK"


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
