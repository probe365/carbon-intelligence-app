
"""
Carbon Intelligence App — Probe365
==================================
Plataforma Flask para visualização e gestão de créditos de carbono.
"""

# Imports
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os, secrets, hashlib, traceback, shutil, sqlite3, csv, io
from db import DB_NAME, init_db, save_user_to_db, get_all_users, upgrade_db
from responses import format_agent_html, generate_fallback_response
from flask_cors import CORS
from openpyxl import Workbook
from enhanced_bilingual_agent import BilingualCarbonAgent

# Flask app initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
CORS(app, supports_credentials=True)

@app.route('/trial')
def trial():
    return render_template("trial_template.html")

# 🔧 Inicialização

init_db()
upgrade_db()
try:
    # Warn if running on Render but DB not on mounted disk (can suppress with SUPPRESS_PERSIST_WARN=1)
    if (
        os.getenv('RENDER')
        and '/var/data/' not in os.path.abspath(DB_NAME)
        and os.getenv('SUPPRESS_PERSIST_WARN', '0') not in ('1', 'true', 'True')
    ):
        print(
            f"[WARN] DB path {os.path.abspath(DB_NAME)} is not on /var/data persistent disk. "
            "Data may reset on new deploy. Upgrade & add a disk or set SUPPRESS_PERSIST_WARN=1 to silence this."
        )
except Exception:
    pass
load_dotenv()



# 🌐 Variáveis externas
MONGODB_URI = os.getenv("MONGODB_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
API_PORT = int(os.getenv("API_PORT", 3000))

# 🤖 Inicializa o agente
try:
    carbon_agent = BilingualCarbonAgent()
    print("✅ BilingualCarbonAgent initialized successfully")
except Exception as e:
    print(f"⚠️ BilingualCarbonAgent initialization failed: {e}")
    carbon_agent = None


# 🌐 Rotas principais
@app.route('/')
def home():
    return render_template("home_template.html")

@app.route('/register-trial')
def register_trial():
    return render_template("register_trial_template.html")

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        if not data.get('fullName') or not data.get('email'):
            return jsonify({"success": False, "message": "Nome completo e email são obrigatórios."}), 400

        email = data.get('email').lower().strip()
        user_data = {
            "email": email,
            "full_name": data.get('fullName'),
            "company": data.get('company', ''),
            "role": data.get('role', ''),
            "country": data.get('country', ''),
            "registration_date": datetime.now().isoformat()
        }
        save_user_to_db(user_data)
        print(f"=== NEW USER REGISTERED ===\nEmail: {email}\nNome: {user_data['full_name']}\n===============================")
        return jsonify({
            "success": True,
            "message": "Cadastro realizado com sucesso!",
            "user": user_data
        })
    except Exception as e:
        print(f"ERROR in register: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": "Erro interno do servidor."}), 500

# ✅ Outras rotas como /search, /login, /health podem vir abaixo

