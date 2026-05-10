# File: openrouter-streamlit-chat/src/utils/settings.py

import os

class Settings:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = "openai/gpt-sso-120b"
        self.max_tokens = int(os.getenv("MAX_TOKENS", 150))
        self.temperature = float(os.getenv("TEMPERATURE", 0.7))

    def validate(self):
        if not self.api_key:
            raise ValueError("API key is not set. Please set the OPENROUTER_API_KEY environment variable.")
        if self.max_tokens <= 0:
            raise ValueError("MAX_TOKENS must be a positive integer.")
        if not (0 <= self.temperature <= 1):
            raise ValueError("TEMPERATURE must be between 0 and 1.")

settings = Settings()

