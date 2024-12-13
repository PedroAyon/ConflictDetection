from transformers import pipeline

# Initialize sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis")

# Sample conversation
conversation = """
Person A: I don't think this is working out.
Person B: What do you mean? I think we're doing fine.
Person A: No, it's just not working for me.
Person B: Why are you always so negative?
"""

# Split the conversation into exchanges
exchanges = conversation.strip().split("\n")

# Analyze each exchange
sentiments = []
for exchange in exchanges:
    speaker, sentence = exchange.split(":", 1)
    sentiment = sentiment_analyzer(sentence.strip())[0]
    sentiments.append({
        "speaker": speaker.strip(),
        "sentence": sentence.strip(),
        "sentiment": sentiment['label'],
        "score": sentiment['score']
    })

# Conflict detection
conflict_detected = False
for sentiment in sentiments:
    if sentiment['sentiment'] == "NEGATIVE" and sentiment['score'] > 0.7:  # Example threshold
        conflict_detected = True
        break

# Output results
print("Sentiment Analysis Results:")
for s in sentiments:
    print(f"{s['speaker']}: {s['sentence']} (Sentiment: {s['sentiment']}, Score: {s['score']:.2f})")

if conflict_detected:
    print("\nConflict detected in the conversation.")
else:
    print("\nNo significant conflict detected.")
