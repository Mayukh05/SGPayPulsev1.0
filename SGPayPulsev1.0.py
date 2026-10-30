"""SGPayPulse v1.1 competition edition. Run: streamlit run SGPayPulsev1.0.py"""
from __future__ import annotations
import base64
import io
import json
import os
from pathlib import Path
import hmac
import pandas as pd
import plotly.express as px
import streamlit as st
from remuneration import load_framework, salary_answer
from profile_search import profile_answer
from rag.engine import DocumentStore, seed_documents
from ai.providers import configured_models, generate
from ai.assistant import rag_answer, llm_answer


BASE=Path(__file__).resolve().parent
st.set_page_config(page_title='SGPayPulse | Singapore AI-Powered Chatbat',page_icon=str(BASE/'assets'/'logo.png'),layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
:root{--sg-red:#b71c2b;--sg-navy:#132b43}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1400px}
[data-testid="stSidebar"]{background:#132b43}
[data-testid="stSidebar"] *{color:#f2f6fa!important}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.3rem .2rem}
div[data-testid="stMetric"]{background:#f6f8fa;border:1px solid #e3e9ee;padding:16px;border-radius:14px}
.sg-brand{background:#b71c2b;color:white;padding:15px 22px;border-radius:14px;display:flex;align-items:center;gap:14px;margin-bottom:16px}
.sg-brand-logo{width:150px;height:150px;min-width:150px;min-height:150px;border-radius:50%;object-fit:cover;object-position:center;clip-path:circle(50% at 50% 50%);background:#fff;display:block;flex-shrink:0}
.sg-brand strong{font-size:50px}.sg-brand small{display:block;font-size:18px;opacity:.92}
.sg-banner{background:linear-gradient(110deg,#102b45,#1a5267);border-radius:18px;overflow:hidden;margin:12px 0 20px}
.sg-banner-text{padding:18px 24px 24px;color:#fff}.sg-banner-text h2{color:#fff;font-size:30px;margin:0 0 8px}
.sg-banner-text p{color:#e7f0f4;margin:0}
.sg-note{border-left:4px solid #b71c2b;background:#fff7f7;padding:12px 16px;border-radius:8px;margin:10px 0}
.sg-feature{border:1px solid #e1e6ec;border-radius:13px;padding:16px;min-height:118px;background:#fff}
[data-testid='stAppViewContainer']{background:#f5f8fc}
[data-testid='stHeader']{background:transparent}
[data-testid='stSidebar']{background:linear-gradient(180deg,#0c233b,#1b3854)}
[data-testid='stSidebar'] [data-testid='stRadio'] label{border-radius:9px;padding:10px 10px;transition:background .2s;font-size:12px!important}[data-testid='stSidebar'] [data-testid='stRadio'] label{border-radius:9px;padding:8px 10px;transition:background .2s}
[data-testid='stSidebar'] [data-testid='stRadio'] label:hover{background:#284760}
[data-testid='stVerticalBlockBorderWrapper']>div{border-radius:14px!important}
.stButton>button[kind='primary']{background:#b71c2b;border-color:#b71c2b}
.stButton>button:hover{border-color:#b71c2b;color:#b71c2b}
.sg-brand{border-radius:0 0 14px 14px;box-shadow:0 3px 14px #12263d19}
.sg-banner{box-shadow:0 8px 24px #12263d19}

 /* Minister Directory: prominent search heading and input */
.sg-search-heading{display:flex;align-items:center;gap:14px;padding:18px 20px;background:#fff4f5;border-left:5px solid #b71c2b;border-radius:12px 12px 0 0;margin-top:20px}
.sg-search-icon{font-size:28px}
.sg-search-title{font-size:23px;font-weight:800;color:#132b43}
.sg-search-subtitle{font-size:14px;color:#526477;margin-top:4px}
.st-key-minister_directory_search input{background:#fff!important;border:2px solid #b71c2b!important;border-radius:10px!important;padding:14px 16px!important;font-size:17px!important;font-weight:600!important;color:#132b43!important}
.st-key-minister_directory_search input:focus{border-color:#8e1420!important;box-shadow:0 0 0 3px rgba(183,28,43,.12)!important}
.st-key-minister_directory_search input::placeholder{color:#697b8d!important;font-weight:400!important}
                                                         
</style>''',unsafe_allow_html=True)

def secret(name,default=''):
    try:return st.secrets.get(name,os.environ.get(name,default))
    except Exception:return os.environ.get(name,default)

@st.cache_data(show_spinner=False)
def profiles():return json.loads((BASE/'data'/'mp_ministers_data.json').read_text(encoding='utf-8'))

@st.cache_resource(show_spinner=False)
def vector_store():
    store=DocumentStore(BASE/'rag_store')
    if store.collection.count()==0:
        seed_documents(store,BASE/'sample_documents')
    store.sync_project_data(BASE)
    return store

def logo_b64():return base64.b64encode((BASE/'assets'/'logo.svg').read_bytes()).decode()

def render_brand():
    st.markdown(f'<div class="sg-brand"><img src="data:image/svg+xml;base64,{logo_b64()}" class="sg-brand-logo" alt="SGPayPulse logo"/><div><strong>SGPayPulse</strong><small>Singapore Leadership &amp; Remuneration Intelligence · AI-Powered Bot </small></div></div>',unsafe_allow_html=True)

def skyline():
    """Home-page banner; set SG_BANNER_ANIMATED=False for a static PNG."""
    animated = True
    filename = 'sgpaypulse_banner_animated.gif' if animated else 'sgpaypulse_banner.png'
    image_path = BASE / 'assets' / filename
    if not image_path.exists():
        image_path = BASE / 'assets' / 'sgpaypulse_banner.png'
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.warning('SGPayPulse banner image is missing from assets/.')
    st.markdown(
        '<div class="sg-banner-text" style="background:#132b43;border-radius:0 0 14px 14px;">'
        '<h2>Explore Singapore’s Public Leadership</h2>'
        '<p>Ask questions, compare ministerial histories, and understand published remuneration frameworks.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

NAV=['🏠 Home','🤖 AI Assistant','⚖️ Minister Comparator','💰 2026 Pay Explorer','🏛️ Minister Directory','📁 Document Manager','🔬 Methodology','ℹ️ About Us']
with st.sidebar:
    st.markdown("""      
        <div style="font-size:35px;font-weight:800;color:#FFFFFF;line-height:1.3;">
            🇸🇬 SGPayPulse
        </div>
        <div style="font-size:15px;font-weight:600;color:#DCE8F2;margin-top:6px;">
            AI-Powered ChatBot v1.0
        </div>
    </div>
    """, unsafe_allow_html=True)
    page=st.radio('Navigate',NAV,label_visibility='collapsed')
    st.divider()
    st.caption('Public users can query indexed documents. Admin access is required to upload or remove documents.')
    st.caption('2026 remuneration values are published references, not verified individual take-home pay.')
    with st.expander('System readiness'):
        import importlib.util

        for pkg in ['chromadb','pypdf','docx','openai']:
            st.write(('✅ ' if importlib.util.find_spec(pkg) else '⚠️ ') + pkg)
        st.caption('If ChromaDB is missing, install dependencies using Python: python -m pip install -r requirements.txt')

render_brand()
people=profiles(); fw=load_framework(); rates=fw['rates']; byid={r['id']:r for r in rates}

def fmt(x):return 'Not published' if x is None else f'S${x:,.0f}'

def sources_block():
    with st.expander('Official remuneration sources'):
        for s in fw.get('sources',[]):st.markdown(f"- [{s['title']}]({s['url']})")

def person_card(name):
    p=people[name]
    with st.container(border=True):
        st.subheader(p['name'])
        st.markdown(f"**Current appointment:** {p.get('current_appointment','Not verified')}")
        st.markdown(f"**Constituency:** {p.get('constituency','Not verified')}")
        st.caption('Individual actual remuneration: Not publicly verified')
        if p.get('historical_portfolios'):
            with st.expander('Documented appointment history'):
                for h in p['historical_portfolios']:
                    st.markdown(f"- **{h.get('term','Date unverified')}** · {h.get('portfolio','')}"+(f" · [Source]({h['source_url']})" if h.get('source_url') else ''))
        if p.get('profile_source_url'):st.markdown(f"[Official biography]({p['profile_source_url']})")

if page==NAV[0]:
    skyline()
    cols=st.columns(4)
    labels=[('🤖 AI Assistant','Ask questions with citations'),('⚖️ Minister Comparator','Compare appointments and history'),('💰 2026 Pay Explorer','Explore reference pay'),('🏛️ Minister Directory','Search the Cabinet roster')]
    for col,(name,desc) in zip(cols,labels):
        with col:
            with st.container(border=True):st.markdown(f'**{name}**');st.caption(desc)
    st.subheader('2026 remuneration snapshot')
    a,b,c=st.columns(3)
    a.metric('PM annual reference',fmt(byid['pm']['current']))
    b.metric('MR4 annual reference',fmt(byid['mr4']['current']))
    c.metric('MP monthly allowance',fmt(byid['mp']['current']))
    st.caption('Effective 15 October 2026. Framework values are not verified individual salaries.')
    st.subheader('Latest updates')
    u1,u2,u3=st.columns(3)
    with u1:
        with st.container(border=True):st.markdown('**2026 remuneration review**');st.caption('Published reference updates · 15 Oct 2026')
    with u2:
        with st.container(border=True):st.markdown('**Expanded Cabinet dataset**');st.caption(f'{len(people)} officeholder profiles in JSON')
    with u3:
        with st.container(border=True):st.markdown('**Document-grounded AI**');st.caption('RAG requires installed ChromaDB and indexed documents')
    st.subheader('Dataset overview')
    x,y,z=st.columns(3)
    x.metric('Cabinet-listed officeholders',len(people))
    y.metric('Published remuneration rate categories',len(rates))
    # z.metric('Document RAG','ChromaDB')
    sources_block()

elif page==NAV[1]:
    st.title('🤖 SGPayPulse AI Assistant')
    st.caption('Ask about Singapore leadership and remuneration. Choose RAG, Structured Facts or LLM.')
    mode=st.radio('Answer mode',['RAG','Structured Facts','LLM'],horizontal=True,index=0,
                  help='RAG generates source-grounded answers. Structured Facts searches curated JSON. LLM is general AI conversation without document retrieval.')
    settings={key:secret(key) for key in ('OPENAI_API_KEY','OPENAI_ALLOWED_MODELS','AZURE_OPENAI_API_KEY','AZURE_OPENAI_ENDPOINT','AZURE_OPENAI_DEPLOYMENTS','AZURE_OPENAI_API_VERSION')}
    options=configured_models(settings)
    chosen=None
    if mode!='Structured Facts':
        if options:
            providers=list(dict.fromkeys(x.provider for x in options))
            provider=st.selectbox('AI provider',providers,key=f'provider_{mode}')
            available=[x for x in options if x.provider==provider]
            chosen=st.selectbox('AI model / Azure deployment',available,format_func=lambda x:x.label,key=f'model_{mode}')
        else:
            st.warning('No approved LLM provider is configured. Set OpenAI or Azure OpenAI credentials in Streamlit secrets. Structured Facts remains available.')
    # with st.expander('How the three modes work'):
    #    st.markdown('**RAG:** ChromaDB retrieves documents and the selected model synthesizes a cited answer. **Structured Facts:** deterministic JSON lookup, no API needed. **LLM:** direct conversation, not grounded in your indexed documents or live news.')
    suggestions=['What does the 2017 salary review say about the MR4 benchmark?',
                 'How does the National Bonus work?',
                 'What changed in ministerial salaries in 2026?',
                 'What is Lawrence Wong’s current appointment?']
    if 'assistant_histories' not in st.session_state:
        st.session_state.assistant_histories={'RAG':[],'Structured Facts':[],'LLM':[]}
    if 'assistant_draft' not in st.session_state:st.session_state.assistant_draft=''
    if 'assistant_pending' not in st.session_state:st.session_state.assistant_pending=None
    history=st.session_state.assistant_histories[mode]
    cols=st.columns(2)
    for i,q in enumerate(suggestions):
        if cols[i%2].button(q,key=f'v12_suggest_{i}',use_container_width=True):
            st.session_state.assistant_pending=(mode,q)
    for idx,item in enumerate(history):
        with st.chat_message(item['role']):
            st.markdown(item['content'])
            if item.get('evidence'):
                with st.expander('Supporting sources' if item.get('status')=='success' else 'View retrieved evidence'):
                    for n,e in enumerate(item['evidence'],1):
                        st.markdown(f"**[{n}] {e.get('filename','Document')} · page {e.get('page','?')}**")
                        if e.get('url'):st.markdown(f"[Open source]({e['url']})")
                        st.caption(e.get('text','')[:800])
            if item.get('can_switch'):
                if st.button('Switch to LLM mode (review question first)',key=f'v12_switch_{idx}'):
                    st.session_state.assistant_draft=item.get('question','')
                    st.session_state.assistant_requested_mode='LLM'
                    st.rerun()
    if st.session_state.get('assistant_requested_mode')=='LLM':
        st.info('Your question has been copied below. Select LLM mode to review and submit it. No request was sent automatically.')
        st.session_state.assistant_requested_mode=None
    if st.session_state.assistant_draft:
        st.text_area('Question to review before submitting in LLM mode',key='assistant_draft')
        if st.button('Use this question',key='v12_use_draft'):
            st.session_state.assistant_pending=(mode,st.session_state.assistant_draft)
            st.session_state.assistant_draft=''
            st.rerun()
    typed=st.chat_input('Ask SGPayPulse a question...')
    question=typed
    if st.session_state.assistant_pending and st.session_state.assistant_pending[0]==mode:
        question=st.session_state.assistant_pending[1]
        st.session_state.assistant_pending=None
    if question:
        prior=[{'role':m['role'],'content':m['content']} for m in history if m['role'] in ('user','assistant')]
        history.append({'role':'user','content':question})
        with st.chat_message('user'):st.write(question)
        with st.chat_message('assistant'):
            if mode=='Structured Facts':
                answer=salary_answer(question) or profile_answer(question) or 'My structured knowledge base does not contain sufficient verified information to answer this question.'
                result={'role':'assistant','content':answer,'status':'facts'}
            elif mode=='LLM':
                output=llm_answer(question,chosen,generate,settings,prior)
                result={'role':'assistant','content':output.text,'status':output.status}
            else:
                try:
                    evidence=vector_store().search(question,k=6)
                    output=rag_answer(question,evidence,chosen,generate,settings,prior)
                    result={'role':'assistant','content':output.text,'status':output.status,'evidence':output.evidence,
                            'can_switch':output.can_switch,'question':question}
                except Exception as exc:
                    # Never disclose provider keys, endpoints, or internal traces in the public UI.
                    result={'role':'assistant','content':'RAG document retrieval is unavailable. Check ChromaDB installation and indexed documents with the administrator.','status':'retrieval_error'}
            st.markdown(result['content'])
            if result.get('evidence'):
                with st.expander('Supporting sources' if result['status']=='success' else 'View retrieved evidence'):
                    for i,e in enumerate(result['evidence'],1):
                        st.markdown(f"**[{i}] {e.get('filename','Document')} · page {e.get('page','?')}**")
                        if e.get('url'):st.markdown(f"[Open source]({e['url']})")
                        st.caption(e.get('text','')[:800])
            if result.get('can_switch'):
                st.info('My indexed knowledge is limited for this question. You may switch to LLM mode to explore further; it does not automatically verify the latest information.')
        history.append(result)
    if history:
        transcript='\n\n'.join(f"{m['role'].upper()}: {m['content']}" for m in history)
        st.download_button('⬇️ Export conversation (.txt)',transcript,file_name=f'sgpaypulse_{mode.lower().replace(" ","_")}_conversation.txt',mime='text/plain')
        if st.button('Clear this mode’s chat',key='v12_clear_chat'):
            st.session_state.assistant_histories[mode]=[]
            st.rerun()

elif page==NAV[2]:
    st.title('⚖️ Minister Comparator')
    st.caption('Compare current appointments and documented history. Missing dates are shown as unverified, not inferred.')
    names=sorted(people)
    c1,c2=st.columns(2)
    with c1:
        st.markdown('**First Minister**')
        n1=st.selectbox(
            'First minister', names,
            index=names.index('Lawrence Wong') if 'Lawrence Wong' in names else 0,
            label_visibility='collapsed'
        )
    with c2:
        st.markdown('**Second Minister**')
        n2=st.selectbox(
            'Second minister', names,
            index=names.index('Ong Ye Kung') if 'Ong Ye Kung' in names else min(1,len(names)-1),
            label_visibility='collapsed'
        )
    a,b=st.columns(2)
    with a:person_card(n1)
    with b:person_card(n2)
    st.warning('Published office-level salary references must not be interpreted as the actual salary of either selected person.')

elif page==NAV[3]:
    st.title('💰 2026 Pay Explorer')
    st.caption('Published reference salary and allowance amounts · Effective 15 October 2026')
    c1,c2,c3=st.columns(3)
    c1.metric('PM annual reference',fmt(byid['pm']['current']))
    c2.metric('MR4 annual reference',fmt(byid['mr4']['current']))
    c3.metric('MP monthly allowance',fmt(byid['mp']['current']))
    st.markdown('<div class="sg-note"><b>Interpretation:</b> The revised benchmark does not mean every existing minister received that amount. Existing political officeholders have differentiated one-off adjustments of up to 9%.</div>',unsafe_allow_html=True)
    annual=[r for r in rates if r['unit']=='annual' and r.get('previous') is not None]
    chart=pd.DataFrame([{'Office':r['label'],'Previous':r['previous'],'2026':r['current']} for r in annual])
    st.plotly_chart(px.bar(chart.melt('Office',var_name='Period',value_name='SGD'),x='Office',y='SGD',color='Period',barmode='group',title='Published annual reference packages (S$)'),use_container_width=True)
    role=st.selectbox('Explore a role',[r['label'] for r in rates]);selected=next(r for r in rates if r['label']==role)
    l,r=st.columns(2)
    l.metric(f"Earlier ({selected['unit']})",fmt(selected.get('previous')))
    r.metric(f"From 15 Oct 2026 ({selected['unit']})",fmt(selected.get('current')))
    st.dataframe(pd.DataFrame([{'Role':r['label'],'Unit':r['unit'],'Earlier SGD':r['previous'],'2026 SGD':r['current'],'Type':r['kind']} for r in rates]),hide_index=True,use_container_width=True)
    # st.download_button('⬇️ Export salary framework (JSON)',json.dumps(fw,indent=2),file_name='remuneration_framework_2026.json',mime='application/json')
    sources_block()

elif page==NAV[4]:
    st.title('🏛️ Minister Directory')
    st.caption('Explore Singapore Cabinet ministers, their appointments, constituencies and history.')
    st.markdown("""
    <div class="sg-search-heading">
        <span class="sg-search-icon">🔎</span>
        <div>
            <div class="sg-search-title">Find a Minister</div>
            <div class="sg-search-subtitle">Search by minister name, constituency or portfolio</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input(
        'Minister search',
        placeholder='Search Lawrence Wong, Lee Hsien Loong, Finance...',
        label_visibility='collapsed',
        key='minister_directory_search',
    )
    matches = [
        (n, p) for n, p in people.items()
        if search.casefold() in (
            n + ' ' + p.get('constituency', '') + ' ' + p.get('current_appointment', '')
        ).casefold()
    ]
    st.caption(f'{len(matches)} matching profiles')
    for n, p in sorted(matches):
        with st.expander(f"{n} · {p.get('current_appointment', '')}"):
            st.write('Constituency:', p.get('constituency', 'Not verified'))
            st.write('Historical coverage:', p.get('historical_coverage', 'Not specified'))
            st.write('Individual actual salary: not publicly verified')
            if p.get('profile_source_url'):
                st.markdown(f"[Official biography]({p['profile_source_url']})")
            for h in p.get('historical_portfolios', []):
                st.markdown(f"- {h.get('term', 'Date not verified')}: {h.get('portfolio', '')}")

elif page==NAV[5]:
    st.title('📁 Document Manager')
    st.caption('Admin-only document ingestion into ChromaDB. Public users can query indexed documents through the AI Assistant.')
    admin_password=secret('ADMIN_PASSWORD')
    if not admin_password or admin_password=='REPLACE_WITH_A_LONG_RANDOM_PASSWORD':
        st.error('Admin upload is disabled until ADMIN_PASSWORD is set in Streamlit secrets or environment variables. Public query access remains available.')
    else:
        if not st.session_state.get('admin_authenticated',False):
            with st.form('admin_login'):
                password=st.text_input('Admin password',type='password')
                submitted=st.form_submit_button('Sign in as Admin')
            if submitted:
                if hmac.compare_digest(password,admin_password):st.session_state.admin_authenticated=True;st.rerun()
                else:st.error('Invalid credentials')
        else:
            if st.button('Sign out Admin'):st.session_state.admin_authenticated=False;st.rerun()
            st.success('Admin authenticated')
            with st.form('upload_docs'):
                files=st.file_uploader('Upload official documents',type=['pdf','docx','txt','md'],accept_multiple_files=True)
                source_label=st.text_input('Source organisation / label','Official government publication')
                source_url=st.text_input('Source URL (optional)')
                submit=st.form_submit_button('Index uploaded documents')
            if submit and files:
                for f in files:
                    try:
                        record=vector_store().add(f.name,f.getvalue(),source_url,source_label)
                        st.success(f"{record['filename']}: {record['chunks']} indexed chunks"+(' (already indexed)' if record.get('duplicate') else ''))
                    except Exception as exc:st.error(f'{f.name}: {exc}')
            if st.button('Index bundled sample documents'):
                try:
                    results=seed_documents(vector_store(),BASE/'sample_documents')
                    st.success(f'{len(results)} sample documents available in index')
                except Exception as exc:st.error(f'Sample indexing failed: {exc}')
            st.subheader('Knowledge base coverage')
            if st.button('Refresh JSON knowledge index'):
                st.success(f"Synchronized: {vector_store().sync_project_data(BASE)}")
            st.json(vector_store().coverage())
            st.caption('Structured profiles are indexed alongside uploaded documents; JSON remains the authoritative data source.')
            st.subheader('Indexed document inventory')
            items=vector_store().manifest()
            if not items:st.info('No indexed documents yet. Use the sample indexing button above.')
            for item in items:
                col1,col2=st.columns([5,1])
                col1.write(f"{item['filename']} · {item['chunks']} chunks · {item.get('source_label','')}")
                if col2.button('Delete',key='del'+item['id']):vector_store().delete(item['id']);st.rerun()
            st.caption('For cloud deployment, local uploads and ChromaDB storage may be ephemeral. Use persistent storage or a reproducible prebuilt index for production.')

elif page==NAV[6]:
    st.title('🔬 Methodology')
    st.subheader('Retrieval-Augmented Generation workflow')
    st.markdown('**1. Ingest** official PDF/DOCX/TXT/MD → **2. Extract** text and page references → **3. Chunk** into overlapping passages → **4. Embed and index** in ChromaDB → **5. Retrieve** relevant passages → **6. Generate** a cited answer with an optional LLM.')
    st.info('Without OPENAI_API_KEY, document mode performs vector retrieval and displays extractive passages. With a key, an OpenAI chat model generates an answer grounded in the retrieved evidence.')
    st.subheader('Structured records')
    st.write('Minister identities, appointment snapshots and published remuneration framework amounts are stored in JSON and queried separately to avoid inventing numerical data.')
    st.subheader('Model and API usage')
    st.markdown('- **Vector store:** ChromaDB persistent local collection.\n- **Embeddings:** Chroma default local ONNX embedding model (downloads on first use).\n- **Generation:** OpenAI Chat Completions API when configured; default `gpt-4.1-mini` (configurable).\n- **Privacy:** Uploaded document passages and the user query are sent to the model provider only when an API key is enabled.\n- **Roles:** Public users can query; Admin password protects ingestion/deletion.')
    st.subheader('Limitations and controls')
    st.markdown('- Source documents may be incomplete or historical.\n- Scanned PDFs without extractable text are not supported.\n- Current individual minister salary amounts are not inferred from grade benchmarks.\n- The RAG model can still make mistakes; verify citations against original documents.\n- Local index storage is not durable on ephemeral cloud hosts.\n- The uploaded research pack is secondary research; verify its claims against official publications.')

elif page==NAV[7]:
    st.title('ℹ️ About Us')
    st.markdown('**SGPayPulse** is an AI Champion Bootcamp capstone prototype helping citizens explore Singapore public leadership, parliamentary appointments and published political remuneration frameworks using source-grounded retrieval.')
    st.subheader('Problem statement')
    st.write('Historical public-office information is fragmented across multiple sources, making comparisons across terms and individuals difficult.')
    st.subheader('Project team')
    st.write('The uploaded proposal lists Mayukh Rastogi, Boon Hwee Ng, Vishal Arya and Keat Jau Yaw. Confirm the final three-member competition team before submission.')
    st.subheader('Competition features')
    st.markdown('1. Admin document management\n2. ChromaDB RAG chatbot\n3. Conversation export and document evidence summaries')
    st.caption('Independent bootcamp prototype; not an official Singapore Government service.')
