#!/usr/bin/env python3
"""
Daemon para manter o marag Agent sempre ativo
Monitora o processo e reinicia automaticamente se necessário
"""

import os
import sys
import time
import signal
import logging
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

class maragDaemon:
    def __init__(self):
        self.marag_dir = Path(__file__).parent
        
        # Carregar variáveis de ambiente do arquivo .env
        env_file = self.marag_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            
        self.log_dir = self.marag_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        self.pid_file = self.marag_dir / "marag.pid"
        self.daemon_pid_file = self.marag_dir / "daemon.pid"
        self.log_file = self.log_dir / "marag_daemon.log"
        
        self.setup_logging()
        self.marag_process = None
        self.running = False
        
    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('maragDaemon')
        
    def is_port_in_use(self, port=10031):
        """Verifica se a porta está em uso"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            return False
            
    def find_marag_process(self):
        """Encontra o processo do marag"""
        try:
            # Usar lsof para verificar se a porta está sendo usada
            result = subprocess.run(['lsof', '-i', ':10031'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:  # Header + pelo menos uma linha de processo
                    # Extrair PID da segunda linha
                    fields = lines[1].split()
                    if len(fields) >= 2:
                        pid = fields[1]
                        return {'pid': int(pid)}
        except:
            pass
        return None
        
    def start_marag(self):
        """Inicia o processo do marag"""
        try:
            self.logger.info("🚀 Iniciando processo marag...")
            
            # Usar o Python do ambiente virtual da UI onde a2a está instalado
            ui_venv_python = "/Users/agents/Desktop/claude-20x/ui/.venv/bin/python"
            
            # Comando para iniciar o marag
            cmd = [
                ui_venv_python, 
                str(self.marag_dir / "server.py")
            ]
            
            # Configurar environment
            env = os.environ.copy()
            env['PYTHONPATH'] = '/Users/agents/Desktop/claude-20x'
            
            # Iniciar o processo
            self.marag_process = subprocess.Popen(
                cmd,
                cwd=self.marag_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            # Salvar PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.marag_process.pid))
                
            self.logger.info(f"✅ marag iniciado com PID: {self.marag_process.pid}")
            
            # Aguardar um pouco para verificar se iniciou corretamente
            time.sleep(3)
            
            if self.marag_process.poll() is None:
                self.logger.info("✅ marag está rodando normalmente")
                return True
            else:
                self.logger.error("❌ marag falhou ao iniciar")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao iniciar marag: {e}")
            return False
            
    def stop_marag(self):
        """Para o processo do marag"""
        try:
            # Tentar encontrar o processo
            marag_proc = self.find_marag_process()
            if marag_proc:
                pid = marag_proc['pid']
                self.logger.info(f"🛑 Parando processo marag (PID: {pid})")
                
                try:
                    # Enviar SIGTERM
                    os.kill(pid, signal.SIGTERM)
                    
                    # Aguardar terminar graciosamente
                    for _ in range(10):
                        try:
                            os.kill(pid, 0)  # Verifica se processo ainda existe
                            time.sleep(1)
                        except ProcessLookupError:
                            break  # Processo terminou
                    
                    # Forçar se necessário
                    try:
                        os.kill(pid, 0)  # Verifica se ainda existe
                        os.kill(pid, signal.SIGKILL)  # Força terminar
                    except ProcessLookupError:
                        pass  # Processo já terminou
                except ProcessLookupError:
                    pass  # Processo já não existe
                    
                self.logger.info("✅ marag parado")
                
            # Limpar arquivo PID
            if self.pid_file.exists():
                self.pid_file.unlink()
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao parar marag: {e}")
            
    def monitor_marag(self):
        """Monitora o processo do marag e reinicia se necessário"""
        self.logger.info("👁️  Iniciando monitoramento do marag...")
        
        while self.running:
            try:
                # Verificar se o processo está rodando
                marag_proc = self.find_marag_process()
                port_in_use = self.is_port_in_use(10031)
                
                if not marag_proc or not port_in_use:
                    self.logger.warning("⚠️  marag não está rodando, reiniciando...")
                    self.stop_marag()  # Limpar qualquer processo morto
                    time.sleep(2)
                    self.start_marag()
                else:
                    self.logger.debug(f"✅ marag rodando (PID: {marag_proc['pid']})")
                    
                # Aguardar antes da próxima verificação
                time.sleep(30)  # Verificar a cada 30 segundos
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"❌ Erro no monitoramento: {e}")
                time.sleep(10)
                
    def start_daemon(self):
        """Inicia o daemon"""
        self.logger.info("🎯 Iniciando marag Daemon...")
        
        # Salvar PID do daemon
        with open(self.daemon_pid_file, 'w') as f:
            f.write(str(os.getpid()))
            
        # Configurar handlers de sinal
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
        
        # Iniciar marag se não estiver rodando
        if not self.find_marag_process():
            self.start_marag()
            
        # Iniciar monitoramento
        self.monitor_marag()
        
    def stop_daemon(self):
        """Para o daemon"""
        self.logger.info("🛑 Parando marag Daemon...")
        self.running = False
        self.stop_marag()
        
        # Limpar arquivo PID do daemon
        if self.daemon_pid_file.exists():
            self.daemon_pid_file.unlink()
            
        self.logger.info("✅ Daemon parado")
        
    def signal_handler(self, signum, frame):
        """Handler para sinais do sistema"""
        self.logger.info(f"📨 Recebido sinal {signum}")
        self.stop_daemon()
        sys.exit(0)
        
    def status(self):
        """Mostra o status do marag e do daemon"""
        marag_proc = self.find_marag_process()
        port_in_use = self.is_port_in_use(10031)
        daemon_running = self.daemon_pid_file.exists()
        
        print("📊 Status do marag:")
        print(f"  Processo marag: {'✅ Rodando' if marag_proc else '❌ Parado'}")
        if marag_proc:
            print(f"  PID: {marag_proc['pid']}")
        print(f"  Porta 10031: {'✅ Em uso' if port_in_use else '❌ Livre'}")
        print(f"  Daemon: {'✅ Rodando' if daemon_running else '❌ Parado'}")
        
        if daemon_running:
            try:
                with open(self.daemon_pid_file, 'r') as f:
                    daemon_pid = int(f.read().strip())
                print(f"  Daemon PID: {daemon_pid}")
            except:
                pass

def main():
    daemon = maragDaemon()
    
    if len(sys.argv) < 2:
        print("Uso: python marag_daemon.py [start|stop|restart|status]")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "start":
        daemon.start_daemon()
    elif command == "stop":
        daemon.stop_daemon()
    elif command == "restart":
        daemon.stop_daemon()
        time.sleep(2)
        daemon.start_daemon()
    elif command == "status":
        daemon.status()
    else:
        print("Comando inválido. Use: start|stop|restart|status")
        sys.exit(1)

if __name__ == "__main__":
    main()