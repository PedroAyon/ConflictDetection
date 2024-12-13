from transformers import pipeline


class ConflictDetector:
    def __init__(self):
        """Initializes the sentiment analysis pipeline."""
        self.sentiment_analyzer = pipeline("sentiment-analysis")

    def detect_conflict(self, conversation: str) -> bool:
        """
        Determines if a conversation contains conflict.

        Args:
            conversation (str): The conversation text.

        Returns:
            bool: True if conflict is detected, False otherwise.
        """
        # Split the conversation into exchanges
        exchanges = conversation.strip().split("\n")
        for exchange in exchanges:
            try:
                # Split into speaker and sentence
                _, sentence = exchange.split(":", 1)
                sentiment = self.sentiment_analyzer(sentence.strip())[0]
                # Conflict detection logic
                if sentiment['label'] == "NEGATIVE" and sentiment['score'] > 0.7:
                    return True  # Conflict detected
            except ValueError:
                # Skip malformed lines
                continue
        return False  # No conflict detected
