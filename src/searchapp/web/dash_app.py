from dash import Dash, dcc, html, callback, Input, Output, State, ClientsideFunction
import dash_bootstrap_components as dbc
from searchapp.core.inference.inference import Inference
from searchapp.core.search.web import WebSearch
from searchapp.api.controller import InputController

# Initialize with both themes available
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.MINTY, dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# Create theme toggle button
theme_toggle = dbc.Button(
    "Toggle Theme",
    id="theme-toggle",
    color="secondary",
    size="sm",
    className="position-fixed top-0 end-0 m-2",
    style={"zIndex": 1000},
)

# Store component for theme state
theme_store = dcc.Store(id="theme-store", storage_type="local")

app.layout = dbc.Container(
    [
        theme_store,  # Add theme store
        theme_toggle,  # Add theme toggle button
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Img(
                            id="logo",
                            src=app.get_asset_url("bg7.jpg"),
                            height=300,  # Increased height for visibility
                            style={
                                "width": "100%",  # Ensure the image takes up the full width of the container
                                "height": "auto",  # Ensure the height scales proportionally
                                "border-radius": "5px",  # Rounded corners for the image
                            },
                        ),
                        # The text that will hover over the image
                        html.H1(
                            "search",
                            className="text-center",
                            style={
                                "color": "#f0f8ff",
                                "position": "absolute",  # Position the text absolutely
                                "top": "50%",  # Center vertically
                                "left": "50%",  # Center horizontally
                                "transform": "translate(-50%, -50%)",  # Shift by half to truly center
                                "background-color": "rgba(0, 0, 0, 0.5)",  # Semi-transparent background
                                "padding": "10px",  # Padding around the text
                                "border-radius": "5px",  # Rounded corners for the text box
                            },
                        ),
                    ],
                    style={
                        "position": "relative",  # Relative position for the container to allow absolute positioning inside
                        "text-align": "center",  # Ensure text is centered
                    },
                ),
                width={"size": 12, "offset": 0},
                className="text-center my-4",
            )
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Input(
                        placeholder="What are you looking for...",
                        type="text",
                        value="",
                        id="search-input",
                        style={"margin-bottom": "10px"},
                    ),
                    className="mb-3",
                )
            ]
        ),
        dbc.Row(
            dbc.Col(
                dbc.Button(
                    "Search",
                    id="search-button",
                    color="primary",
                    outline=True,
                    style={
                        "width": "100%",
                        "border-color": "var(--bs-primary)",
                        "color": "var(--bs-primary)",
                    },
                ),
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
                            className="markdown-container invisible",
                            style={
                                "whiteSpace": "pre-wrap",  # Preserves newlines and spaces
                                "padding": "20px",
                                "border-radius": "5px",
                                "overflow-wrap": "break-word",  # Ensures long words break
                                "word-wrap": "break-word",  # Fallback for older browsers
                                "word-break": "break-word",  # Another fallback
                                "max-width": "100%",  # Ensures markdown doesn't exceed container
                                "color": "var(--bs-body-color)",  # Use Bootstrap's theme-aware color
                                "background-color": "var(--bs-secondary-bg)",  # Use Bootstrap's theme-aware background
                            },
                        ),
                        style={
                            "overflow-x": "auto"
                        },  
                    ),
                ),
            )
        ),
    ],
    fluid=True,  # Makes the container responsive
    style={
        "padding": "20px",
        "max-width": "800px",  # Limit the container width
        "overflow-x": "hidden",  # Prevents horizontal scroll on the container
    },
)

@callback(
    Output("search-button", "outline"),
    Input("search-input", "value"),
    prevent_initial_call=True,
)
def update_search_button_outline(search_input):
    if search_input.strip():
        return False
    return True

@callback(
    Output("search-formatted", "className"),
    Input("search-formatted", "children"),
    prevent_initial_call=True,
)
def update_search_opacity(search_formatted):
    if len(search_formatted) > 0:
        return "markdown-container visible"
    return "markdown-container invisible"

@callback(
    Output("search-formatted", "children"),
    Input("search-button", "n_clicks"),
    State("search-input", "value"),
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
                markdown_content = f"\n{search_results}\n"
            else:
                # Handle unexpected types
                markdown_content = "Unexpected result format."

        except Exception as e:
            # Handle exceptions and provide user feedback
            markdown_content = f"An error occurred during the search: {str(e)}"

        return markdown_content, ""

    elif n_clicks:
        return "Please enter a valid search query."

    return "No search performed yet."

# Theme switching callbacks
@callback(
    Output("theme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
)
def toggle_theme(n_clicks, current_theme):
    if n_clicks is None:
        # Initial load - set default theme
        return {"theme": "light"}
    
    # Toggle between light and dark
    if current_theme is None or current_theme.get("theme") == "light":
        return {"theme": "dark"}
    return {"theme": "light"}

# Update theme CSS
app.clientside_callback(
    """
    function(theme_data) {
        if (!theme_data) return;
        
        const theme = theme_data.theme;
        const lightTheme = document.querySelector('link[href*="MINTY"]');
        const darkTheme = document.querySelector('link[href*="DARKLY"]');
        
        if (theme === 'dark') {
            lightTheme.disabled = true;
            darkTheme.disabled = false;
            document.body.style.backgroundColor = '#1a1a1a';
            document.body.style.color = '#ffffff';
        } else {
            lightTheme.disabled = false;
            darkTheme.disabled = true;
            document.body.style.backgroundColor = '#ffffff';
            document.body.style.color = '#000000';
        }
        return '';
    }
    """,
    Output("theme-toggle", "style"),
    Input("theme-store", "data"),
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
