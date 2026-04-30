# src/app/ui/chatbot_panel.py
from dash import dcc, html
import dash_bootstrap_components as dbc


def chatbot_panel() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Div([
                                        html.H4("💬 Chatbot — Pregunta sobre tu documento", className="mb-0"),
                                        html.Small(
                                            "El asistente conoce el contenido completo del PDF procesado.",
                                            className="text-muted",
                                        ),
                                    ])
                                ),
                                dbc.CardBody(
                                    [
                                        # Área de mensajes (scrollable)
                                        html.Div(
                                            id="chatbot-messages",
                                            style={
                                                "height": "460px",
                                                "overflowY": "auto",
                                                "padding": "12px",
                                                "background": "#f8f9fa",
                                                "borderRadius": "8px",
                                                "marginBottom": "16px",
                                            },
                                            children=[
                                                html.Div(
                                                    "Procesa un PDF primero y luego haz tus preguntas aquí.",
                                                    className="text-muted text-center py-4",
                                                )
                                            ],
                                        ),
                                        # Input y botones
                                        dbc.InputGroup(
                                            [
                                                dbc.Input(
                                                    id="chatbot-input",
                                                    placeholder="Escribe tu pregunta sobre el documento...",
                                                    type="text",
                                                    n_submit=0,
                                                    debounce=False,
                                                ),
                                                dbc.Button(
                                                    "Enviar",
                                                    id="chatbot-send-btn",
                                                    color="primary",
                                                    n_clicks=0,
                                                ),
                                                dbc.Button(
                                                    "Limpiar",
                                                    id="chatbot-clear-btn",
                                                    color="secondary",
                                                    outline=True,
                                                    n_clicks=0,
                                                ),
                                            ]
                                        ),
                                        # Estado interno del chat
                                        dcc.Store(id="chatbot-state", data={}),
                                    ]
                                ),
                            ],
                            className="shadow-sm border-0 panel-card",
                        ),
                        md=10,
                        className="mx-auto",
                    )
                ],
                justify="center",
            )
        ],
        fluid=True,
        className="py-3",
    )