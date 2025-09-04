from google import genai


# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()


def get_unexpected_twist(title, ingredients):
    prompt = f"""
    You are a creative chef.
    Suggest ONE surprising ingredient to elevate this dish and briefly explain why.

    Title: {title}
    Ingredients: {", ".join(ingredients)}
    """
    schema = {
        "type": "object",
        "properties": {
            "twist_ingredient": {"type": "string"},
            "reason": {"type": "string"},
            "how_to_use": {"type": "string"}
        },
        "required": ["twist_ingredient", "reason", "how_to_use"]
    }
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        response_json_schema=schema
    )

    return response.output_parsed
