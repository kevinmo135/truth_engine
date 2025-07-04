# Truth Engine 🇺🇸

A fully-automated, AI-powered platform for generating and sharing truth reports about legislative activity in the U.S.

## ✨ Features
- 🏛 Monitors **federal** and **state** legislation
- 🧠 Uses **GPT-4** to summarize and explain bills in **plain English**
- ✅ Classifies who is **helped or harmed**, and the **short- and long-term effects**
- 📬 Sends daily reports via **email**
- 🌐 Hosts a live **web dashboard** with patriotic design
- 🐳 Runs in **Docker** or deploys to **Railway**
- 🔗 Integrates with **ChatGPT** for interactive Q&A

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/kevinmo135/truth_engine.git
cd truth_engine
pip install -r requirements.txt
```

### 2. Setup Environment Variables
Create a `.env` file with:
```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
CONGRESS_API_KEY=your_congress_api_key_here

# Optional Email Configuration
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_TO=recipient@example.com

# Application Configuration
PORT=8000
PYTHONUNBUFFERED=1
```

**Get your API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Congress.gov: https://api.congress.gov/sign-up/

### 3. Run the Engine
**Generate daily digest:**
```bash
python main.py --run
```

**Start web server:**
```bash
python main.py --web
```

**Both:**
```bash
python main.py --run --web
```

### 4. Docker Deployment
```bash
docker compose up --build
```

## ☁️ Railway Deployment

This project is configured for automatic deployment to Railway using GitHub Actions.

### Setup Railway Deployment

1. **Create Railway Account**: https://railway.app
2. **Create New Project** from GitHub repository
3. **Add GitHub Secrets** in your repository settings:
   ```
   RAILWAY_TOKEN=your_railway_token
   OPENAI_API_KEY=your_openai_api_key
   CONGRESS_API_KEY=your_congress_api_key
   RAILWAY_SERVICE_NAME=truth-engine (optional)
   ```

4. **Deploy**: Push to main branch to trigger automatic deployment

### Manual Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway up
```

## 🎨 Features

### Patriotic Dashboard
- Blue sky background with animated American flag
- Individual bill frames with 3D effects
- Professional typography (Cinzel, Merriweather fonts)
- Balance scale logo representing truth and justice

### AI Analysis
- **GPT-4** powered analysis with structured output
- **Plain English** summaries
- **Impact analysis** showing who benefits/concerned
- **Short-term and long-term** implications
- **Cost/savings** analysis

### Interactive Features
- **Deep analysis** pages for each bill
- **ChatGPT integration** for user questions
- **Source links** to official bill pages
- **Responsive design** for all devices

## 📁 Project Structure

```
truth_engine/
├── analyzer/           # AI analysis modules
├── fetcher/           # Data fetching (Congress.gov, State APIs)
├── writer/            # Report generation
├── notifier/          # Email notifications
├── webapp/            # Web dashboard
├── data/              # Generated reports
├── docker-compose.yml # Docker configuration
├── railway.toml       # Railway deployment config
├── Procfile          # Process file for Railway
└── .github/workflows/ # GitHub Actions for CI/CD
```

## 🔧 Development

### Testing
```bash
# Test OpenAI connection
python test_openai.py

# Test analyzer
python test_analyzer.py
```

### Local Development
```bash
# Start development server
python main.py --web

# Visit http://localhost:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

Licensed under the Apache License, Version 2.0. See `LICENSE` for details.

## 🎯 Mission

**Truth Engine** - Empowering Democracy Through Transparency

Made with ❤️ to bring legislative truth to light and make government more accessible to all citizens.

---

🇺🇸 **"The truth will set you free"** - and it will set democracy free too.
