from dash import Dash, dcc, html, Input, Output, State, callback
import plotly.express as px

import base64
import io

import pandas as pd


def normalise_camel_case(x):
    result_str = "".join([" " + char if char.isupper() and index != 0 else char for index, char in enumerate(x)])
    return result_str.lower()


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

DATE_COL = "calendarDate"
TIME_COLS = ["calendarDate", "week", "month", "year"]
TIME_COLS_LABELS = [{"label": normalise_camel_case(col).capitalize(), "value": col} for col in TIME_COLS]

# TODO: explore dynamically
GARMIN_DATA_COLS = [
    "activeKilocalories",
    "activeSeconds",
    "averageMonitoringEnvironmentAltitude" "bmrKilocalories",
    "burnedKilocalories",
    "currentDayRestingHeartRate",
    "dailyStepGoal",
    "dailyTotalFromEpochData",
    "durationInMilliseconds",
    "floorsAscendedInMeters",
    "floorsDescendedInMeters",
    "highlyActiveSeconds",
    "maxAvgHeartRate",
    "maxHeartRate",
    "minAvgHeartRate",
    "minHeartRate",
    "moderateIntensityMinutes",
    "pushDistance",
    "remainingKilocalories",
    "restingCaloriesFromActivity",
    "restingHeartRate",
    "restingHeartRateTimestamp",
    "totalDistanceMeters",
    "totalKilocalories",
    "totalPushes",
    "totalSteps",
    "userFloorsAscendedGoal",
    "userIntensityMinutesGoal",
    "vigorousIntensityMinutes",
    "wellnessActiveKilocalories",
    "wellnessDistanceMeters",
    "wellnessKilocalories",
    "wellnessTotalKilocalories",
]
GARMIN_DATA_COLS_LABELS = [{"label": normalise_camel_case(col).capitalize(), "value": col} for col in GARMIN_DATA_COLS]
AGGREGATE_FUNCTIONS = ["median", "mean", "sum", "min", "max", "count"]
AGGREGATE_FUNCTIONS_LABELS = [
    {"label": normalise_camel_case(col).capitalize(), "value": col} for col in AGGREGATE_FUNCTIONS
]


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
            GARMIN_DATA_COLS_LABELS,
            id="display-metric",
            placeholder="Display metric",
        ),
        dcc.Dropdown(
            TIME_COLS_LABELS,
            id="group-by",
            placeholder="Group by",
        ),
        dcc.Dropdown(
            AGGREGATE_FUNCTIONS_LABELS,
            id="aggregate-function",
            placeholder="Aggregate via",
        ),
        dcc.Store(id="upload-data-output", storage_type="session"),
        html.Div(id="plot"),
        html.Br(),
        html.A("Download raw data as CSV", id="download-data"),
        html.Div(
            [dcc.Download(id="download-data-as-csv")],
            style={
                "textAlign": "right",
            },
        ),
    ]
)

server = app.server


def parse_content(contents, filename, date):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_json(io.BytesIO(decoded), convert_dates=[DATE_COL])
        num_cols = list(df.select_dtypes(include=["int64", "float64"]).columns)
        df = df[[DATE_COL] + num_cols]
    except Exception as e:
        print(e)
        return html.Div(
            [
                f"There was an error processing this file: {e}",
            ]
        )

    return df


@callback(
    Output("upload-data-output", "data"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def parse_contents(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [parse_content(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)]
    else:
        return

    df = pd.concat(children, ignore_index=True)

    df["week"] = df[DATE_COL] - pd.to_timedelta(df[DATE_COL].dt.dayofweek, unit="D")
    df["month"] = df[DATE_COL] - pd.to_timedelta(df[DATE_COL].dt.day - 1, unit="D")
    df["year"] = df[DATE_COL].dt.year.astype(str)

    df = df.sort_values(DATE_COL)

    return df.to_json()


@callback(
    Output("plot", "children"),
    Input("upload-data-output", "data"),
    Input("display-metric", "value"),
    Input("group-by", "value"),
    Input("aggregate-function", "value"),
)
def update_output(json_data, y_col, x_col, agg_func):
    if json_data is None:
        return

    df = pd.read_json(json_data, convert_dates=[DATE_COL, "week", "month", "year"])

    if x_col is None or y_col is None or agg_func is None:
        return

    plot_df = df.groupby(x_col).agg({y_col: agg_func}).reset_index()

    fig = px.scatter(
        plot_df,
        x=x_col,
        y=y_col,
        title=f"{agg_func.title()} of {normalise_camel_case(y_col)} by {x_col}",
        labels={
            x_col: normalise_camel_case(x_col).capitalize(),
            y_col: normalise_camel_case(y_col).capitalize(),
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
    df = pd.read_json(json_data, convert_dates=[DATE_COL, "week", "month", "year"])
    return dcc.send_data_frame(df.to_csv, "merged-garmin-export-data.csv")


@app.server.route("/ping")
def ping():
    return "OK"


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
