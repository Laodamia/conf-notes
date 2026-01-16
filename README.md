# Conference Notes Tool

A simple web app that converts your Fireflies.ai recordings into structured summaries with key takeaways, action items, and follow-up questions.

## How It Works

1. Record meetings/voice notes using the **Fireflies.ai** mobile app
2. Open this web app on your phone and tap **"Process Latest Recording"**
3. Get a structured summary with:
   - Key Takeaways
   - Action Items
   - Follow-up Questions
   - Notable Quotes
4. Copy to clipboard or auto-save to Google Docs

## Setup Guide

### Step 1: Get Your API Keys

#### Fireflies.ai API Key
1. Log into [Fireflies.ai](https://fireflies.ai)
2. Go to **Settings** → **Integrations** → **API**
3. Copy your API key

#### Anthropic (Claude) API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Go to **API Keys** and create a new key
4. Add some credits ($5-10 is plenty - each summary costs ~$0.01-0.05)

### Step 2: Deploy to Render (Free)

1. **Create a GitHub repository**
   - Go to [github.com](https://github.com) and create a new repository
   - Upload these files to the repository

2. **Deploy on Render**
   - Go to [render.com](https://render.com) and sign up (free)
   - Click **New** → **Web Service**
   - Connect your GitHub repository
   - Configure:
     - **Name**: `conference-notes` (or whatever you like)
     - **Runtime**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

3. **Add Environment Variables**
   - In Render, go to your service → **Environment**
   - Add these variables:
     ```
     FIREFLIES_API_KEY = your_fireflies_key
     ANTHROPIC_API_KEY = your_anthropic_key
     ```

4. **Deploy**
   - Click **Deploy** and wait a few minutes
   - You'll get a URL like `https://conference-notes-xxxx.onrender.com`
   - Bookmark this on your phone!

### Step 3: Google Docs Integration (Optional)

To auto-save summaries to a Google Doc:

1. **Create your conference report doc**
   - Create a new Google Doc for your conference notes
   - Copy the document ID from the URL (the long string between `/d/` and `/edit`)

2. **Create Google Apps Script**
   - Go to [script.google.com](https://script.google.com)
   - Create a new project
   - Delete any existing code and paste the contents of `google-apps-script.js`
   - Replace `YOUR_DOCUMENT_ID` with your doc's ID
   - Save the project

3. **Deploy as Web App**
   - Click **Deploy** → **New deployment**
   - Type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Click **Deploy** and authorize
   - Copy the **Web App URL**

4. **Add to Render**
   - Go back to Render → Environment
   - Add: `GOOGLE_SCRIPT_URL = your_web_app_url`
   - Redeploy

## Usage

### On Your Phone

1. **Record with Fireflies**
   - Open the Fireflies app and record your meeting or voice note
   - Wait for it to finish transcribing (usually a few minutes)

2. **Process with Conference Notes**
   - Open your bookmarked Conference Notes URL
   - Tap **"Process Latest Recording"** or choose from recent recordings
   - View your structured summary
   - Tap **"Copy to Clipboard"** to use elsewhere

### Tips

- **Voice notes**: Quick 1-2 minute notes after sessions work great
- **Full meetings**: Works well with 30+ minute recordings too
- **Batch processing**: Process multiple recordings in a row to build your report
- **Offline viewing**: Copy summaries to a notes app for offline access

## Cost Estimate

- **Fireflies.ai**: Uses your existing company subscription
- **Claude API**: ~$0.01-0.05 per summary (a 30-min meeting ~$0.03)
- **Render hosting**: Free tier is sufficient
- **Google Apps Script**: Free

**For a 3-day conference with 20 sessions**: ~$0.60-1.00 total

## Troubleshooting

**"Fireflies API key not configured"**
- Check that FIREFLIES_API_KEY is set in Render environment variables

**"No transcripts found"**
- Make sure your Fireflies recording has finished processing
- Transcription can take a few minutes after recording ends

**"Claude API error"**
- Verify your ANTHROPIC_API_KEY is correct
- Check you have credits in your Anthropic account

**Summary not saving to Google Docs**
- Verify GOOGLE_SCRIPT_URL is set correctly
- Make sure the Google Apps Script is deployed as a web app
- Check that the document ID in the script is correct

## Local Development

To run locally:

```bash
cd conference-notes
pip install -r requirements.txt

export FIREFLIES_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key

python app.py
```

Open http://localhost:5000 in your browser.
