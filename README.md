# ShopEasy Assistant: an ecommerce auto-reply chatbot

A customer types a question ("where is my order?", "order kab ayega", "I want my money back")
and the bot answers from a FAQ of 99 shop questions. It is built the same way as the
Week 8 course bot: Azure AI Search finds the best FAQ, Streamlit shows the chat page.

**The bot only answers what is in `faq.json`.** It cannot look up a real order, and it
says sorry and gives the support contact when it does not know.

## Files

| File | What it does |
|---|---|
| `faq.json` | The knowledge: 99 questions, answers, and `keywords` (other ways customers ask) |
| `bot_core.py` | The brain: finds the best answer (Azure AI Search, or offline matching) |
| `load_faq.py` | Step 1: creates the Azure search index and uploads `faq.json` |
| `ask.py` | Step 2: asks one question in the terminal and shows the scores |
| `chatbot.py` | Step 3: the chat website (Streamlit) |
| `test_bot.py` | Checks 63 sample customer messages |
| `.env.example` | Copy to `.env` and fill in. `.env` is never uploaded to GitHub |

## Option A: run it now, no Azure (2 minutes)

```
pip install -r requirements.txt
python test_bot.py
streamlit run chatbot.py
```

With no keys in `.env`, the bot uses its own offline matching. The sidebar says
"offline demo mode".

## Option B: run it with Azure AI Search

1. Azure portal: create an **Azure AI Search** resource (Free tier, East US). Reuse your
   class one if you still have it: the free tier allows 3 indexes.
2. Open the resource, **Settings > Keys**. Copy the **Primary admin key**.
   Then **Manage query keys > Add**, and copy that **query key** too.
3. Copy `.env.example` to `.env` and fill in:
   - `SEARCH_ENDPOINT` (the URL on the resource's Overview page)
   - `SEARCH_ADMIN_KEY` (admin key, used only by `load_faq.py`)
   - `SEARCH_KEY` (query key, used by the chatbot; it can read but not change the index)
4. Run `python load_faq.py`. You should see `Upload FAQ: 200` and `Done: 99 questions`.
5. Run `python ask.py`, then `streamlit run chatbot.py`.

If good questions get the sorry message, lower `MIN_SCORE_AZURE` in `bot_core.py`.
If wrong answers sneak through, raise it. `ask.py` prints the scores to help you decide.

## Make it your own store

- The store name, support phone/email, prices (PKR 200 shipping, PKR 3,000 free-shipping
  limit), the 7-day return window and the courier names are **sample values**. Search
  `faq.json` for them and change them to your real policies. Change `STORE_NAME` and
  `NOT_FOUND` at the top of `bot_core.py` too.
- To teach the bot a new question, add an entry to `faq.json`:
  `{"id": "100", "category": "...", "question": "...", "answer": "...", "keywords": "..."}`
  Put every other way a customer might ask it into `keywords`, including Roman Urdu.
  Then run `load_faq.py` again (Azure mode).
- When a customer message gets the wrong answer, add its words to the right entry's `keywords`.
- Add a line to `TESTS` in `test_bot.py` so it never breaks again.

## Keys

Never write a key inside a `.py` file, and never upload `.env`. If a key leaks:
Azure portal > your Search resource > Settings > Keys > Regenerate.

## Ideas for next steps

- Order tracking: a small `orders.json` with fake orders, so "track ORD-1001" returns a status.
- Urdu answers: put a Translator key in `.env` and switch on "Answer in Urdu".
- Log the questions the bot could not answer, and turn them into new FAQ entries.
