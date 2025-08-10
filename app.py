"""
Carbon Intelligence App — Probe365
==================================
Plataforma Flask para visualização e gestão de créditos de carbono.
"""

# 📦 Imports principais
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os, secrets, hashlib, traceback
from flask import Response
from flask import Flask, request, redirect, url_for, session, render_template
import csv
import io

# 🗃️ Banco de dados
from db import (
    DB_NAME, init_db, trial_exists, save_trial_to_db,
    get_trial_by_key, count_trials, increment_queries_used,
    get_all_trials, upgrade_db  # ✅ novo import
)


from responses import (
    format_agent_html,
    generate_fallback_response
)

from flask_cors import CORS

from openpyxl import Workbook

# 🤖 Agente bilíngue
from enhanced_bilingual_agent import BilingualCarbonAgent

# 🔧 Inicialização
init_db()
upgrade_db()


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")
app.config['EXPLAIN_TEMPLATE_LOADING'] = True

CORS(app, supports_credentials=True)



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

# 🔐 Geração de chave de trial
def generate_trial_key(email):
    try:
        unique_string = f"{email}{datetime.now().isoformat()}{secrets.token_hex(4)}"
        trial_key = hashlib.sha256(unique_string.encode()).hexdigest()[:12].upper()
        return f"CARBON-{trial_key}"
    except Exception:
        return f"CARBON-{int(datetime.now().timestamp())}"

# 🌐 Rotas principais
@app.route('/')
def home():
    return render_template("home_template.html")

@app.route('/register-trial')
def register_trial():
    return render_template("register_trial_template.html")

@app.route('/api/register-trial', methods=['POST'])
def api_register_trial():
    try:
        data = request.get_json()
        if not data.get('fullName') or not data.get('email'):
            return jsonify({"success": False, "message": "Nome completo e email são obrigatórios."}), 400

        email = data.get('email').lower().strip()
        if trial_exists(email):
            return jsonify({"success": False, "message": "Este email já possui um trial ativo."}), 400

        trial_key = generate_trial_key(email)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=14)

        trial_data = {
            "trial_key": trial_key,
            "full_name": data.get('fullName'),
            "email": email,
            "company": data.get('company', ''),
            "role": data.get('role', ''),
            "country": data.get('country', ''),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "queries_used": 0,
            "queries_limit": 100,
            "registration_date": datetime.now().isoformat(),
            "status": "active"
        }

        save_trial_to_db(trial_data)

        print(f"=== NEW TRIAL REGISTERED ===\nEmail: {email}\nTrial Key: {trial_key}\n===============================")

        return jsonify({
            "success": True,
            "message": "Trial registrado com sucesso!",
            "trial_key": trial_key,
            "trial_data": {
                "email": email,
                "full_name": trial_data["full_name"],
                "trial_key": trial_key,
                "queries_limit": 100,
                "valid_until": end_date.strftime('%Y-%m-%d'),
                "days_remaining": 14
            }
        })

    except Exception as e:
        print(f"ERROR in register_trial: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": "Erro interno do servidor."}), 500

# ✅ Outras rotas como /search, /validate_trial, /health podem vir abaixo

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
        "total_trials": count_trials(),
        "active_trials": count_trials("active"),
        "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "platform": "Carbon Credits Intelligence",
        "version": "1.0.0"
    })



@app.route('/validate_trial', methods=['POST'])
def validate_trial():
    try:
        data = request.get_json()
        trial_key = data.get('trial_key', '').strip().upper()

        if not trial_key:
            return jsonify({"success": False, "message": "Trial key é obrigatório."}), 400

        trial_data = get_trial_by_key(trial_key)
        if not trial_data:
            return jsonify({"success": False, "message": "Trial key inválido."}), 401

        end_date = datetime.fromisoformat(trial_data['end_date'])
        days_remaining = (end_date - datetime.now()).days

        if days_remaining < 0:
            return jsonify({"success": False, "message": "Trial expirado. Faça upgrade para continuar."}), 401

        return jsonify({
            "success": True,
            "message": "Trial válido",
            "trial_data": trial_data,
            "days_remaining": days_remaining
        })

    except Exception as e:
        print(f"ERROR in validate_trial: {str(e)}")
        return jsonify({"success": False, "message": "Erro interno do servidor."}), 500


