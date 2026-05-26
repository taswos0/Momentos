"""
LLM Service — GPT-4o calls for content summarization and magazine layout generation.
"""
from openai import AsyncOpenAI
from config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)

TOURISM_SYSTEM_PROMPT = """You are a world-class travel writer for National Geographic.
Transform the provided raw web content into beautifully structured magazine prose.
Write with passion, vivid imagery, and a sense of adventure.
Return the result as a JSON object with keys: "title", "subtitle", "sections" (array of 
{"heading": str, "body": str, "image_hint": str})."""

COURSE_SYSTEM_PROMPT = """You are a senior academic editor specializing in educational content.
Transform the provided raw content into a clear, well-structured educational chapter.
Use a calm, authoritative tone. Include key takeaways and a quiz at the end.
Return JSON with: "title", "learning_objectives" (list), "sections" 
(array of {"heading": str, "body": str, "key_point": str}), 
"quiz" (array of {"question": str, "answer": str})."""


async def synthesize_content(text_blocks: list[str], job_type: str) -> dict:
    """
    Sends raw scraped text to GPT-4o with a template-specific system prompt.
    Returns a structured JSON layout ready for the PDF engine.
    """
    combined_text = "\n\n".join(text_blocks[:20])  # cap at 20 blocks to manage token cost

    system_prompt = TOURISM_SYSTEM_PROMPT if job_type == "tourism" else COURSE_SYSTEM_PROMPT

    response = await _client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Raw content to synthesize:\n\n{combined_text}"},
        ],
        temperature=0.7,
        max_tokens=4096,
    )

    import json
    return json.loads(response.choices[0].message.content)
