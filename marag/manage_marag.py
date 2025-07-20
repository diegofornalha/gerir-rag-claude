#!/usr/bin/env python3
"""
Gerenciador do Marag - Iniciar, parar e verificar status
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def check_port(port):
    """Verifica se a porta está em uso"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0  # True se porta em uso
    except:
        return False

def get_pid_from_file():
    """Obtém PID do arquivo"""
    pid_file = Path("marag.pid")
    if pid_file.exists():
        try:
            return int(pid_file.read_text().strip())
        except:
            pass
    return None

def kill_process(pid):
    """Mata processo por PID"""
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return True
    except ProcessLookupError:
        return True
    except Exception as e:
        print(f"❌ Erro ao matar processo: {e}")
        return False

def start_marag():
    """Inicia o Marag"""
    print("🚀 Iniciando Marag...")
    
    # Verificar se já está rodando
    if check_port(10031):
        print("⚠️  Marag já está rodando na porta 10031")
        return True
    
    # Iniciar servidor
    try:
        cmd = ["python3", "simple_server.py"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd())
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Aguardar inicialização
        time.sleep(3)
        
        if process.poll() is None and check_port(10031):
            print("✅ Marag iniciado com sucesso!")
            print(f"🆔 PID: {process.pid}")
            print("🌐 URL: http://localhost:10031")
            
            # Salvar PID
            with open("marag.pid", "w") as f:
                f.write(str(process.pid))
            
            return True
        else:
            print("❌ Falha ao iniciar Marag")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        return False

def stop_marag():
    """Para o Marag"""
    print("🛑 Parando Marag...")
    
    # Tentar parar por PID do arquivo
    pid = get_pid_from_file()
    if pid:
        print(f"🆔 Matando processo {pid}")
        if kill_process(pid):
            print("✅ Processo parado")
        else:
            print("❌ Erro ao parar processo")
    
    # Verificar se porta ainda está em uso
    if check_port(10031):
        print("⚠️  Porta ainda em uso, tentando matar por porta...")
        try:
            result = subprocess.run(['lsof', '-ti', ':10031'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid_str in pids:
                    if pid_str:
                        kill_process(int(pid_str))
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    # Limpar arquivo PID
    pid_file = Path("marag.pid")
    if pid_file.exists():
        pid_file.unlink()
    
    if not check_port(10031):
        print("✅ Marag parado com sucesso!")
    else:
        print("⚠️  Marag pode ainda estar rodando")

def status_marag():
    """Mostra status do Marag"""
    print("📊 Status do Marag:")
    
    # Verificar porta
    port_in_use = check_port(10031)
    print(f"  Porta 10031: {'✅ Em uso' if port_in_use else '❌ Livre'}")
    
    # Verificar PID
    pid = get_pid_from_file()
    if pid:
        try:
            os.kill(pid, 0)  # Verifica se processo existe
            print(f"  Processo: ✅ Rodando (PID: {pid})")
        except ProcessLookupError:
            print(f"  Processo: ❌ Parado (PID: {pid} não existe)")
    else:
        print("  Processo: ❌ Não encontrado")
    
    # Testar conexão
    if port_in_use:
        try:
            import requests
            response = requests.get("http://localhost:10031/health", timeout=2)
            if response.status_code == 200:
                print("  Servidor: ✅ Respondendo")
                data = response.json()
                print(f"  Status: {data.get('status', 'N/A')}")
            else:
                print("  Servidor: ⚠️  Não respondendo corretamente")
        except:
            print("  Servidor: ❌ Não acessível")

def restart_marag():
    """Reinicia o Marag"""
    print("🔄 Reiniciando Marag...")
    stop_marag()
    time.sleep(2)
    start_marag()

def main():
    """Função principal"""
    
    if len(sys.argv) < 2:
        print("🎯 Gerenciador do Marag")
        print("=" * 30)
        print("Uso: python3 manage_marag.py [comando]")
        print()
        print("Comandos:")
        print("  start   - Inicia o Marag")
        print("  stop    - Para o Marag")
        print("  restart - Reinicia o Marag")
        print("  status  - Mostra status")
        print()
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_marag()
    elif command == "stop":
        stop_marag()
    elif command == "restart":
        restart_marag()
    elif command == "status":
        status_marag()
    else:
        print(f"❌ Comando desconhecido: {command}")

if __name__ == "__main__":
    main() 