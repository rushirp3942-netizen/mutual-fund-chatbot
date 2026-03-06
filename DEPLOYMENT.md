# Deployment Guide

## Files to Push to GitHub

### Required for Streamlit Backend:
- `streamlit_backend.py` - Main Streamlit app
- `requirements.txt` - Python dependencies
- `phase1_data_collection/data/processed/extracted_funds.json` - Fund data
- `phase6_chat_app/backend/app/services/fund_data.py` - Fund query logic
- `.gitignore` - Excludes unnecessary files

### Required for Vercel Frontend:
- `vercel-frontend/` folder containing:
  - `index.html`
  - `styles.css`
  - `app.js`
  - `vercel.json`

## Streamlit Cloud Deployment Steps

1. **Push to GitHub:**
   ```powershell
   cd "d:\New folder"
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/mutual-fund-chatbot.git
   git branch -M main
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to: https://share.streamlit.io
   - Click "New app"
   - Repository: `your-username/mutual-fund-chatbot`
   - Branch: `main`
   - Main file path: `streamlit_backend.py`
   - Click "Deploy"

3. **Add Secrets:**
   - Go to Settings → Secrets
   - Add: `GROQ_API_KEY` = your-api-key

## Vercel Deployment Steps

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   cd vercel-frontend
   vercel
   ```

3. **Update API URL:**
   - After Streamlit deploys, copy the URL
   - Update `app.js` line 2: `const API_BASE_URL = 'https://your-app.streamlit.app'`
   - Redeploy to Vercel

## URLs After Deployment

| Service | URL Example |
|---------|-------------|
| Streamlit Backend | `https://mutual-fund-chatbot-xyz123.streamlit.app` |
| Vercel Frontend | `https://mutual-fund-assistant.vercel.app` |
