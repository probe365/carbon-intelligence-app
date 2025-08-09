"""
Carbon Intelligence App — Probe365
==================================
Plataforma Flask para visualização e gestão de créditos de carbono.
"""

# Imports principais
from flask import Flask, render_template, request, jsonify
# from db import init_db, trial_exists
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
import secrets
import hashlib
import traceback

import sqlite3
from db import DB_NAME
from db import (
    init_db, trial_exists, save_trial_to_db,
    get_trial_by_key, count_trials, increment_queries_used
)



# Importa o agente bilíngue
from enhanced_bilingual_agent import BilingualCarbonAgent

init_db()

# Carrega variáveis de ambiente
load_dotenv()

# Configurações da aplicação
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "default-secret-key")

# Variáveis externas
MONGODB_URI = os.getenv("MONGODB_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
API_PORT = int(os.getenv("API_PORT", 3000))

# Inicializa o agente bilíngue
carbon_agent = BilingualCarbonAgent()


def save_trial_to_db(trial_data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trials (
            email, trial_key, full_name, company, role, country,
            start_date, end_date, queries_used, queries_limit,
            registration_date, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trial_data["email"],
        trial_data["trial_key"],
        trial_data["full_name"],
        trial_data["company"],
        trial_data["role"],
        trial_data["country"],
        trial_data["start_date"],
        trial_data["end_date"],
        trial_data["queries_used"],
        trial_data["queries_limit"],
        trial_data["registration_date"],
        trial_data["status"]
    ))
    conn.commit()
    conn.close()

# ADICIONAR após TRIALS_DATA:
try:
    carbon_agent = BilingualCarbonAgent()
    print("✅ BilingualCarbonAgent initialized successfully")
except Exception as e:
    print(f"⚠️ BilingualCarbonAgent initialization failed: {e}")
    carbon_agent = None

app.config['EXPLAIN_TEMPLATE_LOADING'] = True


def generate_trial_key(email):
    try:
        unique_string = f"{email}{datetime.now().isoformat()}{secrets.token_hex(4)}"
        trial_key = hashlib.sha256(unique_string.encode()).hexdigest()[:12].upper()
        return f"CARBON-{trial_key}"
    except Exception as e:
        # Fallback key generation
        import time
        return f"CARBON-{int(time.time())}"

@app.route('/')
def home():
    """Beautiful Carbon Credits Platform as Homepage with Trial Conversion"""
    return render_template("home_template.html")


@app.route('/register-trial')
def register_trial():
    """Trial Registration Form with Trial Key Display"""
    return render_template("register_trial_template.html")


@app.route('/api/register-trial', methods=['POST'])
def api_register_trial():
    """API endpoint to register trial users"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('fullName') or not data.get('email'):
            return jsonify({
                "success": False,
                "message": "Nome completo e email são obrigatórios."
            }), 400
        
        email = data.get('email').lower().strip()
    

        # Check if email already exists
        if trial_exists(email):
            return jsonify({
                    "success": False,
                    "message": "Este email já possui um trial ativo."
                }), 400
        
        # Generate trial data
        trial_key = generate_trial_key(email)
        
        # Calculate trial period (14 days)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=14)
        
        # Store trial data
        TRIALS_DATA[email] = {
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
        
        print(f"=== NEW TRIAL REGISTERED ===")
        print(f"Email: {email}")
        print(f"Trial Key: {trial_key}")
        print(f"Full Name: {data.get('fullName')}")
        print(f"Company: {data.get('company', 'Not provided')}")
        print(f"Role: {data.get('role', 'Not provided')}")
        print(f"Country: {data.get('country', 'Not provided')}")
        print(f"Valid until: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total trials: {len(TRIALS_DATA)}")
        print("===============================")
        
        return jsonify({
            "success": True,
            "message": "Trial registrado com sucesso!",
            "trial_key": trial_key,
            "trial_data": {
                "email": email,
                "full_name": data.get('fullName'),
                "trial_key": trial_key,
                "queries_limit": 100,
                "valid_until": end_date.strftime('%Y-%m-%d'),
                "days_remaining": 14
            }
        })
        
    except Exception as e:
        print(f"ERROR in register_trial: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "message": f"Erro interno do servidor: {str(e)}"
        }), 500

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


@app.route('/search', methods=['POST'])
def search():
    """SEARCH FUNCTION - INTEGRATED WITH BILINGUAL AGENT + SQLITE PERSISTENCE"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400

        query = data.get('query', '').strip()
        trial_key = data.get('trial_key', '').strip().upper()

        print(f"\n=== SEARCH DEBUG ===")
        print(f"Query: '{query}'")
        print(f"Trial Key: '{trial_key}'")

        # Validation
        if not query:
            return jsonify({"success": False, "message": "Query is required"}), 400
        if not trial_key:
            return jsonify({"success": False, "message": "Trial key is required"}), 400

        # Fetch trial from database
        trial_data = get_trial_by_key(trial_key)
        if not trial_data:
            print(f"Trial key '{trial_key}' not found!")
            return jsonify({"success": False, "message": "Invalid trial key"}), 401

        if trial_data['queries_used'] >= trial_data['queries_limit']:
            return jsonify({"success": False, "message": "Query limit reached"}), 403

        # Update usage
        increment_queries_used(trial_key)

        print(f"Trial found for: {trial_data['email']}")
        print(f"Queries used: {trial_data['queries_used'] + 1}")

        # TRY BILINGUAL AGENT FIRST
        try:
            if carbon_agent:
                print(f"=== CALLING BILINGUAL AGENT ===")

                language = carbon_agent.detect_language(query)
                location_specific = carbon_agent.is_location_specific(query)

                print(f"Language detected: {language}")
                print(f"Location specific: {location_specific}")

                search_data = carbon_agent.comprehensive_search(query)
                agent_response = carbon_agent.format_response(search_data)

                language_name = "Portuguese (Brazilian)" if language == 'pt-BR' else "English (US)"
                formatted_response = f"""
                <h5 style="color: #059669; margin: 20px 0 10px 0;">🤖 Análise IA Bilíngue - Pesquisa Realizada:</h5>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb; line-height: 1.6; margin-bottom: 15px;">
                {agent_response.replace(chr(10), '<br>').replace('**', '<strong>').replace('**', '</strong>')}
                </div>
                """

                response_html = f'''<h4 style="color: #6b46c1; margin-bottom: 15px;">🎯 Análise Inteligente: {query}</h4>
<div style="background: #f0f9ff; padding: 12px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #0ea5e9;">
<h5 style="color: #0369a1; margin-bottom: 8px;">🌐 Pesquisa Realizada:</h5>
<p style="margin: 0; font-size: 13px; line-height: 1.4;"><strong>Idioma:</strong> {language_name} | <strong>Fontes:</strong> {search_data['total_found']} resultados encontrados | <strong>Estratégia:</strong> {'Busca local (Brasil)' if location_specific else 'Busca global'}</p>
</div>
{formatted_response}
<div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4CAF50;">
<h5 style="color: #059669; margin-bottom: 10px;">💡 Fontes Consultadas:</h5>
<p style="margin: 0; line-height: 1.6; font-size: 13px;"><strong>APIs utilizadas:</strong> {', '.join([r.source for r in search_data['results'][:3]])} | <strong>Atualização:</strong> Dados em tempo real | <strong>Confiabilidade:</strong> Fontes oficiais verificadas</p>
</div>'''

                print(f"=== BILINGUAL AGENT SUCCESS ===")
                return jsonify({
                    "success": True,
                    "intelligence": response_html,
                    "queries_remaining": trial_data['queries_limit'] - (trial_data['queries_used'] + 1),
                    "language_detected": language_name,
                    "sources_count": search_data['total_found']
                })

        except Exception as agent_error:
            print(f"=== BILINGUAL AGENT ERROR ===")
            print(f"Agent Error: {str(agent_error)}")
            print("Falling back to smart static responses...")

        # SMART STATIC RESPONSES
        query_lower = query.lower()
        if any(term in query_lower for term in ['cop30', 'cop 30', 'belém', 'belem']):
            response_html = generate_cop30_response(query)
        elif any(term in query_lower for term in ['preço', 'precos', 'price', 'valor', 'custo']):
            response_html = generate_price_response(query)
        else:
            response_html = generate_default_response(query)

        print(f"=== SMART RESPONSE GENERATED ===")
        return jsonify({
            "success": True,
            "intelligence": response_html,
            "queries_remaining": trial_data['queries_limit'] - (trial_data['queries_used'] + 1),
            "language_detected": "Portuguese (Brazilian)"
        })

    except Exception as e:
        print(f"\n=== CRITICAL SEARCH ERROR ===")
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

        
@app.route('/api/trial-status', methods=['POST'])
def api_trial_status():
    """Get trial status"""
    try:
        data = request.get_json()
        trial_key = data.get('trial_key', '').strip().upper()
        
        # Find trial by key
        for email, trial_data in TRIALS_DATA.items():
            if trial_data.get('trial_key') == trial_key:
                end_date = datetime.fromisoformat(trial_data['end_date'])
                days_remaining = (end_date - datetime.now()).days
                
                return jsonify({
                    "success": True,
                    "status": trial_data.get('status', 'active'),
                    "queries_used": trial_data['queries_used'],
                    "queries_remaining": trial_data['queries_limit'] - trial_data['queries_used'],
                    "days_remaining": max(0, days_remaining),
                    "email": email,
                    "full_name": trial_data.get('full_name', '')
                })
        
        return jsonify({
            "success": False,
            "message": "Trial não encontrado."
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Erro ao verificar status."
        }), 500

@app.route('/admin/trials')
def admin_trials():
    """Admin page to view all trials"""
    return jsonify({
        "total_trials": len(TRIALS_DATA),
        "trials": [
            {
                "email": email,
                "trial_key": data.get('trial_key'),
                "full_name": data.get('full_name'),
                "company": data.get('company'),
                "queries_used": data.get('queries_used', 0),
                "queries_limit": data.get('queries_limit', 100),
                "registration_date": data.get('registration_date'),
                "status": data.get('status', 'active')
            }
            for email, data in TRIALS_DATA.items()
        ]
    })


@app.route('/debug/search-test', methods=['GET', 'POST'])
def debug_search_test():
    """Debug endpoint to test search functionality"""
    return jsonify({
        "message": "Search endpoint is working",
        "total_trials": len(TRIALS_DATA),
        "sample_response": {
            "success": True,
            "intelligence": "<h4>Test Response</h4><p>This is working!</p>",
            "queries_remaining": 99
        }
    })

@app.route("/healthcheck")
def healthcheck():
    return "ok", 200


if __name__ == '__main__':
    print("=" * 50)
    print("🌱 CARBON CREDITS INTELLIGENCE PLATFORM")
    print("=" * 50)
    print("🔧 DEBUG MODE: ON")
    print("📊 Current trials:", len(TRIALS_DATA))
    print("🌐 Server starting on http://localhost:5000")
    print("=" * 50)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True,
        threaded=True
    )