@app.route('/trial')
def trial_access():
    """TRIAL ACCESS PAGE - CORRIGIDO"""
    return render_template("trial_access_template.html")


from responses import format_agent_html, generate_fallback_response

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        trial_key = data.get('trial_key', '').strip().upper()

        if not query or not trial_key:
            return jsonify({"success": False, "message": "Query e trial key são obrigatórios."}), 400

        trial_data = get_trial_by_key(trial_key)
        # Função utilitária para validar trial
        def is_trial_valid(trial_data):
            if not trial_data:
                return False, "Trial key inválido."
            end_date = datetime.fromisoformat(trial_data['end_date'])
            days_remaining = (end_date - datetime.now()).days
            if days_remaining < 0:
                return False, "Trial expirado. Faça upgrade para continuar."
            if trial_data.get('queries_used', 0) >= trial_data.get('queries_limit', 100):
                return False, "Limite de consultas atingido. Faça upgrade para continuar."
            return True, "Trial válido"

        is_valid, validation_msg = is_trial_valid(trial_data)

        if not is_valid:
            return jsonify({"success": False, "message": validation_msg}), 401

        # ✅ Atualiza contador de uso
        increment_queries_used(trial_key)
        trial_data = get_trial_by_key(trial_key)  # Recarrega dados atualizados

        # 🤖 Chamada ao agente
        try:
            if carbon_agent:
                language = carbon_agent.detect_language(query)
                location_specific = carbon_agent.is_location_specific(query)
                search_data = carbon_agent.comprehensive_search(query)
                agent_response = carbon_agent.format_response(search_data)

                language_name = "Portuguese (Brazilian)" if language == 'pt-BR' else "English (US)"
                response_html = format_agent_html(query, agent_response, language_name, search_data, location_specific)

                return jsonify({
                    "success": True,
                    "intelligence": response_html,
                    "queries_remaining": trial_data['queries_limit'] - trial_data['queries_used'],
                    "language_detected": language_name,
                    "sources_count": search_data['total_found']
                })

        except Exception as agent_error:
            print(f"⚠️ Erro no agente: {agent_error}")
            response_html = generate_fallback_response(query)
            return jsonify({
                "success": True,
                "intelligence": response_html,
                "queries_remaining": trial_data['queries_limit'] - trial_data['queries_used'],
                "language_detected": "Portuguese (Brazilian)"
            })

    except Exception as e:
        print(f"❌ Erro crítico em /search: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": "Erro interno no servidor."}), 500

@app.route('/api/trial-status', methods=['POST'])
def api_trial_status():
    """🔍 Consulta status de um trial via chave"""
    try:
        data = request.get_json()
        trial_key = data.get('trial_key', '').strip().upper()

        trial_data = get_trial_by_key(trial_key)
        if not trial_data:
            return jsonify({"success": False, "message": "Trial não encontrado."}), 404

        end_date = datetime.fromisoformat(trial_data['end_date'])
        days_remaining = max(0, (end_date - datetime.now()).days)

        return jsonify({
            "success": True,
            "status": trial_data.get('status', 'active'),
            "queries_used": trial_data['queries_used'],
            "queries_remaining": trial_data['queries_limit'] - trial_data['queries_used'],
            "days_remaining": days_remaining,
            "email": trial_data.get('email'),
            "full_name": trial_data.get('full_name')
        })

    except Exception as e:
        print(f"Erro em /api/trial-status: {e}")
        return jsonify({"success": False, "message": "Erro ao verificar status."}), 500




@app.route('/admin/trials')
def admin_trials():
    """🔐 Admin — Lista todos os trials registrados"""
    try:
        trials = get_all_trials()  # Retorna lista de dicts
        return jsonify({
            "total_trials": len(trials),
            "trials": trials
        })
    except Exception as e:
        print(f"Erro em /admin/trials: {e}")
        return jsonify({"success": False, "message": "Erro ao listar trials."}), 500

