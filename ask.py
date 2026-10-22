# Step 2: ask one question (no website yet).   python ask.py
# Shows the top 3 matches with their scores, so you can tune the minimum score.
from bot_core import get_reply, search, using_azure

question = "my parcel has not arrived, where is it?"      # change this and run again

print("Mode:", "Azure AI Search" if using_azure() else "Offline matching (no Azure keys found)")
print("Question:", question, "\n")

for hit in search(question, top=3):
    print(round(hit["score"], 2), "| sure enough:", hit["confident"], "|", hit["question"])

reply = get_reply(question)
print("\nBot reply:\n", reply["answer"])
