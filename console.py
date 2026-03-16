import os
import json
import subprocess
import datetime
import socket
from flask import Flask, render_template_string, redirect, url_for, flash, request, jsonify

app = Flask(__name__)
app.secret_key = "lakar_secret_key_1337"

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
PROJECTS_FILE = os.path.join(BASE_DIR, 'projects.json')

# --- INITIALIZATION ---
def init_projects():
    if not os.path.exists(PROJECTS_FILE):
        default = {
            "aibo": {
                "name": "Project AIBO",
                "path": "../Project_AIBO",
                "icon": "bot",
                "color": "cyan"
            }
        }
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(default, f, indent=4)

def get_projects():
    init_projects()
    with open(PROJECTS_FILE, 'r') as f: 
        try:
            data = json.load(f)
        except:
            data = {}
        for key, proj in data.items():
            if proj['path'].startswith('..'):
                proj['real_path'] = os.path.abspath(os.path.join(BASE_DIR, proj['path']))
            else:
                proj['real_path'] = proj['path']
            # Check if directory actually exists
            proj['exists'] = os.path.exists(proj['real_path'])
        return data

def save_projects(data):
    with open(PROJECTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_tree_structure(startpath):
    tree_str = ""
    IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', 'instance', 'node_modules', '.next', 'out'}
    
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += '{}{}/\n'.format(indent, os.path.basename(root))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if not f.endswith('.pyc') and not f.startswith('.'):
                tree_str += '{}{}\n'.format(subindent, f)
    return tree_str

# --- UI TEMPLATE (PREMIUM DARK MODE) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LAKAR STUDIO_ v2.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #030712; --card: #111827; --accent: #10b981; }
        body { font-family: 'Outfit', sans-serif; background: var(--bg); color: #f3f4f6; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .accent-glow { text-shadow: 0 0 10px rgba(16, 185, 129, 0.5); }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-10 flex flex-col items-center">
    
    <div class="w-full max-w-6xl">
        <!-- HEADER -->
        <header class="flex justify-between items-center mb-10">
            <div>
                <h1 class="text-3xl font-bold tracking-tight accent-glow flex items-center gap-3">
                    <span class="text-emerald-500"><i data-lucide="layout-grid"></i></span>
                    LAKAR STUDIO_
                </h1>
                <p class="text-slate-500 text-sm mt-1 uppercase tracking-widest font-semibold">Local Control / v2.0.4</p>
            </div>
            <div class="text-right">
                <div class="flex items-center gap-2 text-slate-400 text-xs font-mono">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    SYSTEM_ONLINE: {{ hostname }}
                </div>
                <div class="text-[10px] text-slate-600 mt-1 uppercase">{{ timestamp }}</div>
            </div>
        </header>

        <!-- ALERTS -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                <div class="mb-6 p-4 rounded-xl border flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300
                    {% if category=='success' %}bg-emerald-500/10 text-emerald-400 border-emerald-500/20{% elif category=='error' %}bg-rose-500/10 text-rose-400 border-rose-500/20{% else %}bg-amber-500/10 text-amber-400 border-amber-500/20{% endif %}">
                    <i data-lucide="{% if category=='success' %}check-circle{% elif category=='error' %}alert-circle{% else %}help-circle{% endif %}" class="w-5 h-5"></i>
                    <span class="text-sm font-semibold">{{ message }}</span>
                </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}

        <footer class="mt-20 py-10 border-t border-white/5 text-center text-slate-600 text-[10px] uppercase tracking-[0.2em]">
            &copy; 2026 Lakar Lab / Advanced Agency Framework
        </footer>
    </div>

    <script>lucide.createIcons();</script>
</body>
</html>
"""

# --- ROUTES ---

@app.context_processor
def inject_global_vars():
    return {
        "hostname": socket.gethostname(),
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S | %d %b %Y")
    }

@app.route('/')
def dashboard():
    projects = get_projects()
    content = """
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {% for key, proj in projects.items() %}
        <div class="group relative">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-2xl blur opacity-0 group-hover:opacity-20 transition duration-500"></div>
            <a href="{{ url_for('manage', key=key) }}" class="relative block glass rounded-2xl p-6 transition duration-300 transform group-hover:-translate-y-1">
                <div class="flex items-start justify-between mb-6">
                    <div class="p-4 rounded-xl bg-slate-800 text-emerald-400">
                        <i data-lucide="{{ proj.icon }}"></i>
                    </div>
                    {% if not proj.exists %}
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/20">DISCONNECTED</span>
                    {% else %}
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/10 uppercase">Active</span>
                    {% endif %}
                </div>
                <div>
                    <h3 class="font-bold text-xl text-white group-hover:text-emerald-400 transition">{{ proj.name }}</h3>
                    <p class="text-xs text-slate-500 mt-2 font-mono truncate">{{ proj.real_path }}</p>
                </div>
                <div class="mt-6 flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-slate-400 group-hover:text-emerald-400 transition">
                    <span>Manage Node</span>
                    <i data-lucide="arrow-right" class="w-3 h-3"></i>
                </div>
            </a>
        </div>
        {% endfor %}

        <!-- ADD PROJECT CARD -->
        <button onclick="document.getElementById('add_modal').classList.remove('hidden')" class="glass rounded-2xl p-6 border-dashed border-2 border-white/10 flex flex-col items-center justify-center gap-4 hover:border-emerald-500/50 hover:bg-emerald-500/5 transition group">
            <div class="w-12 h-12 rounded-full border border-white/20 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 group-hover:border-emerald-500/50">
                <i data-lucide="plus"></i>
            </div>
            <span class="text-xs font-bold uppercase tracking-widest text-slate-500 group-hover:text-emerald-400">Link New Project</span>
        </button>
    </div>

    <!-- MODAL -->
    <div id="add_modal" class="hidden fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div class="glass w-full max-w-md p-8 rounded-2xl">
            <h2 class="text-xl font-bold mb-6 flex items-center gap-3">
                <i data-lucide="folder-plus" class="text-emerald-500"></i>
                Link Repository
            </h2>
            <form action="{{ url_for('add_project') }}" method="POST" class="space-y-4">
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Project Identifier</label>
                    <input type="text" name="key" placeholder="e.g. my_app" class="w-full bg-black/50 border border-white/10 rounded-lg p-3 text-sm focus:border-emerald-500 outline-none" required>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Project Name</label>
                    <input type="text" name="name" placeholder="Visual Studio Pro" class="w-full bg-black/50 border border-white/10 rounded-lg p-3 text-sm focus:border-emerald-500 outline-none" required>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 uppercase mb-1">Relative Path</label>
                    <input type="text" name="path" placeholder="../my_project" class="w-full bg-black/50 border border-white/10 rounded-lg p-3 text-sm font-mono focus:border-emerald-500 outline-none" required>
                </div>
                <div class="flex gap-4 pt-4">
                    <button type="submit" class="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg text-sm uppercase tracking-widest transition">Establish Link</button>
                    <button type="button" onclick="document.getElementById('add_modal').classList.add('hidden')" class="flex-1 bg-white/5 hover:bg-white/10 text-slate-400 font-bold py-3 rounded-lg text-sm uppercase tracking-widest transition">Cancel</button>
                </div>
            </form>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), projects=projects)

