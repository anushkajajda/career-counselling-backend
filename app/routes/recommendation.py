from flask import Blueprint, jsonify
import mysql.connector

from app.config.config import Config
from app.services.recommendation_engine import (
    calculate_career_scores,
    generate_explanation
)


recommendation_bp = Blueprint(
    "recommendation",
    __name__,
    url_prefix="/api/recommendation"
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
# GENERATE CAREER RECOMMENDATIONS
# ==========================================
@recommendation_bp.route("/<int:user_id>", methods=["POST"])
def generate_recommendations(user_id):

    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        # Check user
        cursor.execute(
            """
            SELECT id, name
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "message": "User not found"
            }), 404

        # Get latest assessment
        cursor.execute(
            """
            SELECT id
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
                "message": "Please complete an assessment first"
            }), 404

        assessment_id = assessment["id"]

        # Get assessment answers
        cursor.execute(
            """
            SELECT question_id, answer
            FROM assessment_answers
            WHERE assessment_id = %s
            ORDER BY id ASC
            """,
            (assessment_id,)
        )

        answer_rows = cursor.fetchall()

        if not answer_rows:
            return jsonify({
                "message": "No assessment answers found"
            }), 404

        answers = [
            row["answer"]
            for row in answer_rows
        ]

        # Calculate career scores
        ranked_careers = calculate_career_scores(answers)

        # Keep top 3 recommendations
        top_recommendations = ranked_careers[:3]

        saved_recommendations = []

        for career_name, score in top_recommendations:

            # Find career in database
            cursor.execute(
                """
                SELECT id, career_name, description
                FROM career_paths
                WHERE career_name = %s
                """,
                (career_name,)
            )

            career = cursor.fetchone()

            # If career is not seeded in DB, skip it
            if not career:
                continue

            explanation = generate_explanation(
                career_name,
                score
            )

            # Save recommendation
            cursor.execute(
                """
                INSERT INTO career_recommendations
                (
                    user_id,
                    assessment_id,
                    career_id,
                    recommendation_score,
                    explanation
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    assessment_id,
                    career["id"],
                    score,
                    explanation
                )
            )

            saved_recommendations.append({
                "career_id": career["id"],
                "career_name": career["career_name"],
                "score": score,
                "description": career["description"],
                "explanation": explanation
            })

        connection.commit()

        return jsonify({
            "message": "Career recommendations generated successfully",
            "user_id": user_id,
            "assessment_id": assessment_id,
            "recommendations": saved_recommendations
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
# GET SAVED RECOMMENDATIONS
# ==========================================
@recommendation_bp.route("/<int:user_id>", methods=["GET"])
def get_recommendations(user_id):

    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                cr.id,
                cr.assessment_id,
                cr.recommendation_score,
                cr.explanation,
                cr.created_at,
                cp.career_name,
                cp.description
            FROM career_recommendations cr
            JOIN career_paths cp
                ON cr.career_id = cp.id
            WHERE cr.user_id = %s
            ORDER BY cr.recommendation_score DESC, cr.id DESC
            """,
            (user_id,)
        )

        recommendations = cursor.fetchall()

        return jsonify({
            "message": "Recommendations fetched successfully",
            "recommendations": recommendations
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