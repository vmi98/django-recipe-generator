from google import genai


# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()


def get_unexpected_twist(title, ingredients):
    schema = {
        "type": "object",
        "properties": {
            "twist_ingredient": {"type": "string"},
            "reason": {"type": "string"},
            "how_to_use": {"type": "string"}
        },
        "required": ["twist_ingredient", "reason", "how_to_use"]
    }
    prompt = f"""
    You are an expert culinary advisor and creative chef.
    Your task is to provide a single, surprising,
    yet obtainable ingredient to elevate a given dish.
    Dish Information:
    - Title: {title}
    - Ingredients: {", ".join(ingredients)}
    Instructions:
    1. Analyze the Dish: Review the provided "Title" and "Ingredients."
    2. Suggest ONE Ingredient: Propose a single ingredient that is unexpected
    for this specific dish. Strive for originality and variety. Avoid suggesting
    the same ingredient for different recipes unless it is truly the best fit.
    3. Ensure Feasibility: The ingredient must be reasonably obtainable by a home cook
    (e.g.,available at a well-stocked grocery store,
    not a highly specialized or rare item).
    4. Provide Justification:Briefly explain why this ingredient would elevate the dish.
    Focus on the flavor, texture, or aromatic profile it adds.
    The explanation should be concise.
    5. Strictly JSON Output: Your response must be a valid JSON object
    matching the following schema. No extra text, no preamble, no markdown.
    6. In your JSON Output values for "how_to_use", "reason", "twist_ingredient" must
    be in a language of provided Title and Ingredients.

    JSON Schema: {schema}

    Negative Constraints:
    - Do not suggest more than one ingredient.
    - Do not include any text outside of the JSON object.
    - Do not generate an ingredient that is already in the provided ingredients list.
    - Do not suggest an ingredient if the dish title or ingredients are nonsensical
    or unrealistic. In such a case, respond with a JSON object that has
    `no suggestion` values for "how_to_use"  and "reason" and
    "The provided dish title or ingredients are not realistic." value
    for "twist_ingredient".

    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        }
    )
    return response.parsed
