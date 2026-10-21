LEVEL_VALUES = {
    "Not Added": 0,
    "Beginner": 1,
    "Intermediate": 2,
    "Advanced": 3
}


def get_required_level(importance):
    """
    Convert career skill importance into a required proficiency level.
    """

    importance = float(importance)

    if importance >= 0.90:
        return "Advanced"

    if importance >= 0.75:
        return "Intermediate"

    return "Beginner"


def calculate_gap_status(current_level, required_level):
    """
    Compare current skill level with required skill level.
    """

    current_value = LEVEL_VALUES.get(current_level, 0)
    required_value = LEVEL_VALUES.get(required_level, 1)

    if current_value >= required_value:
        return "Sufficient"

    return "Needs Improvement"


def generate_skill_gap_analysis(
    connection,
    user_id,
    career_id
):
    """
    Generate skill gap analysis for a user and career.
    """

    cursor = connection.cursor(dictionary=True)

    # ------------------------------------------
    # Get required career skills and user's skills
    # ------------------------------------------

    cursor.execute(
        """
        SELECT
            s.id AS skill_id,
            s.skill_name,
            s.category,
            cs.importance,
            us.proficiency_level AS current_level
        FROM career_skills cs

        JOIN skills s
            ON cs.skill_id = s.id

        LEFT JOIN user_skills us
            ON us.skill_id = cs.skill_id
            AND us.user_id = %s

        WHERE cs.career_id = %s

        ORDER BY cs.importance DESC, s.skill_name ASC
        """,
        (user_id, career_id)
    )

    skill_rows = cursor.fetchall()

    if not skill_rows:
        cursor.close()
        return []

    # ------------------------------------------
    # Remove previous analysis for same user
    # and career
    # ------------------------------------------

    cursor.execute(
        """
        DELETE FROM skill_gaps
        WHERE user_id = %s
        AND career_id = %s
        """,
        (user_id, career_id)
    )

    results = []

    # ------------------------------------------
    # Calculate each skill gap
    # ------------------------------------------

    for skill in skill_rows:

        current_level = (
            skill["current_level"]
            if skill["current_level"]
            else "Not Added"
        )

        required_level = get_required_level(
            skill["importance"]
        )

        gap_status = calculate_gap_status(
            current_level,
            required_level
        )

        cursor.execute(
            """
            INSERT INTO skill_gaps
            (
                user_id,
                career_id,
                skill_id,
                current_level,
                required_level,
                gap_status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                career_id,
                skill["skill_id"],
                current_level,
                required_level,
                gap_status
            )
        )

        results.append(
            {
                "skill_id": skill["skill_id"],
                "skill_name": skill["skill_name"],
                "category": skill["category"],
                "importance": float(skill["importance"]),
                "current_level": current_level,
                "required_level": required_level,
                "gap_status": gap_status
            }
        )

    cursor.close()

    return results