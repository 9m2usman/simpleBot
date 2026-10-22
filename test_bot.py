# test_bot.py
# Sends sample customer messages to the bot and checks it picked the right FAQ.
# Run:  python test_bot.py
# Add your own lines to TESTS: (customer message, words that must be in the matched question)
# Write  "word1|word2"  if either FAQ is a correct answer.
# A test with None means "the bot should NOT know this" (it must say sorry).
from bot_core import get_reply, using_azure

TESTS = [
    ("hello", "Hi"),
    ("assalamualaikum", "Hi"),
    ("thanks a lot", "Thank you"),
    ("bye", "Goodbye"),
    ("are you a robot?", "Who are you"),
    ("where is my order", "track my order"),
    ("order kab ayega", "How long does delivery take"),
    ("how many days for delivery to Lahore", "How long does delivery take"),
    ("what is the delivery charge", "shipping fee"),
    ("is delivery free", "free shipping"),
    ("can i pay cash when it arrives", "cash on delivery"),
    ("do you accept jazzcash", "payment methods|JazzCash"),
    ("my card payment failed but the money was cut", "payment failed"),
    ("I want my money back", "refund"),
    ("how do i return something", "How do I return"),
    ("what is your return policy", "return policy"),
    ("the shirt is too small can I swap it", "different size"),
    ("i received a broken phone", "defective|damaged"),
    ("they sent me the wrong product", "wrong item"),
    ("my coupon code is not working", "promo code is not working"),
    ("i forgot my password", "forgot my password"),
    ("login nahi ho raha", "cannot log in|forgot my password"),
    ("cancel my order please", "cancel my order"),
    ("i want to speak to a real person", "human agent"),
    ("someone called asking for my OTP", "OTP"),
    ("does it have warranty", "warranty"),
    ("is this product original", "original"),
    ("can you deliver to dubai", "internationally"),
    ("parcel says delivered but i did not get it", "shows delivered"),
    ("I want to buy a flight ticket", None),
    ("what is the capital of france", None),
    ("asdfgh qwerty", None),
    # ---- messages written after the first version (never used for tuning at the time) ----
    ("hey, I ordered 3 days ago and want to know the status", "track|delayed"),
    ("kya main cash on delivery kar sakta hun", "cash on delivery"),
    ("how long will it take to get my parcel in karachi", "delivery take"),
    ("I have been charged twice for one order", "payment failed|duplicate"),
    ("what happens if i dont like the product", "return policy|return a product"),
    ("my refund still hasnt come after 10 days", "refund has not"),
    ("do you offer free delivery above some amount", "free shipping|shipping fee"),
    ("please cancel the order i just made", "cancel my order"),
    ("how to contact you by phone", "contact customer support"),
    ("the courier never called me", "not home|delayed|delivered"),
    ("is easypaisa available", "payment methods|JazzCash"),
    ("do you ship outside pakistan", "internationally"),
    ("can i get a gift wrapped", "gift"),
    ("promo code expired", "promo code is not working"),
    ("the dress i got does not fit me", "exchange|size"),
    ("i want to talk to someone", "human agent"),
    ("is your store trustworthy", "original|safe|personal"),
    ("can i exchange my shoes for a bigger size", "exchange"),
    ("how do i know if my order is confirmed", "confirmation|track|statuses"),
    ("do you have installments", "instalments"),
    ("somebody is asking me for my pin on whatsapp", "OTP"),
    ("how can i write a review", "review"),
    ("please update my phone number", "change my email"),
    ("thankyou so much", "Thank you"),
    ("good morning", "Hi"),
    ("do you sell mobile phones", "particular product"),
    ("recommend me a good laptop", "choose a product"),
    ("what is bitcoin", None),
    ("order status", "track|statuses"),
    ("I am very angry about your service", "complaint"),
    ("my parcel has not arrived, where is it?", "delayed|track"),
]

print("Mode:", "Azure AI Search" if using_azure() else "Offline matching")
print("-" * 70)
passed = 0
for message, expected in TESTS:
    result = get_reply(message)
    if expected is None:
        ok = not result["found"]
    else:
        options = expected.lower().split("|")          # "a|b" = either is a right answer
        ok = result["found"] and any(o in result["matched"].lower() for o in options)
    passed += ok
    shown = result["matched"] if result["found"] else "(no answer -> support message)"
    print(("PASS" if ok else "FAIL"), "|", message, "->", shown)

print("-" * 70)
print(f"{passed} of {len(TESTS)} tests passed")
