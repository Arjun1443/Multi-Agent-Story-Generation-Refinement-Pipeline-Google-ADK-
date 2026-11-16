import asyncio
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .workflow import run_story

app = FastAPI(title='Storycraft API', version='1.0.0', description='Writer, critic, and bounded story refinement workflow.')
static = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=static), name='static')
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class StoryRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    premise: Text
    genre: Label = 'Mystery'
    tone: Label = 'Suspenseful'
    max_refinements: int = Field(default=2, ge=0, le=3, strict=True)


class Round(BaseModel):
    round: int
    story: str
    critique: str


class StoryResponse(BaseModel):
    draft: str
    story: str
    approved: bool
    refinements: int
    history: list[Round]


class UnusableOutput(Exception):
    pass


async def generate_story(request: StoryRequest):
    key = os.getenv('GOOGLE_API_KEY', '').strip()
    if not key:
        raise HTTPException(503, 'Configure GOOGLE_API_KEY on the server before generating stories.')
    # Lazy import keeps health and request validation independent of credentials.
    from google import genai
    from google.genai import types
    model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash').strip()
    async with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60000)).aio as client:
        async def generate(prompt, budget):
            settings = {'max_output_tokens': budget}
            if model.removeprefix('models/').startswith('gemini-2.5-flash'):
                settings['thinking_config'] = types.ThinkingConfig(thinking_budget=0)
            result = await client.models.generate_content(
                model=model, contents=prompt, config=types.GenerateContentConfig(**settings))
            candidates = result.candidates or []
            reason = str(candidates[0].finish_reason).split('.')[-1] if candidates else ''
            if reason in {'MAX_TOKENS', 'SAFETY', 'BLOCKLIST', 'PROHIBITED_CONTENT', 'RECITATION'}:
                raise UnusableOutput()
            if not result.text or not result.text.strip():
                raise UnusableOutput()
            return result.text.strip()
        return await run_story(request.premise, request.genre, request.tone, request.max_refinements, generate)


@app.get('/', include_in_schema=False)
async def home():
    return FileResponse(static / 'index.html')


@app.get('/health')
async def health():
    return {'status': 'ok', 'configured': bool(os.getenv('GOOGLE_API_KEY', '').strip())}


@app.post('/api/stories', response_model=StoryResponse)
async def stories(request: StoryRequest):
    try:
        async with asyncio.timeout(300):
            return await generate_story(request)
    except HTTPException:
        raise
    except TimeoutError:
        raise HTTPException(504, 'Story generation timed out. Try fewer refinements.') from None
    except UnusableOutput:
        raise HTTPException(502, 'The model returned blocked, incomplete, or empty output. Revise the premise and retry.') from None
    except Exception as exc:
        code = getattr(exc, 'code', None)
        if code == 429:
            raise HTTPException(429, 'Gemini quota or rate limit reached. Check your API project usage.') from None
        if code in {400, 401, 403, 404}:
            raise HTTPException(502, 'Gemini rejected the request. Check server API key, model, and project access.') from None
        raise HTTPException(502, 'The generation service is unavailable. Try again later.') from None