@app.route('/admin/painel')
def admin_painel():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template("admin_trials_template.html")



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

from db import update_expired_trials  # certifique-se de importar

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    

    update_expired_trials()  # 🔄 Atualiza status dos trials expirados
    expired_trials = count_trials(status="expired")

    update_expired_trials()
    trials = get_all_trials()
    active_trials = count_trials(status="active")


    trials = get_all_trials()
    active_trials = count_trials(status="active")

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
        </style>
    </head>
    <body>
        <h1>Admin Dashboard</h1>
        <p><strong>Trials ativos:</strong> {{ active_trials }}</p>
        <p><strong>Trials expirados:</strong> {{ expired_trials }}</p>

        <table>
            <tr>
                <th>Nome</th>
                <th>Email</th>
                <th>Empresa</th>
                <th>País</th>
                <th>Função</th>
                <th>Registro</th>
                <th>Último acesso</th>
                <th>Consultas</th>
                <th>Status</th>
            </tr>
            {% for trial in trials %}
            <tr>
                <td>{{ trial.full_name }}</td>
                <td>{{ trial.email }}</td>
                <td>{{ trial.company }}</td>
                <td>{{ trial.country }}</td>
                <td>{{ trial.role }}</td>
                <td>{{ trial.registration_date }}</td>
                <td>{{ trial.last_access or '—' }}</td>
                <td>{{ trial.queries_used }}/{{ trial.queries_limit }}</td>
                <td style="color: {{ 'red' if trial.status == 'expired' else 'green' }}">{{ trial.status }}</td>
            </tr>
            {% endfor %}
           
            <a href="{{ url_for('export_xlsx') }}">Exportar XLSX</a>


        </table>
       

    </body>
    </html>
    """
    return render_template_string(html_template, trials=trials, active_trials=active_trials)

@app.route('/admin/export-csv')
def export_csv():
    if not session.get('logado'):
        return redirect(url_for('login'))

    trials = get_all_trials()

    output = io.StringIO()
    writer = csv.writer(output)

    # Cabeçalhos
    writer.writerow([
        "Nome", "Email", "Empresa", "País", "Cargo",
        "Data de Registro", "Último Acesso", "Consultas", "Status"
    ])

    # Dados
    for trial in trials:
        writer.writerow([
            trial.get("full_name", ""),
            trial.get("email", ""),
            trial.get("company", ""),
            trial.get("country", ""),
            trial.get("role", ""),
            trial.get("registration_date", ""),
            trial.get("last_access", ""),
            f'{trial.get("queries_used", 0)}/{trial.get("queries_limit", 100)}',
            trial.get("status", "")
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=trials_export.csv"}
    )

from openpyxl import Workbook

@app.route('/admin/export-xlsx')
def export_xlsx():
    if not session.get('logado'):
        return redirect(url_for('login'))

    trials = get_all_trials()

    wb = Workbook()
    ws = wb.active
    ws.title = "Trials"

    # Cabeçalhos
    headers = [
        "Nome", "Email", "Empresa", "País", "Cargo",
        "Data de Início", "Data de Expiração", "Último Acesso",
        "Consultas", "Status"
    ]
    ws.append(headers)

    # Dados
    for trial in trials:
        ws.append([
            trial.get("full_name", ""),
            trial.get("email", ""),
            trial.get("company", ""),
            trial.get("country", ""),
            trial.get("role", ""),
            trial.get("start_date", ""),
            trial.get("end_date", ""),
            trial.get("last_access", ""),
            f'{trial.get("queries_used", 0)}/{trial.get("queries_limit", 100)}',
            trial.get("status", "")
        ])

    # Salvar em memória
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment;filename=trials_export.xlsx"}
    )




if __name__ == '__main__':
    print("=" * 50)
    print("🌱 CARBON CREDITS INTELLIGENCE PLATFORM")
    print("=" * 50)
    print("🔧 DEBUG MODE: ON")
    print("🌐 Server starting on http://localhost:5000")
    print("=" * 50)

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True,
        threaded=True
    )


