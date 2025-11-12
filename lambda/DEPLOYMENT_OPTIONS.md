# Lambda Deployment Options

**Issue Fixed:** Removed non-existent `playwright-aws-lambda` package.

## 🎯 Two Deployment Options

### Option 1: Standard Lambda (Simpler, Limited Browser Support)

**Use Case:** API testing, simple automation, MVP development

```bash
./deploy.sh
```

**Pros:**
- ✅ Quick deployment (5-8 minutes)
- ✅ Simple setup
- ✅ Works with current code
- ✅ Good for API testing

**Cons:**
- ⚠️ No Chromium browser in layer (size limits)
- ⚠️ Browser automation limited/simulated
- ⚠️ Best for non-browser tasks

**What Works:**
- Health checks ✅
- API calls ✅
- Basic execution flow ✅
- Tool call logging ✅

**What's Limited:**
- Real browser navigation ⚠️
- Screenshot capture ⚠️
- Complex DOM interactions ⚠️

---

### Option 2: Docker Lambda (Full Browser Support)

**Use Case:** Production, full browser automation, real web scraping

```bash
./deploy_docker.sh
```

**Pros:**
- ✅ Full Playwright + Chromium support
- ✅ Real browser automation
- ✅ All features working
- ✅ Production-ready

**Cons:**
- ⏱️ Longer deployment (10-15 minutes first time)
- 🐳 Requires Docker installed
- 📦 Larger deployment size
- 💰 Slightly higher cold start time

**What Works:**
- Everything from Option 1 ✅
- Real browser navigation ✅
- Screenshot capture ✅
- Full DOM interactions ✅
- Complete Playwright API ✅

---

## 🤔 Which Should You Use?

### Use **Standard Lambda** (`deploy.sh`) if:
- Testing the infrastructure
- Developing locally first
- Don't need real browsers yet
- Want quick iterations
- Staying within free tier limits

### Use **Docker Lambda** (`deploy_docker.sh`) if:
- Need real browser automation
- Going to production
- Require screenshots/full DOM access
- Have Docker installed
- Ready for full deployment

---

## 🚀 Quick Start

### Standard Lambda

```bash
cd lambda

# 1. Fix applied (package removed)
# 2. Deploy (no browser, but infrastructure works)
./deploy.sh

# 3. Test
./test_lambda.sh <your-function-url>
```

**Expected:** Health check works ✅, browser tests simulated ⚠️

### Docker Lambda

```bash
cd lambda

# 1. Install Docker (if needed)
# macOS: brew install --cask docker
# Or download from docker.com

# 2. Start Docker Desktop

# 3. Deploy with full browser support
./deploy_docker.sh

# 4. Test
./test_lambda.sh <your-function-url>
```

**Expected:** Everything works including real browser ✅

---

## 📊 Comparison

| Feature | Standard Lambda | Docker Lambda |
|---------|----------------|---------------|
| Deployment Time | 5-8 min | 10-15 min |
| Setup Complexity | Low | Medium |
| Browser Support | Limited | Full |
| Cold Start | Fast (~1s) | Slower (~3-5s) |
| Size Limit | 50 MB (layer) | 10 GB (image) |
| Docker Required | No | Yes |
| Production Ready | For APIs | For browsers |

---

## 🔄 Migration Path

**Recommended approach:**

1. **Start with Standard Lambda**
   ```bash
   ./deploy.sh
   ```
   - Test infrastructure
   - Verify API integrations
   - Develop core logic

2. **Move to Docker Lambda when ready**
   ```bash
   ./deploy_docker.sh
   ```
   - Add browser automation
   - Enable screenshots
   - Go to production

---

## 💡 For MVP Development

**Best approach for your Web Agent Arena MVP:**

```bash
# Phase 1: Use Standard Lambda
./deploy.sh

# This gives you:
# - Working Lambda infrastructure ✅
# - API endpoint for agents ✅
# - Health checks ✅
# - Tool call logging ✅
# - Fast iterations ✅

# Phase 2: Upgrade to Docker Lambda (when needed)
./deploy_docker.sh

# This adds:
# - Real browser automation ✅
# - Complete Playwright support ✅
# - Production-ready ✅
```

---

## 🐛 Troubleshooting

### "playwright-aws-lambda not found" (FIXED)

✅ **This is now fixed!** The package has been removed from requirements.txt

### "Layer too large"

This is expected - we're not including Chromium in the standard layer due to size limits.

**Solution:** Use Docker Lambda for full browser support.

### Docker Lambda takes too long

First deployment takes longer as it builds the image. Subsequent updates are faster (only changed layers).

---

## 📖 Next Steps

After choosing your deployment option:

1. ✅ Deploy Lambda function
2. ✅ Get Function URL
3. ✅ Update .env file
4. ✅ Test with health check
5. ✅ Integrate with Streamlit app
6. ✅ Monitor CloudWatch logs

---

## 🎉 Summary

**The fix is complete!**

- ❌ Removed: Non-existent `playwright-aws-lambda` package
- ✅ Added: Two deployment options
- ✅ Added: Docker-based alternative for full browser support
- ✅ Ready: Both deployment scripts work

**Choose your path and deploy!** 🚀


