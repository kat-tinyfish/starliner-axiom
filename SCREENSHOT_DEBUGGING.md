# Screenshot Debugging Guide

## 🔍 **Issue: Screenshots Not Displaying**

From the production deployment, **neither GPT-4 nor TinyFish** are showing screenshots in the arena UI.

---

## ✅ **What's Working:**

1. **TinyFish Output Fixed** ✅
   - Changed from 'response' key to 'summary' key
   - Now properly displays extracted data
   - Commit: ea2d3fa

2. **Race Execution** ✅
   - Both agents complete successfully
   - Checkpoints tracked
   - Tool calls logged
   - Outputs displayed

---

## ❌ **What's Not Working:**

### **Problem:** Placeholder Text Shown
```
📸 Browser screenshots will appear here when race starts
Updates every 2 seconds
```

### **Expected:** Live screenshots of browser session

---

## 🔍 **Investigation Checklist:**

### **1. TinyFish (Expected Behavior)**
- ✅ TinyFish API doesn't provide screenshots
- ✅ This is documented as an API limitation
- ✅ Would need to proxy through BrowserBase to get screenshots

### **2. GPT-4/Claude (Should Work)**
- ❓ Uses BrowserBase via BrowserToolExecutor
- ❓ Code exists to capture screenshots
- ❓ But not appearing in UI

---

## 🔧 **Technical Investigation:**

### **Code Flow:**
1. `BrowserToolExecutor.execute_tool()` calls `_capture_screenshot()`
2. Returns base64 encoded screenshot in `result.screenshot`
3. Agent appends to `self._screenshots` list
4. `AgentResult.screenshots` passed to orchestrator
5. `RaceOrchestrator.get_agent_status()` includes screenshots
6. `arena.py` retrieves screenshots from agent_status
7. Displays using `st.image()`

### **Check Points:**

#### **A. Is BrowserBase Connected?**
- Check: `agents/browser_executor.py` line 60-80
- Look for: Connection to `browserbase_connect_url`
- Error: "BrowserBase connection required" if missing

#### **B. Are Screenshots Being Captured?**
- Check: `agents/browser_executor.py` line 296-302
- Look for: `self.page.screenshot()` calls
- Error: Would print "Failed to capture screenshot"

#### **C. Are Screenshots in Result?**
- Check: `agents/implementations/openai_agent.py` line 153-159
- Look for: `if result.screenshot:` condition
- Debug: Add print statement to see if screenshots exist

#### **D. Are Screenshots in Agent Status?**
- Check: `utils/race_orchestrator.py` line 155, 162
- Look for: `self.result_a.screenshots`
- Debug: Print length of screenshots list

#### **E. Is UI Retrieving Screenshots?**
- Check: `components/arena.py` line 362
- Look for: `agent_status.get("screenshots", [])`
- Debug: Print what agent_status contains

---

## 🐛 **Debug Commands:**

### **1. Test BrowserBase Connection**
```python
# In agents/browser_executor.py, line 65
print(f"🔗 Connecting to BrowserBase: {self.connect_url[:60]}...")
print(f"✅ Connected! Browser contexts: {len(self.browser.contexts)}")
```

### **2. Check Screenshot Capture**
```python
# In agents/browser_executor.py, line 300
screenshot_bytes = await self.page.screenshot(full_page=full_page)
print(f"📸 Screenshot captured: {len(screenshot_bytes)} bytes")
return base64.b64encode(screenshot_bytes).decode()
```

### **3. Verify Screenshot in Result**
```python
# In agents/implementations/openai_agent.py, line 153
if result.screenshot:
    print(f"📸 Screenshot available: {len(result.screenshot)} chars")
    self._screenshots.append({...})
else:
    print("⚠️ No screenshot in result!")
```

### **4. Check AgentResult**
```python
# In agents/implementations/openai_agent.py, line 210
print(f"📸 Total screenshots in result: {len(self._screenshots)}")
return AgentResult(
    success=True,
    screenshots=self._screenshots
)
```

### **5. Verify in Orchestrator**
```python
# In utils/race_orchestrator.py, line 155
screenshots_a = self.result_a.screenshots if self.result_a and hasattr(self.result_a, 'screenshots') and self.result_a.screenshots else []
print(f"📸 Agent A screenshots: {len(screenshots_a)}")
```

---

## 🎯 **Likely Causes:**

### **Most Likely:**
1. **BrowserBase Session Closing Early**
   - Session closes after first tool call
   - Screenshots can't be captured from closed session
   - Related to "Target page, context or browser has been closed" errors

2. **Screenshot Not Being Captured**
   - `_capture_screenshot()` is called but fails silently
   - Exception caught but screenshot remains None
   - Need to check actual error messages

3. **Timing Issue**
   - Screenshots captured but not yet in agent_status when UI renders
   - Need to check if polling is working correctly

### **Less Likely:**
4. **UI Display Issue**
   - Screenshots exist but not rendering in Streamlit
   - Base64 decoding issue
   - Image format issue

---

## 🔬 **Next Steps:**

1. **Add Debug Logging**
   - Add print statements at each checkpoint above
   - Run local test race
   - Check console output

2. **Test Isolated Screenshot**
   - Create minimal test script
   - Just connect to BrowserBase and capture screenshot
   - Verify screenshot capture works

3. **Check Browser Lifecycle**
   - Investigate when/why browser closes
   - Check if screenshots are being captured before close
   - May need to adjust BrowserBase session management

4. **UI Debugging**
   - Add st.write() to show raw screenshot data
   - Verify data reaches the UI component
   - Check if image decoding works

---

## 📝 **Workarounds:**

### **Short-term:**
- Note in UI that screenshots are coming soon
- Focus on tool calls and output for comparison
- Add text-based progress indicators

### **Medium-term:**
- Investigate BrowserBase session lifecycle
- Fix screenshot capture timing
- Add retry logic for failed screenshots

### **Long-term:**
- Consider alternative screenshot approach
- Proxy TinyFish through BrowserBase for consistency
- Implement direct CDP screenshot capture

---

## 📊 **Testing Matrix:**

| Agent | Browser | Expected Screenshots | Actual | Status |
|-------|---------|---------------------|--------|--------|
| GPT-4 | BrowserBase | ✅ Yes | ❌ No | 🔍 Debug |
| Claude | BrowserBase | ✅ Yes | ❌ No | 🔍 Debug |
| Gemini | BrowserBase | ✅ Yes | ⚠️ Untested | ⏳ Pending |
| TinyFish | TinyFish API | ❌ No | ❌ No | ✅ Expected |

---

**Created:** 2025-11-13
**Status:** Under Investigation
**Priority:** Medium (functionality works, visual comparison affected)

