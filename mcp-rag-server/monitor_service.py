#!/usr/bin/env python3
"""
Serviço de monitoramento integrado com MCP
"""

import asyncio
import subprocess
import os
import signal
import json
import time
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MonitorService:
    """Gerencia o monitor em tempo real como um serviço"""
    
    def __init__(self):
        self.monitor_process = None
        self.monitor_pid_file = Path.home() / ".claude" / "mcp-rag-cache" / "monitor.pid"
        self.monitor_log_file = Path.home() / ".claude" / "mcp-rag-cache" / "monitor.log"
        self.monitor_script = Path(__file__).parent / "monitor_lite.py"
        
    def is_running(self) -> bool:
        """Verifica se o monitor está rodando"""
        if self.monitor_pid_file.exists():
            try:
                pid = int(self.monitor_pid_file.read_text().strip())
                # Verificar se o processo existe
                os.kill(pid, 0)
                return True
            except (ProcessLookupError, ValueError):
                # Processo não existe mais, limpar arquivo PID
                self.monitor_pid_file.unlink(missing_ok=True)
                return False
        return False
        
    def start(self, interval: int = 5) -> dict:
        """Inicia o monitor"""
        if self.is_running():
            return {
                "status": "already_running",
                "message": "Monitor já está em execução"
            }
            
        try:
            # Criar diretório se não existir
            self.monitor_pid_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Iniciar processo em background
            with open(self.monitor_log_file, 'w') as log_file:
                self.monitor_process = subprocess.Popen(
                    ["python3", str(self.monitor_script), "--interval", str(interval)],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True  # Desanexar do terminal
                )
                
            # Salvar PID
            self.monitor_pid_file.write_text(str(self.monitor_process.pid))
            
            return {
                "status": "started",
                "pid": self.monitor_process.pid,
                "interval": interval,
                "log_file": str(self.monitor_log_file)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def stop(self) -> dict:
        """Para o monitor"""
        if not self.is_running():
            return {
                "status": "not_running",
                "message": "Monitor não está em execução"
            }
            
        try:
            pid = int(self.monitor_pid_file.read_text().strip())
            
            # Enviar SIGTERM
            os.kill(pid, signal.SIGTERM)
            
            # Aguardar processo terminar (max 5 segundos)
            for _ in range(50):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    break
            else:
                # Forçar SIGKILL se não terminou
                os.kill(pid, signal.SIGKILL)
                
            # Limpar arquivo PID
            self.monitor_pid_file.unlink(missing_ok=True)
            
            return {
                "status": "stopped",
                "message": "Monitor parado com sucesso"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def status(self) -> dict:
        """Retorna status do monitor"""
        if not self.is_running():
            return {
                "status": "stopped",
                "running": False
            }
            
        try:
            pid = int(self.monitor_pid_file.read_text().strip())
            
            # Ler últimas linhas do log
            recent_logs = []
            if self.monitor_log_file.exists():
                with open(self.monitor_log_file, 'r') as f:
                    lines = f.readlines()
                    recent_logs = lines[-10:]  # Últimas 10 linhas
                    
            # Contar documentos indexados do log
            indexed_count = sum(1 for line in recent_logs if "✅" in line)
            
            return {
                "status": "running",
                "running": True,
                "pid": pid,
                "log_file": str(self.monitor_log_file),
                "recent_activity": {
                    "indexed_files": indexed_count,
                    "recent_logs": recent_logs
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "running": False,
                "message": str(e)
            }


# Instância global do serviço
monitor_service = MonitorService()


def handle_monitor_command(command: str, arguments: dict = None) -> dict:
    """Processa comandos do monitor"""
    if command == "start":
        interval = (arguments or {}).get("interval", 5)
        return monitor_service.start(interval)
    elif command == "stop":
        return monitor_service.stop()
    elif command == "status":
        return monitor_service.status()
    else:
        return {"status": "error", "message": f"Comando desconhecido: {command}"}


if __name__ == "__main__":
    # Teste do serviço
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: monitor_service.py [start|stop|status]")
        sys.exit(1)
        
    command = sys.argv[1]
    result = handle_monitor_command(command)
    print(json.dumps(result, indent=2))