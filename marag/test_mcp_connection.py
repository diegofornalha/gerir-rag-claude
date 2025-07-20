#!/usr/bin/env python3
"""
Teste de conexão MCP para Marag
"""

import json
import subprocess
import sys
from pathlib import Path


class MCPTester:
    """Testador de conexão MCP"""
    
    def __init__(self):
        self.mcp_server_path = Path(__file__).parent / "mcp_server.py"
        self.process = None
    
    def start_server(self):
        """Inicia o servidor MCP"""
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(self.mcp_server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("✅ Servidor MCP iniciado")
            return True
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False
    
    def send_request(self, request):
        """Envia requisição para o servidor MCP"""
        if not self.process:
            print("❌ Servidor não está rodando")
            return None
        
        try:
            # Enviar requisição
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # Ler resposta
            response_line = self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
            else:
                return None
        except Exception as e:
            print(f"❌ Erro ao enviar requisição: {e}")
            return None
    
    def test_initialize(self):
        """Testa inicialização"""
        print("\n🧪 Testando inicialização...")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = self.send_request(request)
        if response and "result" in response:
            print("✅ Inicialização bem-sucedida")
            print(f"📊 Versão: {response['result'].get('protocolVersion', 'N/A')}")
            return True
        else:
            print("❌ Falha na inicialização")
            return False
    
    def test_list_tools(self):
        """Testa listagem de ferramentas"""
        print("\n🧪 Testando listagem de ferramentas...")
        
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = self.send_request(request)
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            print(f"✅ {len(tools)} ferramentas encontradas:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            return True
        else:
            print("❌ Falha ao listar ferramentas")
            return False
    
    def test_extract_contact(self):
        """Testa extração de contato"""
        print("\n🧪 Testando extração de contato...")
        
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "extract_contact",
                "arguments": {
                    "text": "Meu nome é João Silva, email: joao.silva@exemplo.com, telefone: (11) 99999-9999"
                }
            }
        }
        
        response = self.send_request(request)
        if response and "result" in response:
            result = response["result"]
            if "extracted_data" in result:
                data = result["extracted_data"]
                print("✅ Extração bem-sucedida:")
                print(f"  Nome: {data.get('name', 'N/A')}")
                print(f"  Email: {data.get('email', 'N/A')}")
                print(f"  Telefone: {data.get('phone', 'N/A')}")
                return True
            else:
                print("❌ Falha na extração")
                return False
        else:
            print("❌ Falha ao chamar ferramenta")
            return False
    
    def test_save_to_rag(self):
        """Testa salvamento no RAG"""
        print("\n🧪 Testando salvamento no RAG...")
        
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "save_to_rag",
                "arguments": {
                    "title": "Teste MCP - João Silva",
                    "content": "Contato extraído via MCP: João Silva - joao.silva@exemplo.com",
                    "source": "marag_mcp_test"
                }
            }
        }
        
        response = self.send_request(request)
        if response and "result" in response:
            result = response["result"]
            if result.get("success"):
                print("✅ Salvamento bem-sucedido")
                print(f"  ID: {result.get('document_id', 'N/A')}")
                return True
            else:
                print("❌ Falha no salvamento")
                return False
        else:
            print("❌ Falha ao salvar no RAG")
            return False
    
    def test_search_rag(self):
        """Testa busca no RAG"""
        print("\n🧪 Testando busca no RAG...")
        
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "search_rag",
                "arguments": {
                    "query": "João Silva",
                    "limit": 3
                }
            }
        }
        
        response = self.send_request(request)
        if response and "result" in response:
            result = response["result"]
            total = result.get("total", 0)
            print(f"✅ Busca bem-sucedida: {total} resultados")
            return True
        else:
            print("❌ Falha na busca")
            return False
    
    def test_get_rag_stats(self):
        """Testa estatísticas do RAG"""
        print("\n🧪 Testando estatísticas do RAG...")
        
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_rag_stats",
                "arguments": {}
            }
        }
        
        response = self.send_request(request)
        if response and "result" in response:
            result = response["result"]
            print("✅ Estatísticas obtidas:")
            print(f"  Total de documentos: {result.get('total_documents', 0)}")
            print(f"  Documentos Marag: {result.get('marag_documents', 0)}")
            print(f"  Tamanho do cache: {result.get('cache_size', 0)} bytes")
            return True
        else:
            print("❌ Falha ao obter estatísticas")
            return False
    
    def stop_server(self):
        """Para o servidor"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("✅ Servidor MCP parado")
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🧪 Teste de Conexão MCP - Marag")
        print("=" * 50)
        
        # Iniciar servidor
        if not self.start_server():
            return False
        
        try:
            # Executar testes
            tests = [
                ("Inicialização", self.test_initialize),
                ("Listagem de Ferramentas", self.test_list_tools),
                ("Extração de Contato", self.test_extract_contact),
                ("Salvamento no RAG", self.test_save_to_rag),
                ("Busca no RAG", self.test_search_rag),
                ("Estatísticas do RAG", self.test_get_rag_stats)
            ]
            
            results = []
            for test_name, test_func in tests:
                try:
                    success = test_func()
                    results.append((test_name, success))
                except Exception as e:
                    print(f"❌ Erro no teste {test_name}: {e}")
                    results.append((test_name, False))
            
            # Mostrar resultados
            print("\n" + "=" * 50)
            print("📊 Resultados dos Testes:")
            
            passed = 0
            for test_name, success in results:
                status = "✅ PASSOU" if success else "❌ FALHOU"
                print(f"  {test_name}: {status}")
                if success:
                    passed += 1
            
            print(f"\n🎯 Total: {passed}/{len(results)} testes passaram")
            
            if passed == len(results):
                print("\n🎉 Todos os testes passaram! MCP funcionando perfeitamente!")
                return True
            else:
                print("\n⚠️  Alguns testes falharam. Verifique a configuração.")
                return False
                
        finally:
            self.stop_server()


def main():
    """Função principal"""
    tester = MCPTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 Marag está pronto para conectar ao MCP A2A Gateway!")
        print("📝 Configure o arquivo ~/.cursor/mcp.json para usar o servidor.")
    else:
        print("\n❌ Problemas detectados. Verifique os logs acima.")


if __name__ == "__main__":
    main() 