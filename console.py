import os
import json
import subprocess
import datetime
from flask import Flask, render_template_string, redirect, url_for, flash, request

app = Flask(__name__)
app.secret_key = "local_dev_key"

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_FILE = os.path.join(BASE_DIR, 'projects.json')

# --- HELPER FUNCTIONS ---
def get_projects():
    if not os.path.exists(PROJECTS_FILE): return {}
    with open(PROJECTS_FILE, 'r') as f: 
        data = json.load(f)
        # Fix paths to be absolute based on where console.py is
        for key, proj in data.items():
            if proj['path'].startswith('..'):
                proj['real_path'] = os.path.abspath(os.path.join(BASE_DIR, proj['path']))
            else:
                proj['real_path'] = proj['path']
        return data

def get_tree_structure(startpath):
    tree_str = ""
    # --- UPDATED IGNORE LIST ---
    IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', 'instance', 'node_modules', 'audio_cache'}
    
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

# --- UI TEMPLATE (Tailwind + Lucide) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Lakar Studio</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>body { font-family: monospace; background: #0f172a; color: #e2e8f0; }</style>
</head>
<body class="p-8">
    <div class="max-w-6xl mx-auto border border-slate-700 bg-slate-800/50 rounded-xl p-6 relative">
        <div class="flex justify-between items-center mb-6 border-b border-slate-700 pb-4">
            <h1 class="text-2xl font-bold text-emerald-400 flex items-center gap-2">
                <i data-lucide="cpu"></i> LAKAR STUDIO_
            </h1>
            <span class="text-xs text-slate-500">LOCAL MODE</span>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                <div class="mb-4 p-3 rounded text-sm font-bold border 
                    {% if category=='success' %}bg-green-900/30 text-green-300 border-green-600{% elif category=='error' %}bg-red-900/30 text-red-300 border-red-600{% else %}bg-amber-900/30 text-amber-300 border-amber-600{% endif %}">
                    {{ message }}
                </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script>lucide.createIcons();</script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def dashboard():
    projects = get_projects()
    content = """
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {% for key, proj in projects.items() %}
        <a href="{{ url_for('manage', key=key) }}" class="block bg-slate-900 border border-slate-700 p-6 rounded-lg hover:border-emerald-500 transition group">
            <div class="flex items-center gap-4 mb-4">
                <div class="bg-slate-800 p-3 rounded text-emerald-400"><i data-lucide="{{ proj.icon }}"></i></div>
                <div>
                    <h3 class="font-bold text-lg text-white">{{ proj.name }}</h3>
                    <p class="text-xs text-slate-500">{{ proj.real_path }}</p>
                </div>
            </div>
            <div class="text-xs text-emerald-500 font-bold opacity-0 group-hover:opacity-100 transition">OPEN CONSOLE &rarr;</div>
        </a>
        {% endfor %}
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), projects=projects)

@app.route('/manage/<key>')
def manage(key):
    projects = get_projects()
    proj = projects.get(key)
    if not proj: return "Not Found"
    
    # Check Git Status
    try:
        git_status = subprocess.check_output(['git', 'status'], cwd=proj['real_path'], stderr=subprocess.STDOUT).decode('utf-8')
    except Exception as e:
        git_status = "GIT NOT INITIALIZED. Run 'git init' in project folder.\n" + str(e)

    content = """
    <div class="mb-6 flex justify-between items-center">
        <h2 class="text-xl font-bold text-white">Target: <span class="text-emerald-400">{{ proj.name }}</span></h2>
        <a href="{{ url_for('dashboard') }}" class="text-slate-500 hover:text-white">&larr; Back</a>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <a href="{{ url_for('manage', key=key) }}" class="bg-blue-600 text-white p-4 rounded text-center hover:bg-blue-500">
            <i data-lucide="refresh-cw" class="mx-auto mb-2"></i><span class="text-xs font-bold block">Refresh Status</span>
        </a>
        <form action="{{ url_for('git_save', key=key) }}" method="POST" class="contents">
            <button class="bg-emerald-600 text-white p-4 rounded text-center hover:bg-emerald-500 w-full">
                <i data-lucide="save" class="mx-auto mb-2"></i><span class="text-xs font-bold block">Quick Save</span>
            </button>
        </form>
        <a href="{{ url_for('history', key=key) }}" class="bg-violet-600 text-white p-4 rounded text-center hover:bg-violet-500">
            <i data-lucide="history" class="mx-auto mb-2"></i><span class="text-xs font-bold block">Time Machine</span>
        </a>
        <a href="{{ url_for('generate_context', key=key) }}" class="bg-amber-600 text-white p-4 rounded text-center hover:bg-amber-500">
            <i data-lucide="brain-circuit" class="mx-auto mb-2"></i><span class="text-xs font-bold block">AI Context</span>
        </a>
    </div>

    <div class="bg-black border border-slate-800 p-4 rounded text-xs font-mono text-green-400 overflow-x-auto">
        <pre>{{ status }}</pre>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), proj=proj, key=key, status=git_status)

