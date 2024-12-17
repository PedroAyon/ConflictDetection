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
                sentiment = self.sentiment_analyzer(exchange)
                # Conflict detection logic
                sentiment_result = sentiment[0]  # Extract the first result
                if sentiment_result['label'] == "NEGATIVE" and sentiment_result['score'] > 0.7:
                    return True

            except ValueError:
                # Skip malformed lines
                continue
        return False  # No conflict detected
