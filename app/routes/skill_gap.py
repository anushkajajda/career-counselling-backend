from flask import Blueprint, request, jsonify
import mysql.connector

from app.config.config import Config
from app.services.skill_gap import generate_skill_gap_analysis


skill_gap_bp = Blueprint(
    "skill_gap",
    __name__,
    url_prefix="/api/skill-gap"
)


def get_database_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


# =========================================================
# SAVE / UPDATE USER SKILLS
# =========================================================

@skill_gap_bp.route("/<int:user_id>/skills", methods=["POST"])
def save_user_skills(user_id):

    data = request.get_json(silent=True) or {}

    skills = data.get("skills", [])

    if not skills:
        return jsonify({
            "message": "Skills are required"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        # Check user

        cursor.execute(
            "SELECT id FROM users WHERE id = %s",
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "message": "User not found"
            }), 404

        saved_skills = []

        for skill in skills:

            skill_name = skill.get(
                "skill_name",
                ""
            ).strip()

            proficiency_level = skill.get(
                "proficiency_level",
                "Beginner"
            )

            valid_levels = [
                "Beginner",
                "Intermediate",
                "Advanced"
            ]

            if not skill_name:
                return jsonify({
                    "message": "skill_name is required"
                }), 400

            if proficiency_level not in valid_levels:
                return jsonify({
                    "message": (
                        "Invalid proficiency level. "
                        "Use Beginner, Intermediate or Advanced."
                    )
                }), 400

            cursor.execute(
                """
                SELECT id
                FROM skills
                WHERE skill_name = %s
                """,
                (skill_name,)
            )

            skill_row = cursor.fetchone()

            if not skill_row:
                return jsonify({
                    "message": f"Skill not found: {skill_name}"
                }), 404

            skill_id = skill_row["id"]

            cursor.execute(
                """
                INSERT INTO user_skills
                (
                    user_id,
                    skill_id,
                    proficiency_level
                )
                VALUES (%s, %s, %s)

                ON DUPLICATE KEY UPDATE
                    proficiency_level = VALUES(proficiency_level)
                """,
                (
                    user_id,
                    skill_id,
                    proficiency_level
                )
            )

            saved_skills.append({
                "skill_id": skill_id,
                "skill_name": skill_name,
                "proficiency_level": proficiency_level
            })

        connection.commit()

        return jsonify({
            "message": "User skills saved successfully",
            "user_id": user_id,
            "skills": saved_skills
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


# =========================================================
# GENERATE SKILL GAP ANALYSIS
# =========================================================

@skill_gap_bp.route("/<int:user_id>", methods=["POST"])
def generate_skill_gap(user_id):

    connection = None
    cursor = None

    try:

        connection = get_database_connection()

        cursor = connection.cursor(dictionary=True)

        # ------------------------------------------
        # Check user
        # ------------------------------------------

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

        # ------------------------------------------
        # Get latest career recommendation
        # ------------------------------------------

        cursor.execute(
            """
            SELECT
                cr.id,
                cr.career_id,
                cr.recommendation_score,
                cp.career_name
            FROM career_recommendations cr

            JOIN career_paths cp
                ON cr.career_id = cp.id

            WHERE cr.user_id = %s

            ORDER BY
                cr.recommendation_score DESC,
                cr.id DESC

            LIMIT 1
            """,
            (user_id,)
        )

        recommendation = cursor.fetchone()

        if not recommendation:
            return jsonify({
                "message": (
                    "Please generate career recommendations "
                    "before running skill gap analysis."
                )
            }), 404

        career_id = recommendation["career_id"]

        # ------------------------------------------
        # Generate skill gap analysis
        # ------------------------------------------

        results = generate_skill_gap_analysis(
            connection,
            user_id,
            career_id
        )

        if not results:
            return jsonify({
                "message": (
                    "No required skills found for "
                    "the recommended career."
                )
            }), 404

        connection.commit()

        # ------------------------------------------
        # Summary
        # ------------------------------------------

        total_skills = len(results)

        sufficient_skills = sum(
            1
            for skill in results
            if skill["gap_status"] == "Sufficient"
        )

        skills_needing_improvement = sum(
            1
            for skill in results
            if skill["gap_status"] == "Needs Improvement"
        )

        return jsonify({
            "message": "Skill gap analysis generated successfully",

            "user_id": user_id,

            "career": {
                "career_id": recommendation["career_id"],
                "career_name": recommendation["career_name"],
                "recommendation_score": float(
                    recommendation["recommendation_score"]
                )
            },

            "summary": {
                "total_required_skills": total_skills,
                "sufficient_skills": sufficient_skills,
                "skills_needing_improvement":
                    skills_needing_improvement
            },

            "skill_gaps": results
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


# =========================================================
# GET LATEST SKILL GAP ANALYSIS
# =========================================================

@skill_gap_bp.route("/<int:user_id>", methods=["GET"])
def get_skill_gap(user_id):

    connection = None
    cursor = None

    try:

        connection = get_database_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                sg.id,
                sg.user_id,
                sg.career_id,
                cp.career_name,
                sg.skill_id,
                s.skill_name,
                s.category,
                sg.current_level,
                sg.required_level,
                sg.gap_status,
                sg.created_at

            FROM skill_gaps sg

            JOIN skills s
                ON sg.skill_id = s.id

            JOIN career_paths cp
                ON sg.career_id = cp.id

            WHERE sg.user_id = %s

            AND sg.created_at = (
                SELECT MAX(sg2.created_at)
                FROM skill_gaps sg2
                WHERE sg2.user_id = sg.user_id
                AND sg2.career_id = sg.career_id
            )

            ORDER BY
                sg.gap_status DESC,
                s.skill_name ASC
            """,
            (user_id,)
        )

        results = cursor.fetchall()

        if not results:
            return jsonify({
                "message": "Skill gap analysis not found"
            }), 404

        return jsonify({
            "message": "Skill gap analysis fetched successfully",
            "user_id": user_id,
            "skill_gaps": results
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