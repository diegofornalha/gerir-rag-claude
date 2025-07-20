#!/usr/bin/env python3
"""
Teste da mudança de porta do agente Marag
"""

import socket
import subprocess
import time
from pathlib import Path


def test_port_availability(port):
    """Testa se a porta está disponível"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result != 0  # True se porta livre
    except:
        return False


def check_port_usage(port):
    """Verifica se a porta está sendo usada"""
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                              capture_output=True, text=True)
        return result.returncode == 0 and result.stdout.strip()
    except:
        return False


def main():
    """Testa a mudança de porta"""
    
    print("🧪 Testando mudança de porta do agente Marag")
    print("=" * 50)
    
    # Testar porta antiga (10030)
    print(f"\n🔍 Verificando porta 10030:")
    port_10030_free = test_port_availability(10030)
    port_10030_used = check_port_usage(10030)
    
    print(f"  ✅ Livre: {port_10030_free}")
    print(f"  🔗 Em uso: {bool(port_10030_used)}")
    
    # Testar nova porta (10031)
    print(f"\n🔍 Verificando porta 10031:")
    port_10031_free = test_port_availability(10031)
    port_10031_used = check_port_usage(10031)
    
    print(f"  ✅ Livre: {port_10031_free}")
    print(f"  🔗 Em uso: {bool(port_10031_used)}")
    
    print("\n" + "=" * 50)
    print("📊 Resultados:")
    print(f"  Porta 10030: {'❌ Em uso' if port_10030_used else '✅ Livre'}")
    print(f"  Porta 10031: {'❌ Em uso' if port_10031_used else '✅ Livre'}")
    
    if port_10031_free:
        print("\n✅ Nova porta 10031 está disponível!")
        print("🚀 Agente Marag pode ser iniciado na nova porta.")
    else:
        print("\n⚠️  Porta 10031 está em uso. Verifique outros serviços.")
    
    print("\n📝 Para iniciar o agente na nova porta:")
    print("   cd /Users/agents/.claude/marag")
    print("   python3 server.py")
    print("   # ou")
    print("   python3 start_marag_with_rag.py")


if __name__ == "__main__":
    main() 