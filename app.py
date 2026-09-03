import os
import re
from datetime import date, timedelta

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# APPLICATION CONFIGURATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-this-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///typinn.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Render uses HTTPS.
# Local development can still use normal HTTP.
if os.environ.get("FLASK_ENV") == "production":
    app.config["SESSION_COOKIE_SECURE"] = True
else:
    app.config["SESSION_COOKIE_SECURE"] = False


# =========================================================
# DATABASE
# =========================================================

db = SQLAlchemy(app)


# =========================================================
# LOGIN MANAGER
# =========================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please log in to continue."


# =========================================================
# USER MODEL
# =========================================================

class User(db.Model, UserMixin):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    xp = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    streak = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    last_test_date = db.Column(
        db.Date,
        nullable=True
    )

    def level(self):
        return (self.xp // 100) + 1

    def level_xp(self):
        return self.xp % 100

    def xp_to_next_level(self):
        return 100 - self.level_xp()


# =========================================================
# ACHIEVEMENT MODEL
# =========================================================

class Achievement(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.String(255),
        nullable=False
    )

    icon = db.Column(
        db.String(10),
        nullable=False
    )


# =========================================================
# USER ACHIEVEMENT MODEL
# =========================================================

class UserAchievement(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    achievement_id = db.Column(
        db.Integer,
        db.ForeignKey("achievement.id"),
        nullable=False
    )

    earned_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "achievement_id"
        ),
    )


# =========================================================
# TYPING RESULT MODEL
# =========================================================

class TypingResult(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    wpm = db.Column(
        db.Integer,
        nullable=False
    )

    accuracy = db.Column(
        db.Integer,
        nullable=False
    )

    errors = db.Column(
        db.Integer,
        nullable=False
    )

    characters = db.Column(
        db.Integer,
        nullable=False
    )

    duration = db.Column(
        db.Integer,
        nullable=False
    )

    language = db.Column(
        db.String(30),
        default="english",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False
    )


# =========================================================
# XP SYSTEM
# =========================================================

def calculate_xp(wpm, accuracy, duration):

    base_xp = min(
        duration,
        120
    )

    speed_bonus = min(
        wpm // 10,
        20
    )

    if accuracy >= 95:
        accuracy_bonus = 15

    elif accuracy >= 90:
        accuracy_bonus = 10

    elif accuracy >= 80:
        accuracy_bonus = 5

    else:
        accuracy_bonus = 0

    return (
        base_xp
        + speed_bonus
        + accuracy_bonus
    )


# =========================================================
# DEFAULT ACHIEVEMENTS
# =========================================================

DEFAULT_ACHIEVEMENTS = [

    {
        "name": "First Steps",
        "description": "Complete your first typing test.",
        "icon": "🏆"
    },

    {
        "name": "Speed Demon",
        "description": "Reach 50 WPM.",
        "icon": "⚡"
    },

    {
        "name": "Fast Fingers",
        "description": "Reach 75 WPM.",
        "icon": "🚀"
    },

    {
        "name": "Speed Master",
        "description": "Reach 100 WPM.",
        "icon": "💨"
    },

    {
        "name": "Perfect",
        "description": "Achieve 100% accuracy.",
        "icon": "💯"
    },

    {
        "name": "On Fire",
        "description": "Maintain a 3-day streak.",
        "icon": "🔥"
    },

    {
        "name": "Dedicated",
        "description": "Maintain a 7-day streak.",
        "icon": "🔥"
    },

    {
        "name": "Typing Habit",
        "description": "Complete 10 typing tests.",
        "icon": "⌨️"
    }

]


# =========================================================
# CREATE ACHIEVEMENTS
# =========================================================

def create_achievements():

    for data in DEFAULT_ACHIEVEMENTS:

        existing = Achievement.query.filter_by(
            name=data["name"]
        ).first()

        if existing:
            continue

        achievement = Achievement(
            name=data["name"],
            description=data["description"],
            icon=data["icon"]
        )

        db.session.add(achievement)

    try:
        db.session.commit()

    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Failed to create achievements."
        )


# =========================================================
# CHECK ACHIEVEMENTS
# =========================================================

def check_achievements(user, result):

    earned = []

    total_tests = TypingResult.query.filter_by(
        user_id=user.id
    ).count()

    achievements = Achievement.query.all()

    for achievement in achievements:

        already_earned = UserAchievement.query.filter_by(
            user_id=user.id,
            achievement_id=achievement.id
        ).first()

        if already_earned:
            continue

        unlocked = False

        if achievement.name == "First Steps":

            unlocked = total_tests >= 1

        elif achievement.name == "Speed Demon":

            unlocked = result.wpm >= 50

        elif achievement.name == "Fast Fingers":

            unlocked = result.wpm >= 75

        elif achievement.name == "Speed Master":

            unlocked = result.wpm >= 100

        elif achievement.name == "Perfect":

            unlocked = result.accuracy == 100

        elif achievement.name == "On Fire":

            unlocked = user.streak >= 3

        elif achievement.name == "Dedicated":

            unlocked = user.streak >= 7

        elif achievement.name == "Typing Habit":

            unlocked = total_tests >= 10

        if unlocked:

            user_achievement = UserAchievement(
                user_id=user.id,
                achievement_id=achievement.id
            )

            db.session.add(
                user_achievement
            )

            earned.append(
                achievement
            )

    return earned


