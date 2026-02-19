# Fanga Intelligent File Classifier

AI-powered pipeline that automatically classifies, renames, and organizes heterogeneous files for FANGA, an Ivorian electric 2-wheeler mobility platform.

## Tech Stack

- Python 3.10+
- OpenAI GPT-4o (text + vision)
- Local filesystem storage
- Structured logging

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env

python generate_mocks.py
python main.py
```
