from fasthtml.common import *
from pathlib import Path

# link to main theme with fallback to local copy
pico_link = Link(rel="stylesheet",
                 href="https://cdn.jsdelivr.net/npm/@picocss/pico@latest/css/pico.pumpkin.min.css",
                 onerror="this.onerror=null;this.href='css/vendor/pico.pumpkin.min.css';")

app, rt = fast_app(pico=False,
                   hdrs=(pico_link,),
                   static_path="src/static",
                   live=True,
                   debug=True)

@rt("/")
def get():
    return Titled("FastHTML",
                  Div("Hello, World!"),
                  Button("Button"))

serve()