import importlib, sys
print('Python:', sys.executable, sys.version.split()[0])
failed=[]
for name in ['streamlit','chromadb','pypdf','docx','plotly','pandas','openai']:
    try:
        m=importlib.import_module(name)
        print('OK',name,getattr(m,'__version__','installed'))
    except Exception as e:
        print('MISSING/FAILED',name,type(e).__name__,str(e));failed.append(name)
if failed:
    print('Install into THIS interpreter:',sys.executable,'-m pip install -r requirements.txt')
    raise SystemExit(1)
print('Dependencies ready. First vector embedding may download a model; Internet is needed.')
