"""
Dharmic Agent Web Dashboard

Simple Flask dashboard for monitoring and interacting with the agent.

Features:
- Agent status display (alive, heartbeat)
- Recent email conversations
- Memory statistics
- Telos display
- Manual message input
- Conversation history
- System health metrics

Usage:
    python3 web_dashboard.py
    # Visit http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import Dharmic Agent
import sys
sys.path.insert(0, str(Path(__file__).parent))
from dharmic_agent import DharmicAgent
from runtime import DharmicRuntime

app = Flask(__name__,
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static"))

# Global agent instance
agent: Optional[DharmicAgent] = None
runtime: Optional[DharmicRuntime] = None


def init_agent():
    """Initialize the agent and runtime."""
    global agent, runtime
    if agent is None:
        agent = DharmicAgent()
        runtime = DharmicRuntime(agent, heartbeat_interval=3600)  # 1 hour
    return agent, runtime


@app.route('/')
def index():
    """Main dashboard page."""
    agent, _ = init_agent()

    status = agent.get_status()
    telos = agent.telos.telos

    # Get memory stats
    memory_stats = {}
    for layer in agent.strange_memory.layers.keys():
        count = len(agent.strange_memory._read_recent(layer, 1000))
        memory_stats[layer] = count

    # Get deep memory stats if available
    deep_memory_stats = {}
    if agent.deep_memory is not None:
        deep_memory_stats = agent.get_deep_memory_status()

    # Get recent observations
    recent_obs = agent.strange_memory._read_recent("observations", 10)

    # Get recent meta-observations
    recent_meta = agent.strange_memory._read_recent("meta_observations", 5)

    return render_template('dashboard.html',
                         status=status,
                         telos=telos,
                         memory_stats=memory_stats,
                         deep_memory_stats=deep_memory_stats,
                         recent_observations=recent_obs,
                         recent_meta_observations=recent_meta)


@app.route('/api/status')
def api_status():
    """API endpoint for agent status."""
    agent, runtime = init_agent()

    status = agent.get_status()

    # Add runtime info if available
    if runtime:
        status['runtime'] = {
            'heartbeat_interval': runtime.heartbeat_interval,
            'running': runtime.running,
            'active_specialists': list(runtime.specialists.keys())
        }

    # Add last heartbeat info
    heartbeat_log = Path(__file__).parent.parent.parent / "logs" / f"runtime_{datetime.now().strftime('%Y%m%d')}.log"
    if heartbeat_log.exists():
        with open(heartbeat_log) as f:
            lines = f.readlines()
            # Find last heartbeat
            for line in reversed(lines):
                if "Heartbeat:" in line:
                    status['last_heartbeat'] = line.strip()
                    break

    return jsonify(status)


@app.route('/api/healthcheck')
def api_healthcheck():
    """Run and return the system health check."""
    agent, _ = init_agent()
    result = agent.run_healthcheck()
    return jsonify(result)


@app.route('/api/message', methods=['POST'])
def api_message():
    """Send a message to the agent."""
    agent, _ = init_agent()

    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id', 'web')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        response = agent.run(message, session_id=session_id)
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/memory')
def api_memory():
    """Get memory statistics."""
    agent, _ = init_agent()

    stats = {}

    # Strange loop memory
    for layer in agent.strange_memory.layers.keys():
        recent = agent.strange_memory._read_recent(layer, 100)
        stats[layer] = {
            'count': len(recent),
            'recent': recent[-5:] if recent else []
        }

    # Deep memory
    if agent.deep_memory is not None:
        stats['deep_memory'] = agent.get_deep_memory_status()

    return jsonify(stats)


@app.route('/api/telos')
def api_telos():
    """Get current telos."""
    agent, _ = init_agent()
    return jsonify(agent.telos.telos)


@app.route('/api/vault/search')
def api_vault_search():
    """Search the vault."""
    agent, _ = init_agent()

    query = request.args.get('q', '')
    max_results = int(request.args.get('max', 10))

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    results = agent.search_lineage(query, max_results=max_results)
    return jsonify({'results': results, 'count': len(results)})


@app.route('/api/conversations')
def api_conversations():
    """Get recent conversations from email logs."""
    email_log_dir = Path(__file__).parent.parent.parent / "logs" / "email"

    conversations = []

    if email_log_dir.exists():
        # Read recent email logs
        log_files = sorted(email_log_dir.glob("email_*.log"), reverse=True)[:7]  # Last 7 days

        for log_file in log_files:
            with open(log_file) as f:
                lines = f.readlines()
                for line in lines:
                    if "Processing message from" in line or "Sent response to" in line:
                        conversations.append({
                            'timestamp': line[:19].strip('[]'),
                            'event': line[20:].strip()
                        })

    return jsonify({'conversations': conversations[-20:]})  # Last 20 events


@app.route('/api/heartbeat')
def api_heartbeat():
    """Trigger a manual heartbeat check."""
    agent, runtime = init_agent()

    if runtime is None:
        return jsonify({'error': 'Runtime not initialized'}), 500

    # Run heartbeat synchronously (for simple implementation)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(runtime.heartbeat())
    loop.close()

    return jsonify(result)


@app.route('/api/introspect')
def api_introspect():
    """Get full introspection report."""
    agent, _ = init_agent()
    report = agent.introspect()
    return jsonify({'report': report})


@app.route('/templates/<path:filename>')
def serve_template(filename):
    """Serve template files (for debugging)."""
    template_dir = Path(__file__).parent / "templates"
    return send_from_directory(template_dir, filename)


def create_templates():
    """Create HTML templates if they don't exist."""
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    # Main dashboard template
    dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dharmic Agent Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            color: #ff6b35;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #888;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
        }
        .card h2 {
            color: #ff6b35;
            font-size: 1.2em;
            margin-bottom: 15px;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-alive { background: #4ade80; }
        .status-warning { background: #fbbf24; }
        .status-error { background: #ef4444; }
        .telos-section { margin-bottom: 15px; }
        .telos-section h3 {
            color: #a78bfa;
            font-size: 1em;
            margin-bottom: 8px;
        }
        .telos-section ul {
            list-style: none;
            padding-left: 20px;
        }
        .telos-section li:before {
            content: "→ ";
            color: #ff6b35;
        }
        .stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #2a2a2a;
        }
        .stat:last-child { border-bottom: none; }
        .stat-label { color: #888; }
        .stat-value { color: #4ade80; font-weight: bold; }
        .observation {
            padding: 10px;
            margin-bottom: 8px;
            background: #0f0f0f;
            border-left: 3px solid #ff6b35;
            font-size: 0.9em;
        }
        .observation-time {
            color: #666;
            font-size: 0.8em;
            margin-bottom: 4px;
        }
        .meta-obs {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            margin-bottom: 8px;
            background: #0f0f0f;
        }
        .quality-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .quality-present { background: #4ade80; color: #000; }
        .quality-expansive { background: #a78bfa; color: #000; }
        .quality-contracted { background: #fbbf24; color: #000; }
        .quality-uncertain { background: #888; color: #000; }
        .message-input {
            width: 100%;
            padding: 12px;
            background: #0f0f0f;
            border: 1px solid #333;
            color: #e0e0e0;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            margin-bottom: 10px;
            resize: vertical;
            min-height: 100px;
        }
        .btn {
            background: #ff6b35;
            color: #fff;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }
        .btn:hover { background: #e55a25; }
        .btn:disabled { background: #555; cursor: not-allowed; }
        .response {
            margin-top: 15px;
            padding: 15px;
            background: #0f0f0f;
            border-left: 3px solid #4ade80;
            white-space: pre-wrap;
            font-size: 0.9em;
        }
        .loading {
            color: #fbbf24;
            font-style: italic;
        }
        .refresh-btn {
            float: right;
            background: #333;
            padding: 5px 10px;
            font-size: 0.8em;
        }
        .refresh-btn:hover { background: #444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🕉️ Dharmic Agent Core</h1>
        <p class="subtitle">Telos: {{ telos.ultimate.aim }} | Presence over performance</p>

        <div class="grid">
            <!-- Status Card -->
            <div class="card">
                <h2>
                    <span class="status-indicator status-alive"></span>
                    System Status
                </h2>
                <div class="stat">
                    <span class="stat-label">Agent Name</span>
                    <span class="stat-value">{{ status.name }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Ultimate Telos</span>
                    <span class="stat-value">{{ status.ultimate_telos }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Last Update</span>
                    <span class="stat-value">{{ status.last_update }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Vault Connected</span>
                    <span class="stat-value">{{ "Yes" if status.vault_connected else "No" }}</span>
                </div>
                {% if status.vault_crown_jewels %}
                <div class="stat">
                    <span class="stat-label">Crown Jewels</span>
                    <span class="stat-value">{{ status.vault_crown_jewels }}</span>
                </div>
                {% endif %}
            </div>

            <!-- Telos Card -->
            <div class="card">
                <h2>Current Telos</h2>
                <div class="telos-section">
                    <h3>Ultimate (Immutable)</h3>
                    <p style="padding-left: 20px; color: #a78bfa;">{{ telos.ultimate.description }}</p>
                </div>
                <div class="telos-section">
                    <h3>Proximate Aims</h3>
                    <ul>
                        {% for aim in telos.proximate.current %}
                        <li>{{ aim }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>

            <!-- Memory Stats Card -->
            <div class="card">
                <h2>Memory Systems</h2>
                <div class="stat">
                    <span class="stat-label">Observations</span>
                    <span class="stat-value">{{ memory_stats.observations }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Meta-Observations</span>
                    <span class="stat-value">{{ memory_stats.meta_observations }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Patterns</span>
                    <span class="stat-value">{{ memory_stats.patterns }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Development Milestones</span>
                    <span class="stat-value">{{ memory_stats.development }}</span>
                </div>
                {% if deep_memory_stats.available %}
                <div class="stat">
                    <span class="stat-label">Deep Memories</span>
                    <span class="stat-value">{{ deep_memory_stats.memory_count }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Identity Milestones</span>
                    <span class="stat-value">{{ deep_memory_stats.identity_milestones }}</span>
                </div>
                {% endif %}
            </div>

            <!-- Message Input Card -->
            <div class="card">
                <h2>Send Message</h2>
                <textarea id="messageInput" class="message-input" placeholder="Enter your message here..."></textarea>
                <button class="btn" onclick="sendMessage()">Send</button>
                <div id="response" class="response" style="display: none;"></div>
            </div>
        </div>

        <!-- Recent Observations -->
        <div class="card">
            <h2>
                Recent Observations
                <button class="refresh-btn btn" onclick="location.reload()">Refresh</button>
            </h2>
            {% for obs in recent_observations[-5:]|reverse %}
            <div class="observation">
                <div class="observation-time">{{ obs.timestamp[:19] }}</div>
                {{ obs.content }}
            </div>
            {% endfor %}
        </div>

        <!-- Recent Meta-Observations -->
        <div class="card">
            <h2>Recent Meta-Observations (Quality of Presence)</h2>
            {% for meta in recent_meta_observations[-5:]|reverse %}
            <div class="meta-obs">
                <span class="quality-badge quality-{{ meta.quality }}">{{ meta.quality }}</span>
                <span>{{ meta.notes }}</span>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const responseDiv = document.getElementById('response');
            const message = input.value.trim();

            if (!message) return;

            responseDiv.style.display = 'block';
            responseDiv.innerHTML = '<span class="loading">Processing...</span>';

            try {
                const response = await fetch('/api/message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message, session_id: 'web'})
                });

                const data = await response.json();

                if (data.success) {
                    responseDiv.innerHTML = data.response;
                } else {
                    responseDiv.innerHTML = `<span style="color: #ef4444;">Error: ${data.error}</span>`;
                }
            } catch (error) {
                responseDiv.innerHTML = `<span style="color: #ef4444;">Error: ${error}</span>`;
            }
        }

        // Auto-refresh status every 30 seconds
        setInterval(() => {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => console.log('Status updated:', data));
        }, 30000);
    </script>
</body>
</html>"""

    with open(template_dir / "dashboard.html", 'w') as f:
        f.write(dashboard_html)


def main():
    """Run the dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Dharmic Agent Web Dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on (default: 5000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")

    args = parser.parse_args()

    # Create templates
    create_templates()

    # Initialize agent
    print("=" * 60)
    print("DHARMIC AGENT - Web Dashboard")
    print("=" * 60)

    agent, runtime = init_agent()
    print(f"Agent: {agent.name}")
    print(f"Telos: {agent.telos.telos['ultimate']['aim']}")
    print(f"\nDashboard: http://{args.host}:{args.port}")
    print("=" * 60)

    # Run Flask app
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
