# VNC Browser Streaming Implementation Plan

## 🎯 Objective

Enable real-time browser viewing in the Web Agent Arena by streaming live browser sessions from AWS Lambda to the Streamlit UI using VNC technology.

---

## 📋 Current State

**What Works:**
- ✅ Lambda executes Playwright with Chromium
- ✅ Screenshots captured at intervals
- ✅ Agent actions logged and displayed
- ✅ UI has iframe placeholders for browser sessions
- ✅ VNC Manager module created
- ✅ Lambda handler updated for VNC

**What's Missing:**
- ❌ Live browser session streaming
- ❌ VNC server in Lambda container (in progress)
- ❌ VNC client in Streamlit UI
- ❌ WebSocket connection between Lambda and UI

**⚠️ Implementation Deviation:**
- Using TigerVNC instead of x11vnc (x11vnc not available in AL2023 repos)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Agent A Panel          │ Agent B Panel               │  │
│  │ ┌──────────────────┐   │ ┌──────────────────┐        │  │
│  │ │ noVNC Client     │   │ │ noVNC Client     │        │  │
│  │ │ (WebSocket)      │   │ │ (WebSocket)      │        │  │
│  │ └────────┬─────────┘   │ └────────┬─────────┘        │  │
│  └──────────┼──────────────┴──────────┼──────────────────┘  │
└─────────────┼───────────────────────────┼───────────────────┘
              │                           │
              │ WebSocket                 │ WebSocket
              │                           │
┌─────────────▼───────────────────────────▼───────────────────┐
│              API Gateway (WebSocket)                        │
│  - Routes WebSocket connections                             │
│  - Manages session state                                    │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
┌─────────────▼───────────────────────────▼───────────────────┐
│            AWS Lambda (Docker Container)                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ VNC Server (x11vnc or TigerVNC)                        │ │
│  │   ↓                                                    │ │
│  │ Xvfb (Virtual Display :99)                            │ │
│  │   ↓                                                    │ │
│  │ Chromium Browser (controlled by Playwright)           │ │
│  │   - Agent executes web actions                        │ │
│  │   - Screen content streamed via VNC                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Technical Components

### 1. Lambda Container Updates

**Add to Dockerfile:**
```dockerfile
# Install VNC Server and Xvfb
RUN dnf install -y \
    xorg-x11-server-Xvfb \
    x11vnc \
    fluxbox \
    websockify \
    && dnf clean all

# Install noVNC for web access
RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC && \
    cd /opt/noVNC && \
    git checkout v1.4.0

# Set up VNC
RUN mkdir -p ~/.vnc && \
    x11vnc -storepasswd changeme ~/.vnc/passwd
```

### 2. Lambda Handler Updates

**New Functions:**
- `start_vnc_server()` - Initialize VNC server on virtual display
- `get_vnc_websocket_url()` - Return WebSocket URL for client connection
- `stop_vnc_server()` - Clean up VNC resources

### 3. API Gateway WebSocket

**Setup:**
- Create WebSocket API in API Gateway
- Routes: `$connect`, `$disconnect`, `$default`
- Integrate with Lambda for session management

### 4. Streamlit UI Updates

**noVNC Integration:**
```python
# components/vnc_viewer.py
def render_vnc_viewer(websocket_url: str, width: int = 800, height: int = 600):
    """
    Embed noVNC viewer for live browser session.
    """
    novnc_html = f"""
    <div id="novnc-container">
        <canvas id="noVNC_canvas"></canvas>
        <script src="https://cdn.jsdelivr.net/npm/novnc@1.4.0/app/ui.js"></script>
        <script>
            const rfb = new RFB(document.getElementById('noVNC_canvas'), 
                              '{websocket_url}');
        </script>
    </div>
    """
    st.components.v1.html(novnc_html, width=width, height=height)
```

---

## 🔨 Implementation Steps

### Phase 1: Lambda VNC Setup (Week 1)

#### Step 1.1: Update Dockerfile
**File:** `lambda/deploy_docker.sh`

