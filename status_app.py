import os
import secrets
import html
import psutil
from fastapi import FastAPI, Request, Response, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import docker

app = FastAPI(title="Parachi System Dashboard")

ACTIVE_SESSIONS = set()
COOKIE_NAME = "parachi_session"

BASIC_USER = "admin"
BASIC_PASS = "parachi1234"

def get_current_user(request: Request):
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id or session_id not in ACTIVE_SESSIONS:
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"})
    return "admin"

def get_docker_client():
    try:
        return docker.from_env()
    except Exception:
        return None

TARGET_CONTAINERS = [
    "bid_bot",
    "bid_backuper",
    "bid_transactions_report",
    "navasan-to-bale",
    "order-book",
    "parachi-auth-bot",
    "parachi-price-story-image",
    "parachi-price-updates",
    "update_handler",
    "status_dashboard"
]

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parachi Dashboard Login</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #050505;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        .login-card {
            background: #111111;
            border: 1px solid #222222;
            border-radius: 8px;
            padding: 32px;
            width: 100%;
            max-width: 380px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .login-title {
            font-size: 16px;
            font-weight: 800;
            letter-spacing: -0.5px;
            text-transform: uppercase;
            text-align: center;
        }
        .login-subtitle {
            font-size: 11px;
            color: #777777;
            text-align: center;
            font-family: monospace;
        }
        .input-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        label {
            font-size: 11px;
            color: #aaaaaa;
            font-family: monospace;
            text-transform: uppercase;
        }
        input {
            background: #000000;
            border: 1px solid #333333;
            color: #ffffff;
            padding: 10px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-family: monospace;
            outline: none;
        }
        input:focus { border-color: #ffffff; }
        .btn {
            background: #ffffff;
            color: #000000;
            border: none;
            padding: 12px;
            font-weight: 800;
            font-size: 12px;
            cursor: pointer;
            border-radius: 4px;
            font-family: monospace;
            text-transform: uppercase;
            margin-top: 8px;
            transition: background 0.15s ease;
        }
        .btn:hover { background: #cccccc; }
    </style>
</head>
<body>
    <form class="login-card" action="/login" method="POST">
        <div>
            <div class="login-title">PARACHI DASHBOARD</div>
            <div class="login-subtitle">MONOCHROME SYSTEM CONTROL PANEL</div>
        </div>
        <div class="input-group">
            <label>Username</label>
            <input type="text" name="username" required autofocus placeholder="admin">
        </div>
        <div class="input-group">
            <label>Password</label>
            <input type="password" name="password" required placeholder="••••••••">
        </div>
        <button type="submit" class="btn">SIGN IN ➔</button>
    </form>
</body>
</html>"""

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == BASIC_USER and password == BASIC_PASS:
        token = secrets.token_hex(16)
        ACTIVE_SESSIONS.add(token)
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key=COOKIE_NAME, value=token, httponly=True, max_age=86400*7)
        return response
    return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if token in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.remove(token)
    response = RedirectResponse(url="/login")
    response.delete_cookie(COOKIE_NAME)
    return response

@app.post("/api/action/{action}/{container_name}")
async def container_action(action: str, container_name: str, user: str = Depends(get_current_user)):
    client = get_docker_client()
    if not client:
        return JSONResponse({"success": False, "error": "Docker service unavailable"}, status_code=500)

    try:
        if container_name == "all":
            containers_to_act = [c for c in TARGET_CONTAINERS if c != "status_dashboard"]
            for name in containers_to_act:
                try:
                    c = client.containers.get(name)
                    if action == "restart": c.restart()
                    elif action == "stop": c.stop()
                    elif action == "start": c.start()
                except Exception:
                    pass
            return {"success": True, "message": f"{action.upper()} executed for ALL containers"}

        if container_name not in TARGET_CONTAINERS:
            return JSONResponse({"success": False, "error": "Invalid container name"}, status_code=400)

        container = client.containers.get(container_name)
        if action == "restart":
            container.restart()
        elif action == "stop":
            container.stop()
        elif action == "start":
            container.start()
        else:
            return JSONResponse({"success": False, "error": "Invalid action"}, status_code=400)
        return {"success": True, "message": f"{action.upper()} executed for {container_name}"}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/logs/{container_name}")
async def get_logs(container_name: str, user: str = Depends(get_current_user)):
    client = get_docker_client()
    if not client:
        return JSONResponse({"error": "Docker service unavailable"}, status_code=500)

    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=200).decode("utf-8", errors="replace")
        return {"container": container_name, "logs": logs}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parachi System Dashboard</title>
    <style>
        :root {
            --bg: #050505;
            --surface: #111111;
            --border: #222222;
            --border-hover: #444444;
            --text-main: #ffffff;
            --text-muted: #888888;
            --running-fg: #ffffff;
            --running-bg: #222222;
            --stopped-fg: #777777;
            --stopped-bg: #1a1a1a;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            padding: 20px;
            min-height: 100vh;
        }

        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 16px;
        }

        .brand {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .brand-title {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: -0.5px;
            text-transform: uppercase;
        }

        .brand-subtitle {
            font-size: 11px;
            color: var(--text-muted);
            font-family: monospace;
        }

        .nav-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .telemetry-bar {
            display: flex;
            gap: 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 12px 18px;
            border-radius: 6px;
            margin-bottom: 24px;
            font-size: 12px;
            font-family: monospace;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
        }

        .metric-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .metric-label { color: var(--text-muted); }
        .metric-val { font-weight: 700; color: #ffffff; }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 20px;
        }

        @media (max-width: 600px) {
            body { padding: 12px; }
            .dashboard-grid { grid-template-columns: 1fr; }
            .telemetry-bar { flex-direction: column; align-items: flex-start; gap: 8px; }
        }

        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            transition: border-color 0.2s ease;
        }

        .card:hover { border-color: var(--border-hover); }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }

        .service-title {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot { font-size: 10px; }
        .dot-running { color: #ffffff; }
        .dot-stopped { color: #444444; }

        .service-name {
            font-size: 14px;
            font-weight: 700;
            font-family: monospace;
        }

        .badge {
            font-size: 10px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 3px;
            text-transform: uppercase;
            font-family: monospace;
            letter-spacing: 0.5px;
        }

        .badge-running {
            background: var(--running-bg);
            color: var(--running-fg);
            border: 1px solid #444;
        }

        .badge-stopped {
            background: var(--stopped-bg);
            color: var(--stopped-fg);
            border: 1px solid var(--border);
        }

        .info-row {
            font-size: 11px;
            color: var(--text-muted);
            font-family: monospace;
            margin-bottom: 12px;
        }

        .log-container {
            position: relative;
            margin-bottom: 12px;
        }

        .log-box, .modal-log-box {
            background: #000000;
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 12px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 11px;
            line-height: 1.45;
            color: #d0d0d0;
            height: 180px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;

            -ms-overflow-style: none;
            scrollbar-width: none;
        }

        .log-box::-webkit-scrollbar, .modal-log-box::-webkit-scrollbar {
            display: none;
        }

        .log-line-err { color: #ff6b6b; font-weight: 700; }
        .log-line-warn { color: #ffd166; }
        .log-line-ok { color: #51cf66; }

        .card-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .action-btn-group {
            display: flex;
            gap: 6px;
        }

        .btn {
            border: none;
            padding: 8px 14px;
            font-weight: 700;
            font-size: 11px;
            cursor: pointer;
            border-radius: 4px;
            font-family: monospace;
            text-transform: uppercase;
            transition: all 0.15s ease;
            text-decoration: none;
        }

        .btn-solid { background: #ffffff; color: #000000; }
        .btn-solid:hover { background: #cccccc; }

        .btn-outline { background: transparent; color: #ffffff; border: 1px solid #333333; }
        .btn-outline:hover { border-color: #ffffff; background: #111111; }

        .btn-subtle { background: #181818; color: #aaaaaa; border: 1px solid var(--border); }
        .btn-subtle:hover { color: #ffffff; border-color: #555555; }

        .btn-danger { background: #220000; color: #ff5555; border: 1px solid #550000; }
        .btn-danger:hover { background: #440000; color: #ffffff; }

        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.88);
            backdrop-filter: blur(4px);
            z-index: 9999;
            padding: 24px;
            align-items: center;
            justify-content: center;
        }

        .modal-content {
            background: #0d0d0d;
            border: 1px solid var(--border-hover);
            border-radius: 8px;
            width: 100%;
            max-width: 1100px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            padding: 20px;
            gap: 16px;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title { font-size: 15px; font-weight: 700; font-family: monospace; }
        .modal-log-box { flex: 1; height: auto; font-size: 12px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="brand">
            <div class="brand-title">PARACHI SYSTEM CONTROL PANEL</div>
            <div class="brand-subtitle">MONOCHROME DOCKER ORCHESTRATION & TELEMETRY</div>
        </div>
        <div class="nav-controls">
            <button class="btn btn-outline" onclick="doAction('restart', 'all')">🔄 RESTART ALL</button>
            <button class="btn btn-danger" onclick="doAction('stop', 'all')">🛑 STOP ALL</button>
            <button class="btn btn-solid" onclick="location.reload()">REFRESH ↻</button>
            <a class="btn btn-subtle" href="/logout">LOGOUT</a>
        </div>
    </div>

    <div class="telemetry-bar">
        <div class="metric-item">
            <span class="metric-label">CONTAINERS:</span>
            <span class="metric-val">__TOTAL_RUNNING__ RUNNING / __TOTAL_CONTAINERS__ TOTAL</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">CPU USAGE:</span>
            <span class="metric-val">__CPU_PERCENT__% (__CPU_CORES__ CORES)</span>
        </div>
        <div class="metric-item">
            <span class="metric-label">HOST RAM:</span>
            <span class="metric-val">__RAM_USED_GB__ GB / __RAM_TOTAL_GB__ GB (__RAM_PERCENT__%)</span>
        </div>
    </div>

    <div class="dashboard-grid">
        __CARDS_HTML__
    </div>

    <div class="modal-overlay" id="logModal" onclick="closeModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle">FULL LOGS</div>
                <div class="action-btn-group">
                    <button class="btn btn-subtle" onclick="copyModalLogs()">📋 COPY LOGS</button>
                    <button class="btn btn-outline" onclick="hideModal()">✕ CLOSE</button>
                </div>
            </div>
            <pre class="modal-log-box" id="modalLogContent">Loading logs...</pre>
        </div>
    </div>

    <script>
        function colorizeText(text) {
            if (!text) return "";
            const lines = text.split('\n');
            return lines.map(line => {
                const lower = line.toLowerCase();
                if (lower.includes('error') || lower.includes('exception') || lower.includes('traceback') || lower.includes('failed') || lower.includes('nameerror')) {
                    return `<span class="log-line-err">${line}</span>`;
                } else if (lower.includes('warn') || lower.includes('warning')) {
                    return `<span class="log-line-warn">${line}</span>`;
                } else if (lower.includes('success') || lower.includes('started') || lower.includes('✓') || lower.includes('active') || lower.includes('bot started')) {
                    return `<span class="log-line-ok">${line}</span>`;
                }
                return line;
            }).join('\n');
        }

        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.log-box').forEach(box => {
                box.innerHTML = colorizeText(box.innerHTML);
            });
        });

        async function doAction(action, name) {
            const targetStr = name === 'all' ? 'ALL CONTAINERS' : `container '${name}'`;
            if (!confirm(`Are you sure you want to ${action.toUpperCase()} ${targetStr}?`)) return;
            
            try {
                const res = await fetch(`/api/action/${action}/${name}`, { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    alert(`✓ ${data.message}`);
                    location.reload();
                } else {
                    alert(`❌ Error: ${data.error}`);
                }
            } catch (err) {
                alert(`❌ Request failed: ${err}`);
            }
        }

        function copyLogs(name) {
            const el = document.getElementById(`logs-${name}`);
            if (!el) return;
            navigator.clipboard.writeText(el.innerText).then(() => {
                const btn = document.getElementById(`copy-btn-${name}`);
                if (btn) {
                    const orig = btn.innerText;
                    btn.innerText = "COPIED!";
                    setTimeout(() => btn.innerText = orig, 1500);
                }
            });
        }

        async function expandLogs(name) {
            document.getElementById('modalTitle').innerText = `FULL RECENT LOGS — ${name.toUpperCase()}`;
            const content = document.getElementById('modalLogContent');
            content.innerText = "Fetching live logs from Docker daemon...";
            document.getElementById('logModal').style.display = 'flex';

            try {
                const res = await fetch(`/api/logs/${name}`);
                const data = await res.json();
                content.innerHTML = colorizeText(htmlEscape(data.logs || "(No logs returned)"));
                content.scrollTop = content.scrollHeight;
            } catch (err) {
                content.innerText = `Error loading logs: ${err}`;
            }
        }

        function htmlEscape(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        function copyModalLogs() {
            const content = document.getElementById('modalLogContent');
            if (content) {
                navigator.clipboard.writeText(content.innerText);
                alert("✓ Logs copied to clipboard!");
            }
        }

        function hideModal() {
            document.getElementById('logModal').style.display = 'none';
        }

        function closeModal(e) {
            if (e.target.id === 'logModal') hideModal();
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') hideModal();
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(get_current_user)):
    client = get_docker_client()
    
    cards_html = ""
    total_running = 0
    total_stopped = 0

    if client:
        for name in TARGET_CONTAINERS:
            try:
                container = client.containers.get(name)
                c_status = container.status.upper()
                is_running = (c_status == "RUNNING")
                
                if is_running: total_running += 1
                else: total_stopped += 1

                badge_class = "badge-running" if is_running else "badge-stopped"
                dot_class = "dot-running" if is_running else "dot-stopped"
                
                try:
                    raw_logs = container.logs(tail=35).decode("utf-8", errors="replace")
                    logs_safe = html.escape(raw_logs.strip()) if raw_logs.strip() else "(No recent log output)"
                except Exception as log_err:
                    logs_safe = f"Error fetching logs: {html.escape(str(log_err))}"

                created_time = container.attrs.get("Created", "")[:19].replace("T", " ")

                if is_running:
                    stop_start_btn = f'<button class="btn btn-sm btn-outline" onclick="doAction(\'stop\', \'{name}\')">⏹ STOP</button>'
                else:
                    stop_start_btn = f'<button class="btn btn-sm btn-solid" onclick="doAction(\'start\', \'{name}\')">▶ START</button>'

                cards_html += f"""
                <div class="card" id="card-{name}">
                    <div class="card-header">
                        <div class="service-title">
                            <span class="status-dot {dot_class}">●</span>
                            <span class="service-name">{name}</span>
                        </div>
                        <span class="badge {badge_class}">{c_status}</span>
                    </div>

                    <div class="info-row">
                        ID: {container.short_id} | CREATED: {created_time}
                    </div>

                    <div class="log-container">
                        <pre class="log-box" id="logs-{name}">{logs_safe}</pre>
                    </div>

                    <div class="card-actions">
                        <div class="action-btn-group">
                            {stop_start_btn}
                            <button class="btn btn-sm btn-outline" onclick="doAction('restart', '{name}')">🔄 RESTART</button>
                        </div>
                        <div class="action-btn-group">
                            <button class="btn btn-sm btn-subtle" onclick="copyLogs('{name}')" id="copy-btn-{name}">📋 COPY</button>
                            <button class="btn btn-sm btn-subtle" onclick="expandLogs('{name}')">⤢ EXPAND</button>
                        </div>
                    </div>
                </div>
                """
            except Exception as e:
                total_stopped += 1
                cards_html += f"""
                <div class="card card-disabled">
                    <div class="card-header">
                        <span class="service-name">● {name}</span>
                        <span class="badge badge-stopped">NOT FOUND</span>
                    </div>
                    <div class="info-row">STATUS: UNREACHABLE</div>
                    <div class="log-box">Container does not exist or has been removed.</div>
                    <div class="card-actions">
                        <button class="btn btn-sm btn-solid" onclick="location.reload()">RE-CHECK ↻</button>
                    </div>
                </div>
                """
    else:
        cards_html = "<div class='card'><div class='log-box'>Docker socket unreachable (/var/run/docker.sock).</div></div>"

    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count(logical=True)
        ram = psutil.virtual_memory()
        ram_used_gb = round(ram.used / (1024**3), 2)
        ram_total_gb = round(ram.total / (1024**3), 2)
        ram_percent = ram.percent
    except Exception:
        cpu_percent, cpu_cores, ram_used_gb, ram_total_gb, ram_percent = 0, 0, 0, 0, 0

    page_html = HTML_TEMPLATE.replace("__TOTAL_RUNNING__", str(total_running))                             .replace("__TOTAL_CONTAINERS__", str(len(TARGET_CONTAINERS)))                             .replace("__CPU_PERCENT__", str(cpu_percent))                             .replace("__CPU_CORES__", str(cpu_cores))                             .replace("__RAM_USED_GB__", str(ram_used_gb))                             .replace("__RAM_TOTAL_GB__", str(ram_total_gb))                             .replace("__RAM_PERCENT__", str(ram_percent))                             .replace("__CARDS_HTML__", cards_html)

    return page_html