# Endpoint dinâmico de busca
@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        if not query:
            return jsonify({"success": False, "error": "Query não informada."}), 400
        # Executa busca usando o agente
        search_data = carbon_agent.comprehensive_search(query)
        # Formata resposta para frontend
        results = []
        for r in search_data.get('results', []):
            results.append({
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source
            })
        return jsonify({
            "success": True,
            "query": query,
            "language": search_data.get('language'),
            "location": search_data.get('location'),
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('username')
        senha = request.form.get('password')
        if usuario == 'admin' and senha == 'senha123':
            session['logado'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template("login_template.html", erro="Login inválido")
    return render_template("login_template.html")



@app.route('/health', methods=['GET', 'POST'])
def health_check():
    return jsonify({
        "status": "online",
        "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "platform": "Carbon Credits Intelligence",
    "version": "1.1.0"
    })


@app.route('/health/db', methods=['GET'])
def health_db():
    """DB smoke test: ensure SQLite is reachable and table is queryable."""
    try:
        path = os.path.abspath(DB_NAME)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM trials")
        total = cur.fetchone()[0]
        cur.execute("SELECT trial_key FROM trials LIMIT 1")
        row = cur.fetchone()
        sample = row[0] if row else None
        conn.close()
        return jsonify({
            "success": True,
            "db_path": path,
            "total_trials": total,
            "sample_trial_key": sample
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "db_path": os.path.abspath(DB_NAME)
        }), 500








from responses import format_agent_html, generate_fallback_response





@app.route('/admin/users')
def admin_users():
    """🔐 Admin — Lista todos os usuários registrados"""
    try:
        users = get_all_users()  # Retorna lista de dicts
        return jsonify({
            "total_users": len(users),
            "users": users
        })
    except Exception as e:
        print(f"Erro em /admin/users: {e}")
        return jsonify({"success": False, "message": "Erro ao listar usuários."}), 500

@app.route('/admin/painel')
def admin_painel():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template("admin_trials_template.html")


@app.route('/admin/diagnostics')
def admin_diagnostics():
    """🔎 Admin — Diagnóstico de saúde e persistência do banco de dados.

    Mostra caminho do DB, existência, tamanho, data de modificação e uso do disco
    do diretório onde o DB está. Útil para confirmar persistência no Render.
    """
    if not session.get('logado'):
        return redirect(url_for('login'))

    db_path = DB_NAME
    db_dir = os.path.dirname(db_path) or '.'
    exists = os.path.exists(db_path)
    size = os.path.getsize(db_path) if exists else 0
    mtime = datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat() if exists else None

    try:
        usage = shutil.disk_usage(db_dir)
        disk_info = {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "dir": os.path.abspath(db_dir)
        }
    except Exception as e:
        disk_info = {"error": str(e), "dir": os.path.abspath(db_dir)}

    # Get users list for counts
    users = get_all_users()

    return jsonify({
        "success": True,
        "db": {
            "path": os.path.abspath(db_path),
            "exists": exists,
            "size_bytes": size,
            "last_modified": mtime
        },
        "env": {
            "DB_PATH": os.getenv("DB_PATH"),
            "PORT": os.getenv("PORT"),
            "FLASK_DEBUG": os.getenv("FLASK_DEBUG")
        },
        "disk": disk_info,
        "counts": {
            "total_users": len(users),
            "active_users": len([u for u in users if u['status'] == 'active']),
            "inactive_users": len([u for u in users if u['status'] == 'inactive'])
        },
        "server_time": datetime.utcnow().isoformat() + "Z"
    })



@app.route('/debug/search-test', methods=['GET'])
def debug_search_test():
    """🧪 Teste rápido do endpoint de busca"""
    return jsonify({
        "message": "Search endpoint is funcionando",
        "sample_response": {
            "success": True,
            "intelligence": "<h4>Resposta de Teste</h4><p>Está funcionando!</p>",
            "queries_remaining": 99
        }
    })

from flask import render_template_string

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))
    

    users = get_all_users()
    html_template = """
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f4f4f4; }
            h1 { color: #333; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 10px; border: 1px solid #ccc; text-align: left; }
            th { background-color: #eee; }
            tr:nth-child(even) { background-color: #fafafa; }
            .links { margin: 10px 0 20px; }
            .links a { margin-right: 16px; }
            .btn { display: inline-block; padding: 8px 12px; background: #2f7d32; color: #fff; border-radius: 6px; text-decoration: none; }
            .btn:hover { background: #256428; }
            .toast { position: fixed; right: 16px; bottom: 16px; background: #333; color: #fff; padding: 10px 12px; border-radius: 6px; display: none; }
        </style>
    </head>
    <body>
        <h1>Admin Dashboard</h1>
        <div class="links">
            <a href="{{ url_for('export_xlsx') }}">Exportar XLSX</a>
            <a href="{{ url_for('export_csv') }}">Exportar CSV</a>
            <a href="{{ url_for('admin_diagnostics_view') }}">Ver Diagnóstico</a>
        </div>
        <table>
            <tr>
                <th>Nome</th>
                <th>Email</th>
                <th>Empresa</th>
                <th>País</th>
                <th>Função</th>
                <th>Registro</th>
                <th>Status</th>
            </tr>
            {% for user in users %}
            <tr>
                <td>{{ user.full_name }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.company }}</td>
                <td>{{ user.country }}</td>
                <td>{{ user.role }}</td>
                <td>{{ user.registration_date }}</td>
                <td>{{ user.status }}</td>
            </tr>
            {% endfor %}
        </table>
        </body>
        </html>
        """
    users = get_all_users()
    return render_template_string(html_template, users=users)

@app.route('/admin/export-csv')
def export_csv():
    if not session.get('logado'):
        return redirect(url_for('login'))


    output = io.StringIO()
    writer = csv.writer(output)

    # Cabeçalhos
    writer.writerow([
        "Nome", "Email", "Empresa", "País", "Cargo",
        "Data de Registro", "Status"
    ])
    # Dados
    users = get_all_users()
    for u in users:
        writer.writerow([
            u.get("full_name", ""), u.get("email", ""), u.get("company", ""),
            u.get("country", ""), u.get("role", ""), u.get("registration_date", ""),
            u.get("status", "")
        ])
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=users_export.csv"}
    )

@app.route('/admin/export-csv-full')
def export_csv_full():
    """Enhanced lossless CSV export including all key fields for backup/restore."""
    if not session.get('logado'):
        return redirect(url_for('login'))
    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        "email","full_name","company","role","country","registration_date","status"
    ]
    writer.writerow(headers)
    users = get_all_users()
    for u in users:
        writer.writerow([
            u.get("email", ""), u.get("full_name", ""), u.get("company", ""),
            u.get("role", ""), u.get("country", ""), u.get("registration_date", ""),
            u.get("status", "")
        ])
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=users_export_full.csv"}
    )

from openpyxl import Workbook

@app.route('/admin/export-xlsx')
def export_xlsx():
    if not session.get('logado'):
        return redirect(url_for('login'))

    wb = Workbook()
    ws = wb.active

    # Cabeçalhos
    headers = [
        "Nome", "Email", "Empresa", "País", "Cargo",
        "Data de Registro", "Status"
    ]
    ws.append(headers)
    users = get_all_users()
    for u in users:
        ws.append([
            u.get("full_name", ""), u.get("email", ""), u.get("company", ""),
            u.get("country", ""), u.get("role", ""), u.get("registration_date", ""),
            u.get("status", "")
        ])
    # Salvar em memória
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=users_export.xlsx"}
    )


@app.route('/admin/diagnostics-view')
def admin_diagnostics_view():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('diagnostics_template.html')


@app.route('/admin/run-expire', methods=['POST'])
def admin_run_expire():
    if not session.get('logado'):
        return jsonify({"success": False, "message": "Não autorizado"}), 401
    return jsonify({"success": True})


@app.route('/cron/run-expire', methods=['POST'])
def cron_run_expire():
    token = request.headers.get('X-CRON-SECRET') or request.args.get('token')
    expected = os.getenv('CRON_SECRET')
    if not expected or token != expected:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    return jsonify({"success": True,})




if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5000"))

    print("=" * 50)
    print("🌱 CARBON CREDITS INTELLIGENCE PLATFORM")
    print("=" * 50)
    print(f"🔧 DEBUG MODE: {'ON' if debug_mode else 'OFF'}")
    print(f"🌐 Server starting on http://0.0.0.0:{port}")
    print("=" * 50)

    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=port,
        use_reloader=debug_mode,
        threaded=True
    )


