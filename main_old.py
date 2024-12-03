from fasthtml.common import *
from pathlib import Path
from hmac import compare_digest
from datetime import datetime
import bcrypt

pico_link = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@latest/css/pico.pumpkin.min.css")
style = Style("""
            :root { --pico-font-size: 100%; }
            .login-container {
              text-align: center;
              padding: 2rem;
            }
            .login-container form {
              margin: 0 auto;
              max-width: 30rem;
            }
            .error-message {
              display: block;
              background-color: #ffebee;
              color: #d32f2f;
              border: 1px solid #ef5350;
              padding: 1rem;
              border-radius: var(--pico-border-radius);
              margin-bottom: 1rem;
            }
            input[name="email"].invalid-email {
              border-color: #ef5350 !important;
              outline-color: #ef5350 !important;
            }
            input[name="email"].valid-email {
              border-color: #4caf50 !important;
              outline-color: #4caf50 !important;
            }
            .password-input.valid-password {
              border-color: #4caf50 !important;
              outline-color: #4caf50 !important;
            }
            .password-input.invalid-password {
              border-color: #ef5350 !important;
              outline-color: #ef5350 !important;
            }
            .validation-message {
              font-size: 0.875rem;
              margin-top: 0.0rem;
              margin-bottom: 1.0rem;
              display: none;
            }
            .invalid-email + .validation-message {
              display: block;
              color: #ef5350;
            }
            .password-strength {
              font-size: 0.875rem;
              margin-top: 0.0rem;
              margin-bottom: 0.0rem;
            }
            .requirements-container {
              font-size: 0.875rem;
              margin-top: 0.0rem;
              margin-bottom: 1.0rem;
              background-color: #f5f5f5;
              border-radius: var(--pico-border-radius);
              padding: 0.5rem 1rem;
            }
            .requirements-list {
              list-style: none;
              padding-left: 0;
              margin: 0.5rem 0;
            }
            .requirement-met {
              color: #388e3c;
            }
            .requirement-met::before {
              content: "✓";
              margin-right: 0.5rem;
            }
            .requirement-unmet {
              color: #d32f2f;
            }
            .requirement-unmet::before {
              content: "✗";
              margin-right: 0.5rem;
            }
            .password-mismatch {
              border-color: #ef5350 !important;
              outline-color: #ef5350 !important;
            }
            .password-match {
              border-color: #4caf50 !important;
              outline-color: #4caf50 !important;
            }
            .match-message {
              font-size: 0.875rem;
              margin-top: 0.25rem;
              margin-bottom: 1.0rem;
              display: none;
            }
            .password-mismatch + .match-message {
              display: block;
              color: #ef5350;
            }
            """)
validator_script = Script(src="https://cdnjs.cloudflare.com/ajax/libs/validator/13.11.0/validator.min.js")
script = Script("""
                const validateEmail = (input) => {
                    // Skip validation if empty
                    if (!input.value.trim()) {
                        input.classList.remove('invalid-email');
                        input.classList.remove('valid-email');
                        return;
                    }
                    if (validator.isEmail(input.value)) {
                        input.classList.remove("invalid-email");
                        input.classList.add("valid-email");
                    } else {
                        input.classList.remove("valid-email");
                        input.classList.add("invalid-email");
                    }
                };

                document.addEventListener("DOMContentLoaded", () => {
                    const emailInputs = document.querySelectorAll('input[name="email"]');
                    emailInputs.forEach(input => {
                        input.addEventListener('input', debounce((e) => validateEmail(e.target), 100));
                    });
                
                    const confirmPasswordInput = document.getElementById('confirm_password');
                    confirmPasswordInput.addEventListener('input', 
                        debounce((e) => validatePasswordMatch(e.target), 100)
                    );
                
                    document.body.addEventListener('htmx:afterSwap', function(evt) {
                        console.log('Swap completed:', evt.detail);
                    });
                
                });

                function debounce(func, wait) {
                    let timeout;
                    return function(...args) {
                        clearTimeout(timeout);
                        timeout = setTimeout(() => func.apply(this, args), wait);
                    };
                }

                const validatePasswordMatch = (confirmInput) => {
                    const password = document.getElementById('password').value;
                    const confirmPassword = confirmInput.value;
                    
                    // Skip validation if either field is empty
                    if (!password || !confirmPassword) {
                        confirmInput.classList.remove('password-mismatch');
                        confirmInput.classList.remove('password-match');
                        return;
                    }
                    
                    if (password === confirmPassword) {
                        confirmInput.classList.remove('password-mismatch');
                        confirmInput.classList.add('password-match');
                    } else {
                        confirmInput.classList.remove('password-match');
                        confirmInput.classList.add('password-mismatch');
                    }
                };
                """)