@app.route('/add', methods=['POST'])
def add_project():
    data = get_projects()
    key = request.form['key'].lower().replace(' ', '_')
    data[key] = {
        "name": request.form['name'],
        "path": request.form['path'],
        "icon": "box",
        "color": "emerald"
    }
    save_projects(data)
    flash(f"Project '{request.form['name']}' linked successfully.", "success")
    return redirect(url_for('dashboard'))

@app.route('/manage/<key>')
def manage(key):
    projects = get_projects()
    proj = projects.get(key)
    if not proj: return "Not Found"
    
    # Check Git Status
    try:
        git_status = subprocess.check_output(['git', 'status'], cwd=proj['real_path'], stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        git_status = "⚠️ GIT ENGINE NOT INITIALIZED\nRun 'git init' in the project directory to enable Time Machine features.\n\n" + str(e)

    content = """
    <div class="mb-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
            <div class="flex items-center gap-4 text-slate-500 mb-2">
                <a href="{{ url_for('dashboard') }}" class="hover:text-emerald-400 transition flex items-center gap-1 text-xs uppercase font-bold tracking-widest">
                    <i data-lucide="chevron-left" class="w-4 h-4"></i> Dashboard
                </a>
                <span class="text-slate-800">/</span>
                <span class="text-xs uppercase font-bold tracking-widest">Project Console</span>
            </div>
            <h2 class="text-4xl font-black text-white tracking-tighter uppercase">{{ proj.name }}_</h2>
        </div>
        
        <div class="flex gap-3">
            <form action="{{ url_for('git_save', key=key) }}" method="POST">
                <button class="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-widest shadow-lg shadow-emerald-500/20 transition flex items-center gap-2">
                    <i data-lucide="save" class="w-4 h-4"></i> Snapshot
                </button>
            </form>
            <a href="{{ url_for('history', key=key) }}" class="glass hover:bg-white/10 text-white px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-widest transition flex items-center gap-2">
                <i data-lucide="history" class="w-4 h-4"></i> Time Machine
            </a>
            <a href="{{ url_for('generate_context', key=key) }}" class="glass hover:bg-white/10 text-amber-500 px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-widest transition flex items-center gap-2">
                <i data-lucide="brain-circuit" class="w-4 h-4"></i> AI Context
            </a>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- GIT STATUS -->
        <div class="lg:col-span-2 space-y-6">
            <div class="glass rounded-2xl overflow-hidden">
                <div class="bg-black/40 px-6 py-4 border-b border-white/5 flex justify-between items-center">
                    <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Git Status Output</span>
                    <span class="flex items-center gap-2 text-[10px] font-bold text-emerald-500 opacity-50">
                        <i data-lucide="cpu" class="w-3 h-3"></i> LIVE_STREAM
                    </span>
                </div>
                <div class="p-6 overflow-x-auto scrollbar-hide">
                    <pre class="mono text-xs text-emerald-400 leading-relaxed">{{ status }}</pre>
                </div>
            </div>
        </div>

        <!-- FILE EXPLORER (BASIC) -->
        <div class="space-y-6">
            <div class="glass rounded-2xl overflow-hidden h-full">
                <div class="bg-black/40 px-6 py-4 border-b border-white/5">
                    <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400">File Tree</span>
                </div>
                <div class="p-6 font-mono text-[10px] text-slate-500 max-h-[600px] overflow-y-auto scrollbar-hide">
                    <pre>{{ tree }}</pre>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), proj=proj, key=key, status=git_status, tree=get_tree_structure(proj['real_path']))

@app.route('/action/<key>/save', methods=['POST'])
def git_save(key):
    proj = get_projects().get(key)
    try:
        subprocess.check_call(['git', 'add', '.'], cwd=proj['real_path'])
        # Check if there are changes
        status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=proj['real_path'])
        if not status.strip():
            flash("System Integrity confirmed: No changes detected.", "info")
        else:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.check_call(['git', 'commit', '-m', f"Studio Snapshot: {ts}"], cwd=proj['real_path'])
            flash(f"Chronological Snapshot created: {ts}", "success")
    except Exception as e: flash(f"Git Engine Failure: {e}", "error")
    return redirect(url_for('manage', key=key))

@app.route('/action/<key>/history')
def history(key):
    proj = get_projects().get(key)
    try:
        log = subprocess.check_output(['git', 'log', '--pretty=format:%h|%ad|%s', '--date=short', '-n', '15'], cwd=proj['real_path']).decode('utf-8')
        history_list = [{'hash': l.split('|')[0], 'date': l.split('|')[1], 'msg': l.split('|')[2]} for l in log.strip().split('\n') if '|' in l]
    except: history_list = []
    
    content = """
    <div class="mb-10 flex justify-between items-center">
        <h2 class="text-3xl font-bold text-white">Time Machine_</h2>
        <a href="{{ url_for('manage', key=key) }}" class="text-slate-500 hover:text-white flex items-center gap-2 text-xs font-bold uppercase tracking-widest">
            <i data-lucide="chevron-left" class="w-4 h-4"></i> Cancel
        </a>
    </div>

    <div class="glass rounded-2xl overflow-hidden">
        <table class="w-full text-left text-sm text-slate-300">
            <thead class="bg-black/40 border-b border-white/5">
                <tr>
                    <th class="p-6 text-[10px] uppercase tracking-widest text-slate-500">Hash</th>
                    <th class="p-6 text-[10px] uppercase tracking-widest text-slate-500">Timestamp</th>
                    <th class="p-6 text-[10px] uppercase tracking-widest text-slate-500">Snapshot Label</th>
                    <th class="p-6 text-right text-[10px] uppercase tracking-widest text-slate-500">Action</th>
                </tr>
            </thead>
            <tbody>
                {% for item in log %}
                <tr class="border-b border-white/5 hover:bg-white/5 transition">
                    <td class="p-6 mono text-emerald-500 text-xs">{{ item.hash }}</td>
                    <td class="p-6 text-xs text-slate-400">{{ item.date }}</td>
                    <td class="p-6 text-sm font-semibold text-white">{{ item.msg }}</td>
                    <td class="p-6 text-right">
                        <a href="{{ url_for('restore', key=key, commit=item.hash) }}" class="px-3 py-1.5 rounded-lg border border-rose-500/20 text-rose-500 hover:bg-rose-500 hover:text-white transition text-[10px] font-bold uppercase tracking-widest" onclick="return confirm('WARNING: This will reset all files to this state. Continue?')">Restore</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% if not log %}
        <div class="p-20 text-center text-slate-600 italic">No temporal records found.</div>
        {% endif %}
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), proj=proj, key=key, log=history_list)

