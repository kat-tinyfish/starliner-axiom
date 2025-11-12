# AWS Lambda Setup Checklist

Quick reference for creating your Lambda function via AWS Console.

## 📋 Pre-Setup Checklist

- [ ] AWS account created and logged in
- [ ] Have OpenAI API key ready
- [ ] Have Anthropic API key ready (optional for MVP)
- [ ] Have Google API key ready (optional for MVP)
- [ ] Have TinyFish API key ready (optional for MVP)
- [ ] Function code packaged (`function.zip` created)

### Create function.zip

```bash
cd lambda/
zip -r function.zip handler.py agent_executor.py
```

---

## 🚀 Console Setup Steps

### Step 1: Create Function (2 minutes)

1. [ ] Go to AWS Console → Lambda
2. [ ] Click **Create function**
3. [ ] Fill in:
   - **Function name**: `web-agent-executor`
   - **Runtime**: `Python 3.11`
   - **Architecture**: `x86_64`
4. [ ] Click **Create function**

### Step 2: Upload Code (1 minute)

1. [ ] In **Code source** section
2. [ ] Click **Upload from** → **.zip file**
3. [ ] Upload `function.zip`
4. [ ] Click **Save**
5. [ ] Wait for "Successfully updated"

### Step 3: Configure Memory & Timeout (1 minute)

1. [ ] Click **Configuration** tab
2. [ ] Click **General configuration**
3. [ ] Click **Edit**
4. [ ] Set **Memory**: `2048 MB`
5. [ ] Set **Timeout**: `5 min 0 sec`
6. [ ] Click **Save**

### Step 4: Add Environment Variables (2 minutes)

1. [ ] Click **Configuration** tab
2. [ ] Click **Environment variables**
3. [ ] Click **Edit**
4. [ ] Add these variables:

```
OPENAI_API_KEY = sk-...
ANTHROPIC_API_KEY = sk-ant-...
GOOGLE_API_KEY = AI...
TINYFISH_API_KEY = ...
```

5. [ ] Click **Save**

### Step 5: Enable Function URL (2 minutes)

1. [ ] Click **Configuration** tab
2. [ ] Click **Function URL**
3. [ ] Click **Create function URL**
4. [ ] Select **Auth type**: `NONE`
5. [ ] Check **Configure CORS**
   - **Allow origin**: `*`
   - **Allow methods**: `POST`
   - **Allow headers**: `content-type`
6. [ ] Click **Save**
7. [ ] **COPY THE FUNCTION URL** ← Important!

### Step 6: Test Function (2 minutes)

1. [ ] Click **Test** tab
2. [ ] Click **Create new event**
3. [ ] Name: `health-check`
4. [ ] Paste this JSON:

```json
{
  "body": "{\"action\": \"health_check\"}"
}
```

5. [ ] Click **Save**
6. [ ] Click **Test**
7. [ ] Verify status = `200` and status = `healthy`

---

## ✅ Post-Setup

### Update Your Project

1. [ ] Add Function URL to `.env`:

```bash
AWS_LAMBDA_FUNCTION_URL=https://your-url-here.lambda-url.us-east-1.on.aws/
```

2. [ ] Test from Streamlit app

### Verify It Works

Test with curl:

```bash
curl -X POST "YOUR_FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{"action":"health_check"}'
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Lambda function is running",
  "playwright_available": true
}
```

---

## 📊 Summary

**Total Setup Time**: ~10 minutes

**What You Have**:
- ✅ Lambda function deployed
- ✅ Public HTTPS endpoint
- ✅ API keys configured
- ✅ Function tested and working

**Next**: Integrate with your Streamlit app!

---

## 🔧 Troubleshooting

### Function URL not working?
- Check CORS settings
- Verify Auth type is NONE
- Look at CloudWatch logs

### Timeout errors?
- Increase timeout in Configuration
- Check if API keys are valid

### Import errors?
- Verify zip structure: `unzip -l function.zip`
- Should show `handler.py` and `agent_executor.py` at root

---

## 📚 Reference Docs

- Full setup guide: `AWS_CONSOLE_SETUP.md`
- Code documentation: `README.md`
- AWS CLI alternative: `deploy.sh`

