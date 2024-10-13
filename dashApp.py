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
        dbc.Row(
            dbc.Col(
                html.H1("LLM Search"),
                width={'size': 12, 'offset': 0},
                className="text-center my-4",
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Input(
                    placeholder="Enter a value to search...",
                    type="text",
                    value="",
                    id="search-input",
                    style={"margin-bottom": "10px"},
                ),
                width={'size': 8, 'offset': 2},
                className="mb-3",
            )
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    "Search",
                    id="search-button",
                    color="primary",
                    style={"width": "100%"},
                ),
                width={'size': 8, 'offset': 2},
                className="mb-4",
            )
        ),
        dbc.Row(
            dbc.Col(
                dcc.Loading(
                    id="loading",
                    type="default",
                    children=html.Div(
                        dcc.Markdown(
                            id="search-formatted",
                            children="Enter a query and click Search to see results here.",
                            className="markdown-container",
                            style={
                                "whiteSpace": "pre-wrap",          # Preserves newlines and spaces
                                "background-color": "#f8f9fa",
                                "padding": "20px",
                                "border-radius": "5px",
                                "overflow-wrap": "break-word",     # Ensures long words break
                                "word-wrap": "break-word",         # Fallback for older browsers
                                "word-break": "break-word",        # Another fallback
                                "max-width": "100%",               # Ensures markdown doesn't exceed container
                            },
                        ),
                        style={"overflow-x": "auto"},  # Allows internal horizontal scrolling if needed
                    ),
                ),
                width={'size': 8, 'offset': 2},
            )
        ),
    ],
    fluid=True,  # Makes the container responsive
    style={
        "padding": "20px",
        "overflow-x": "hidden",  # Prevents horizontal scroll on the container
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
                # Option 1: Use code block
                markdown_content = f"```\n{search_results}\n```"
                
                # Option 2: Use bullet points or headers for better readability
                # markdown_content = f"### Search Results\n\n{search_results.replace('\n', '\n\n')}"
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
