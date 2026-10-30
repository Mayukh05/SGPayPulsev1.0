# SGPayPulse v1.2 – Unified RAG Release

Python 3.11, Streamlit, ChromaDB, JSON, OpenAI/Azure OpenAI.

## Start (CMD or Anaconda Prompt, not PowerShell)

```cmd
conda activate sgpaypulse
python -m pip install -r requirements.txt
python -m streamlit run SGPayPulsev1.0.py --server.port 8502
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` **on your computer** and enter your credentials there. Your original populated file was deliberately excluded from this distributable ZIP. Never commit it or share it in ZIPs. If earlier credentials were shared, rotate them.

## Knowledge sources
- `data/mp_ministers_data.json`: 21 minister profiles (including Jasmin Lau and Lee Hsien Loong)
- `data/remuneration_framework_2026.json`: historical/revised published reference figures
- `sample_documents/`: three bundled sample documents
- `rag_store/chroma`: existing Chroma index carried forward from the uploaded project to preserve any indexed-only uploads. Its manifest is not a full inventory of structured JSON records.

At startup the application synchronizes curated JSON into the **same** Chroma collection as uploaded documents. It updates changed entries and deletes stale structured entries. Uploaded document vectors are not deleted. It also prioritizes exact person-name and known alias matches before semantic retrieval.

If the JSON changes while the app is running, use **Document Manager → Refresh JSON knowledge index** (Admin access). Restarting Streamlit also refreshes it. `Structured Facts` still reads JSON; RAG uses the indexed representation plus documents.

### Limitations
- The index reflects supplied records; no independent verification of all 21 biographies was performed in this release.
- Scanned PDFs without text are not ingested. The uploaded index may contain documents whose original files are not in the ZIP.
- RAG synthesis requires a configured reachable LLM; retrieval evidence alone is not a generated answer.
- On a cloud host, persist Chroma data or rebuild it from original documents and JSON. Local uploads may disappear on redeployment.
- The provided index may require compatible ChromaDB versions; if it fails to open, back it up and rebuild from the bundled documents. Any uploaded-only documents must be reuploaded.

## Tests
`python -m unittest discover -s tests -v`

See `CLEANUP_REPORT.md` for retained/removed file rationale.