# =========================================================
# LOAD USER
# =========================================================

@login_manager.user_loader
def load_user(user_id):

    try:

        return db.session.get(
            User,
            int(user_id)
        )

    except (
        TypeError,
        ValueError
    ):

        return None


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        # -------------------------------------------------
        # USERNAME VALIDATION
        # -------------------------------------------------

        if not username:

            flash(
                "Username is required."
            )

            return redirect(
                url_for("register")
            )

        if len(username) < 3:

            flash(
                "Username must be at least 3 characters."
            )

            return redirect(
                url_for("register")
            )

        if len(username) > 80:

            flash(
                "Username is too long."
            )

            return redirect(
                url_for("register")
            )

        if not re.fullmatch(
            r"[A-Za-z0-9_]+",
            username
        ):

            flash(
                "Username can only contain letters, numbers, and underscores."
            )

            return redirect(
                url_for("register")
            )


        # -------------------------------------------------
        # EMAIL VALIDATION
        # -------------------------------------------------

        if not email:

            flash(
                "Email is required."
            )

            return redirect(
                url_for("register")
            )

        if len(email) > 120:

            flash(
                "Email address is too long."
            )

            return redirect(
                url_for("register")
            )

        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        ):

            flash(
                "Please enter a valid email address."
            )

            return redirect(
                url_for("register")
            )


        # -------------------------------------------------
        # PASSWORD VALIDATION
        # -------------------------------------------------

        if not password:

            flash(
                "Password is required."
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password must be at least 6 characters."
            )

            return redirect(
                url_for("register")
            )

        if len(password) > 128:

            flash(
                "Password is too long."
            )

            return redirect(
                url_for("register")
            )


        # -------------------------------------------------
        # DUPLICATE CHECK
        # -------------------------------------------------

        existing_user = User.query.filter(
            (User.username == username)
            |
            (User.email == email)
        ).first()

        if existing_user:

            flash(
                "Username or email already exists."
            )

            return redirect(
                url_for("register")
            )


        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        new_user = User(

            username=username,

            email=email,

            password_hash=generate_password_hash(
                password
            ),

            xp=0,

            streak=0,

            last_test_date=None

        )

        try:

            db.session.add(
                new_user
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

            app.logger.exception(
                "Failed to create user."
            )

            flash(
                "Could not create your account. Please try again."
            )

            return redirect(
                url_for("register")
            )


        flash(
            "Account created successfully. Please log in."
        )

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if (
            user
            and check_password_hash(
                user.password_hash,
                password
            )
        ):

            login_user(
                user
            )

            flash(
                "Welcome back!"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password."
        )


    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    results = (
        TypingResult.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            TypingResult.created_at.desc()
        )
        .all()
    )

    total_tests = len(
        results
    )

    if results:

        best_wpm = max(
            result.wpm
            for result in results
        )

        average_wpm = round(
            sum(
                result.wpm
                for result in results
            )
            / total_tests
        )

        average_accuracy = round(
            sum(
                result.accuracy
                for result in results
            )
            / total_tests
        )

        total_characters = sum(
            result.characters
            for result in results
        )

        total_time = sum(
            result.duration
            for result in results
        )

        latest_wpm = results[0].wpm

    else:

        best_wpm = 0

        average_wpm = 0

        average_accuracy = 0

        total_characters = 0

        total_time = 0

        latest_wpm = 0


    # -----------------------------------------------------
    # ACHIEVEMENTS
    # -----------------------------------------------------

    user_achievements = (
        UserAchievement.query
        .filter_by(
            user_id=current_user.id
        )
        .all()
    )

    achievement_ids = {
        item.achievement_id
        for item in user_achievements
    }

    achievements = (
        Achievement.query
        .order_by(
            Achievement.id.asc()
        )
        .all()
    )


    return render_template(

        "dashboard.html",

        user=current_user,

        results=results,

        total_tests=total_tests,

        best_wpm=best_wpm,

        average_wpm=average_wpm,

        average_accuracy=average_accuracy,

        total_characters=total_characters,

        total_time=total_time,

        latest_wpm=latest_wpm,

        level=current_user.level(),

        xp=current_user.xp,

        level_xp=current_user.level_xp(),

        xp_to_next=current_user.xp_to_next_level(),

        streak=current_user.streak,

        achievements=achievements,

        achievement_ids=achievement_ids

    )


# =========================================================
# LEADERBOARD
# =========================================================

@app.route("/leaderboard")
def leaderboard():

    leaderboard_data = (

        db.session.query(

            User.username,

            db.func.max(
                TypingResult.wpm
            ).label("best_wpm")

        )

        .join(
            TypingResult,
            TypingResult.user_id == User.id
        )

        .group_by(
            User.id
        )

        .order_by(
            db.desc("best_wpm"),
            User.username.asc()
        )

        .limit(100)

        .all()

    )

    return render_template(

        "leaderboard.html",

        leaderboard=leaderboard_data

    )


