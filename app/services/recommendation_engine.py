# app/services/recommendation_engine.py


CAREER_RULES = {
    "Software Developer": {
        "programming": 10,
        "software development": 10,
        "coding": 9,
        "problem solving": 8,
        "technology": 6,
        "web development": 7,
        "computer science": 6
    },

    "Web Developer": {
        "web development": 10,
        "programming": 9,
        "coding": 8,
        "software development": 8,
        "technology": 6,
        "problem solving": 5
    },

    "Data Scientist": {
        "data science": 10,
        "data analysis": 10,
        "statistics": 9,
        "python": 8,
        "artificial intelligence": 7,
        "problem solving": 6,
        "machine learning": 9
    },

    "AI/ML Engineer": {
        "artificial intelligence": 10,
        "machine learning": 10,
        "python": 8,
        "programming": 8,
        "problem solving": 8,
        "technology": 6,
        "data science": 7
    },

    "Cybersecurity Analyst": {
        "cybersecurity": 10,
        "security": 10,
        "networking": 8,
        "technology": 7,
        "problem solving": 7,
        "programming": 5
    }
}


def calculate_career_scores(answers):
    """
    Calculate weighted scores for each career
    based on assessment answers.
    """

    scores = {
        career: 0
        for career in CAREER_RULES
    }

    # Convert all answers into lowercase text
    answer_text = " ".join(
        str(answer).lower()
        for answer in answers
    )

    # Calculate weighted score
    for career, rules in CAREER_RULES.items():

        for keyword, weight in rules.items():

            if keyword in answer_text:
                scores[career] += weight

    # Sort careers by score
    ranked_careers = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return ranked_careers


def generate_explanation(career, score):
    """
    Generate a basic explanation for the recommendation.
    """

    return (
        f"{career} received a recommendation score of {score} "
        f"based on the student's assessment responses, "
        f"including relevant interests, skills and career preferences."
    )