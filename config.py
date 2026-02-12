import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "qa_chatbot")

# Check for missing essential variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment or .env file.")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in the environment or .env file.")
if not MYSQL_PASSWORD:
    raise ValueError("MYSQL_PASSWORD is not set in the environment or .env file.")