@app.route('/action/<key>/restore/<commit>')
def restore(key, commit):
    proj = get_projects().get(key)
    try:
        subprocess.check_call(['git', 'reset', '--hard', commit], cwd=proj['real_path'])
        flash(f"Chronology Restored to: {commit}", "success")
    except Exception as e: flash(f"Restoration Failed: {e}", "error")
    return redirect(url_for('manage', key=key))

@app.route('/action/<key>/context')
def generate_context(key):
    proj = get_projects().get(key)
    path = proj['real_path']
    
    output = [f"=== LAKAR AI CONTEXT: {proj['name']} ==="]
    output.append(f"GENERATED: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("\n=== FILE TREE ===")
    output.append(get_tree_structure(path))
    output.append("\n=== SOURCE CODE ===")
    
    IGNORE_EXTS = {'.db', '.sqlite3', '.pyc', '.png', '.jpg', '.vrm', '.glb', '.mp3', '.git', '.ico', '.woff', '.woff2'}
    IGNORE_DIRS = {'.git', '__pycache__', 'instance', 'audio_cache', 'node_modules', '.next'}
    
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if os.path.splitext(file)[1].lower() not in IGNORE_EXTS:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, path)
                output.append(f"\n--- [FILE: {rel_path}] ---")
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        output.append(f.read())
                except: output.append("[Error: Undecodable sequence]")
                output.append(f"--- [END: {rel_path}] ---")
    
    content = """
    <div class="mb-6 flex justify-between items-center">
        <h2 class="text-3xl font-bold text-amber-500">AI Neural Context_</h2>
        <a href="{{ url_for('manage', key=key) }}" class="text-slate-500 hover:text-white flex items-center gap-2 text-xs font-bold uppercase tracking-widest">
            <i data-lucide="chevron-left" class="w-4 h-4"></i> Back
        </a>
    </div>
    
    <div class="glass p-8 rounded-2xl">
        <p class="text-xs text-slate-400 mb-6 leading-relaxed">Copy the payload below and feed it to your Agent (Gemini/Claude/GPT). This provides the model with "Complete Situational Awareness" of your codebase.</p>
        
        <div class="relative group">
            <textarea id="ctx" class="w-full h-[500px] bg-black/60 text-[10px] text-emerald-400 p-6 rounded-xl font-mono border border-white/5 outline-none focus:border-emerald-500/50 transition scrollbar-hide" readonly>{{ data }}</textarea>
            <div class="absolute bottom-4 right-4 flex gap-4">
                <button onclick="copyToClipboard()" id="copyBtn" class="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-3 rounded-lg font-bold text-xs uppercase tracking-widest shadow-xl transition active:scale-95">Copy Neural Link</button>
            </div>
        </div>
    </div>

    <script>
    function copyToClipboard() {
        const copyText = document.getElementById("ctx");
        copyText.select();
        copyText.setSelectionRange(0, 99999);
        navigator.clipboard.writeText(copyText.value);
        
        const btn = document.getElementById("copyBtn");
        const original = btn.innerText;
        btn.innerText = "COPIED TO NEURAL SYSTEM!";
        btn.classList.replace('bg-emerald-600', 'bg-emerald-400');
        setTimeout(() => {
            btn.innerText = original;
            btn.classList.replace('bg-emerald-400', 'bg-emerald-600');
        }, 2000);
    }
    </script>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), proj=proj, key=key, data='\n'.join(output))

if __name__ == '__main__':
    print("--------------------------------------------------")
    print("   LAKAR STUDIO V2 IS IGNITING...")
    print("   CONTROL CENTER: http://localhost:8000")
    print("--------------------------------------------------")
    app.run(debug=False, port=8000, host='0.0.0.0')