```dockerfile
# Add after Chromium dependencies
RUN dnf install -y \
    xorg-x11-server-Xvfb \
    x11vnc \
    fluxbox \
    websockify \
    git \
    && dnf clean all

# Install noVNC
RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC && \
    cd /opt/noVNC && \
    git checkout v1.4.0 && \
    ln -s /opt/noVNC/vnc.html /opt/noVNC/index.html

# Configure VNC
ENV DISPLAY=:99
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080
RUN mkdir -p ~/.vnc
```

**Estimated Time:** 2 hours  
**Validation:** Docker builds successfully with VNC packages

#### Step 1.2: Create VNC Manager Module
**New File:** `lambda/vnc_manager.py`

```python
import subprocess
import os
import signal
import time
from typing import Optional

class VNCManager:
    """Manages VNC server lifecycle in Lambda."""
    
    def __init__(self, display: str = ":99", port: int = 5900):
        self.display = display
        self.port = port
        self.xvfb_process = None
        self.vnc_process = None
        self.websockify_process = None
    
    def start(self) -> bool:
        """Start Xvfb, VNC server, and websockify."""
        try:
            # Start Xvfb
            self.xvfb_process = subprocess.Popen([
                'Xvfb', self.display,
                '-screen', '0', '1920x1080x24',
                '-ac', '-nolisten', 'tcp'
            ])
            time.sleep(1)
            
            # Set DISPLAY env var
            os.environ['DISPLAY'] = self.display
            
            # Start x11vnc
            self.vnc_process = subprocess.Popen([
                'x11vnc',
                '-display', self.display,
                '-rfbport', str(self.port),
                '-forever',
                '-shared',
                '-nopw',  # No password for simplicity
                '-quiet'
            ])
            time.sleep(1)
            
            # Start websockify for web access
            self.websockify_process = subprocess.Popen([
                'websockify',
                '--web', '/opt/noVNC',
                '6080',
                f'localhost:{self.port}'
            ])
            
            return True
        except Exception as e:
            print(f"Failed to start VNC: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop all VNC-related processes."""
        for process in [self.websockify_process, self.vnc_process, self.xvfb_process]:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
    
    def get_websocket_url(self, public_url: str) -> str:
        """Return WebSocket URL for noVNC client."""
        return f"{public_url}/websockify"
```

**Estimated Time:** 3 hours  
**Validation:** Unit tests pass, VNC starts/stops correctly

#### Step 1.3: Update Lambda Handler
**File:** `lambda/handler.py`

```python
from vnc_manager import VNCManager

vnc_manager = None  # Global instance

def lambda_handler(event, context):
    global vnc_manager
    
    # ... existing code ...
    
    # Initialize VNC for agent execution
    if action == "execute":
        if not vnc_manager:
            vnc_manager = VNCManager()
            if not vnc_manager.start():
                return create_response(500, {
                    "status": "error",
                    "error": "Failed to start VNC server"
                })
        
        # Get VNC URL for response
        vnc_url = vnc_manager.get_websocket_url(
            os.environ.get('LAMBDA_FUNCTION_URL', 'http://localhost')
        )
        
        # Execute agent with VNC available
        result = execute_agent(...)
        result['vnc_url'] = vnc_url
        
        return create_response(200, result)
```

**Estimated Time:** 2 hours  
**Validation:** Lambda returns VNC URL in response

#### Step 1.4: Build and Deploy Updated Lambda
```bash
cd lambda
./deploy_docker.sh
# Wait for CodeBuild
# Test with health check
```

**Estimated Time:** 30 minutes + 20 min build time  
**Validation:** Lambda health check returns `vnc_available: true`

---

### Phase 2: API Gateway WebSocket (Week 1-2)

#### Step 2.1: Create API Gateway WebSocket API
**Location:** AWS Console → API Gateway

1. Create new **WebSocket API**
   - Name: `web-agent-vnc-streams`
   - Route Selection Expression: `$request.body.action`

2. Add Routes:
   - `$connect` → Lambda: `vnc-connection-handler`
   - `$disconnect` → Lambda: `vnc-disconnection-handler`
   - `$default` → Lambda: `vnc-message-handler`

3. Deploy:
   - Stage: `production`
   - Note WebSocket URL: `wss://abc123.execute-api.us-east-1.amazonaws.com/production`

