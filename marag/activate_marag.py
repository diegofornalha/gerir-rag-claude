#!/usr/bin/env python3
"""
Script para ativar o Marag de forma robusta
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def check_port(port):
    """Verifica se a porta está livre"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result != 0  # True se porta livre
    except:
        return False

def kill_process_on_port(port):
    """Mata processo na porta especificada"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"🛑 Matando processo {pid} na porta {port}")
                    os.kill(int(pid), signal.SIGKILL)
                    time.sleep(1)
    except Exception as e:
        print(f"⚠️  Erro ao matar processo: {e}")

def start_marag_server():
    """Inicia o servidor Marag"""
    
    port = 10031
    
    print("🚀 Ativando Marag...")
    print(f"📊 Porta: {port}")
    print(f"🌐 URL: http://localhost:{port}")
    print()
    
    # Verificar se porta está livre
    if not check_port(port):
        print(f"⚠️  Porta {port} está em uso. Tentando liberar...")
        kill_process_on_port(port)
        time.sleep(2)
    
    if not check_port(port):
        print(f"❌ Porta {port} ainda está em uso")
        return False
    
    print(f"✅ Porta {port} está livre")
    
    # Tentar diferentes métodos de inicialização
    methods = [
        # Método 1: Servidor simples
        {
            "name": "Servidor Simples",
            "cmd": ["python3", "simple_server.py"],
            "env": os.environ.copy()
        },
        # Método 2: Servidor com ambiente virtual
        {
            "name": "Servidor com Venv",
            "cmd": [".venv/bin/python", "simple_server.py"],
            "env": os.environ.copy()
        },
        # Método 3: Uvicorn direto
        {
            "name": "Uvicorn Direto",
            "cmd": ["python3", "-m", "uvicorn", "simple_server:app", "--host", "localhost", "--port", str(port)],
            "env": os.environ.copy()
        }
    ]
    
    for method in methods:
        print(f"\n🔄 Tentando: {method['name']}")
        
        try:
            # Configurar ambiente
            env = method["env"].copy()
            env["PYTHONPATH"] = str(Path.cwd())
            
            # Iniciar processo
            process = subprocess.Popen(
                method["cmd"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Aguardar um pouco
            time.sleep(3)
            
            # Verificar se está rodando
            if process.poll() is None and check_port(port):
                print(f"✅ {method['name']} iniciado com sucesso!")
                print(f"🆔 PID: {process.pid}")
                print(f"🌐 Acesse: http://localhost:{port}")
                
                # Salvar PID
                with open("marag.pid", "w") as f:
                    f.write(str(process.pid))
                
                return True
            else:
                print(f"❌ {method['name']} falhou")
                process.terminate()
                
        except Exception as e:
            print(f"❌ Erro no {method['name']}: {e}")
    
    print("\n❌ Todos os métodos falharam")
    return False

def main():
    """Função principal"""
    
    print("🎯 Ativador do Marag")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not Path("server.py").exists():
        print("❌ Execute este script no diretório do Marag")
        return
    
    # Iniciar servidor
    success = start_marag_server()
    
    if success:
        print("\n🎉 Marag ativado com sucesso!")
        print("📝 Para parar: kill $(cat marag.pid)")
    else:
        print("\n❌ Falha ao ativar Marag")
        print("💡 Verifique as dependências e configurações")

if __name__ == "__main__":
    main() 