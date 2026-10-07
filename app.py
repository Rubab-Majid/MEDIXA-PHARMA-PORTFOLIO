from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    g,
)
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

import sqlite3
import os
import re
import hashlib
import secrets
import smtplib

from email.message import EmailMessage
from urllib.parse import urlparse, urljoin
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

IS_PRODUCTION_DATABASE = bool(
    os.environ.get("DATABASE_URL")
)

SECRET_KEY = os.environ.get("MEDIXA_SECRET_KEY")

if IS_PRODUCTION_DATABASE and not SECRET_KEY:
    raise RuntimeError(
        "MEDIXA_SECRET_KEY must be set when DATABASE_URL is configured."
    )

app.secret_key = SECRET_KEY or secrets.token_hex(32)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.environ.get(
            "MEDIXA_COOKIE_SECURE",
            "0"
        ) == "1"
    ),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# Render sits behind a proxy.
# This allows Flask to correctly understand HTTPS requests.
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
)


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).strip()

# Render may provide postgres://.
# Psycopg expects postgresql://.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

database_setting = os.environ.get(
    "MEDIXA_DATABASE",
    "pharma.db"
)

if not os.path.isabs(database_setting):
    database_setting = os.path.join(
        BASE_DIR,
        database_setting
    )

SQLITE_DATABASE = database_setting


# =========================================================
# APPLICATION SETTINGS
# =========================================================

APP_BASE_URL = os.environ.get(
    "MEDIXA_BASE_URL",
    ""
).rstrip("/")

LOW_STOCK_LIMIT = 10

RESET_TOKEN_MINUTES = 30

DEV_RESET_LINK = (
    os.environ.get(
        "MEDIXA_DEV_RESET_LINK",
        "0"
    ) == "1"
)

BUSINESS_TIMEZONE = ZoneInfo(
    os.environ.get(
        "MEDIXA_TIMEZONE",
        "Asia/Karachi"
    )
)


def business_today():
    return datetime.now(
        BUSINESS_TIMEZONE
    ).date()


# =========================================================
# DATABASE COMPATIBILITY LAYER
# =========================================================

class DatabaseConnection:

    def __init__(self, connection, postgres=False):
        self.connection = connection
        self.postgres = postgres

    def execute(self, sql, params=()):
        if self.postgres:
            # Application SQL uses ? placeholders.
            # PostgreSQL uses %s.
            sql = sql.replace("?", "%s")

            return self.connection.execute(
                sql,
                params
            )

        return self.connection.execute(
            sql,
            params
        )

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def get_db():

    if "db" not in g:

        if DATABASE_URL:

            connection = psycopg.connect(
                DATABASE_URL,
                row_factory=dict_row,
                connect_timeout=15,
            )

            g.db = DatabaseConnection(
                connection,
                postgres=True
            )

        else:

            connection = sqlite3.connect(
                SQLITE_DATABASE,
                timeout=30,
            )

            connection.row_factory = sqlite3.Row

            connection.execute(
                "PRAGMA foreign_keys = ON"
            )

            g.db = DatabaseConnection(
                connection,
                postgres=False
            )

    return g.db