@app.route('/action/<key>/save', methods=['POST'])
def git_save(key):
    proj = get_projects().get(key)
    try:
        subprocess.check_call(['git', 'add', '.'], cwd=proj['real_path'])
        status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=proj['real_path'])
        if not status.strip():
            flash("No changes to save.", "warning")
        else:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subprocess.check_call(['git', 'commit', '-m', f"Studio Save: {ts}"], cwd=proj['real_path'])
            flash(f"Saved snapshot: {ts}", "success")
    except Exception as e: flash(f"Git Error: {e}", "error")
    return redirect(url_for('manage', key=key))

@app.route('/action/<key>/history')
def history(key):
    proj = get_projects().get(key)
    try:
        log = subprocess.check_output(['git', 'log', '--pretty=format:%h|%ad|%s', '--date=short', '-n', '10'], cwd=proj['real_path']).decode('utf-8')
        history_list = [{'hash': l.split('|')[0], 'date': l.split('|')[1], 'msg': l.split('|')[2]} for l in log.strip().split('\n') if '|' in l]
    except: history_list = []
    
    content = """
    <h2 class="text-xl font-bold mb-4">Time Machine</h2>
    <div class="bg-slate-900 rounded border border-slate-700">
        <table class="w-full text-left text-sm text-slate-300">
            {% for item in log %}
            <tr class="border-b border-slate-800 hover:bg-slate-800">
                <td class="p-3 font-mono text-indigo-400">{{ item.hash }}</td>
                <td class="p-3">{{ item.date }}</td>
                <td class="p-3">{{ item.msg }}</td>
                <td class="p-3 text-right">
                    <a href="{{ url_for('restore', key=key, commit=item.hash) }}" class="text-red-400 hover:text-white border border-red-900 px-2 py-1 rounded text-xs" onclick="return confirm('Revert all files to this point?')">RESTORE</a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
    <div class="mt-4"><a href="{{ url_for('manage', key=key) }}" class="text-slate-500">&larr; Back</a></div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), proj=proj, key=key, log=history_list)

@app.route('/action/<key>/restore/<commit>')
def restore(key, commit):
    proj = get_projects().get(key)
    try:
        subprocess.check_call(['git', 'reset', '--hard', commit], cwd=proj['real_path'])
        flash(f"Restored to {commit}", "success")
    except Exception as e: flash(f"Error: {e}", "error")
    return redirect(url_for('manage', key=key))

@app.route('/action/<key>/context')
def generate_context(key):
    proj = get_projects().get(key)
    path = proj['real_path']
    
    output = [f"=== CONTEXT: {proj['name']} ==="]
    output.append("=== FILE TREE ===")
    output.append(get_tree_structure(path))
    output.append("=== FILE CONTENTS ===")
    
    IGNORE_EXTS = {'.db', '.sqlite3', '.pyc', '.png', '.jpg', '.vrm', '.glb', '.mp3', '.git'}
    # --- UPDATED IGNORE LIST ---
    IGNORE_DIRS = {'.git', '__pycache__', 'instance', 'audio_cache'}
    
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if os.path.splitext(file)[1].lower() not in IGNORE_EXTS:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, path)
                output.append(f"\n--- FILE: {rel_path} ---")
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        output.append(f.read())
                except: output.append("[Binary or Read Error]")
                output.append(f"--- END: {rel_path} ---")
    
    content = """
    <h2 class="text-xl font-bold text-amber-500 mb-2">AI Context Generator</h2>
    <p class="text-xs text-slate-400 mb-2">Copy this and paste it to Gemini to give it full project awareness.</p>
    <textarea id="ctx" class="w-full h-96 bg-black text-xs text-green-400 p-4 rounded font-mono">{{ data }}</textarea>
    <div class="mt-4 flex gap-4">
        <button onclick="navigator.clipboard.writeText(document.getElementById('ctx').value); this.innerText='COPIED!';" class="bg-amber-600 text-white px-6 py-2 rounded font-bold hover:bg-amber-500">COPY TO CLIPBOARD</button>
        <a href="{{ url_for('manage', key=key) }}" class="text-slate-500 py-2">Close</a>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), proj=proj, key=key, data='\n'.join(output))

if __name__ == '__main__':
    # Run on port 8000 so it doesn't conflict with AIBO (5000)
    print("--- LAKAR STUDIO ONLINE: http://localhost:8000 ---")
    app.run(debug=True, port=8000)