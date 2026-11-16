# FastAPI Storycraft application

This application adapts the story portion of the Google ADK notebook into an async HTTP service and browser UI. It uses explicit Gemini calls for the writer, critic, and refiner roles; it does not execute the notebook or run ADK agents. The notebook and Streamlit companion remain available.

## Setup (Python 3.11+)

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r fastapi_app/requirements.txt
```

Copy `.env.example` to `.env` and set a valid `GOOGLE_API_KEY`. Set `GEMINI_MODEL` to an available text-generation model for your Google project. Never commit `.env`.

```bash
python -m uvicorn fastapi_app.main:app --env-file .env --reload
```

Open http://127.0.0.1:8000 for the browser app or http://127.0.0.1:8000/docs for interactive Swagger documentation.

## Endpoints

- `GET /`: story creation interface, editorial history, Markdown download.
- `GET /health`: process health and whether a server key is configured; does not verify key validity or quota.
- `POST /api/stories`: generate, critique, and refine a story.

Example JSON body:

```json
{
  "premise": "A lighthouse keeper discovers a mysterious glowing map.",
  "genre": "Mystery",
  "tone": "Suspenseful",
  "max_refinements": 2
}
```

Example from Python:

```python
import httpx
response = httpx.post(
    "http://127.0.0.1:8000/api/stories",
    json={"premise": "A robot learns to garden.", "max_refinements": 1},
    timeout=310,
)
response.raise_for_status()
print(response.json()["story"])
```

The response includes `draft`, `story`, `approved`, `refinements`, and `history` with the story and critique for every round. Only an exact `APPROVED` critique (ignoring surrounding whitespace) ends the loop early. The last revision receives a final critique, so approval refers to the returned story. Reaching the limit returns `approved: false`; approval is a model judgment, not a measured guarantee of quality.

Premises are limited to 3,000 characters; genre/tone to 80 characters; refinements to 0–3. The workflow uses 2–8 model calls, with a 300-second overall deadline. No automatic retries or persistent story storage are provided. Requests are independent; a failed request must restart. The browser retains results until refresh and lets users download them. Prompts and story text are sent to Google.

## Docker

```bash
docker build -t storycraft-api .
docker run --rm --env-file .env -p 8000:8000 storycraft-api
```

The image runs as a non-root user. Secrets are excluded from the build context. This is a local starter application without authentication or rate limiting; before exposing a shared server API key publicly, add access control and usage limits. A hosting proxy must allow requests lasting up to five minutes.

## Verification

```bash
python -m pip install httpx
python -m unittest discover -s tests -v
```

Eight automated tests cover workflow termination, final critique, validation, UI/health/docs routes, missing credentials, response shape, and error redaction using mocked generation. Live Gemini generation and Docker builds were not verified in the development environment. Dependency ranges are not a lockfile.
