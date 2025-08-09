# responses.py

def format_agent_html(query, agent_response, language_name, search_data, location_specific):
    """Formata a resposta do agente em HTML"""
    formatted = f"""
    <h4 style="color: #6b46c1;">🎯 Análise Inteligente: {query}</h4>
    <div style="background: #f0f9ff; padding: 12px; border-radius: 8px; border-left: 4px solid #0ea5e9;">
        <h5 style="color: #0369a1;">🌐 Pesquisa Realizada:</h5>
        <p style="font-size: 13px;"><strong>Idioma:</strong> {language_name} | <strong>Fontes:</strong> {search_data['total_found']} | <strong>Estratégia:</strong> {'Local (Brasil)' if location_specific else 'Global'}</p>
    </div>
    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb;">
        {agent_response.replace(chr(10), '<br>').replace('**', '<strong>').replace('**', '</strong>')}
    </div>
    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">
        <h5 style="color: #059669;">💡 Fontes Consultadas:</h5>
        <p style="font-size: 13px;"><strong>APIs:</strong> {', '.join([r.source for r in search_data['results'][:3]])} | <strong>Atualização:</strong> Dados em tempo real</p>
    </div>
    """
    return formatted

def generate_fallback_response(query):
    """Gera resposta estática inteligente"""
    query_lower = query.lower()
    if any(term in query_lower for term in ['cop30', 'cop 30', 'belém', 'belem']):
        return generate_cop30_response(query)
    elif any(term in query_lower for term in ['preço', 'precos', 'price', 'valor', 'custo']):
        return generate_price_response(query)
    else:
        return generate_default_response(query)

def generate_default_response(query):
    return f"""
    <h4 style="color: #059669;">Informação sobre Créditos de Carbono</h4>
    <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #0ea5e9;">
        <p>
            Não encontramos uma resposta específica para sua consulta: <strong>{query}</strong>.<br>
            Por favor, refine sua pergunta ou tente termos relacionados a créditos de carbono, COP30, preços ou regulamentações.
        </p>
        <p>
            <strong>Fontes:</strong> <a href="https://carboncredits.com/" target="_blank">CarbonCredits.com</a>, <a href="https://unfccc.int" target="_blank">UNFCCC</a>
        </p>
    </div>
    """

def generate_price_response(query):
    return """
    <h4 style="color: #059669;">Preços de Créditos de Carbono</h4>
    <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #0ea5e9;">
        <p>
            O preço dos créditos de carbono pode variar significativamente dependendo do mercado, tipo de projeto e região. Em mercados voluntários, os preços geralmente variam entre US$ 2 e US$ 20 por tonelada de CO₂ equivalente, enquanto em mercados regulados podem ser superiores a US$ 40/tCO₂e.
        </p>
        <p>
            <strong>Fontes:</strong> <a href="https://carboncredits.com/carbon-prices-today/" target="_blank">CarbonCredits.com</a>, <a href="https://www.iea.org/reports/carbon-pricing" target="_blank">IEA</a>
        </p>
    </div>
    """

def generate_cop30_response(query):
    return """
    <h4 style="color: #059669;">COP30 — Conferência das Partes em Belém</h4>
    <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #0ea5e9;">
        <p>
            A COP30 será realizada em Belém, Pará, Brasil, em 2025, reunindo líderes globais para discutir ações climáticas e políticas de carbono.
            O evento destaca a importância da Amazônia na agenda climática internacional e deve impulsionar debates sobre créditos de carbono, sustentabilidade e preservação ambiental.
        </p>
        <p>
            <strong>Fontes:</strong> <a href="https://unfccc.int" target="_blank">UNFCCC</a>, <a href="https://www.gov.br/mre/pt-br" target="_blank">Itamaraty</a>
        </p>
    </div>
    """
