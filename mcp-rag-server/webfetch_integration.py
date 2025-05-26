#!/usr/bin/env python3
"""
WebFetch Integration para MCP-RAG
Captura e indexa automaticamente documentações web
"""

import json
import re
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import hashlib

class WebFetchRAGIntegration:
    """Integra WebFetch com RAG para criar knowledge base automático"""
    
    def __init__(self, rag_index):
        self.rag_index = rag_index
        self.processed_urls = set()
        self.domain_configs = {
            "modelcontextprotocol.io": {
                "name": "MCP Documentation",
                "selectors": {
                    "content": ["main", "article", ".content"],
                    "title": ["h1", "title"],
                    "sections": ["h2", "h3"]
                },
                "index_subpages": True
            },
            "docs.anthropic.com": {
                "name": "Claude Documentation", 
                "selectors": {
                    "content": ["main", ".docs-content"],
                    "title": ["h1", "title"],
                    "sections": ["h2", "h3"]
                },
                "index_subpages": True
            },
            "langchain.com": {
                "name": "LangChain Documentation",
                "selectors": {
                    "content": [".docs-content", "main"],
                    "title": ["h1"],
                    "sections": ["h2", "h3"]
                },
                "index_subpages": True
            }
        }
    
    async def fetch_and_index_url(self, url: str, depth: int = 0, max_depth: int = 2) -> Dict:
        """Busca e indexa conteúdo de uma URL"""
        # Evitar reprocessamento
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in self.processed_urls:
            return {"status": "already_processed", "url": url}
        
        self.processed_urls.add(url_hash)
        
        try:
            # Identificar domínio e configuração
            domain = self._extract_domain(url)
            config = self.domain_configs.get(domain, self._get_default_config())
            
            # Buscar conteúdo
            content_data = await self._fetch_content(url, config)
            
            if not content_data:
                return {"status": "fetch_failed", "url": url}
            
            # Preparar documento para indexação
            doc_content = self._prepare_document(content_data, url, config)
            
            # Indexar no RAG
            doc_id = self.rag_index.add_document(
                content=doc_content,
                source=f"web:{domain}",
                metadata={
                    "url": url,
                    "domain": domain,
                    "title": content_data.get("title", ""),
                    "fetch_date": datetime.now().isoformat(),
                    "depth": depth
                }
            )
            
            result = {
                "status": "indexed",
                "url": url,
                "doc_id": doc_id,
                "title": content_data.get("title", ""),
                "sections": len(content_data.get("sections", [])),
                "subpages": []
            }
            
            # Indexar subpáginas se configurado
            if config.get("index_subpages") and depth < max_depth:
                subpage_urls = self._extract_relevant_links(
                    content_data.get("html", ""), 
                    url, 
                    domain
                )
                
                for subpage_url in subpage_urls[:10]:  # Limitar a 10 subpáginas
                    sub_result = await self.fetch_and_index_url(
                        subpage_url, 
                        depth + 1, 
                        max_depth
                    )
                    result["subpages"].append(sub_result)
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    async def _fetch_content(self, url: str, config: Dict) -> Optional[Dict]:
        """Busca conteúdo HTML de uma URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extrair conteúdo baseado nos seletores
                    content_parts = []
                    
                    # Título
                    title = ""
                    for selector in config["selectors"]["title"]:
                        elem = soup.select_one(selector)
                        if elem:
                            title = elem.get_text(strip=True)
                            break
                    
                    # Conteúdo principal
                    for selector in config["selectors"]["content"]:
                        elements = soup.select(selector)
                        for elem in elements:
                            text = elem.get_text(separator='\n', strip=True)
                            if text:
                                content_parts.append(text)
                    
                    # Seções
                    sections = []
                    for selector in config["selectors"]["sections"]:
                        headers = soup.select(selector)
                        for header in headers:
                            sections.append(header.get_text(strip=True))
                    
                    return {
                        "title": title,
                        "content": "\n\n".join(content_parts),
                        "sections": sections,
                        "html": str(soup)
                    }
                    
        except Exception as e:
            print(f"Erro ao buscar {url}: {e}")
            return None
    
    def _prepare_document(self, content_data: Dict, url: str, config: Dict) -> str:
        """Prepara documento para indexação"""
        parts = [
            f"# {content_data.get('title', 'Sem título')}",
            f"Fonte: {url}",
            f"Tipo: {config.get('name', 'Documentação Web')}",
            ""
        ]
        
        # Adicionar índice de seções se houver
        sections = content_data.get('sections', [])
        if sections:
            parts.append("## Índice")
            for section in sections[:20]:  # Limitar a 20 seções
                parts.append(f"- {section}")
            parts.append("")
        
        # Adicionar conteúdo principal
        content = content_data.get('content', '')
        # Limitar tamanho do conteúdo
        if len(content) > 10000:
            content = content[:10000] + "\n\n[Conteúdo truncado...]"
        
        parts.append(content)
        
        return "\n".join(parts)
    
    def _extract_domain(self, url: str) -> str:
        """Extrai domínio de uma URL"""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower()
    
    def _get_default_config(self) -> Dict:
        """Configuração padrão para sites não mapeados"""
        return {
            "name": "Web Documentation",
            "selectors": {
                "content": ["main", "article", "[role='main']", ".content", "#content"],
                "title": ["h1", "title"],
                "sections": ["h2", "h3"]
            },
            "index_subpages": False
        }
    
    def _extract_relevant_links(self, html: str, base_url: str, domain: str) -> List[str]:
        """Extrai links relevantes para indexação"""
        import urllib.parse
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Resolver URL relativa
            full_url = urllib.parse.urljoin(base_url, href)
            parsed = urllib.parse.urlparse(full_url)
            
            # Filtrar apenas links do mesmo domínio
            if parsed.netloc.lower() == domain:
                # Ignorar âncoras e recursos
                if not any(ext in parsed.path for ext in ['.pdf', '.zip', '.png', '.jpg', '#']):
                    links.add(full_url)
        
        return list(links)
    
    async def create_knowledge_base(self, urls: List[str]) -> Dict:
        """Cria knowledge base a partir de lista de URLs"""
        results = {
            "total_urls": len(urls),
            "indexed": 0,
            "failed": 0,
            "details": []
        }
        
        for url in urls:
            print(f"Indexando: {url}")
            result = await self.fetch_and_index_url(url)
            
            if result["status"] == "indexed":
                results["indexed"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append(result)
        
        # Salvar índice
        self.rag_index.save()
        
        return results

# Exemplo de uso standalone
async def example_usage():
    """Exemplo de como usar a integração"""
    from pathlib import Path
    import sys
    sys.path.append(str(Path(__file__).parent))
    from server import RAGIndex
    
    # Criar índice RAG
    cache_dir = Path.home() / ".claude" / "mcp-rag-cache"
    rag_index = RAGIndex(cache_dir)
    
    # Criar integração
    web_integration = WebFetchRAGIntegration(rag_index)
    
    # URLs para indexar
    urls = [
        "https://modelcontextprotocol.io/docs/concepts/architecture",
        "https://modelcontextprotocol.io/docs/concepts/tools", 
        "https://docs.anthropic.com/en/docs/claude-code",
        "https://langchain.com/docs/concepts/rag"
    ]
    
    # Criar knowledge base
    print("Criando knowledge base...")
    results = await web_integration.create_knowledge_base(urls)
    
    print(f"\nResultados:")
    print(f"- Indexados: {results['indexed']}")
    print(f"- Falhas: {results['failed']}")
    
    # Testar busca
    print("\nTestando busca...")
    search_results = rag_index.search("MCP tools architecture", mode="hybrid")
    for i, result in enumerate(search_results, 1):
        print(f"\n{i}. {result['source']} (Score: {result['score']:.2f})")
        print(f"   {result['content'][:200]}...")

if __name__ == "__main__":
    asyncio.run(example_usage())