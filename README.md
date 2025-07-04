# truth_engine

A fully-automated, AI-powered platform for generating and sharing truth reports about legislative activity in the U.S.

## Features
- 🏛 Monitors **federal** and **Florida** state legislation
- 🧠 Uses AI to summarize and explain bills in **plain English**
- ✅ Classifies who is **helped or harmed**, and the **short- and long-term effects**
- 📬 Sends daily reports via **email**
- 🌐 Hosts a live **web page** with the latest digest
- 🐳 Runs in a **Docker container** or on **Kubernetes**

## Getting Started

### 1. Clone the Repo and Install Dependencies
```bash
git clone <your-repo-url>
cd truth_engine
pip install -r requirements.txt
```

### 2. Setup Environment Variables
Copy `.env.example` to `.env` and fill in:
```env
OPENAI_API_KEY=your-key
PROPUBLICA_API_KEY=your-key
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_USERNAME=you@example.com
EMAIL_PASSWORD=yourpassword
EMAIL_TO=recipient@example.com
OPENAI_MODEL=gpt-4
```

### 3. Run the Engine
To generate the digest and email it:
```bash
python main.py --run
```

To start the web server:
```bash
python main.py --web
```

Or do both:
```bash
python main.py --run --web
```

### 4. Docker
```bash
docker build -t truth_engine .
docker run --env-file .env -p 8000:8000 truth_engine
```

## License

Apache 2.0 with ethical use clause:
You may not use this project to promote hate, misinformation, voter suppression, or harassment.

---

Made with ❤️ to bring truth to light.