@app.teardown_appcontext
def close_db(exception=None):

    db = g.pop(
        "db",
        None
    )

    if db is not None:

        if exception is not None:

            try:
                db.rollback()
            except Exception:
                pass

        db.close()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    db = get_db()

    if db.postgres:

        statements = [

            """
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                name TEXT NOT NULL,
                medicine_type TEXT NOT NULL,
                date_added TEXT NOT NULL
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

                medicine_id INTEGER NOT NULL,

                transaction_type TEXT NOT NULL
                    CHECK (
                        transaction_type IN ('Purchase', 'Sell')
                    ),

                quantity INTEGER NOT NULL
                    CHECK (quantity > 0),

                purchase_price DOUBLE PRECISION NOT NULL DEFAULT 0,

                selling_price DOUBLE PRECISION NOT NULL DEFAULT 0,

                unit_profit DOUBLE PRECISION NOT NULL DEFAULT 0,

                total_profit DOUBLE PRECISION NOT NULL DEFAULT 0,

                transaction_date TEXT NOT NULL,

                manufacturing_date TEXT,

                expiry_date TEXT,

                FOREIGN KEY (medicine_id)
                    REFERENCES medicines(id)
                    ON DELETE CASCADE
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

                username TEXT NOT NULL,

                email TEXT NOT NULL,

                password_hash TEXT NOT NULL,

                created_at TEXT NOT NULL
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

                user_id INTEGER NOT NULL,

                token_hash TEXT NOT NULL UNIQUE,

                expires_at TEXT NOT NULL,

                used_at TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """,

            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_medicines_name_lower
            ON medicines (LOWER(name))
            """,

            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_username_lower
            ON users (LOWER(username))
            """,

            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_email_lower
            ON users (LOWER(email))
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_transactions_medicine
            ON transactions(medicine_id)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_transactions_type
            ON transactions(transaction_type)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_transactions_date
            ON transactions(transaction_date)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_password_resets_token
            ON password_resets(token_hash)
            """,

            """
            CREATE INDEX IF NOT EXISTS
            idx_password_resets_user
            ON password_resets(user_id)
            """,
        ]

        for statement in statements:
            db.execute(statement)

        db.commit()

    else:

        schema = """

        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            medicine_type TEXT NOT NULL,
            date_added TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            medicine_id INTEGER NOT NULL,

            transaction_type TEXT NOT NULL
                CHECK (
                    transaction_type IN ('Purchase', 'Sell')
                ),

            quantity INTEGER NOT NULL
                CHECK (quantity > 0),

            purchase_price REAL NOT NULL DEFAULT 0,

            selling_price REAL NOT NULL DEFAULT 0,

            unit_profit REAL NOT NULL DEFAULT 0,

            total_profit REAL NOT NULL DEFAULT 0,

            transaction_date TEXT NOT NULL,

            manufacturing_date TEXT,

            expiry_date TEXT,

            FOREIGN KEY (medicine_id)
                REFERENCES medicines(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL UNIQUE COLLATE NOCASE,

            email TEXT NOT NULL UNIQUE COLLATE NOCASE,

            password_hash TEXT NOT NULL,

            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            token_hash TEXT NOT NULL UNIQUE,

            expires_at TEXT NOT NULL,

            used_at TEXT,

            created_at TEXT NOT NULL,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS
        idx_transactions_medicine
        ON transactions(medicine_id);

        CREATE INDEX IF NOT EXISTS
        idx_transactions_type
        ON transactions(transaction_type);

        CREATE INDEX IF NOT EXISTS
        idx_transactions_date
        ON transactions(transaction_date);

        CREATE INDEX IF NOT EXISTS
        idx_password_resets_token
        ON password_resets(token_hash);

        CREATE INDEX IF NOT EXISTS
        idx_password_resets_user
        ON password_resets(user_id);
        """

        # SQLite supports executescript directly.
        db.connection.executescript(schema)

        db.commit()


# Create tables only.
# No users, medicines or transactions are inserted.
with app.app_context():
    init_db()


# =========================================================
# TEMPLATE FILTER
# =========================================================

@app.template_filter("format_date")
def format_date(value):

    if not value:
        return "-"

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).strftime("%m/%d/%Y")

    except (TypeError, ValueError):

        return value


# =========================================================
# MEDICINE STATISTICS
# =========================================================

def get_medicine_stats(medicine_id):

    db = get_db()

    purchase_row = db.execute(
        """
        SELECT
            COALESCE(SUM(quantity), 0) AS quantity,
            COALESCE(
                SUM(quantity * purchase_price),
                0
            ) AS value
        FROM transactions
        WHERE medicine_id = ?
          AND transaction_type = 'Purchase'
        """,
        (medicine_id,)
    ).fetchone()

    sell_row = db.execute(
        """
        SELECT
            COALESCE(SUM(quantity), 0) AS quantity,
            COALESCE(
                SUM(total_profit),
                0
            ) AS profit
        FROM transactions
        WHERE medicine_id = ?
          AND transaction_type = 'Sell'
        """,
        (medicine_id,)
    ).fetchone()

    latest_price_row = db.execute(
        """
        SELECT selling_price
        FROM transactions
        WHERE medicine_id = ?
          AND transaction_type = 'Sell'
        ORDER BY id DESC
        LIMIT 1
        """,
        (medicine_id,)
    ).fetchone()

    total_purchased = purchase_row["quantity"]
    total_purchase_value = purchase_row["value"]

    total_sold = sell_row["quantity"]
    total_profit = sell_row["profit"]

    balance = (
        total_purchased
        - total_sold
    )

    if total_purchased > 0:

        average_purchase_price = (
            total_purchase_value
            / total_purchased
        )

    else:

        average_purchase_price = 0

    if total_sold > 0:

        average_profit = (
            total_profit
            / total_sold
        )

    else:

        average_profit = 0

    latest_selling_price = (
        latest_price_row["selling_price"]
        if latest_price_row
        else 0
    )

    return {
        "total_purchased": total_purchased,
        "total_purchase_value": total_purchase_value,
        "total_sold": total_sold,
        "total_profit": total_profit,
        "balance": balance,
        "average_purchase_price": average_purchase_price,
        "average_profit": average_profit,
        "latest_selling_price": latest_selling_price,
    }


# =========================================================
# SECURITY HELPERS
# =========================================================

def is_safe_url(target):

    if not target:
        return False

    host_url = urlparse(
        request.host_url
    )

    redirect_url = urlparse(
        urljoin(
            request.host_url,
            target
        )
    )

    return (
        redirect_url.scheme
        in ("http", "https")
        and redirect_url.netloc
        == host_url.netloc
    )


def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if g.user is None:

            next_url = request.full_path

            if next_url.endswith("?"):
                next_url = next_url[:-1]

            return redirect(
                url_for(
                    "login",
                    next=next_url
                )
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped_view


# =========================================================
# VALIDATION HELPERS
# =========================================================

def normalize_email(email):

    return (
        email or ""
    ).strip().lower()


def normalize_username(username):

    return (
        username or ""
    ).strip()


def valid_username(username):

    return bool(
        re.fullmatch(
            r"[A-Za-z0-9_.-]{3,50}",
            username
        )
    )


def valid_email(email):

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        )
    )


def valid_password(password):

    if not password:
        return False

    if len(password) < 8:
        return False

    if len(password) > 128:
        return False

    if not re.search(
        r"[A-Za-z]",
        password
    ):
        return False

    if not re.search(
        r"\d",
        password
    ):
        return False

    return True


def hash_reset_token(token):

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# =========================================================
# EMAIL CONFIGURATION
# =========================================================

SMTP_HOST = os.environ.get(
    "MEDIXA_SMTP_HOST"
)

SMTP_PORT = int(
    os.environ.get(
        "MEDIXA_SMTP_PORT",
        "587"
    )
)

SMTP_USER = os.environ.get(
    "MEDIXA_SMTP_USER"
)

SMTP_PASSWORD = os.environ.get(
    "MEDIXA_SMTP_PASSWORD"
)

SMTP_FROM = os.environ.get(
    "MEDIXA_SMTP_FROM"
)


def send_password_reset_email(
    recipient,
    reset_url
):

    if not (
        SMTP_HOST
        and SMTP_USER
        and SMTP_PASSWORD
        and SMTP_FROM
    ):
        return False

    message = EmailMessage()

    message["Subject"] = (
        "MEDIXA PHARMA - Password Reset"
    )

    message["From"] = SMTP_FROM
    message["To"] = recipient

    message.set_content(
        f"""
Hello,

A password reset request was made for your MEDIXA PHARMA account.

Use the following link to reset your password:

{reset_url}

This link expires in {RESET_TOKEN_MINUTES} minutes.

If you did not request this password reset, you can ignore this email.

MEDIXA PHARMA
Inventory Management System
"""
    )

    try:

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20
        ) as server:

            server.starttls()

            server.login(
                SMTP_USER,
                SMTP_PASSWORD
            )

            server.send_message(
                message
            )

        return True

    except Exception as exc:

        app.logger.exception(
            "Password reset email failed: %s",
            exc
        )

        return False


# =========================================================
# LOAD LOGGED-IN USER
# =========================================================

@app.before_request
def load_logged_in_user():

    public_endpoints = {
        "static",
        "health",
        "login",
        "register",
        "forgot_password",
        "reset_password",
        "logout",
    }

    if request.endpoint in public_endpoints:

        g.user = None

        if "user_id" in session:

            db = get_db()

            g.user = db.execute(
                """
                SELECT id, username, email
                FROM users
                WHERE id = ?
                """,
                (session["user_id"],)
            ).fetchone()

        return

    g.user = None

    if "user_id" in session:

        db = get_db()

        g.user = db.execute(
            """
            SELECT id, username, email
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()

    if g.user is None:

        session.clear()

        return redirect(
            url_for(
                "login",
                next=request.full_path
            )
        )


# =========================================================
# GLOBAL USER CONTEXT
# =========================================================

@app.context_processor
def inject_current_user():

    return {
        "current_user": g.user
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    try:

        db = get_db()

        db.execute(
            "SELECT 1"
        ).fetchone()

        return {
            "status": "ok",
            "database": (
                "postgresql"
                if db.postgres
                else "sqlite"
            )
        }, 200

    except Exception:

        app.logger.exception(
            "Health check failed"
        )

        return {
            "status": "error"
        }, 503


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if g.user is not None:
        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        username_or_email = (
            request.form.get(
                "username_or_email",
                ""
            ).strip()
        )

        password = request.form.get(
            "password",
            ""
        )

        if (
            not username_or_email
            or not password
        ):

            flash(
                "Please enter your username/email and password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(username) = LOWER(?)
               OR LOWER(email) = LOWER(?)
            LIMIT 1
            """,
            (
                username_or_email,
                username_or_email
            )
        ).fetchone()

        if user is None:

            flash(
                "Invalid username/email or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        if not check_password_hash(
            user["password_hash"],
            password
        ):

            flash(
                "Invalid username/email or password.",
                "danger"
            )

            return render_template(
                "login.html"
            )

        session.clear()

        session["user_id"] = user["id"]

        session.permanent = True

        next_url = request.args.get(
            "next"
        )

        if (
            next_url
            and is_safe_url(next_url)
        ):

            return redirect(
                next_url
            )

        return redirect(
            url_for("home")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if g.user is not None:

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        username = normalize_username(
            request.form.get(
                "username"
            )
        )

        email = normalize_email(
            request.form.get(
                "email"
            )
        )

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        error = None

        if not valid_username(username):

            error = (
                "Username must contain 3-50 "
                "letters, numbers, dots, "
                "underscores or hyphens."
            )

        elif not valid_email(email):

            error = (
                "Please enter a valid email address."
            )

        elif not valid_password(password):

            error = (
                "Password must be 8-128 characters "
                "and contain at least one letter "
                "and one number."
            )

        elif password != confirm_password:

            error = (
                "Passwords do not match."
            )

        if error is None:

            db = get_db()

            existing = db.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(username) = LOWER(?)
                   OR LOWER(email) = LOWER(?)
                LIMIT 1
                """,
                (
                    username,
                    email
                )
            ).fetchone()

            if existing:

                error = (
                    "Username or email already exists."
                )

        if error:

            flash(
                error,
                "danger"
            )

        else:

            db.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password_hash,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    generate_password_hash(
                        password
                    ),
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )
            )

            db.commit()

            flash(
                "Account created successfully. Please log in.",
                "success"
            )

            return redirect(
                url_for("login")
            )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if g.user is not None:

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        email = normalize_email(
            request.form.get(
                "email"
            )
        )

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(email) = LOWER(?)
            LIMIT 1
            """,
            (email,)
        ).fetchone()

        if user:

            token = secrets.token_urlsafe(
                48
            )

            token_hash = hash_reset_token(
                token
            )

            now = datetime.now(
                timezone.utc
            )

            expires = (
                now
                + timedelta(
                    minutes=RESET_TOKEN_MINUTES
                )
            )

            db.execute(
                """
                UPDATE password_resets
                SET used_at = ?
                WHERE user_id = ?
                  AND used_at IS NULL
                """,
                (
                    now.isoformat(),
                    user["id"]
                )
            )

            db.execute(
                """
                INSERT INTO password_resets
                (
                    user_id,
                    token_hash,
                    expires_at,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    user["id"],
                    token_hash,
                    expires.isoformat(),
                    now.isoformat()
                )
            )

            db.commit()

            if APP_BASE_URL:

                reset_url = (
                    f"{APP_BASE_URL}"
                    f"{url_for('reset_password', token=token)}"
                )

            else:

                reset_url = url_for(
                    "reset_password",
                    token=token,
                    _external=True
                )

            sent = send_password_reset_email(
                email,
                reset_url
            )

            if (
                not sent
                and DEV_RESET_LINK
            ):

                app.logger.warning(
                    "DEV PASSWORD RESET LINK: %s",
                    reset_url
                )

        flash(
            "If an account exists for that email, "
            "password reset instructions have been generated.",
            "info"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "forgot_password.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    token_hash = hash_reset_token(
        token
    )

    db = get_db()

    reset = db.execute(
        """
        SELECT *
        FROM password_resets
        WHERE token_hash = ?
          AND used_at IS NULL
        """,
        (token_hash,)
    ).fetchone()

    if not reset:

        flash(
            "This password reset link is invalid.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    try:

        expires_at = datetime.fromisoformat(
            reset["expires_at"]
        )

    except ValueError:

        expires_at = datetime.min.replace(
            tzinfo=timezone.utc
        )

    if (
        expires_at
        < datetime.now(timezone.utc)
    ):

        flash(
            "This password reset link has expired.",
            "danger"
        )

        return redirect(
            url_for("forgot_password")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not valid_password(password):

            flash(
                "Password must be 8-128 characters "
                "and contain at least one letter "
                "and one number.",
                "danger"
            )

        elif password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

        else:

            db.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
                """,
                (
                    generate_password_hash(
                        password
                    ),
                    reset["user_id"]
                )
            )

            db.execute(
                """
                UPDATE password_resets
                SET used_at = ?
                WHERE id = ?
                """,
                (
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
                    reset["id"]
                )
            )

            db.commit()

            flash(
                "Password reset successfully. Please log in.",
                "success"
            )

            return redirect(
                url_for("login")
            )

    return render_template(
        "reset_password.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def home():

    db = get_db()

    medicines = db.execute(
        """
        SELECT *
        FROM medicines
        ORDER BY LOWER(name)
        """
    ).fetchall()

    medicine_data = []

    total_stock = 0
    low_stock_count = 0

    for medicine in medicines:

        stats = get_medicine_stats(
            medicine["id"]
        )

        item = dict(medicine)

        item.update(stats)

        medicine_data.append(item)

        total_stock += stats["balance"]

        if (
            stats["balance"]
            <= LOW_STOCK_LIMIT
        ):

            low_stock_count += 1

    transaction_count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        """
    ).fetchone()["count"]

    today = business_today()

    expired_count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE transaction_type = 'Purchase'
          AND expiry_date IS NOT NULL
          AND expiry_date < ?
        """,
        (today.isoformat(),)
    ).fetchone()["count"]

    expiring_date = (
        today
        + timedelta(days=30)
    )

    expiring_count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE transaction_type = 'Purchase'
          AND expiry_date IS NOT NULL
          AND expiry_date >= ?
          AND expiry_date <= ?
        """,
        (
            today.isoformat(),
            expiring_date.isoformat()
        )
    ).fetchone()["count"]

    return render_template(
        "home.html",
        medicines=medicine_data,
        total_stock=total_stock,
        low_stock_count=low_stock_count,
        transaction_count=transaction_count,
        expired_count=expired_count,
        expiring_count=expiring_count,
    )


