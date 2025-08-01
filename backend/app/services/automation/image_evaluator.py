"""
contains the logic for evaluating images against a prompt
It is used by the validation task to evaluate scraped images against the prompt

Algorithm and rationale:
1. Split the prompt into adjectives and nouns
- allows us to individually validate the style and object of the prompt
2. Create a prompt for the image evaluator
- this prompt is used to evaluate the image against the prompt
3. Send the prompt to the image evaluator
- the image evaluator returns a score and a description of the image
4. Return the score and the description
- the score is a float between 0 and 1
- the description is a string
"""

import spacy
from typing import Tuple
from app.util.config import get_settings
from json import loads as json_loads
from requests import post, RequestException

# Configuration constants
EVALUATION_CONFIG = {
    "object_weight": 0.5,
    "style_weight": 0.5,
    "timeout_seconds": 30,
    "max_retries": 3,
    "retry_delay": 1,
}


def split_prompt_by_nouns_and_adjectives(prompt: str) -> Tuple[str, str]:
    """
    Splits the prompt into adjectives and nouns
    """
    NLP = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    ADJ = {"ADJ"}
    NOUNS = {"NOUN", "PROPN"}
    prompt_lower = prompt.lower()
    doc = NLP(prompt_lower)

    adjectives = [tok.text for tok in doc if tok.pos_ in ADJ]
    nouns = [tok.text for tok in doc if tok.pos_ in NOUNS]

    style_phrase = " ".join(adjectives)
    object_phrase = " ".join(nouns)

    # Fallbacks ensure non‑empty strings
    if not style_phrase:
        style_phrase = prompt_lower
    if not object_phrase:
        object_phrase = prompt_lower

    return style_phrase, object_phrase


def create_image_evaluation_prompt(
    prompt: str, image_url: str, style_phrase: str, object_phrase: str
) -> dict:
    """
    Creates the prompt for the image evaluator
    """
    system_message = (
        "You are an image curator."
        "Respond ONLY with valid JSON of format:\n"
        '{"object":0.00, "style":0.00, "image_description":"...", "evaluation_explanation":"..."}'
    )

    user_message = (
        "Critically rate how well this image matches the prompt in the following way:"
        "Provide two floats between 0 and 1 for how well the image matches the style phrase and the object phrase respectively."
        "Provide a brief explanation for your score, 15 words max."
        "Provide a description of the image, 15 words max."
        f"Prompt: {prompt}\n"
        f"Image URL: {image_url}\n"
        f"Style phrase: {style_phrase}\n"
        f"Object phrase: {object_phrase}\n"
    )

    return {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        "temperature": 0,
    }


def score_image_against_prompt(image_url: str, prompt: str) -> tuple[float, dict]:
    """
    Scores the image against the prompt
    """
    # Input validation
    if not image_url or not prompt:
        raise ValueError("Both image_url and prompt must be provided and non-empty")

    if not isinstance(image_url, str) or not isinstance(prompt, str):
        raise TypeError("Both image_url and prompt must be strings")

    if not image_url.startswith(("http://", "https://")):
        raise ValueError("image_url must be a valid HTTP/HTTPS URL")

    settings = get_settings()
    style, object_ = split_prompt_by_nouns_and_adjectives(prompt)
    body = create_image_evaluation_prompt(prompt, image_url, style, object_)

    try:
        response = post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=EVALUATION_CONFIG["timeout_seconds"],
        )
        response.raise_for_status()
    except RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            if e.response.status_code == 429:
                raise RuntimeError("OpenAI API rate limit exceeded")
            elif e.response.status_code == 401:
                raise RuntimeError(
                    "OpenAI API authentication failed - check your API key"
                )
            elif e.response.status_code == 400:
                raise RuntimeError(
                    "OpenAI API bad request - check your prompt or image URL"
                )
            else:
                raise RuntimeError(
                    f"OpenAI API request failed (HTTP {e.response.status_code}): {e}"
                )
        else:
            raise RuntimeError(f"OpenAI API request failed (network error): {e}")

    try:
        raw_json = response.json()
        message_content = raw_json["choices"][0]["message"]["content"]
        resp = json_loads(message_content)

        # Validate response structure
        if "object" not in resp or "style" not in resp:
            raise RuntimeError(
                "OpenAI response missing required 'object' or 'style' fields"
            )

        obj_score = float(resp["object"])
        style_score = float(resp["style"])

        # Validate score ranges
        if not (0 <= obj_score <= 1):
            raise RuntimeError(f"Invalid object score: {obj_score} (must be 0-1)")
        if not (0 <= style_score <= 1):
            raise RuntimeError(f"Invalid style score: {style_score} (must be 0-1)")

    except (KeyError, json_loads, ValueError) as e:
        raise RuntimeError(f"Malformed OpenAI response: {e}")

    final = (
        EVALUATION_CONFIG["object_weight"] * obj_score
        + EVALUATION_CONFIG["style_weight"] * style_score
    )
    detail = {
        "object_score": obj_score,
        "style_score": style_score,
        "explanation": resp.get("evaluation_explanation", ""),
    }
    return final, detail
