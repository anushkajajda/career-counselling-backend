from flask import Flask
from flask_cors import CORS
import mysql.connector

from app.config.config import Config

from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.assessment import assessment_bp
from app.routes.recommendation import recommendation_bp
from app.routes.skill_gap import skill_gap_bp
from app.routes.roadmap import roadmap_bp


app = Flask(__name__)

CORS(app)


# =========================================================
# REGISTER API BLUEPRINTS
# =========================================================

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(recommendation_bp)
app.register_blueprint(skill_gap_bp)
app.register_blueprint(roadmap_bp)


# =========================================================
# DATABASE CONNECTION TEST
# =========================================================

def test_database_connection():

    try:

        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

        if connection.is_connected():
            print("MySQL connection successful!")

        connection.close()

    except mysql.connector.Error as error:

        print("MySQL connection failed!")
        print("Error:", error)


# =========================================================
# HOME ROUTE
# =========================================================

@app.route("/")
def home():

    return {
        "message": "Career Counselling Backend is running",
        "status": "success"
    }


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    test_database_connection()

    app.run(debug=True)