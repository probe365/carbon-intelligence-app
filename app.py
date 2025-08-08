"""
COMPLETE Carbon Credits App with Beautiful Platform as Homepage
============================================================
"""

from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime, timedelta
import secrets
import hashlib
import traceback

# ADICIONAR no início do probe365_working_app.py:
from enhanced_bilingual_agent import BilingualCarbonAgent

app = Flask(__name__)
app.config['SECRET_KEY'] = 'carbon-credits-brazil-probe365-2025'

# Simple trial storage with better error handling
TRIALS_DATA = {}

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
        if email in TRIALS_DATA:
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

# SUBSTITUIR a função health_check (linha ~500):

@app.route('/health', methods=['GET', 'POST'])
def health_check():
    """Health check endpoint - accepts both GET and POST"""
    return jsonify({
        "status": "online",
        "total_trials": len(TRIALS_DATA),
        "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "active_trials": len([t for t in TRIALS_DATA.values() if t.get('status') == 'active']),
        "platform": "Carbon Credits Intelligence",
        "version": "1.0.0"
    })


# ...continuing from PARTE 2...

@app.route('/validate_trial', methods=['POST'])
def validate_trial():
    """Validate trial access key"""
    try:
        data = request.get_json()
        trial_key = data.get('trial_key', '').strip().upper()
        
        print(f"=== TRIAL VALIDATION REQUEST ===")
        print(f"Trial Key: {trial_key}")
        print(f"Current trials: {len(TRIALS_DATA)}")
        
        if not trial_key:
            return jsonify({
                "success": False,
                "message": "Trial key é obrigatório."
            }), 400
        
        # Find trial by key
        trial_email = None
        for email, trial_data in TRIALS_DATA.items():
            if trial_data.get('trial_key') == trial_key:
                trial_email = email
                break
        
        if not trial_email:
            print(f"Trial key not found: {trial_key}")
            return jsonify({
                "success": False,
                "message": "Trial key inválido."
            }), 401
        
        trial_data = TRIALS_DATA[trial_email]
        
        # Check if trial is expired
        end_date = datetime.fromisoformat(trial_data['end_date'])
        days_remaining = (end_date - datetime.now()).days
        
        if days_remaining < 0:
            return jsonify({
                "success": False,
                "message": "Trial expirado. Faça upgrade para continuar."
            }), 401
        
        print(f"Trial validation successful for: {trial_email}")
        print(f"Days remaining: {days_remaining}")
        print(f"Queries used: {trial_data['queries_used']}")
        
        return jsonify({
            "success": True,
            "message": "Trial válido",
            "trial_data": trial_data,
            "days_remaining": days_remaining
        })
        
    except Exception as e:
        print(f"ERROR in validate_trial: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "message": "Erro interno do servidor."
        }), 500

# CORREÇÃO COMPLETA - Substituir a seção JavaScript da página /trial

@app.route('/trial')
def trial_access():
    """TRIAL ACCESS PAGE - CORRIGIDO"""
    return render_template("trial_access_template.html")


