import streamlit as st
from ui import page,secret

page('Storycraft Studio','Move from a story idea to a draft, editorial critique, and revised narrative.','MULTI-STAGE GENERATION')
with st.sidebar:
    key=st.text_input('Google API key',type='password',value=secret('GOOGLE_API_KEY'))
    model=st.text_input('Gemini model',value=secret('GEMINI_MODEL','gemini-2.5-flash'))
    st.caption('Your prompt is sent to Google only when you select Generate. Each run makes three model calls.')
with st.form('story'):
    prompt=st.text_area('Your story premise',value='A lighthouse keeper discovers a mysterious glowing map.',max_chars=3000)
    a,b=st.columns(2)
    genre=a.selectbox('Genre',['Mystery','Science fiction','Fantasy','Literary fiction'])
    tone=b.selectbox('Tone',['Reflective','Suspenseful','Playful','Hopeful'])
    go=st.form_submit_button('Generate → critique → refine',type='primary')
if go:
    if not key or not prompt.strip(): st.warning('Enter a Google API key and a story premise.')
    else:
        try:
            from google import genai
            from google.genai import types
            client=genai.Client(api_key=key,http_options=types.HttpOptions(timeout=60000))
            config=types.GenerateContentConfig(max_output_tokens=1600)
            with st.status('Writing the first draft…',expanded=True) as status:
                draft=client.models.generate_content(model=model,contents=f'Write a complete short {genre} story, 350–500 words. Tone: {tone}. Premise: {prompt}',config=config).text
                if not draft: raise ValueError('The model returned no draft.')
                st.write('Reviewing coherence, specificity, and the ending…')
                critique=client.models.generate_content(model=model,contents=f'Act as an editor. Give concise, actionable critique of this story. Focus on coherence, character, specificity, and ending. Story:\n{draft}',config=config).text
                st.write('Revising from editorial feedback…')
                revision=client.models.generate_content(model=model,contents=f'Revise the story using the editorial feedback. Return only the complete revised story. Story:\n{draft}\nFeedback:\n{critique}',config=config).text
                if not revision: raise ValueError('The model returned no revision.')
                st.session_state.story_result=(draft,critique or '',revision)
                status.update(label='Three-stage workflow complete',state='complete',expanded=False)
        except Exception:
            st.error('Generation failed. Check model availability, API-key permissions, quota, and network access. No result has been fabricated.')
if 'story_result' in st.session_state:
    draft,critique,revision=st.session_state.story_result
    a,b,c=st.tabs(['Revised story','Editorial critique','Original draft'])
    a.markdown(revision); b.markdown(critique); c.markdown(draft)
    st.download_button('Download revised story',revision,'revised-story.md','text/markdown')
with st.expander('Architecture and scope'):
    st.write('The notebook uses Google ADK orchestration. This cloud companion performs the same generator–critic–refiner stages through three explicit Gemini API calls. It does not claim measured improvement in creative quality or execute an autonomous ADK loop.')
