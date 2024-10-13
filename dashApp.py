from dash import Dash, dcc, html, callback, Input, Output
from getPDFs import Inference, WebSearch, InputController

import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.MINTY],
    
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

search_formatted = ""

color_mode_switch = html.Span(
    [
        dbc.Label(className="fa fa-moon", html_for="switch"),
        dbc.Switch(
            id="switch", value=True, className="d-inline-block ms-1", persistence=True
        ),
        dbc.Label(className="fa fa-sun", html_for="switch"),
    ]
)

app.layout = dbc.Container(
    [
        html.H1("LLM Search"),
        dbc.Input(placeholder="Enter a value to search...", type="text", value="", id="search-input"),

        dbc.Button(
            "Search",
            id="search-button",
            color="primary",
            style={"margin-top": "10px", "width": "100%"},
        ),
        html.P(id="formatted-results"),
        html.H3(
            f"",
            id="search-formatted",
            hidden=False,
        ),
    ],
    style={
        # "textAlign": "center",
        # "width": "100%",
        "margintop": "10",
        "position": "absolute",
        "top": "1",
    },
)

@callback(
    Output("search-formatted", "children"),
    Input("search-button", "n_clicks"),
    prevent_initial_call=True,
)
def update_search_formatted(n_clicks):
    print("n_clicks: ", n_clicks)
    if n_clicks>0:
        test = "Test for now"
        return f"Output: {test}"

if __name__ == "__main__":
    app.run(debug=True)
