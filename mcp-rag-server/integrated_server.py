#!/usr/bin/env python3
"""
Servidor MCP integrado com o sistema RAG do projeto
Usa a API HTTP existente ao invés de reimplementar
"""
import asyncio
import json
import aiohttp
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuração
API_BASE_URL = "http://localhost:3333/api"  # Porta do seu backend
app = Server("rag-webfetch")

class ProjectRAGClient:
    """Cliente para integrar com o RAG do projeto via API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, mode: str = "hybrid"):
        """Busca via API do projeto"""
        await self.ensure_session()
        
        try:
            async with self.session.post(
                f"{self.base_url}/webfetch/search",
                json={"query": query, "mode": mode}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"API retornou status {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def add_url(self, url: str, category: str = None, max_depth: int = 1):
        """Adiciona URL para indexar via API"""
        await self.ensure_session()
        
        try:
            async with self.session.post(
                f"{self.base_url}/webfetch",
                json={
                    "url": url,
                    "category": category,
                    "maxDepth": max_depth
                }
            ) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    return {"error": f"API retornou status {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_stats(self):
        """Obtém estatísticas via API"""
        await self.ensure_session()
        
        try:
            async with self.session.get(f"{self.base_url}/webfetch/stats") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"API retornou status {response.status}"}
        except Exception as e:
            return {"error": str(e)}

# Cliente global
rag_client = ProjectRAGClient(API_BASE_URL)

@app.list_tools()
async def list_tools():
    """Lista ferramentas disponíveis"""
    return [
        Tool(
            name="rag_search",
            description="Busca informações no RAG do projeto",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto para buscar"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["naive", "local", "global", "hybrid"],
                        "default": "hybrid",
                        "description": "Modo de busca"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="rag_webfetch",
            description="Adiciona URL para indexar no RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL da documentação"
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria (opcional)"
                    },
                    "max_depth": {
                        "type": "integer",
                        "default": 1,
                        "description": "Profundidade máxima (0-3)"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="rag_stats",
            description="Obtém estatísticas do RAG",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Executa ferramentas"""
    
    try:
        if name == "rag_search":
            query = arguments.get("query", "")
            mode = arguments.get("mode", "hybrid")
            
            result = await rag_client.search(query, mode)
            
            if "error" in result:
                return [TextContent(
                    type="text",
                    text=f"❌ Erro na busca: {result['error']}"
                )]
            
            # Formatar resultados
            if result.get("results"):
                output = f"🔍 Encontrados {len(result['results'])} resultados para '{query}':\n\n"
                
                for i, res in enumerate(result['results'], 1):
                    # Se tem documento associado
                    if res.get('doc'):
                        doc = res['doc']
                        output += f"{i}. {doc.get('title', doc.get('url', 'Sem título'))}\n"
                        output += f"   📌 {doc.get('domain', 'N/A')} | {doc.get('category', 'Sem categoria')}\n"
                        output += f"   💡 Score: {res.get('score', 0):.3f}\n"
                    else:
                        output += f"{i}. Resultado {i}\n"
                        output += f"   💡 Score: {res.get('score', 0):.3f}\n"
                    
                    # Mostrar preview do conteúdo
                    content = res.get('content', '')[:200]
                    if content:
                        output += f"   📄 {content}...\n"
                    
                    output += "\n"
            else:
                output = f"❌ Nenhum resultado encontrado para '{query}'"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "rag_webfetch":
            url = arguments.get("url", "")
            category = arguments.get("category")
            max_depth = arguments.get("max_depth", 1)
            
            result = await rag_client.add_url(url, category, max_depth)
            
            if "error" in result:
                return [TextContent(
                    type="text",
                    text=f"❌ Erro ao adicionar URL: {result['error']}"
                )]
            
            output = f"✅ URL adicionada com sucesso!\n\n"
            output += f"🔗 URL: {url}\n"
            output += f"📁 Categoria: {category or 'Não especificada'}\n"
            output += f"🔍 Profundidade: {max_depth} níveis\n"
            output += f"⏳ Status: {result.get('status', 'pending')}\n"
            output += f"\n💡 A indexação será processada em breve pelo sistema."
            
            return [TextContent(type="text", text=output)]
        
        elif name == "rag_stats":
            result = await rag_client.get_stats()
            
            if "error" in result:
                return [TextContent(
                    type="text",
                    text=f"❌ Erro ao obter estatísticas: {result['error']}"
                )]
            
            output = "📊 Estatísticas do RAG:\n\n"
            output += f"📚 Total de documentos: {result.get('total', 0)}\n"
            output += f"✅ Indexados: {result.get('indexed', 0)}\n"
            output += f"⏳ Pendentes: {result.get('pending', 0)}\n"
            output += f"❌ Falhados: {result.get('failed', 0)}\n"
            output += f"📝 Seções totais: {result.get('totalSections', 0)}\n"
            output += f"🔤 Palavras totais: {result.get('totalWords', 0)}\n"
            
            categories = result.get('categories', [])
            if categories:
                output += f"\n🏷️ Categorias: {', '.join(categories)}"
            
            recent = result.get('recentSearches', [])
            if recent:
                output += f"\n\n🔍 Buscas recentes:"
                for search in recent[:5]:
                    output += f"\n  • '{search['query']}' ({search['resultsCount']} resultados)"
            
            return [TextContent(type="text", text=output)]
        
        else:
            return [TextContent(
                type="text",
                text=f"❌ Ferramenta '{name}' não encontrada"
            )]
            
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Erro: {str(e)}"
        )]

async def main():
    """Função principal"""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        await rag_client.close()

if __name__ == "__main__":
    asyncio.run(main())