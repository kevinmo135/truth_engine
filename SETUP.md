# Truth Engine Setup Guide

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Congress.gov API (for federal bills)
CONGRESS_API_KEY=your_congress_api_key_here

# Open States API (for state bills - Florida, etc.)
OPENSTATES_API_KEY=your_openstates_api_key_here

# Email Configuration (optional, for email notifications)
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_email_password
EMAIL_TO=recipient@email.com

# Application Configuration
PORT=8000
```

## API Keys Required

### 1. OpenAI API Key
- Visit: https://platform.openai.com/api-keys
- Create an account and generate an API key
- Used for GPT-4 analysis of bills

### 2. Congress.gov API Key
- Visit: https://api.congress.gov/sign-up/
- Request a free API key
- Used for fetching federal bills from Congress.gov

### 3. Open States API Key
- Visit: https://openstates.org/accounts/profile/
- Create an account and generate an API key
- Used for fetching state bills (Florida and other states)
- **Free tier available** with rate limits

### 4. Email Configuration (Optional)
- Used for sending email notifications
- Gmail account recommended for SMTP settings

## Application Features

With all API keys configured, Truth Engine will:

✅ **Fetch real federal bills** from Congress.gov  
✅ **Fetch real state bills** from Open States (Florida, etc.)  
✅ **Analyze all bills** with GPT-4  
✅ **Generate structured analysis** with impact assessments  
✅ **Provide working source URLs** to original bills  
✅ **Daily automatic refresh** of data  

## Testing Your Setup

1. **Test federal bills:**
   ```bash
   python -c "from fetcher.congress_api import fetch_recent_federal_bills; print(len(fetch_recent_federal_bills(2)))"
   ```

2. **Test Florida bills:**
   ```bash
   python -c "from fetcher.openstates_api import fetch_recent_florida_bills; print(len(fetch_recent_florida_bills(2)))"
   ```

3. **Run full application:**
   ```bash
   python main.py --run
   ```

## Deployment

For Railway deployment, add all environment variables in the Railway dashboard under "Variables".

The application includes automatic daily refresh and a web interface accessible at `http://localhost:8000` when running locally. 