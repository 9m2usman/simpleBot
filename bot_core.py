# bot_core.py
# The "brain" of the bot. ask.py, chatbot.py and test_bot.py all use it.
#
# Two ways to find an answer:
#   1. Azure AI Search  -> used when SEARCH_ENDPOINT and SEARCH_KEY are in .env
#   2. Offline matching -> used when they are missing (no Azure needed, good for testing)
import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT", "").rstrip("/")
SEARCH_KEY = os.getenv("SEARCH_KEY")            # QUERY key: can only read the index
TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")     # optional, for Urdu answers
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION", "eastus")

INDEX_NAME = "shop-faq"
API = "?api-version=2024-07-01"

STORE_NAME = "ShopEasy"
MIN_SCORE_AZURE = 2.0   # lower Azure score = "I don't know". Tune it with ask.py
MIN_SCORE_LOCAL = 2     # same idea for the offline matcher

NOT_FOUND = ("Sorry, I could not find an answer to that. Please contact our support team: "
             "WhatsApp +92 300 0000000 or support@shopeasy.example (9 am to 9 pm, 7 days). "
             "Please mention your order number.")


def using_azure():
    """True when real Azure AI Search keys are in .env (placeholders do not count)."""
    if not SEARCH_ENDPOINT or not SEARCH_KEY:
        return False
    if "YOUR-SEARCH" in SEARCH_ENDPOINT or SEARCH_KEY.startswith("paste"):
        return False
    return True


# ------------------------------------------------------------
# 1. AZURE AI SEARCH
# ------------------------------------------------------------
def azure_search(question, top=3):
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/search{API}"
    body = {"search": question, "top": top, "select": "id,category,question,answer"}
    r = requests.post(url, headers={"api-key": SEARCH_KEY}, json=body, timeout=30)
    r.raise_for_status()
    hits = r.json()["value"]
    for h in hits:
        h["score"] = h["@search.score"]
        h["confident"] = h["score"] >= MIN_SCORE_AZURE
    return hits


# ------------------------------------------------------------
# 2. OFFLINE MATCHING (simple word overlap, no libraries)
# ------------------------------------------------------------
# Words that carry no meaning for matching
STOPWORDS = set("""a an the is are was were am be do does did can could would should will
i me my we our you your it its to of in on at for from with by and or but so if then than
this that these those there here what when which who how why please tell about
want need get got have has had any some just also as not no yes
something anything thing lot much very really receive received
take takes come comes came item items
nahi nahin ho hai hain raha rahi rahe ka ki ke ko se mein mai par pe kya mera meri mere mujhe aap hy""".split())

# A few words that mean the same thing, so they should match each other
SAME = {"delivery": "deliver", "payment": "pay", "cancellation": "cancel",
        "replacement": "replac", "installment": "instal", "instalment": "instal"}

_FAQ = None    # loaded once
_VOCAB = set() # every word that appears in the FAQ


def _stem(word):
    """Tiny stemmer so that return/returns/returned and ship/shipping all match."""
    if word.endswith("ies") and len(word) > 4:        # deliveries -> delivery
        word = word[:-3] + "y"
    else:
        for end in ("ing", "ed", "s"):
            if word.endswith(end) and len(word) - len(end) >= 3:
                word = word[:-len(end)]
                break
    if len(word) > 3 and word.endswith("e"):          # charge/charges/charged -> charg
        word = word[:-1]
    if len(word) > 3 and word[-1] == word[-2]:        # shipp -> ship
        word = word[:-1]
    return SAME.get(word, word)


def _words(text):
    found = re.findall(r"[a-z0-9]+", text.lower())
    return {_stem(w) for w in found if w not in STOPWORDS}


def _load_faq():
    global _FAQ, _VOCAB
    if _FAQ is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faq.json")
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        _VOCAB = set()
        for it in items:                       # prepare the word sets once
            it["q_words"] = _words(it["question"])
            it["k_words"] = _words(it["keywords"])
            it["a_words"] = _words(it["answer"])
            _VOCAB |= it["q_words"] | it["k_words"] | it["a_words"]
        _FAQ = items
    return _FAQ


def local_search(question, top=3):
    faq = _load_faq()
    query = _words(question)
    # Words the FAQ has never seen (a product name like "iphone") should not hurt the score
    known = [w for w in query if w in _VOCAB]
    first = re.findall(r"[a-z]+", question.lower())[:1]     # first word, e.g. "how"
    results = []
    for it in faq:
        score = 0
        matched = 0
        for w in known:
            if w in it["q_words"]:
                score += 3.25       # a match in the question counts most
                matched += 1
            elif w in it["k_words"]:
                score += 3          # a match in "other ways to ask" counts almost the same
                matched += 1
            elif w in it["a_words"]:
                score += 1          # a match only in the answer counts a little
                matched += 1
        if matched == 0:
            continue
        # reward FAQs that cover MORE of the words the customer typed
        score = score * (0.5 + 0.5 * matched / len(known))
        # tiny bonus when both start with the same word ("how ...", "what ...")
        if first and it["question"].lower().startswith(first[0]):
            score += 0.5
        # Sure enough? Need a decent score, and either 2+ matching words
        # or a very short message ("hello", "broken phone")
        confident = score >= MIN_SCORE_LOCAL and (matched >= 2 or len(query) <= 2)
        results.append({"score": score, "confident": confident, "id": it["id"],
                        "category": it["category"], "question": it["question"],
                        "answer": it["answer"]})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top]


# ------------------------------------------------------------
# 3. ONE FUNCTION THE WEBSITE CALLS
# ------------------------------------------------------------
def search(question, top=3):
    return azure_search(question, top) if using_azure() else local_search(question, top)


def get_reply(question):
    """Returns a dict: found (True/False), answer, matched question, related questions."""
    hits = search(question, top=3)
    good = [h for h in hits if h["confident"]]
    if not good:
        return {"found": False, "answer": NOT_FOUND, "matched": None, "related": []}
    best = good[0]
    # suggest other questions only when they score nearly as well as the best one
    related = [h["question"] for h in good[1:] if h["score"] >= 0.7 * best["score"]]
    return {"found": True, "answer": best["answer"], "matched": best["question"],
            "related": related}


# ------------------------------------------------------------
# 4. OPTIONAL: URDU ANSWERS (Azure Translator)
# ------------------------------------------------------------
def to_urdu(text):
    url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=ur"
    headers = {"Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
               "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION}
    r = requests.post(url, headers=headers, json=[{"Text": text}], timeout=30)
    r.raise_for_status()
    return r.json()[0]["translations"][0]["text"]
