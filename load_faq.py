# Step 1: create the search index and fill it with the shop FAQ.
# Run once (and again any time you edit faq.json):   python load_faq.py
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
endpoint = os.getenv("SEARCH_ENDPOINT", "").rstrip("/")
admin_key = os.getenv("SEARCH_ADMIN_KEY")        # the ADMIN key is needed to create an index

if not endpoint or not admin_key or "YOUR-SEARCH" in endpoint or admin_key.startswith("paste"):
    raise SystemExit("Put SEARCH_ENDPOINT and SEARCH_ADMIN_KEY in your .env file first.")

api = "?api-version=2024-07-01"
headers = {"api-key": admin_key, "Content-Type": "application/json"}
INDEX = "shop-faq"

index = {
    "name": INDEX,
    "fields": [
        {"name": "id",       "type": "Edm.String", "key": True},
        {"name": "category", "type": "Edm.String", "filterable": True, "facetable": True},
        # en.lucene understands English word endings: return = returns = returned
        {"name": "question", "type": "Edm.String", "searchable": True, "analyzer": "en.lucene"},
        {"name": "keywords", "type": "Edm.String", "searchable": True, "analyzer": "en.lucene"},
        {"name": "answer",   "type": "Edm.String", "searchable": True, "analyzer": "en.lucene"},
    ],
    # A match in the question counts more than a match in the answer
    "scoringProfiles": [
        {"name": "boost", "text": {"weights": {"question": 3, "keywords": 2, "answer": 1}}}
    ],
    "defaultScoringProfile": "boost",
}

# Delete the old index (if any) so you can safely run this again after changes
r = requests.delete(f"{endpoint}/indexes/{INDEX}{api}", headers=headers, timeout=30)
print("Delete old index:", r.status_code, "(404 is fine on the first run)")

r = requests.put(f"{endpoint}/indexes/{INDEX}{api}", headers=headers, json=index, timeout=30)
print("Create index:", r.status_code)
r.raise_for_status()

docs = json.load(open("faq.json", encoding="utf-8"))
batch = {"value": [dict(d, **{"@search.action": "upload"}) for d in docs]}
r = requests.post(f"{endpoint}/indexes/{INDEX}/docs/index{api}", headers=headers, json=batch, timeout=60)
print("Upload FAQ:", r.status_code)
r.raise_for_status()
print("Done:", len(docs), "questions are now in the index")
