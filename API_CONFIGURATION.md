# 🔧 API Configuration & Troubleshooting

## Issue: "RBAC: access denied" Error

If you see this error when uploading documents:
```
ERROR: Batch embedding generation failed: RBAC: access denied
```

This means the Custom LLM API authentication is failing. You have two options:

---

## Option 1: Use Ollama (Recommended for Local Development)

### Step 1: Install Ollama
```bash
# macOS
brew install ollama

# Or download from https://ollama.ai
```

### Step 2: Pull the Model
```bash
ollama pull llama3.2
```

### Step 3: Start Ollama
```bash
ollama serve
```

### Step 4: Use Ollama in the App
When uploading documents or chatting, select **"Ollama"** as the LLM provider instead of "Custom API".

---

## Option 2: Configure Custom API (TCS GenAI Lab)

If you have access to the TCS GenAI Lab API:

### Step 1: Get Your API Key
Contact your TCS GenAI Lab administrator to obtain an API key.

### Step 2: Update `.env` File
```bash
cd backend
nano .env  # or use your preferred editor
```

### Step 3: Set the API Key
```env
# Custom LLM API (genailab)
CUSTOM_LLM_BASE_URL=https://genailab.tcs.in
CUSTOM_LLM_MODEL=azure_ai/genailab-maas-DeepSeek-V3-0324
CUSTOM_LLM_API_KEY=your-actual-api-key-here  # ← Replace this
CUSTOM_EMBEDDING_MODEL=azure/genailab-maas-text-embedding-3-large
```

### Step 4: Restart the Backend
```bash
# Kill the current process
lsof -ti:8000 | xargs kill -9

# Restart
./venv/bin/python -m uvicorn main:app --reload --port 8000
```

---

## Quick Test

### Test Ollama
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should return a list of installed models
```

### Test Custom API
```bash
# Test authentication
curl -X POST https://genailab.tcs.in/openai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "azure_ai/genailab-maas-DeepSeek-V3-0324",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

---

## Current Configuration

Check your current setup:

```bash
cd backend
cat .env | grep -E "(CUSTOM_LLM|OLLAMA)"
```

Expected output:
```env
CUSTOM_LLM_BASE_URL=https://genailab.tcs.in
CUSTOM_LLM_MODEL=azure_ai/genailab-maas-DeepSeek-V3-0324
CUSTOM_LLM_API_KEY=sk-xxxxxxxxxxxx  # Should NOT be empty
CUSTOM_EMBEDDING_MODEL=azure/genailab-maas-text-embedding-3-large
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

## Switching Between Providers in the UI

### Documents Page
- Top right dropdown: Select "Custom API" or "Ollama"
- Upload your document

### Chat Page
- Top right dropdown: Select your preferred provider
- Both providers work with the same document store

---

## Common Issues

### "Custom LLM API not initialized"
❌ **Problem**: `CUSTOM_LLM_API_KEY` is empty in `.env`
✅ **Solution**: Either set a valid API key OR use Ollama

### "Ollama not initialized"
❌ **Problem**: Ollama server is not running
✅ **Solution**: Run `ollama serve` in a terminal

### "Connection refused" (Ollama)
❌ **Problem**: Ollama is not installed or not running
✅ **Solution**: Install Ollama and run `ollama serve`

### "404 Not Found" (Custom API)
❌ **Problem**: Wrong base URL or model name
✅ **Solution**: Verify URL and model in `.env` match your API setup

---

## Recommended Setup for Development

```bash
# 1. Use Ollama for local development
ollama pull llama3.2
ollama serve

# 2. Leave Custom API key empty in .env
CUSTOM_LLM_API_KEY=""

# 3. Select "Ollama" in the UI
```

This avoids any authentication issues and works completely offline!

---

## Production Setup

For production with Custom API:

1. Set a valid `CUSTOM_LLM_API_KEY` in `.env`
2. Ensure the backend can reach `https://genailab.tcs.in`
3. Test the connection before deploying
4. Set up proper error monitoring

---

## Need Help?

- Check backend logs: `tail -f backend.log`
- Check if API key is set: `echo $CUSTOM_LLM_API_KEY`
- Test Ollama: `ollama list`
- Restart everything: `./stop.sh && ./start.sh`