**Estimated Time:** 1 hour  
**Validation:** WebSocket API created and accessible

#### Step 2.2: Create Connection Handler Lambda
**New File:** `lambda/websocket_handler.py`

```python
import json
import boto3

dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table('vnc-connections')

def connect_handler(event, context):
    """Handle new WebSocket connections."""
    connection_id = event['requestContext']['connectionId']
    
    # Store connection
    connections_table.put_item(Item={
        'connectionId': connection_id,
        'timestamp': int(time.time())
    })
    
    return {'statusCode': 200, 'body': 'Connected'}

def disconnect_handler(event, context):
    """Handle WebSocket disconnections."""
    connection_id = event['requestContext']['connectionId']
    
    # Remove connection
    connections_table.delete_item(Key={'connectionId': connection_id})
    
    return {'statusCode': 200, 'body': 'Disconnected'}

def message_handler(event, context):
    """Forward VNC messages to Lambda execution."""
    # Proxy VNC protocol messages
    # This is handled by websockify in the execution Lambda
    return {'statusCode': 200}
```

**Estimated Time:** 2 hours  
**Validation:** Connections tracked in DynamoDB

#### Step 2.3: Create DynamoDB Table
```bash
aws dynamodb create-table \
    --table-name vnc-connections \
    --attribute-definitions AttributeName=connectionId,AttributeType=S \
    --key-schema AttributeName=connectionId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

**Estimated Time:** 10 minutes  
**Validation:** Table created and accessible

---

### Phase 3: Streamlit UI Integration (Week 2)

#### Step 3.1: Create VNC Viewer Component
**New File:** `components/vnc_viewer.py`

```python
import streamlit as st
import streamlit.components.v1 as components