# =========================================================
# INVENTORY
# =========================================================

@app.route("/inventory")
@login_required
def inventory():

    db = get_db()

    medicines = db.execute(
        """
        SELECT *
        FROM medicines
        ORDER BY LOWER(name)
        """
    ).fetchall()

    inventory_data = []

    for medicine in medicines:

        stats = get_medicine_stats(
            medicine["id"]
        )

        item = dict(medicine)

        item.update(stats)

        inventory_data.append(item)

    return render_template(
        "inventory.html",
        medicines=inventory_data
    )


# =========================================================
# ADD MEDICINE
# =========================================================

@app.route(
    "/add-medicine",
    methods=["GET", "POST"]
)
@login_required
def add_medicine():

    if request.method == "POST":

        name = (
            request.form.get(
                "name",
                ""
            ).strip()
        )

        medicine_type = (
            request.form.get(
                "medicine_type",
                ""
            ).strip()
        )

        date_added = (
            request.form.get(
                "date_added",
                ""
            ).strip()
        )

        if not name:

            flash(
                "Medicine name is required.",
                "danger"
            )

            return render_template(
                "add_medicine.html"
            )

        if not medicine_type:

            flash(
                "Medicine type is required.",
                "danger"
            )

            return render_template(
                "add_medicine.html"
            )

        if not date_added:

            date_added = (
                business_today()
                .isoformat()
            )

        try:

            datetime.strptime(
                date_added,
                "%Y-%m-%d"
            )

        except ValueError:

            flash(
                "Invalid date.",
                "danger"
            )

            return render_template(
                "add_medicine.html"
            )

        db = get_db()

        existing = db.execute(
            """
            SELECT id
            FROM medicines
            WHERE LOWER(name) = LOWER(?)
            LIMIT 1
            """,
            (name,)
        ).fetchone()

        if existing:

            flash(
                "This medicine already exists.",
                "danger"
            )

            return render_template(
                "add_medicine.html"
            )

        db.execute(
            """
            INSERT INTO medicines
            (
                name,
                medicine_type,
                date_added
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                medicine_type,
                date_added
            )
        )

        db.commit()

        flash(
            "Medicine added successfully.",
            "success"
        )

        return redirect(
            url_for("inventory")
        )

    return render_template(
        "add_medicine.html"
    )


# =========================================================
# EDIT MEDICINE
# =========================================================

@app.route(
    "/edit-medicine/<int:medicine_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_medicine(medicine_id):

    db = get_db()

    medicine = db.execute(
        """
        SELECT *
        FROM medicines
        WHERE id = ?
        """,
        (medicine_id,)
    ).fetchone()

    if medicine is None:

        flash(
            "Medicine not found.",
            "danger"
        )

        return redirect(
            url_for("inventory")
        )

    if request.method == "POST":

        name = (
            request.form.get(
                "name",
                ""
            ).strip()
        )

        medicine_type = (
            request.form.get(
                "medicine_type",
                ""
            ).strip()
        )

        date_added = (
            request.form.get(
                "date_added",
                ""
            ).strip()
        )

        if not name or not medicine_type:

            flash(
                "Medicine name and type are required.",
                "danger"
            )

        else:

            duplicate = db.execute(
                """
                SELECT id
                FROM medicines
                WHERE LOWER(name) = LOWER(?)
                  AND id != ?
                LIMIT 1
                """,
                (
                    name,
                    medicine_id
                )
            ).fetchone()

            if duplicate:

                flash(
                    "Another medicine already has this name.",
                    "danger"
                )

            else:

                db.execute(
                    """
                    UPDATE medicines
                    SET name = ?,
                        medicine_type = ?,
                        date_added = ?
                    WHERE id = ?
                    """,
                    (
                        name,
                        medicine_type,
                        date_added,
                        medicine_id
                    )
                )

                db.commit()

                flash(
                    "Medicine updated successfully.",
                    "success"
                )

                return redirect(
                    url_for("inventory")
                )

    return render_template(
        "edit_medicine.html",
        medicine=medicine
    )


# =========================================================
# DELETE MEDICINE
# =========================================================

@app.route(
    "/delete-medicine/<int:medicine_id>",
    methods=["POST"]
)
@login_required
def delete_medicine(medicine_id):

    db = get_db()

    medicine = db.execute(
        """
        SELECT *
        FROM medicines
        WHERE id = ?
        """,
        (medicine_id,)
    ).fetchone()

    if medicine is None:

        flash(
            "Medicine not found.",
            "danger"
        )

        return redirect(
            url_for("inventory")
        )

    transaction_exists = db.execute(
        """
        SELECT id
        FROM transactions
        WHERE medicine_id = ?
        LIMIT 1
        """,
        (medicine_id,)
    ).fetchone()

    if transaction_exists:

        flash(
            "This medicine has transaction history and cannot be deleted.",
            "danger"
        )

        return redirect(
            url_for("inventory")
        )

    db.execute(
        """
        DELETE FROM medicines
        WHERE id = ?
        """,
        (medicine_id,)
    )

    db.commit()

    flash(
        "Medicine deleted successfully.",
        "success"
    )

    return redirect(
        url_for("inventory")
    )


# =========================================================
# MEDICINE DETAILS
# =========================================================

@app.route(
    "/medicine/<int:medicine_id>"
)
@login_required
def medicine_details(medicine_id):

    db = get_db()

    medicine = db.execute(
        """
        SELECT *
        FROM medicines
        WHERE id = ?
        """,
        (medicine_id,)
    ).fetchone()

    if medicine is None:

        flash(
            "Medicine not found.",
            "danger"
        )

        return redirect(
            url_for("inventory")
        )

    stats = get_medicine_stats(
        medicine_id
    )

    transaction_history = db.execute(
        """
        SELECT *
        FROM transactions
        WHERE medicine_id = ?
        ORDER BY transaction_date DESC, id DESC
        """,
        (medicine_id,)
    ).fetchall()

    purchase_history = db.execute(
        """
        SELECT *
        FROM transactions
        WHERE medicine_id = ?
          AND transaction_type = 'Purchase'
        ORDER BY transaction_date DESC, id DESC
        """,
        (medicine_id,)
    ).fetchall()

    sell_history = db.execute(
        """
        SELECT *
        FROM transactions
        WHERE medicine_id = ?
          AND transaction_type = 'Sell'
        ORDER BY transaction_date DESC, id DESC
        """,
        (medicine_id,)
    ).fetchall()

    return render_template(
        "medicine_details.html",
        medicine=medicine,
        stats=stats,
        transactions=transaction_history,
        purchase_history=purchase_history,
        sell_history=sell_history,
    )


# =========================================================
# PURCHASE
# =========================================================

@app.route(
    "/purchase",
    methods=["GET", "POST"]
)
@login_required
def purchase():

    db = get_db()

    medicines = db.execute(
        """
        SELECT *
        FROM medicines
        ORDER BY LOWER(name)
        """
    ).fetchall()

    if request.method == "POST":

        medicine_id = request.form.get(
            "medicine_id",
            ""
        )

        quantity_raw = request.form.get(
            "quantity",
            ""
        )

        purchase_price_raw = request.form.get(
            "purchase_price",
            ""
        )

        purchase_date = request.form.get(
            "purchase_date",
            ""
        )

        manufacturing_date = request.form.get(
            "manufacturing_date",
            ""
        )

        expiry_date = request.form.get(
            "expiry_date",
            ""
        )

        try:

            medicine_id = int(
                medicine_id
            )

        except ValueError:

            flash(
                "Please select a valid medicine.",
                "danger"
            )

            return render_template(
                "purchase.html",
                medicines=medicines
            )

        try:

            quantity = int(
                quantity_raw
            )

            if quantity <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Quantity must be a positive whole number.",
                "danger"
            )

            return render_template(
                "purchase.html",
                medicines=medicines
            )

        try:

            purchase_price = float(
                purchase_price_raw
            )

            if purchase_price < 0:
                raise ValueError

        except ValueError:

            flash(
                "Purchase price must be a valid number.",
                "danger"
            )

            return render_template(
                "purchase.html",
                medicines=medicines
            )

        try:

            purchase_dt = datetime.strptime(
                purchase_date,
                "%Y-%m-%d"
            ).date()

            manufacturing_dt = datetime.strptime(
                manufacturing_date,
                "%Y-%m-%d"
            ).date()

            expiry_dt = datetime.strptime(
                expiry_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Please provide valid dates.",
                "danger"
            )

            return render_template(
                "purchase.html",
                medicines=medicines
            )

        if manufacturing_dt > expiry_dt:

            flash(
                "Manufacturing date cannot be after expiry date.",
                "danger"
            )

            return render_template(
                "purchase.html",
                medicines=medicines
            )

        if expiry_dt < purchase_dt:

            flash(
                "Expiry date cannot be before the purchase date.",
                "danger"
            )

            return render_template(
                "purchase.html",
                medicines=medicines
            )

        medicine = db.execute(
            """
            SELECT *
            FROM medicines
            WHERE id = ?
            """,
            (medicine_id,)
        ).fetchone()

        if medicine is None:

            flash(
                "Medicine not found.",
                "danger"
            )

            return render_template(
                "purchase.html",
                medicines=medicines
            )

        db.execute(
            """
            INSERT INTO transactions
            (
                medicine_id,
                transaction_type,
                quantity,
                purchase_price,
                selling_price,
                unit_profit,
                total_profit,
                transaction_date,
                manufacturing_date,
                expiry_date
            )
            VALUES (?, 'Purchase', ?, ?, 0, 0, 0, ?, ?, ?)
            """,
            (
                medicine_id,
                quantity,
                purchase_price,
                purchase_date,
                manufacturing_date,
                expiry_date
            )
        )

        db.commit()

        flash(
            "Purchase recorded successfully.",
            "success"
        )

        return redirect(
            url_for("inventory")
        )

    return render_template(
        "purchase.html",
        medicines=medicines
    )


# =========================================================
# SELL
# =========================================================

@app.route(
    "/sell",
    methods=["GET", "POST"]
)
@login_required
def sell():

    db = get_db()

    if request.method == "POST":

        medicine_id = request.form.get(
            "medicine_id",
            ""
        ).strip()

        quantity_text = request.form.get(
            "quantity",
            ""
        ).strip()

        selling_price_text = request.form.get(
            "selling_price",
            ""
        ).strip()

        sell_date = request.form.get(
            "sell_date",
            ""
        ).strip()

        if not medicine_id:

            flash(
                "Please select a medicine.",
                "danger"
            )

            return redirect(
                url_for("sell")
            )

        try:

            medicine_id = int(
                medicine_id
            )

        except ValueError:

            flash(
                "Invalid medicine selected.",
                "danger"
            )

            return redirect(
                url_for("sell")
            )

        try:

            quantity = int(
                quantity_text
            )

            if quantity <= 0:
                raise ValueError

        except ValueError:

            flash(
                "Quantity must be a positive whole number.",
                "danger"
            )

            return redirect(
                url_for("sell")
            )

        try:

            selling_price = float(
                selling_price_text
            )

            if selling_price < 0:
                raise ValueError

        except ValueError:

            flash(
                "Selling price must be a valid number.",
                "danger"
            )

            return redirect(
                url_for("sell")
            )

        try:

            datetime.strptime(
                sell_date,
                "%Y-%m-%d"
            )

        except ValueError:

            flash(
                "Please enter a valid selling date.",
                "danger"
            )

            return redirect(
                url_for("sell")
            )

        medicine = db.execute(
            """
            SELECT *
            FROM medicines
            WHERE id = ?
            """,
            (medicine_id,)
        ).fetchone()

        if medicine is None:

            flash(
                "Medicine not found.",
                "danger"
            )

            return redirect(
                url_for("sell")
            )

        stats = get_medicine_stats(
            medicine_id
        )

        balance = stats["balance"]

        average_purchase_price = (
            stats["average_purchase_price"]
        )

        if quantity > balance:

            flash(
                f"Insufficient stock. Available balance is {balance}.",
                "danger"
            )

            return redirect(
                url_for("sell")
            )

        unit_profit = (
            selling_price
            - average_purchase_price
        )

        total_profit = (
            unit_profit
            * quantity
        )

        db.execute(
            """
            INSERT INTO transactions
            (
                medicine_id,
                transaction_type,
                quantity,
                purchase_price,
                selling_price,
                unit_profit,
                total_profit,
                transaction_date,
                manufacturing_date,
                expiry_date
            )
            VALUES (
                ?,
                'Sell',
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                NULL,
                NULL
            )
            """,
            (
                medicine_id,
                quantity,
                average_purchase_price,
                selling_price,
                unit_profit,
                total_profit,
                sell_date,
            )
        )

        db.commit()

        flash(
            f"{medicine['name']} sold successfully. "
            f"Total profit: {total_profit:.2f}",
            "success"
        )

        return redirect(
            url_for("inventory")
        )

    medicines = db.execute(
        """
        SELECT *
        FROM medicines
        ORDER BY LOWER(name)
        """
    ).fetchall()

    medicine_data = []

    for medicine in medicines:

        stats = get_medicine_stats(
            medicine["id"]
        )

        item = dict(medicine)

        item.update(stats)

        medicine_data.append(item)

    return render_template(
        "sell.html",
        medicines=medicine_data
    )


# =========================================================
# TRANSACTIONS
# =========================================================

@app.route("/transactions")
@login_required
def transactions():

    db = get_db()

    transactions_data = db.execute(
        """
        SELECT
            t.*,
            m.name AS medicine_name,
            m.medicine_type
        FROM transactions t
        JOIN medicines m
            ON m.id = t.medicine_id
        ORDER BY
            t.transaction_date DESC,
            t.id DESC
        """
    ).fetchall()

    return render_template(
        "transactions.html",
        transactions=transactions_data
    )


# =========================================================
# EXPIRY MANAGEMENT
# =========================================================

@app.route("/expiry")
@login_required
def expiry():

    db = get_db()

    purchases = db.execute(
        """
        SELECT
            t.*,
            m.name AS medicine_name,
            m.medicine_type
        FROM transactions t
        JOIN medicines m
            ON m.id = t.medicine_id
        WHERE t.transaction_type = 'Purchase'
          AND t.expiry_date IS NOT NULL
        ORDER BY t.expiry_date ASC
        """
    ).fetchall()

    today = business_today()

    expiring = []
    expired = []
    valid = []

    for purchase_record in purchases:

        purchase_dict = dict(
            purchase_record
        )

        balance = get_medicine_stats(
            purchase_record["medicine_id"]
        )["balance"]

        purchase_dict[
            "remaining_balance"
        ] = balance

        try:

            expiry_date = datetime.strptime(
                purchase_record["expiry_date"],
                "%Y-%m-%d"
            ).date()

        except (
            TypeError,
            ValueError
        ):

            expiry_date = None

        if expiry_date is None:

            valid.append(
                purchase_dict
            )

        elif expiry_date < today:

            expired.append(
                purchase_dict
            )

        elif expiry_date <= (
            today
            + timedelta(days=30)
        ):

            expiring.append(
                purchase_dict
            )

        else:

            valid.append(
                purchase_dict
            )

    return render_template(
        "expiry.html",
        expired=expired,
        expiring=expiring,
        valid=valid,
        expired_count=len(expired),
        expiring_count=len(expiring),
        valid_count=len(valid),
    )


# =========================================================
# SECURITY HEADERS
# =========================================================

@app.after_request
def add_security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "SAMEORIGIN"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=()"
    )

    if (
        os.environ.get(
            "MEDIXA_COOKIE_SECURE",
            "0"
        ) == "1"
    ):

        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000; "
            "includeSubDomains"
        )

    return response


# =========================================================
# LOCAL DEVELOPMENT SERVER
# =========================================================

if __name__ == "__main__":

    use_waitress = (
        os.environ.get(
            "MEDIXA_USE_WAITRESS",
            "0"
        ) == "1"
    )

    port = int(
        os.environ.get(
            "PORT",
            "5000"
        )
    )

    if use_waitress:

        from waitress import serve

        serve(
            app,
            host="0.0.0.0",
            port=port
        )

    else:

        app.run(
            host="0.0.0.0",
            port=port,
            debug=False
        )