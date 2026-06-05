# Knowledge base PDF folders

Copy your books here, then index into Pinecone with `store_index_to_pinecone.py`.

| Folder | Pinecone index (suggested name) | Used by app today? |
|--------|----------------------------------|--------------------|
| `mental_health/` | `medical-chatbot-mh` | Yes — set `PINECONE_MENTAL_HEALTH_INDEX_NAME` in `.env` |
| `lab_results/` | `medical-chatbot-lab` | Yes — set `PINECONE_LAB_RESULTS_INDEX_NAME` in `.env` (hybrid: parser + RAG) |

Do not commit large copyrighted PDFs to git unless you have rights.
