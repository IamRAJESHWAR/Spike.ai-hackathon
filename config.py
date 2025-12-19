"""Configuration settings for the AI Backend."""

import os

# Server Configuration
HOST = "0.0.0.0"
PORT = 8080

# LiteLLM Configuration
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-itE0QuhkM_Gb1fZ1MGl53g")
LITELLM_BASE_URL = "http://3.110.18.218"
LITELLM_MODEL = "gemini-2.5-flash"  # Default model for reasoning

# Google Analytics Configuration
GA4_CREDENTIALS_PATH = "credentials.json"
GA4_PROPERTY_ID = "516815205"  # Default property ID, always available

# SEO Data Configuration
SEO_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE/edit?gid=1438203274#gid=1438203274"
SEO_SPREADSHEET_ID = "1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE"

# Agent Configuration
MAX_RETRIES = 3
BASE_DELAY = 1  # seconds for exponential backoff
