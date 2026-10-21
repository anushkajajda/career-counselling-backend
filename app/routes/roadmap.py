
import logging

from flask import Blueprint, jsonify, request
import mysql.connector

from app.config.config import Config
from app.services.llm_service import generate_learning_roadmap


roadmap_bp = Blueprint(
    "roadmap",
    __name__,
    url_prefix="/api/roadmap"
)

logger = logging.getLogger(__name__)


def get_database_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )


# =========================================================
# GENERATE LEARNING ROADMAP
# =========================================================

@roadmap_bp.route("/<int:user_id>", methods=["POST"])
def create_roadmap(user_id):
    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        # Check user
        cursor.execute(
            "SELECT id, name FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        # Get latest career recommendation
        cursor.execute(
            """
            SELECT
                cr.career_id,
                cr.recommendation_score,
                cp.career_name
            FROM career_recommendations cr
            JOIN career_paths cp ON cr.career_id = cp.id
            WHERE cr.user_id = %s
            ORDER BY cr.recommendation_score DESC, cr.id DESC
            LIMIT 1
            """,
            (user_id,)
        )
        recommendation = cursor.fetchone()

        if not recommendation:
            return jsonify({
                "message": (
                    "Please generate career recommendations "
                    "before creating a roadmap."
                )
            }), 404

        career_id = recommendation["career_id"]
        career_name = recommendation["career_name"]

        # Get skill gap analysis
        cursor.execute(
            """
            SELECT
                sg.id,
                sg.skill_id,
                s.skill_name,
                s.category,
                sg.current_level,
                sg.required_level,
                sg.gap_status
            FROM skill_gaps sg
            JOIN skills s ON sg.skill_id = s.id
            WHERE sg.user_id = %s AND sg.career_id = %s
            ORDER BY sg.id ASC
            """,
            (user_id, career_id)
        )
        skill_gaps = cursor.fetchall()

        if not skill_gaps:
            return jsonify({
                "message": (
                    "Please generate skill gap analysis "
                    "before creating a roadmap."
                )
            }), 404

        # Generate roadmap using Gemini
        try:
            roadmap_items = generate_learning_roadmap(
                career_name,
                skill_gaps
            )
        except Exception:
            logger.exception("Learning roadmap generation failed")
            return jsonify({
                "message": (
                    "Could not generate the learning roadmap. "
                    "Please try again later."
                )
            }), 502

        if not roadmap_items:
            return jsonify({
                "message": (
                    "No skill gaps were found. "
                    "A learning roadmap is not required."
                )
            }), 200

        # Create roadmap
        roadmap_title = (
            f"Personalized {career_name} Learning Roadmap"
        )
        roadmap_description = (
            "This personalized learning roadmap is designed "
            f"to help {user['name']} improve the skills required "
            f"for a career as a {career_name}."
        )

        cursor.execute(
            """
            INSERT INTO learning_roadmaps
                (user_id, career_id, title, description)
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                career_id,
                roadmap_title,
                roadmap_description
            )
        )
        roadmap_id = cursor.lastrowid

        # Save roadmap items
        saved_items = []

        for item in roadmap_items:
            cursor.execute(
                """
                INSERT INTO roadmap_items
                    (
                        roadmap_id,
                        skill_id,
                        title,
                        description,
                        resource_type,
                        resource_url,
                        sequence_order,
                        status
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    roadmap_id,
                    item["skill_id"],
                    item["title"],
                    item["description"],
                    item["resource_type"],
                    item["resource_url"],
                    item["sequence_order"],
                    "Not Started"
                )
            )

            saved_items.append({
                "skill_id": item["skill_id"],
                "title": item["title"],
                "description": item["description"],
                "resource_type": item["resource_type"],
                "resource_url": item["resource_url"],
                "sequence_order": item["sequence_order"],
                "status": "Not Started"
            })

        connection.commit()

        return jsonify({
            "message": "Learning roadmap generated successfully",
            "roadmap": {
                "roadmap_id": roadmap_id,
                "user_id": user_id,
                "career_id": career_id,
                "career_name": career_name,
                "title": roadmap_title,
                "description": roadmap_description
            },
            "total_items": len(saved_items),
            "items": saved_items
        }), 201

    except Exception:
        if connection:
            connection.rollback()

        logger.exception("Learning roadmap creation failed")

        return jsonify({
            "message": "Could not create the learning roadmap."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET LATEST ROADMAP
# =========================================================

@roadmap_bp.route("/<int:user_id>", methods=["GET"])
def get_roadmap(user_id):
    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        # Get latest roadmap
        cursor.execute(
            """
            SELECT
                lr.id,
                lr.user_id,
                lr.career_id,
                cp.career_name,
                lr.title,
                lr.description,
                lr.created_at
            FROM learning_roadmaps lr
            LEFT JOIN career_paths cp ON lr.career_id = cp.id
            WHERE lr.user_id = %s
            ORDER BY lr.id DESC
            LIMIT 1
            """,
            (user_id,)
        )
        roadmap = cursor.fetchone()

        if not roadmap:
            return jsonify({
                "message": "Learning roadmap not found"
            }), 404

        roadmap_id = roadmap["id"]

        # Get roadmap items
        cursor.execute(
            """
            SELECT
                ri.id,
                ri.skill_id,
                s.skill_name,
                s.category,
                ri.title,
                ri.description,
                ri.resource_type,
                ri.resource_url,
                ri.sequence_order,
                ri.status
            FROM roadmap_items ri
            LEFT JOIN skills s ON ri.skill_id = s.id
            WHERE ri.roadmap_id = %s
            ORDER BY ri.sequence_order ASC
            """,
            (roadmap_id,)
        )
        roadmap["items"] = cursor.fetchall()

        return jsonify({
            "message": "Learning roadmap fetched successfully",
            "roadmap": roadmap
        }), 200

    except mysql.connector.Error:
        logger.exception("Failed to fetch learning roadmap")
        return jsonify({"message": "Database error"}), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# UPDATE ROADMAP ITEM STATUS
# =========================================================

@roadmap_bp.route("/item/<int:item_id>", methods=["PUT"])
def update_roadmap_item(item_id):
    connection = None
    cursor = None

    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        # Validate status
        data = request.get_json(silent=True) or {}
        status = data.get("status")

        valid_statuses = [
            "Not Started",
            "In Progress",
            "Completed"
        ]

        if status not in valid_statuses:
            return jsonify({
                "message": (
                    "Invalid status. Use "
                    "Not Started, In Progress or Completed."
                )
            }), 400

        # Update item status
        cursor.execute(
            """
            UPDATE roadmap_items
            SET status = %s
            WHERE id = %s
            """,
            (status, item_id)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "message": "Roadmap item not found"
            }), 404

        connection.commit()

        return jsonify({
            "message": "Roadmap item updated successfully",
            "item_id": item_id,
            "status": status
        }), 200

    except mysql.connector.Error:
        if connection:
            connection.rollback()

        logger.exception("Failed to update roadmap item")

        return jsonify({"message": "Database error"}), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
