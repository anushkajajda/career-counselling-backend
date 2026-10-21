from flask import Blueprint, request, jsonify
import mysql.connector
from app.config.config import Config


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/api/profile"
)


def get_database_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


# ==========================================
# CREATE / UPDATE STUDENT PROFILE
# ==========================================
@profile_bp.route("/<int:user_id>", methods=["POST"])
def save_profile(user_id):
    data = request.get_json(silent=True) or {}

    education_level = data.get("education_level")
    course = data.get("course")
    specialization = data.get("specialization")
    institution = data.get("institution")
    graduation_year = data.get("graduation_year")
    career_goal = data.get("career_goal")
    interests = data.get("interests")

    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        # Check whether user exists
        cursor.execute(
            "SELECT id FROM users WHERE id = %s",
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "message": "User not found"
            }), 404

        # Check whether profile already exists
        cursor.execute(
            """
            SELECT id
            FROM student_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        )

        existing_profile = cursor.fetchone()

        if existing_profile:
            # Update existing profile
            cursor.execute(
                """
                UPDATE student_profiles
                SET
                    education_level = %s,
                    course = %s,
                    specialization = %s,
                    institution = %s,
                    graduation_year = %s,
                    career_goal = %s,
                    interests = %s
                WHERE user_id = %s
                """,
                (
                    education_level,
                    course,
                    specialization,
                    institution,
                    graduation_year,
                    career_goal,
                    interests,
                    user_id
                )
            )

            message = "Profile updated successfully"

        else:
            # Create new profile
            cursor.execute(
                """
                INSERT INTO student_profiles
                (
                    user_id,
                    education_level,
                    course,
                    specialization,
                    institution,
                    graduation_year,
                    career_goal,
                    interests
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    education_level,
                    course,
                    specialization,
                    institution,
                    graduation_year,
                    career_goal,
                    interests
                )
            )

            message = "Profile created successfully"

        connection.commit()

        return jsonify({
            "message": message,
            "user_id": user_id
        }), 200

    except mysql.connector.Error:
        if connection:
            connection.rollback()

        return jsonify({
            "message": "Database error"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ==========================================
# GET STUDENT PROFILE
# ==========================================
@profile_bp.route("/<int:user_id>", methods=["GET"])
def get_profile(user_id):

    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                education_level,
                course,
                specialization,
                institution,
                graduation_year,
                career_goal,
                interests,
                created_at,
                updated_at
            FROM student_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        )

        profile = cursor.fetchone()

        if not profile:
            return jsonify({
                "message": "Profile not found"
            }), 404

        return jsonify({
            "message": "Profile fetched successfully",
            "profile": profile
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "message": "Database error"
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()