# =========================================================
# SAVE TYPING RESULT
# =========================================================

@app.route(
    "/api/save-result",
    methods=["POST"]
)
@login_required
def save_result():

    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict
    ):

        return jsonify({

            "success": False,

            "message":
                "Invalid request data."

        }), 400


    # =====================================================
    # READ VALUES
    # =====================================================

    try:

        wpm = int(
            data.get(
                "wpm",
                0
            )
        )

        accuracy = int(
            data.get(
                "accuracy",
                0
            )
        )

        errors = int(
            data.get(
                "errors",
                0
            )
        )

        characters = int(
            data.get(
                "characters",
                0
            )
        )

        duration = int(
            data.get(
                "duration",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "success": False,

            "message":
                "Invalid result values."

        }), 400


    # =====================================================
    # BASIC VALIDATION
    # =====================================================

    if not 0 <= wpm <= 300:

        return jsonify({

            "success": False,

            "message":
                "Invalid WPM value."

        }), 400


    if not 0 <= accuracy <= 100:

        return jsonify({

            "success": False,

            "message":
                "Invalid accuracy value."

        }), 400


    if errors < 0:

        return jsonify({

            "success": False,

            "message":
                "Invalid error count."

        }), 400


    if characters < 0:

        return jsonify({

            "success": False,

            "message":
                "Invalid character count."

        }), 400


    if duration < 1 or duration > 7200:

        return jsonify({

            "success": False,

            "message":
                "Invalid test duration."

        }), 400


    if errors > characters:

        return jsonify({

            "success": False,

            "message":
                "Invalid typing statistics."

        }), 400


    if accuracy == 100 and errors > 0:

        return jsonify({

            "success": False,

            "message":
                "Invalid accuracy statistics."

        }), 400


    # =====================================================
    # CHARACTER / ACCURACY CONSISTENCY
    # =====================================================

    if characters > 0:

        calculated_accuracy = round(
            (
                (characters - errors)
                / characters
            )
            * 100
        )

        if abs(
            calculated_accuracy - accuracy
        ) > 2:

            return jsonify({

                "success": False,

                "message":
                    "Typing statistics are inconsistent."

            }), 400


    # =====================================================
    # WPM CONSISTENCY
    # =====================================================

    if characters > 0 and duration > 0:

        correct_characters = (
            characters - errors
        )

        calculated_wpm = round(
            (
                correct_characters / 5
            )
            /
            (
                duration / 60
            )
        )

        # Small tolerance because the frontend
        # sends rounded elapsed seconds.

        if abs(
            calculated_wpm - wpm
        ) > 8:

            return jsonify({

                "success": False,

                "message":
                    "Typing speed data is inconsistent."

            }), 400


    # =====================================================
    # LANGUAGE
    # =====================================================

    language = str(
        data.get(
            "language",
            "english"
        )
    ).strip().lower()

    allowed_languages = {
        "english"
    }

    if language not in allowed_languages:

        language = "english"


    # =====================================================
    # CREATE RESULT
    # =====================================================

    result = TypingResult(

        user_id=current_user.id,

        wpm=wpm,

        accuracy=accuracy,

        errors=errors,

        characters=characters,

        duration=duration,

        language=language

    )


    try:

        db.session.add(
            result
        )

        db.session.flush()


        # -------------------------------------------------
        # XP
        # -------------------------------------------------

        earned_xp = calculate_xp(

            wpm,

            accuracy,

            duration

        )

        current_user.xp += (
            earned_xp
        )


        # -------------------------------------------------
        # STREAK
        # -------------------------------------------------

        today = date.today()


        if (
            current_user.last_test_date
            is None
        ):

            current_user.streak = 1


        elif (
            current_user.last_test_date
            == today
        ):

            pass


        elif (
            current_user.last_test_date
            == today - timedelta(days=1)
        ):

            current_user.streak += 1


        else:

            current_user.streak = 1


        current_user.last_test_date = today


        # -------------------------------------------------
        # ACHIEVEMENTS
        # -------------------------------------------------

        earned_achievements = (
            check_achievements(
                current_user,
                result
            )
        )


        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        db.session.commit()


    except Exception:

        db.session.rollback()

        app.logger.exception(
            "Failed to save typing result."
        )

        return jsonify({

            "success": False,

            "message":
                "Could not save typing result."

        }), 500


    # =====================================================
    # RESPONSE
    # =====================================================

    return jsonify({

        "success": True,

        "message":
            "Result saved successfully.",

        "xp_earned":
            earned_xp,

        "total_xp":
            current_user.xp,

        "level":
            current_user.level(),

        "streak":
            current_user.streak,

        "achievements": [

            {

                "name":
                    achievement.name,

                "description":
                    achievement.description,

                "icon":
                    achievement.icon

            }

            for achievement
            in earned_achievements

        ]

    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out."
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

with app.app_context():

    db.create_all()

    create_achievements()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get(
            "FLASK_DEBUG",
            "0"
        ) == "1"
    )