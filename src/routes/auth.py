from fasthtml.common import *

rt = APIRouter()

@rt.get("/login")
def get():
    return Titled("Login", Div("Login"))