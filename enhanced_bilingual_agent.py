"""
🌱 Enhanced Carbon Credits Agent with Portuguese Support
======================================================
Multi-language Carbon Credits Intelligence Platform for global markets
"""

import os
import requests
import json
from datetime import datetime
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    score: float = 0.0

class BilingualCarbonAgent:
    """Enhanced Carbon Credits Agent with Portuguese/English support"""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BilingualCarbonAgent, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return  # Evita reexecutar o __init__
        self._initialized = True

        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = os.getenv('GOOGLE_CSE_ID')
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        
        self.search_priority = ["google", "serper", "tavily", "duckduckgo"]
        # Global time budget for a search (seconds)
        try:
            self.global_timeout = float(os.getenv('SEARCH_TIMEOUT_SECONDS', '9'))
        except Exception:
            self.global_timeout = 9.0
        # Toggle for DDG usage (disable on platforms that rate-limit)
        self.use_ddg = os.getenv('SEARCH_USE_DDG', '1') not in ('0', 'false', 'False', '')
        # Suppress noisy logs from duckduckgo_search
        logging.getLogger('duckduckgo_search').setLevel(logging.WARNING)
        
        if self.google_api_key and self.google_cse_id:
            print("✅ Google Custom Search API configured - Primary search engine")
        if self.serper_api_key:
            print("✅ Serper API key configured - Secondary search engine")
        if self.tavily_api_key:
            print("✅ Tavily AI API key configured - Tertiary search engine")
        
        self.setup_language_detection()
        self.setup_portuguese_responses()

    def setup_language_detection(self):
        self.portuguese_keywords = [
            'créditos', 'carbono', 'compensação', 'mercado', 'brasil', 'onde',
            'como', 'posso', 'comprar', 'vender', 'preço', 'certificação',
            'sustentabilidade', 'emissões', 'empresa', 'investimento',
            'qual', 'quando', 'porque', 'quem', 'quanto', 'devo', 'preciso'
        ]
        self.brazilian_entities = [
            'brasil', 'brazil', 'bvrio', 'b3', 'petrobras', 'bndes',
            'amazônia', 'amazon', 'cerrado', 'mata atlântica'
        ]

    def setup_portuguese_responses(self):
        self.pt_responses = {
            'welcome': """🌱 **Especialista em Créditos de Carbono com IA**

Olá! Sou seu assistente inteligente para o mercado de créditos de carbono. 

**🔍 Posso ajudá-lo com:**
• Preços atuais e tendências de mercado
• Análise de projetos e oportunidades
• Regulamentações e padrões (VCS, Gold Standard)
• Cálculos de compensação de carbono
• Mercado brasileiro e global
• Pesquisas e dados acadêmicos

**Experimente perguntar:**
• "Qual o preço atual dos créditos de carbono no Brasil?"
• "Onde comprar créditos verificados?"
• "Como calcular compensação para minha empresa?"

Como posso ajudá-lo hoje?""",

            'search_results': """🔍 **Resultados da Pesquisa - {query}**

{results_content}""",
            'market_summary': """🇧🇷 **Resumo do Mercado Brasileiro (2024):**

• **Volume:** 50M+ créditos negociados
• **Valor:** R$ 2+ bilhões
• **Crescimento:** 25-30% ao ano
• **Principais setores:** Energia, florestal, agricultura

**🏢 Principais plataformas:**
• BVRio - maior volume
• B3 - futuros de carbono
• Mercado internacional via Verra""",

            'api_status': """⚙️ **Status das APIs de Pesquisa:**

{api_status_content}

**🔄 Sistema de Busca Inteligente:**
1. **Google Custom Search** - Resultados acadêmicos e técnicos
2. **Tavily AI** - Consultas específicas por localização  
3. **Serper API** - Dados de mercado em tempo real
4. **DuckDuckGo** - Backup para disponibilidade máxima"""
        }
    
    def detect_language(self, query: str) -> str:
        """Detect if query is in Portuguese or English"""
        query_lower = query.lower()
        
        pt_score = 0
        for keyword in self.portuguese_keywords:
            if keyword in query_lower:
                pt_score += 1
        
        for entity in self.brazilian_entities:
            if entity in query_lower:
                pt_score += 2
        
        return 'pt-BR' if pt_score > 0 else 'en'
    
    def is_location_specific(self, query: str) -> bool:
        """Check if query is asking about a specific location"""
        location_indicators = [
            'where', 'onde', 'in brazil', 'no brasil', 'brasil',
            'são paulo', 'rio de janeiro', 'amazon', 'amazônia'
        ]
        return any(indicator in query.lower() for indicator in location_indicators)
    
    def _search_tavily(self, query: str, language: str) -> List[SearchResult]:
        """Search using Tavily AI - best for location-specific queries"""
        if not self.tavily_api_key:
            return []
        
        try:
            search_query = query
            if language == 'pt-BR':
                # Enhance Portuguese queries for better results
                if 'brasil' in query.lower() or 'brazil' in query.lower():
                    search_query += " Brasil carbon credits market BVRio B3"
            
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {self.tavily_api_key}"},
                json={
                    "query": search_query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_domains": ["bvrio.org", "b3.com.br", "verra.org", "goldstandard.org"],
                    "max_results": 8
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('results', []):
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('content', '')[:300],
                        source="Tavily AI",
                        score=0.9
                    ))
                
                return results[:5]
                
        except Exception as e:
            print(f"⚠️ Tavily search error: {e}")
            return []
    
    def _search_serper(self, query: str) -> List[SearchResult]:
        """Search using Serper API (Google Search alternative)"""
        if not self.serper_api_key:
            return []
            
        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': 8,
                'autocorrect': True,
                'safe': 'active'
            }
            
            response = requests.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('organic', []):
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', '')[:300],
                        source="Serper API",
                        score=0.95
                    ))
                
                return results[:5]
            else:
                print(f"⚠️ Serper API returned status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️ Serper search error: {e}")
            return []
    
    def _search_google(self, query: str) -> List[SearchResult]:
        """Search using Google Custom Search API with enhanced error handling"""
        if not self.google_api_key or not self.google_cse_id:
            print("⚠️ Google API credentials not configured, skipping...")
            return []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'num': 5
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('items', []):
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', ''),
                        source="Google Custom Search",
                        score=0.8
                    ))
                
                print(f"✅ Google Custom Search: Found {len(results)} results")
                return results
            elif response.status_code == 403:
                print("❌ Google API Error (403): API blocked or quota exceeded")
                print("🔧 Solution: Check API billing, quotas, or use alternative search")
                return []
            elif response.status_code == 429:
                print("⚠️ Google API Rate Limit: Too many requests")
                return []
            else:
                print(f"⚠️ Google API Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️ Google search error: {e}")
            return []
    
    def _search_duckduckgo(self, query: str) -> List[SearchResult]:
        """Fallback search using DuckDuckGo"""
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for result in ddgs.text(query, max_results=5):
                    results.append(SearchResult(
                        title=result.get('title', ''),
                        url=result.get('href', ''),
                        snippet=result.get('body', '')[:200],
                        source="DuckDuckGo",
                        score=0.6
                    ))

            return results

        except Exception as e:
            # Treat DDG issues as non-fatal
            print(f"⚠️ DuckDuckGo fallback unavailable: {e}")
            return []
    
    def comprehensive_search(self, query: str) -> Dict:
        """Perform searches in parallel within a global time budget to avoid timeouts."""
        language = self.detect_language(query)
        is_location_query = self.is_location_specific(query)
        print(f"🔍 Language: {'Portuguese' if language == 'pt-BR' else 'English'}")
        print(f"📍 Location-specific: {'Yes' if is_location_query else 'No'}")

        tasks = []
        results_map: Dict[str, List[SearchResult]] = {}

        def submit(executor, name, fn, *args):
            try:
                future = executor.submit(fn, *args)
                tasks.append((name, future))
            except Exception as e:
                print(f"⚠️ Failed to submit task {name}: {e}")

        with ThreadPoolExecutor(max_workers=4) as executor:
            if self.google_api_key and self.google_cse_id:
                submit(executor, 'Google Custom Search', self._search_google, query)
            if self.serper_api_key:
                submit(executor, 'Serper API', self._search_serper, query)
            # Tavily: only if location or we need more coverage
            submit(executor, 'Tavily AI', self._search_tavily, query, language)
            # DDG as optional final fallback
            if self.use_ddg:
                submit(executor, 'DuckDuckGo', self._search_duckduckgo, query)

            try:
                deadline = self.global_timeout
                start = datetime.now()
                for name, future in tasks:
                    remaining = max(0.1, deadline - (datetime.now() - start).total_seconds())
                    if remaining <= 0:
                        break
                    try:
                        data = future.result(timeout=remaining)
                        if data:
                            results_map[name] = data
                    except Exception as e:
                        print(f"⚠️ {name} timed out/failed: {e}")
            finally:
                # Best-effort: cancel unfinished tasks
                for _, f in tasks:
                    if not f.done():
                        f.cancel()

        all_results: List[SearchResult] = []
        sources_used: List[str] = []
        # Preserve a priority order when merging
        for key in ["Google Custom Search", "Serper API", "Tavily AI", "DuckDuckGo"]:
            if key in results_map and results_map[key]:
                sources_used.append(key)
                all_results.extend(results_map[key])

        print(f"📊 Total sources used: {', '.join(sources_used) if sources_used else 'None'}")
        print(f"📈 Total results found: {len(all_results)}")

        return {
            'query': query,
            'language': language,
            'results': all_results[:10],
            'sources_used': sources_used,
            'total_found': len(all_results),
            'timestamp': datetime.now().isoformat()
        }
    
    def format_response(self, search_data: Dict) -> str:
        """Format response in appropriate language"""
        language = search_data['language']
        query = search_data['query']
        results = search_data['results']
        
        if language == 'pt-BR':
            return self._format_portuguese_response(query, results)
        else:
            return self._format_english_response(query, results)
    
    def _format_portuguese_response(self, query: str, results: List[SearchResult]) -> str:
        """Format response in Portuguese"""
        if not results:
            return self.pt_responses['welcome']
        
        results_content = ""
        for i, result in enumerate(results[:5], 1):
            results_content += f"""
**{i}. {result.title}**
🔗 {result.url}
📝 {result.snippet}
🏷️ Fonte: {result.source}
"""
        
        market_analysis = """
• Preços atuais: R$ 40-250 por tCO2e (mercado voluntário)
• Tendência: Alta demanda por projetos brasileiros
• Regulamentação: Aguardando marco legal nacional
• Oportunidades: REDD+, energia renovável, agricultura regenerativa
"""
        
        recommendations = """
• Verifique certificações (VCS, Gold Standard)
• Considere co-benefícios socioambientais  
• Avalie adicionalidade dos projetos
• Monitore tendências regulatórias
"""
        
        return self.pt_responses['search_results'].format(
            query=query,
            results_content=results_content,
            market_analysis=market_analysis,
            recommendations=recommendations
        )
    
    def _format_english_response(self, query: str, results: List[SearchResult]) -> str:
        """Format response in English"""
        if not results:
            return """🌱 **Carbon Credits Intelligence Agent**

Hello! I'm your AI assistant for carbon credits research and market intelligence.

**🔍 I can help you with:**
• Current market prices and trends
• Project analysis and investment opportunities  
• Standards and verification (VCS, Gold Standard)
• Carbon offset calculations
• Brazilian and global markets
• Academic research and data

**Try asking:**
• "Current carbon credit prices in Brazil"
• "Where to buy verified carbon credits"
• "How to calculate corporate carbon offsets"

How can I assist you today?"""
        
        results_content = ""
        for i, result in enumerate(results[:5], 1):
            results_content += f"""
**{i}. {result.title}**
🔗 {result.url}
📝 {result.snippet}
🏷️ Source: {result.source}
"""
        
        return f"""🔍 **Search Results - {query}**

{results_content}

**📊 Market Analysis:**
• Current prices: $10-50 per tCO2e (voluntary market)
• Trend: Growing demand for high-quality credits
• Regulation: Evolving frameworks globally
• Opportunities: Nature-based solutions, direct air capture

**💡 Next Steps:**
• Verify project certifications (VCS, Gold Standard)
• Consider co-benefits and permanence
• Evaluate additionality claims
• Monitor regulatory developments"""
    
    def check_api_status(self, language: str = 'en') -> str:
        """Check status of all search APIs"""
        status_info = []
        
        # Google API
        if self.google_api_key and self.google_cse_id:
            status_info.append("✅ Google Custom Search: Configurado")
        else:
            status_info.append("❌ Google Custom Search: Chaves ausentes")
        
        # Tavily API  
        if self.tavily_api_key:
            status_info.append("✅ Tavily AI: Configurado")
        else:
            status_info.append("❌ Tavily AI: Chave ausente")
        
        # Serper API
        if self.serper_api_key:
            status_info.append("✅ Serper API: Configurado")
        else:
            status_info.append("❌ Serper API: Chave ausente")
        
        # DuckDuckGo status
        status_info.append("✅ DuckDuckGo: Disponível" if self.use_ddg else "⏸️ DuckDuckGo: Desativado")
        
        if language == 'pt-BR':
            return self.pt_responses['api_status'].format(
                api_status_content='\n'.join(status_info)
            )
        else:
            return f"""⚙️ **Search APIs Status:**

{chr(10).join(status_info)}

**🔄 Intelligent Search System:**
1. **Google Custom Search** - Academic and technical results
2. **Tavily AI** - Location-specific queries
3. **Serper API** - Real-time market data  
4. **DuckDuckGo** - Backup for maximum availability"""

def main():
    """Main function for testing"""
    agent = BilingualCarbonAgent()
    
    print("🌱 Enhanced Bilingual Carbon Credits Agent")
    print("=" * 50)
    
    test_queries = [
        "Onde posso comprar créditos de carbono no Brasil?",
        "Qual é o preço atual dos créditos de carbono?",
        "Como funciona o mercado de carbono brasileiro?",
        "Where can I buy carbon credits in Brazil?",
        "What are the current carbon credit prices?",
        "How does the Brazilian carbon market work?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 40)
        
        search_data = agent.comprehensive_search(query)
        response = agent.format_response(search_data)
        
        # Show first 300 characters
        print(response[:300] + "..." if len(response) > 300 else response)
        print()

if __name__ == "__main__":
    main()
