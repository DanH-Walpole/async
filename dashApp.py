from dash import Dash, dcc, html, callback, Input, Output
from getPDFs import Inference, WebSearch, InputController

import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.MINTY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.layout = dbc.Container(
    [
        html.H1("LLM Search"),
        dbc.Input(
            placeholder="Enter a value to search...",
            type="text",
            value="",
            id="search-input",
            style={"margin-top": "20px"},
        ),

        dbc.Button(
            "Search",
            id="search-button",
            color="primary",
            style={"margin-top": "10px", "width": "100%"},
        ),
        dcc.Loading(
            id="loading",
            type="default",
            children=dcc.Markdown(
                id="search-formatted",
                children="Enter a query and click Search to see results here.",
                style={
                    "whiteSpace": "pre-wrap",
                    "word-wrap": "break-word",
                    "margin-top": "20px",
                    # "background-color": "#f8f9fa",
                    "padding": "20px",
                    "border-radius": "5px",
                    "overflow": "auto",
                    "max-width": "100%", 
                },
            ),
        ),
    ],
    fluid=True,
    style={
        "padding": "20px",
    },
)

@callback(
    Output("search-formatted", "children"),
    [Input("search-button", "n_clicks"),
     Input("search-input", "value")],
    prevent_initial_call=True,
)
def update_search_formatted(n_clicks, search_input):
    if n_clicks and search_input.strip():
        # Initialize the InputController and run the search
        controller = InputController()
        try:
            search_results = controller.run(search_input)
            
            # Check if search_results is a string
            if isinstance(search_results, str):
                # Format the output with markdown syntax
                markdown_content = f"```\n{search_results}\n```"
            else:
                # Handle unexpected types
                markdown_content = "Unexpected result format."
        except Exception as e:
            # Handle exceptions and provide user feedback
            markdown_content = f"An error occurred during the search: {str(e)}"
        
        return markdown_content

    elif n_clicks:
        return "Please enter a valid search query."
    
    return "No search performed yet."

if __name__ == "__main__":
    app.run(debug=True)
