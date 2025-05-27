#!/usr/bin/env python3
"""
Teste da integração do monitor com MCP
"""

import json
import asyncio
import sys
sys.path.append('.')

from monitor_service import monitor_service

async def test_monitor():
    """Testa o serviço de monitor"""
    print("🧪 Testando Monitor Service")
    print("=" * 50)
    
    # 1. Verificar status inicial
    print("\n1️⃣ Verificando status inicial...")
    status = monitor_service.status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # 2. Iniciar monitor
    print("\n2️⃣ Iniciando monitor...")
    result = monitor_service.start(interval=3)
    print(f"Resultado: {json.dumps(result, indent=2)}")
    
    # 3. Aguardar um pouco
    print("\n⏳ Aguardando 10 segundos para o monitor processar arquivos...")
    await asyncio.sleep(10)
    
    # 4. Verificar status novamente
    print("\n3️⃣ Verificando status após iniciar...")
    status = monitor_service.status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    # 5. Parar monitor
    print("\n4️⃣ Parando monitor...")
    result = monitor_service.stop()
    print(f"Resultado: {json.dumps(result, indent=2)}")
    
    # 6. Status final
    print("\n5️⃣ Status final...")
    status = monitor_service.status()
    print(f"Status: {json.dumps(status, indent=2)}")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    asyncio.run(test_monitor())