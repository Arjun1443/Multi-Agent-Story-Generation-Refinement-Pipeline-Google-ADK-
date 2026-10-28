import httpx
import streamlit as st
from google import genai
from google.genai import types
from ui import page, secret


class EmptyResponse(Exception):
    pass


def diagnose(exc):
    """Render fixed diagnoses, never raw provider messages or request URLs."""
    messages = {
        400: 'Google rejected the request (HTTP 400). Check API-key validity, project eligibility, and the selected model settings.',
        401: 'Authentication failed (HTTP 401). Check your Gemini API key in Streamlit Secrets or use the sidebar override.',
        402: 'Google requires available credits or billing configuration (HTTP 402). Check the API project in Google AI Studio.',
        403: 'Access denied (HTTP 403). Check API-key restrictions, project access, and model/region eligibility in Google AI Studio.',
        404: 'Model unavailable (HTTP 404). Select Check API access and copy an available generation model into the Gemini model field.',
        429: 'Quota or rate limit reached (HTTP 429). Check your Gemini API project usage and limits. Wait if temporary; repeated retries cannot fix exhausted quota.',
        500: 'Google returned an internal error (HTTP 500). Retry the unfinished stage later.',
        502: 'Google returned a gateway error (HTTP 502). Retry the unfinished stage later.',
        503: 'The Gemini service or model is temporarily unavailable (HTTP 503). Retry later or select another available model.',
        504: 'Google timed out upstream (HTTP 504). Retry the unfinished stage later.',
    }
    code = getattr(exc, 'code', None)
    if isinstance(code, int) and code in messages:
        return messages[code]
    if isinstance(exc, httpx.TimeoutException):
        return 'The API request timed out. Check connectivity and retry the unfinished stage later.'
    if isinstance(exc, httpx.RequestError):
        return 'The app could not reach the Gemini API. Check hosted network access and retry later.'
    if isinstance(exc, EmptyResponse):
        return str(exc)  # Fixed application messages only.
    return 'An unexpected application error occurred. Check dependency compatibility and the app logs. Do not share API keys or raw request URLs.'


def generate(client, model, prompt, budget):
    settings = {'max_output_tokens': budget}
    if model.removeprefix('models/').startswith('gemini-2.5-flash'):
        settings['thinking_config'] = types.ThinkingConfig(thinking_budget=0)
    result = client.models.generate_content(model=model, contents=prompt, config=types.GenerateContentConfig(**settings))
    candidates = result.candidates or []
    reason = str(candidates[0].finish_reason).split('.')[-1] if candidates else ''
    if reason == 'MAX_TOKENS':
        raise EmptyResponse('The model reached its output limit. Shorten the requested story or select another available model, then retry.')
    if reason in {'SAFETY', 'BLOCKLIST', 'PROHIBITED_CONTENT', 'RECITATION'}:
        raise EmptyResponse('The model stopped for a content restriction. Revise the story premise and try again.')
    if not result.text or not result.text.strip():
        raise EmptyResponse('The model returned no usable text. Try another available text-generation model or revise the premise.')
    return result.text


page('Storycraft Studio', 'Move from a story idea to a draft, editorial critique, and revised narrative.', 'MULTI-STAGE GENERATION')
with st.sidebar:
    configured = secret('GOOGLE_API_KEY').strip()
    # Never populate a browser input with the server's configured secret.
    override = st.text_input('Your Google API key (optional override)', type='password')
    key = override.strip() or configured
    if configured:
        st.caption('An API key is configured in Streamlit Secrets; its value is not displayed.')
    model = st.text_input('Gemini model', value=secret('GEMINI_MODEL', 'gemini-2.5-flash')).strip()
    st.caption('Each completed story uses three generation calls. The access check lists models without generating a story.')
    if st.button('Check API access'):
        if not key:
            st.warning('Configure GOOGLE_API_KEY in Streamlit Secrets or enter a key above.')
        else:
            try:
                with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=30000)) as client:
                    names = sorted({m.name.removeprefix('models/') for m in client.models.list() if m.name and 'generateContent' in (m.supported_actions or [])})
                st.session_state.available_models = names
                st.success('Authentication and model listing succeeded. Generation quota is not checked by this test.')
            except Exception as exc:
                st.error(diagnose(exc))
    if st.session_state.get('available_models'):
        with st.expander('Available generation models'):
            st.code('\n'.join(st.session_state.available_models))
            st.caption('Copy a model name into the Gemini model field. Listing does not guarantee remaining generation quota.')

with st.form('story'):
    prompt = st.text_area('Your story premise', value='A lighthouse keeper discovers a mysterious glowing map.', max_chars=3000)
    a, b = st.columns(2)
    genre = a.selectbox('Genre', ['Mystery', 'Science fiction', 'Fantasy', 'Literary fiction'])
    tone = b.selectbox('Tone', ['Reflective', 'Suspenseful', 'Playful', 'Hopeful'])
    go = st.form_submit_button('Generate / resume story', type='primary')
if go:
    if not key or not prompt.strip() or not model:
        st.warning('Enter an API key, a model name, and a story premise.')
    else:
        identity = (prompt, genre, tone, model)
        if st.session_state.get('story_identity') != identity:
            st.session_state.story_identity = identity
            st.session_state.story_progress = {}
        progress = st.session_state.story_progress
        stage, status = 'Draft', None
        try:
            with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=90000)) as client:
                with st.status('Running story workflow…', expanded=True) as status:
                    if 'draft' not in progress:
                        st.write('Writing the first draft…')
                        progress['draft'] = generate(client, model, f'Write a complete short {genre} story, 250–350 words. Tone: {tone}. Premise: {prompt}', 4096)
                    stage = 'Critique'
                    if 'critique' not in progress:
                        st.write('Reviewing coherence and the ending…')
                        progress['critique'] = generate(client, model, f'Act as an editor. Give actionable feedback in at most 200 words on coherence, character, specificity, and ending. Story:\n{progress["draft"]}', 2048)
                    stage = 'Revision'
                    if 'revision' not in progress:
                        st.write('Revising from editorial feedback…')
                        progress['revision'] = generate(client, model, f'Revise this story using the feedback. Return only the complete revised story, 250–350 words. Story:\n{progress["draft"]}\nFeedback:\n{progress["critique"]}', 4096)
                    status.update(label='Three-stage workflow complete', state='complete', expanded=False)
        except Exception as exc:
            if status is not None:
                status.update(label=f'{stage} stage did not complete', state='error', expanded=False)
            st.error(diagnose(exc))
            if progress:
                st.info('Completed stages are retained in this session. Submit the same settings to retry only the unfinished stage.')

progress = st.session_state.get('story_progress', {})
if progress.get('revision'):
    a, b, c = st.tabs(['Revised story', 'Editorial critique', 'Original draft'])
    a.markdown(progress['revision']); b.markdown(progress.get('critique', '')); c.markdown(progress['draft'])
    st.download_button('Download revised story', progress['revision'], 'revised-story.md', 'text/markdown')
elif progress:
    st.subheader('Completed stages — workflow unfinished')
    st.markdown(progress.get('draft', ''))
    if progress.get('critique'):
        with st.expander('Editorial critique'):
            st.markdown(progress['critique'])
with st.expander('Architecture and scope'):
    st.write('The notebook uses Google ADK orchestration. This cloud companion uses three explicit Gemini API calls for generation, critique, and refinement. It does not claim measured improvement in creative quality or execute an autonomous ADK loop.')