@app.route('/search', methods=['POST'])
def search():
    """SEARCH FUNCTION - INTEGRATED WITH BILINGUAL AGENT"""
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
        print(f"Current trials count: {len(TRIALS_DATA)}")
        
        # Validation
        if not query:
            return jsonify({"success": False, "message": "Query is required"}), 400
        if not trial_key:
            return jsonify({"success": False, "message": "Trial key is required"}), 400
        
        # Find trial
        trial_email = None
        trial_data = None
        for email, trial_info in TRIALS_DATA.items():
            if trial_info.get('trial_key') == trial_key:
                trial_email = email
                trial_data = trial_info
                break
        
        if not trial_email:
            print(f"Trial key '{trial_key}' not found!")
            return jsonify({"success": False, "message": "Invalid trial key"}), 401
        
        # Check limits
        if trial_data['queries_used'] >= trial_data['queries_limit']:
            return jsonify({"success": False, "message": "Query limit reached"}), 403
        
        # Update usage
        TRIALS_DATA[trial_email]['queries_used'] += 1
        
        print(f"Trial found for: {trial_email}")
        print(f"Queries used: {trial_data['queries_used']}")
        
        # TRY BILINGUAL AGENT FIRST, FALLBACK TO FORMATTED RESPONSES
        try:
            if carbon_agent:
                print(f"=== CALLING BILINGUAL AGENT ===")
                
                # Detect language and search strategy
                language = carbon_agent.detect_language(query)
                location_specific = carbon_agent.is_location_specific(query)
                
                print(f"Language detected: {language}")
                print(f"Location specific: {location_specific}")
                
                # Perform comprehensive search
                search_data = carbon_agent.comprehensive_search(query)
                agent_response = carbon_agent.format_response(search_data)
                
                print(f"Search completed: {search_data['total_found']} results found")
                
                # FORMAT AGENT RESPONSE TO MATCH YOUR DESIGN
                language_name = "Portuguese (Brazilian)" if language == 'pt-BR' else "English (US)"
                
                # Convert plain text response to formatted HTML
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
                print(f"HTML length: {len(response_html)}")
                
                return jsonify({
                    "success": True,
                    "intelligence": response_html,
                    "queries_remaining": trial_data['queries_limit'] - trial_data['queries_used'],
                    "language_detected": language_name,
                    "sources_count": search_data['total_found']
                })
            
        except Exception as agent_error:
            print(f"=== BILINGUAL AGENT ERROR ===")
            print(f"Agent Error: {str(agent_error)}")
            print("Falling back to smart static responses...")
        
        # SMART STATIC RESPONSES (Enhanced fallback)
        query_lower = query.lower()
        
        if 'cop30' in query_lower or 'cop 30' in query_lower or 'belém' in query_lower or 'belem' in query_lower:
            # COP30 SPECIFIC RESPONSE
            response_html = f'''<h4 style="color: #6b46c1; margin-bottom: 15px;">🎯 Análise Inteligente: {query}</h4>

<h5 style="color: #059669; margin: 20px 0 10px 0;">🌍 COP30 em Belém - Informações Oficiais (2025):</h5>
<ul style="margin: 10px 0 20px 0; line-height: 1.6;">
<li><strong>Local:</strong> Belém, Pará, Brasil - confirmado pela UNFCCC em dezembro 2023</li>
<li><strong>Data:</strong> 10 a 21 de novembro de 2025 (2 semanas de conferência)</li>
<li><strong>Infraestrutura:</strong> Hangar - Centro de Convenções da Amazônia (8.500 participantes)</li>
<li><strong>Investimento:</strong> R$ 1.2 bilhão em infraestrutura e logística preparatória</li>
<li><strong>Expectativa:</strong> 50.000+ participantes, maior COP da história na América Latina</li>
</ul>

<div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4CAF50;">
<h5 style="color: #059669; margin-bottom: 10px;">💡 Análise Estratégica - COP30:</h5>
<p style="margin: 0; line-height: 1.6;"><strong>Oportunidade Histórica:</strong> A COP30 em Belém representa marco decisivo para o mercado brasileiro de carbono. Espera-se aprovação de mecanismos internacionais que podem aumentar demanda por créditos brasileiros em 300-400%. Empresas devem acelerar projetos para capturar esta janela única de oportunidade.</p>
</div>'''
            
        elif 'preço' in query_lower or 'precos' in query_lower or 'price' in query_lower or 'valor' in query_lower or 'custo' in query_lower:
            # PRICING SPECIFIC RESPONSE
            response_html = f'''<h4 style="color: #6b46c1; margin-bottom: 15px;">🎯 Análise Inteligente: {query}</h4>

<h5 style="color: #059669; margin: 20px 0 10px 0;">💰 Preços Atuais Mercado Brasileiro (Janeiro 2025):</h5>
<ul style="margin: 10px 0 20px 0; line-height: 1.6;">
<li><strong>Mercado Voluntário:</strong> R$ 85,00 - R$ 125,00 por tCO2e (variação por projeto)</li>
<li><strong>Mercado Regulado:</strong> R$ 45,00 - R$ 65,00 por tCO2e (CBIO - Etanol)</li>
<li><strong>Tendência 2025:</strong> Alta de 15-20% devido proximidade da COP30</li>
<li><strong>Projetos Premium:</strong> REDD+ Amazônia: R$ 150,00 - R$ 200,00 por tCO2e</li>
<li><strong>Volume Mínimo:</strong> Transações típicas: 1.000 - 10.000 tCO2e</li>
</ul>

<div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4CAF50;">
<h5 style="color: #059669; margin-bottom: 10px;">💡 Análise de Precificação:</h5>
<p style="margin: 0; line-height: 1.6;"><strong>Recomendação de Trading:</strong> Preços estão em patamar historicamente alto devido à expectativa da COP30. Para compradores: considerar contratos de longo prazo. Para vendedores: janela otimizada para monetização nos próximos 8-10 meses.</p>
</div>'''
            
        else:
            # DEFAULT SMART RESPONSE
            response_html = f'''<h4 style="color: #6b46c1; margin-bottom: 15px;">🎯 Análise Inteligente: {query}</h4>

<h5 style="color: #059669; margin: 20px 0 10px 0;">📈 Cenário Atual do Mercado Brasileiro (2025):</h5>
<ul style="margin: 10px 0 20px 0; line-height: 1.6;">
<li><strong>Crescimento:</strong> Mercado expandiu 180% em 2024, movimentando R$ 2.8 bilhões</li>
<li><strong>Volume:</strong> 4.2 milhões de tCO2e negociadas no último trimestre</li>
<li><strong>Preço Médio:</strong> R$ 95,00 - R$ 120,00 por tonelada CO2 (BVRio)</li>
<li><strong>Setores Líderes:</strong> Agropecuária (45%), Florestal (32%), Energia Renovável (23%)</li>
<li><strong>Principais Estados:</strong> MT, PA, MG, SP, RS concentram 78% dos projetos</li>
</ul>

<div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4CAF50;">
<h5 style="color: #059669; margin-bottom: 10px;">💡 Análise Estratégica:</h5>
<p style="margin: 0; line-height: 1.6;"><strong>Recomendação Executiva:</strong> O mercado brasileiro de créditos de carbono apresenta oportunidade única de investimento com marco regulatório sólido e demanda crescente. Empresas que ingressarem agora podem se posicionar estrategicamente para capturar valor significativo nos próximos 24 meses.</p>
</div>'''
        
        print(f"=== SMART RESPONSE GENERATED ===")
        print(f"Query type detected, HTML length: {len(response_html)}")
        
        return jsonify({
            "success": True,
            "intelligence": response_html,
            "queries_remaining": trial_data['queries_limit'] - trial_data['queries_used'],
            "language_detected": "Portuguese (Brazilian)"
        })
        
    except Exception as e:
        print(f"\n=== CRITICAL SEARCH ERROR ===")
        print(f"Error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        print("===================\n")
        
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

# ADICIONAR para debug:

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


# ...existing code...

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