app, rt = fast_app(pico=False,
                   hdrs=(pico_link, style, validator_script, script),
                   live=True,
                   debug=True)

db_path = Path("data")
db_path.mkdir(exist_ok=True)
db = database(db_path / "application.db")
users = db.t.users

if users not in db.t:
    users.create(dict(
        email=str,
        password=str,
        status=str,
        created_at=str,
        updated_at=str,
    ), pk="email")

@rt("/")
def get():
    return Titled("Image Generation Site",
                  Article(P("Please log in or register to continue"),
                          Form(Div(Input(id="email", name="email", placeholder="Email"),
                                   Span("Not a valid email address", cls="validation-message")),
                               Input(id="password", name="password", type="password", placeholder="Password"),
                               P(id="login-error",
                                 style="display: none;"),
                               Button("Login", type="submit"),
                               hx_post="/login",
                               hx_target="#login-error",
                               hx_swap="outerHTML"),
                          P("Don't have an account?"),
                          A("Register here", href="/register"),
                          cls="container login-container"))


@rt("/register")
def get():
    return Titled("Register",
                  Article(P("Enter an email and password to register"),
                          Form(Div(Input(id="email", name="email", placeholder="Email"),
                                   Span("Not a valid email address", cls="validation-message")),
                               Div(Input(id="password", name="password", type="password", placeholder="Password",
                                         cls="password-input",
                                         hx_post="/password-strength",
                                         hx_trigger="keyup changed delay:100ms",
                                         hx_target="#password-strength",
                                         hx_swap_oob="true"),
                                    Div(id="password-strength")),
                               Div(Input(id="confirm_password", name="confirm_password", type="password", placeholder="Confirm Password"),
                                   Span("Passwords do not match", cls="match-message")),
                               P(id="register-error",
                                 style="display: none;"),
                               Button("Register", type="submit"),
                               hx_post="/register",
                               hx_target="#register-error",
                               hx_swap="outerHTML"),
                          P("Already have an account?"),
                          A("Login here", href="/"),
                          cls="container login-container"))

@rt("/password-strength")
def post(password: str):
    # return nothing if password empty
    if not password.strip():
        return (
            Div(id="password-strength"),
            Div(id="password", 
                cls="password-input",  # Keep base class
                hx_swap_oob="class")
        )
    
    # define requirements
    requirements = {
        "length": {"met": len(password) >= 8,
                   "text": "At least 8 characters"},
        "uppercase": {"met": any(c.isupper() for c in password),
                      "text": "At least one uppercase letter"},
        "lowercase": {"met": any(c.islower() for c in password),
                      "text": "At least one lowercase letter"},
        "number": {"met": any(c.isdigit() for c in password),
                   "text": "At least one number"},
        "special": {"met": any(not c.isalnum() for c in password),
                     "text": "At least one special character"},
    }

    # create list of items for requirements
    requirement_items = [
        Li(req["text"], cls=f"requirement-{'met' if req['met'] else 'unmet'}")
        for req in requirements.values()
    ]

    # Check if all requirements are met
    all_requirements_met = all(req['met'] for req in requirements.values())

    return_value = (
        # main response for password strenght div
        Div("Password requirements:",
            Ul(*requirement_items, cls="requirements-list"),
            id="password-strength",
            cls="requirements-container"),
        # Set complete class string including base class
        Div(id="password",
            cls=f"password-input {('valid-password' if all_requirements_met else 'invalid-password')}",
            hx_swap_oob="class")
    )

    return return_value


@rt("/dashboard")
def get(session):
    return P("Welcome to the dashboard")


@rt("/login")
def post(email: str, password: str, session):
    try:
        user = users[email]
    except NotFoundError:
        return P("Invalid email or password",
                 id="login-error",
                 cls="error-message")
    
    session["auth"] = email
    response = Response(status_code=303)
    response.headers["hx-redirect"] = "/dashboard"
    return response


@rt("/register")
def post(email: str, password: str, confirm_password: str, session):
    # check whether email is already in use
    if email in users:
        return P("Email already in use",
                 id="register-error",
                 cls="error-message")
    # check whether passwords match
    if password != confirm_password:
        return P("Passwords do not match",
                 id="register-error",
                 cls="error-message")
    # since email not in use and passwords match, create user
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    new_user = users.insert(dict(
        email=email,
        password=hashed_password.decode("utf-8"),
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    ))
    response = Response(status_code=303)
    response.headers["hx-redirect"] = "/"
    return response


serve()
