# QA Chatbot with Memory and RAG

A powerful QA chatbot featuring short-term memory (sliding window), long-term semantic memory (RAG with FAISS), and multi-interface support (Web UI & Telegram).

## 🚀 Features

- **Intelligent Memory**: 
  - **Short-term**: Remembers recent conversation context.
  - **Long-term**: Stores and retrieves relevant Q&A pairs using vector embeddings (FAISS).
- **Dual Interface**:
  - **Web UI**: Built with Streamlit for a rich, interactive experience.
  - **Telegram Bot**: integrated for mobile access.
- **Robust Backend**:
  - **FastAPI**: High-performance API handling chat logic and memory management.
  - **MySQL**: Persistent storage for conversations and messages.
  - **OpenAI GPT-4o-mini**: Cost-effective and capable LLM for generating responses.
  - **Dockerized**: Easy deployment with Docker Compose.

## 🛠️ Technology Stack

- **Python 3.12+**
- **FastAPI** (Backend API)
- **Streamlit** (Frontend UI)
- **MySQL** (Database)
- **OpenAI API** (LLM & Embeddings)
- **FAISS** (Vector Database)
- **python-telegram-bot** (Telegram Integration)
- **Docker & Docker Compose**

## 🐳 Quick Start (Docker)

The easiest way to run the application is using Docker.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/AlinaMuradyan/LLM-Agent.git
    cd LLM-Agent
    ```

2.  **Create a `.env` file**:
    Create a file named `.env` in the root directory and add your credentials:
    ```ini
    OPENAI_API_KEY=sk-your-key
    TELEGRAM_TOKEN=your-telegram-token
    MYSQL_PASSWORD=rootpassword
    MYSQL_DATABASE=qa_chatbot
    ```

3.  **Run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```

4.  **Access the App**:
    - **Web UI**: http://localhost:8501
    - **API Docs**: http://localhost:8000/docs

## ⚙️ Manual Setup (Development)

If you prefer to run locally without Docker, ensure you have Python 3.12+ and MySQL installed.

1.  Install dependencies: `pip install -r requirements.txt`
2.  Set up the database: `mysql -u root -p < schema.sql`
3.  Create a `.env` file with your credentials.
4.  Run the components in separate terminals:

```bash
uvicorn api:app --reload
streamlit run streamlit_app.py
python telegram.py
```

## 🧪 Testing and Debugging

A comprehensive test suite is included to verify all components.

### Interactive Debug Runner
Run the interactive tool to execute tests and view results:
```bash
python debug_runner.py
```

### Standalone Test Scripts
You can also run specific test layers individually:
- **Database**: `python test_database_standalone.py`
- **API**: `python test_api_standalone.py` (Requires API running)
- **Model**: `python test_model_standalone.py`
- **Telegram**: `python test_telegram_standalone.py`

## 📁 Project Structure

- `api.py`: FastAPI application endpoints.
- `model.py`: Core logic for LLM interaction, memory, and RAG.
- `database.py`: Database operations (MySQL).
- `streamlit_app.py`: Frontend Web UI.
- `telegram.py`: Telegram bot implementation.
- `config.py`: Configuration settings.
- `schema.sql`: Database schema.
- `debug_runner.py`: Test runner utility.

## ⚠️ Common Issues

- **Authentication Error (500)**: Check your `OPENAI_API_KEY` in `config.py`.
- **Database Connection Error**: Ensure MySQL is running and credentials in `config.py` are correct.
- **Telegram Bot Not Responding**: Ensure `telegram.py` is running and the token is valid.
