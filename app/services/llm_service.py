
import json

from google import genai
from google.genai import types

from app.config.config import Config


def generate_learning_roadmap(career_name, skill_gaps):
    api_key = Config.GEMINI_API_KEY

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured")

    gaps_to_improve = [
        gap for gap in skill_gaps
        if gap.get("gap_status") == "Needs Improvement"
    ]

    if not gaps_to_improve:
        return []

    client = genai.Client(api_key=api_key)

    gap_details = [
        {
            "skill_id": gap.get("skill_id"),
            "skill_name": gap.get("skill_name"),
            "current_level": gap.get("current_level"),
            "required_level": gap.get("required_level"),
        }
        for gap in gaps_to_improve
    ]

    prompt = f"""
You are an AI career counsellor creating a beginner-friendly
learning roadmap for a student pursuing {career_name}.

Use the following skill gaps:
{json.dumps(gap_details, ensure_ascii=False)}

Return a JSON object with this exact structure:
{{
  "roadmap": [
    {{
      "skill_id": 1,
      "title": "Short learning step title",
      "description": "Practical learning and practice instructions"
    }}
  ]
}}

Rules:
- Include one or more useful steps for each skill gap.
- Use the matching skill_id from the input.
- Keep titles under 200 characters.
- Make descriptions practical and beginner-friendly.
- Return valid JSON only.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response")

    result = json.loads(response.text)
    generated_items = result.get("roadmap", [])

    if not isinstance(generated_items, list):
        raise ValueError("Gemini returned an invalid roadmap format")

    valid_skill_ids = {
        gap.get("skill_id") for gap in gaps_to_improve
    }

    roadmap_items = []

    for item in generated_items:
        if not isinstance(item, dict):
            continue

        skill_id = item.get("skill_id")
        title = item.get("title")
        description = item.get("description")

        if skill_id not in valid_skill_ids:
            continue

        if not isinstance(title, str) or not title.strip():
            continue

        if not isinstance(description, str) or not description.strip():
            continue

        roadmap_items.append({
            "skill_id": skill_id,
            "title": title.strip()[:200],
            "description": description.strip(),
            "resource_type": "AI Learning Guidance",
            "resource_url": None,
            "sequence_order": len(roadmap_items) + 1,
        })

    if not roadmap_items:
        raise ValueError("Gemini did not return any valid roadmap steps")

    return roadmap_items