def render_vnc_viewer(websocket_url: str, width: int = 800, height: int = 600):
    """
    Render noVNC viewer for live browser session.
    
    Args:
        websocket_url: WebSocket URL for VNC connection
        width: Viewer width in pixels
        height: Viewer height in pixels
    """
    novnc_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Browser Session</title>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/novnc@1.4.0/app/styles/base.css">
    </head>
    <body>
        <div id="screen">
            <canvas id="noVNC_canvas"></canvas>
        </div>
        
        <script type="module">
            import RFB from 'https://cdn.jsdelivr.net/npm/novnc@1.4.0/core/rfb.js';
            
            const url = '{websocket_url}';
            const rfb = new RFB(document.getElementById('noVNC_canvas'), url);
            
            rfb.scaleViewport = true;
            rfb.resizeSession = false;
            
            rfb.addEventListener('connect', () => {{
                console.log('VNC connected');
            }});
            
            rfb.addEventListener('disconnect', () => {{
                console.log('VNC disconnected');
            }});
        </script>
        
        <style>
            body {{ margin: 0; padding: 0; background: #000; }}
            #screen {{ width: 100%; height: 100%; }}
            canvas {{ width: 100% !important; height: 100% !important; }}
        </style>
    </body>
    </html>
    """
    
    components.html(novnc_html, width=width, height=height, scrolling=False)
```

**Estimated Time:** 2 hours  
**Validation:** VNC viewer renders in Streamlit

#### Step 3.2: Update Arena Component
**File:** `components/arena.py`

```python
from components.vnc_viewer import render_vnc_viewer

def render_agent_panel(title: str, agent_status: dict, agent):
    """Render a panel for a single agent with Tool Calls (left) | Browser (right) layout."""
    st.markdown(f"### {title}: {agent_status['name']}")
    
    col_tools, col_browser = st.columns([1, 2])
    
    with col_tools:
        st.markdown("**🔧 Tool Calls**")
        # ... existing tool call display ...
    
    with col_browser:
        st.markdown("**🖥️ Browser Session**")
        st.markdown("---")
        
        # Check if we have VNC URL from Lambda
        vnc_url = agent_status.get('vnc_url')
        
        if vnc_url:
            # Show live VNC stream
            render_vnc_viewer(vnc_url, width=800, height=500)
        else:
            # Fallback to placeholder
            st.info("🔧 Connecting to browser session...")
```

**Estimated Time:** 1 hour  
**Validation:** VNC viewer shows in arena when VNC URL available

#### Step 3.3: Update Lambda Client
**File:** `utils/lambda_client.py`

```python
def invoke_agent_execution(self, agent_config, prompt, constraints):
    """Invoke Lambda function to execute an agent task."""
    payload = {
        "body": {
            "action": "execute",
            "agent_config": agent_config,
            "prompt": prompt,
            "constraints": constraints,
            "enable_vnc": True  # Request VNC streaming
        }
    }
    
    response = requests.post(self.function_url, json=payload, timeout=300)
    result = response.json()
    
    # Parse response
    body = result.get('body', {})
    if isinstance(body, str):
        body = json.loads(body)
    
    # Extract VNC URL if available
    vnc_url = body.get('vnc_url')
    if vnc_url:
        # Store for agent status updates
        self._vnc_urls[body.get('session_id')] = vnc_url
    
    return body
```

**Estimated Time:** 30 minutes  
**Validation:** VNC URL propagates from Lambda to UI

---

### Phase 4: Testing & Optimization (Week 2-3)

#### Step 4.1: Local Testing
```python
# Test VNC locally with Docker
docker run -it \
    -p 5900:5900 \
    -p 6080:6080 \
    your-lambda-image:latest \
    /bin/bash

# Inside container:
python3 -c "
from vnc_manager import VNCManager
vnc = VNCManager()
vnc.start()
# Open browser: http://localhost:6080
"
```

**Estimated Time:** 2 hours  
**Validation:** VNC accessible locally via browser

#### Step 4.2: Lambda Testing
```python
# Test event
{
  "body": {
    "action": "execute",
    "agent_config": {...},
    "prompt": "Go to example.com",
    "enable_vnc": true
  }
}
```

**Expected Response:**
```json
{
  "status": "success",
  "vnc_url": "wss://abc123.execute-api.us-east-1.amazonaws.com/production",
  "session_id": "xyz789",
  "result": {...}
}
```

**Estimated Time:** 2 hours  
**Validation:** VNC URL returned and accessible

#### Step 4.3: End-to-End Testing
1. Start race in Streamlit
2. Verify VNC viewers appear for both agents
3. Watch live browser sessions
4. Verify actions in real-time
5. Test multiple concurrent races

**Estimated Time:** 3 hours  
**Validation:** Full user flow works with live streaming

#### Step 4.4: Performance Optimization
- Add connection pooling
- Optimize VNC frame rate (10-15 FPS)
- Reduce bandwidth with compression
- Add reconnection logic
- Implement session timeouts

**Estimated Time:** 4 hours  
**Validation:** Smooth performance, low latency (<500ms)

---

## 📊 Resource Requirements

### AWS Costs (Estimated)

| Resource | Usage | Cost/Month |
|----------|-------|------------|
| Lambda (with VNC) | 100 races @ 120s each | $0.50 |
| API Gateway WebSocket | 100 connections @ 2 min | $0.03 |
| DynamoDB (connections) | 1,000 operations | $0.00 (free tier) |
| **Total** | | **~$1-2/month** |

### Lambda Configuration

- **Memory:** 3008 MB (increased for VNC server)
- **Timeout:** 300 seconds (5 minutes)
- **Ephemeral Storage:** 2048 MB
- **Concurrent Executions:** 10 (adjustable)

### Image Size Impact

- **Current:** ~1.5 GB
- **With VNC:** ~1.8 GB (+300 MB)
- **Build Time:** +5 minutes

---

## 🔄 Alternative Approaches

### Option A: Screenshot Polling (Simpler)
**Instead of VNC, take screenshots every 2 seconds**

**Pros:**
- Much simpler to implement (2-3 hours)
- No WebSocket complexity
- Lower bandwidth

**Cons:**
- Not real-time (2s delay)
- Higher Lambda costs (constant polling)
- Less smooth user experience

**Implementation:**
```python
# Lambda: Take screenshot every 2s
screenshots = []
while task_running:
    screenshot = page.screenshot()
    screenshots.append(upload_to_s3(screenshot))
    time.sleep(2)

# Streamlit: Poll for latest screenshot
st.image(get_latest_screenshot(session_id), use_column_width=True)
st_autorefresh(interval=2000)  # Refresh every 2s
```

### Option B: BrowserBase API (Fastest)
**Use BrowserBase's built-in streaming**

**Pros:**
- Already built and tested
- No infrastructure to maintain
- Professional-grade streaming
- Works out of the box

**Cons:**
- Monthly cost ($49-299)
- Dependency on third-party service
- Less customization

**Implementation:**
```python
# Replace Lambda with BrowserBase API
import browserbase

session = browserbase.create_session()
stream_url = session.get_live_view_url()

# In Streamlit
st.components.v1.iframe(stream_url, height=600)
```

### Option C: CloudFlare Tunnel (Hybrid)
**Use CloudFlare to expose Lambda VNC**

**Pros:**
- Simpler than API Gateway
- Better WebSocket handling
- Built-in DDoS protection

**Cons:**
- Additional service dependency
- Setup complexity

---

## 📅 Timeline Summary

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| **Phase 1** | Lambda VNC Setup | 1 week | Docker, CodeBuild |
| **Phase 2** | API Gateway WebSocket | 3-4 days | Phase 1 complete |
| **Phase 3** | Streamlit UI Integration | 2-3 days | Phase 2 complete |
| **Phase 4** | Testing & Optimization | 4-5 days | Phase 3 complete |
| **Total** | | **2-3 weeks** | Full-time work |

### Part-Time Schedule (10 hrs/week)
- **Week 1-2:** Lambda VNC setup
- **Week 3:** API Gateway setup
- **Week 4:** Streamlit integration
- **Week 5-6:** Testing and optimization
- **Total:** 5-6 weeks

---

## ✅ Success Criteria

### Must Have
- [ ] VNC server starts in Lambda
- [ ] WebSocket connection established
- [ ] Live browser visible in Streamlit
- [ ] Actions appear in real-time (<1s delay)
- [ ] Multiple concurrent sessions work
- [ ] Sessions clean up properly

### Nice to Have
- [ ] Reconnection on disconnect
- [ ] Bandwidth optimization
- [ ] Recording capability
- [ ] Session replay
- [ ] Mobile-friendly viewer

---

## 🚀 Quick Start (Recommended Path)

### For MVP (This Week)
**Use Screenshot Polling** - 3 hours of work
1. Lambda takes screenshot every 2s
2. Upload to S3 or return base64
3. Streamlit auto-refreshes image
4. Deploy and test

### For Production (Next Sprint)
**Implement Full VNC** - Follow Phase 1-4
1. Week 1: Lambda + VNC
2. Week 2: API Gateway + UI
3. Week 3: Testing + Polish

### For Enterprise (Later)
**Switch to BrowserBase** - 1 hour integration
1. Sign up for BrowserBase
2. Replace Lambda calls with BrowserBase API
3. Use their built-in viewer
4. Done!

---

## 📝 Next Steps

1. **Decide approach:**
   - Screenshot polling (fast, good enough)
   - Full VNC (professional, complex)
   - BrowserBase (easiest, $$$)

2. **Set timeline:**
   - MVP this week?
   - Full solution this month?
   - Enterprise later?

3. **Assign resources:**
   - Solo: 5-6 weeks part-time
   - Team: 2-3 weeks full-time
   - Outsource: 1-2 weeks

4. **Start with:**
   - Phase 1, Step 1.1 (Update Dockerfile)
   - OR Option A (Screenshot polling)
   - OR Option B (BrowserBase trial)

---

## 🤝 Support Resources

- **VNC Documentation:** https://github.com/LibVNC/x11vnc
- **noVNC GitHub:** https://github.com/novnc/noVNC
- **API Gateway WebSocket:** https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html
- **BrowserBase Docs:** https://docs.browserbase.com
- **Playwright Screenshots:** https://playwright.dev/docs/screenshots

---

## 💡 Recommendation

**For fastest time-to-value:**

1. **Now:** Deploy app with current functionality (working!)
2. **This Week:** Add screenshot polling (3 hours)
3. **Next Sprint:** Evaluate VNC vs BrowserBase based on:
   - User feedback
   - Usage volume
   - Budget constraints

**Screenshot polling gets you 80% of the value with 10% of the effort!**

