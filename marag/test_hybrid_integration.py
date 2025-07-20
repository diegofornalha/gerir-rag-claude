#!/usr/bin/env python3
"""
Teste de Integração A2A + MCP - Marag Hybrid Agent
"""

import asyncio
import json
import time
from pathlib import Path
from marag_hybrid_agent import MaragHybridAgent, A2AMessage


class HybridIntegrationTester:
    """Testador de integração A2A + MCP"""
    
    def __init__(self):
        self.agent = MaragHybridAgent()
        self.test_results = []
    
    async def run_integration_tests(self):
        """Executa testes de integração"""
        print("🧪 Teste de Integração A2A + MCP - Marag")
        print("=" * 60)
        
        try:
            # Inicia o agente
            await self.agent.start()
            
            # Executa testes
            await self._test_a2a_communication()
            await self._test_mcp_rag_integration()
            await self._test_mcp_database_integration()
            await self._test_mcp_filesystem_integration()
            await self._test_hybrid_workflow()
            
            # Mostra resultados
            self._show_results()
            
        finally:
            await self.agent.stop()
    
    async def _test_a2a_communication(self):
        """Testa comunicação A2A"""
        print("\n📡 Teste 1: Comunicação A2A")
        print("-" * 40)
        
        # Simula mensagem A2A
        message = A2AMessage(
            role="user",
            parts=[{"kind": "text", "text": "Olá, sou o agente Claude. Preciso extrair um contato."}],
            messageId="test_a2a_1"
        )
        
        response = await self.agent.handle_a2a_request(message)
        
        if response.success:
            print("✅ Comunicação A2A funcionando")
            self.test_results.append(("A2A Communication", True))
        else:
            print(f"❌ Falha na comunicação A2A: {response.error}")
            self.test_results.append(("A2A Communication", False))
    
    async def _test_mcp_rag_integration(self):
        """Testa integração MCP com RAG"""
        print("\n🔍 Teste 2: Integração MCP + RAG")
        print("-" * 40)
        
        # Testa extração e salvamento no RAG
        message = A2AMessage(
            role="user",
            parts=[{"kind": "text", "text": "Extraia o contato: Meu nome é Maria Santos, email: maria.santos@empresa.com, telefone: (11) 98765-4321"}],
            messageId="test_rag_1"
        )
        
        response = await self.agent.handle_a2a_request(message)
        
        if response.success and "extracted_contact" in response.data:
            contact = response.data["extracted_contact"]
            print(f"✅ Contato extraído: {contact['name']} ({contact['email']})")
            print(f"✅ Salvo no RAG: {response.data['saved_to_rag']['document_id']}")
            self.test_results.append(("MCP RAG Integration", True))
        else:
            print(f"❌ Falha na integração RAG: {response.error}")
            self.test_results.append(("MCP RAG Integration", False))
    
    async def _test_mcp_database_integration(self):
        """Testa integração MCP com banco de dados"""
        print("\n🗄️  Teste 3: Integração MCP + Database")
        print("-" * 40)
        
        # Simula consulta ao banco via MCP
        db_session = self.agent.mcp_client.get_session("database")
        result = await db_session.query("SELECT * FROM users LIMIT 5")
        
        if result["success"] and "data" in result:
            print(f"✅ Consulta executada: {len(result['data'])} registros encontrados")
            for user in result["data"][:2]:  # Mostra apenas 2
                print(f"  - {user['name']} ({user['email']})")
            self.test_results.append(("MCP Database Integration", True))
        else:
            print(f"❌ Falha na consulta ao banco: {result}")
            self.test_results.append(("MCP Database Integration", False))
    
    async def _test_mcp_filesystem_integration(self):
        """Testa integração MCP com sistema de arquivos"""
        print("\n📁 Teste 4: Integração MCP + Filesystem")
        print("-" * 40)
        
        # Testa escrita de arquivo
        fs_session = self.agent.mcp_client.get_session("filesystem")
        test_content = "Dados de teste salvos via MCP\nTimestamp: " + time.strftime("%Y-%m-%d %H:%M:%S")
        
        write_result = await fs_session.write_file(
            path="/tmp/mcp_test_file.txt",
            content=test_content
        )
        
        if write_result["success"]:
            print(f"✅ Arquivo criado: {write_result['path']}")
            
            # Testa leitura do arquivo
            read_result = await fs_session.read_file("/tmp/mcp_test_file.txt")
            
            if read_result["success"]:
                print("✅ Arquivo lido com sucesso")
                print(f"  Conteúdo: {read_result['content'][:50]}...")
                self.test_results.append(("MCP Filesystem Integration", True))
            else:
                print(f"❌ Falha na leitura: {read_result['error']}")
                self.test_results.append(("MCP Filesystem Integration", False))
        else:
            print(f"❌ Falha na escrita: {write_result}")
            self.test_results.append(("MCP Filesystem Integration", False))
    
    async def _test_hybrid_workflow(self):
        """Testa workflow híbrido completo"""
        print("\n🔄 Teste 5: Workflow Híbrido Completo")
        print("-" * 40)
        
        # Simula workflow completo: A2A → MCP → RAG → Database → Filesystem
        workflow_steps = [
            ("1. Recebe requisição A2A", "Busque informações sobre João Silva e salve em arquivo"),
            ("2. Processa via MCP RAG", "Busca no RAG"),
            ("3. Consulta banco de dados", "Busca dados adicionais"),
            ("4. Salva resultado", "Salva em arquivo")
        ]
        
        message = A2AMessage(
            role="user",
            parts=[{"kind": "text", "text": "Busque informações sobre João Silva e salve em arquivo"}],
            messageId="test_workflow_1"
        )
        
        response = await self.agent.handle_a2a_request(message)
        
        if response.success:
            print("✅ Workflow híbrido executado com sucesso")
            print("  Fluxo: A2A → MCP RAG → MCP Filesystem")
            self.test_results.append(("Hybrid Workflow", True))
        else:
            print(f"❌ Falha no workflow: {response.error}")
            self.test_results.append(("Hybrid Workflow", False))
    
    def _show_results(self):
        """Mostra resultados dos testes"""
        print("\n" + "=" * 60)
        print("📊 Resultados dos Testes de Integração")
        print("=" * 60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, success in self.test_results:
            status = "✅ PASSOU" if success else "❌ FALHOU"
            print(f"  {test_name}: {status}")
            if success:
                passed += 1
        
        print(f"\n🎯 Total: {passed}/{total} testes passaram")
        
        if passed == total:
            print("\n🎉 Todos os testes passaram! Integração A2A + MCP funcionando perfeitamente!")
            print("\n🚀 Marag está pronto para:")
            print("  - Comunicar com outros agentes via A2A")
            print("  - Acessar ferramentas via MCP")
            print("  - Executar workflows híbridos")
            print("  - Integrar RAG, Database e Filesystem")
        else:
            print(f"\n⚠️  {total - passed} teste(s) falharam. Verifique a configuração.")
    
    async def run_performance_test(self):
        """Executa teste de performance"""
        print("\n⚡ Teste de Performance")
        print("-" * 40)
        
        await self.agent.start()
        
        # Testa múltiplas requisições simultâneas
        messages = [
            A2AMessage(
                role="user",
                parts=[{"kind": "text", "text": f"Extraia contato {i}: Nome{i}@exemplo.com"}],
                messageId=f"perf_{i}"
            )
            for i in range(5)
        ]
        
        start_time = time.time()
        
        # Executa requisições em paralelo
        tasks = [
            self.agent.handle_a2a_request(msg) 
            for msg in messages
        ]
        
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        successful = sum(1 for r in responses if r.success)
        
        print(f"✅ {successful}/{len(responses)} requisições bem-sucedidas")
        print(f"⏱️  Tempo total: {duration:.2f}s")
        print(f"📈 Taxa: {len(responses)/duration:.2f} req/s")
        
        await self.agent.stop()


async def main():
    """Função principal"""
    tester = HybridIntegrationTester()
    
    # Executa testes de integração
    await tester.run_integration_tests()
    
    # Executa teste de performance
    await tester.run_performance_test()


if __name__ == "__main__":
    asyncio.run(main()) 