from flask import Blueprint, request, jsonify
import mysql.connector
from app.config.config import Config


assessment_bp = Blueprint(
    "assessment",
    __name__,
    url_prefix="/api/assessment"
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
# CREATE ASSESSMENT + SAVE ANSWERS
# ==========================================
@assessment_bp.route("/<int:user_id>", methods=["POST"])
def create_assessment(user_id):
    data = request.get_json(silent=True) or {}

    answers = data.get("answers", [])

    if not answers:
        return jsonify({
            "message": "Assessment answers are required"
        }), 400

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

        # Create assessment
        cursor.execute(
            """
            INSERT INTO assessments (user_id, status)
            VALUES (%s, %s)
            """,
            (user_id, "completed")
        )

        assessment_id = cursor.lastrowid

        # Save each answer
        for answer in answers:
            question_id = answer.get("question_id")
            answer_value = answer.get("answer")

            if question_id is None or answer_value is None:
                connection.rollback()

                return jsonify({
                    "message": "Each answer must contain question_id and answer"
                }), 400

            cursor.execute(
                """
                INSERT INTO assessment_answers
                (
                    assessment_id,
                    question_id,
                    answer
                )
                VALUES (%s, %s, %s)
                """,
                (
                    assessment_id,
                    question_id,
                    str(answer_value)
                )
            )

        connection.commit()

        return jsonify({
            "message": "Assessment submitted successfully",
            "assessment_id": assessment_id,
            "user_id": user_id,
            "total_answers": len(answers)
        }), 201

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
# GET LATEST ASSESSMENT
# ==========================================
@assessment_bp.route("/<int:user_id>", methods=["GET"])
def get_assessment(user_id):

    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        # Get latest assessment
        cursor.execute(
            """
            SELECT
                id,
                user_id,
                assessment_date,
                status
            FROM assessments
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,)
        )

        assessment = cursor.fetchone()

        if not assessment:
            return jsonify({
                "message": "Assessment not found"
            }), 404

        assessment_id = assessment["id"]

        # Get answers
        cursor.execute(
            """
            SELECT
                id,
                question_id,
                answer
            FROM assessment_answers
            WHERE assessment_id = %s
            ORDER BY id ASC
            """,
            (assessment_id,)
        )

        answers = cursor.fetchall()

        assessment["answers"] = answers

        return jsonify({
            "message": "Assessment fetched successfully",
            "assessment": assessment
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