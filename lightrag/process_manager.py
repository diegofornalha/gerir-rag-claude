#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de Processos LightRAG

Este script é responsável por verificar e gerenciar processos do LightRAG,
garantindo que não existam processos duplicados e que o sistema esteja
funcionando de forma eficiente.

Funcionalidades:
- Identificação de processos LightRAG (servidor, UI, monitor)
- Detecção de processos duplicados e órfãos
- Limpeza de processos zumbis ou duplicados
- Verificação de integridade do sistema de PIDs
- Interface CLI para opções de gerenciamento
"""

import os
import sys
import time
import glob
import signal
import subprocess
import argparse
import logging
import json
import re
from datetime import datetime
import psutil

# Configuração de caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "process_manager.log")
PID_DIR = os.path.join(SCRIPT_DIR, ".pids")

# Garantir que diretórios existam
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(PID_DIR, exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('process_manager')

# Definições de processos LightRAG
LIGHTRAG_PROCESSES = {
    'server': {
        'pid_file': os.path.join(PID_DIR, 'lightrag_server.pid'),
        'patterns': ['flask', 'server.py', 'api/server'],
        'service_name': 'Servidor LightRAG'
    },
    'ui': {
        'pid_file': os.path.join(PID_DIR, 'lightrag_ui.pid'),
        'patterns': ['streamlit', 'app.py', 'lightrag_ui'],
        'service_name': 'Interface Streamlit'
    },
    'monitor': {
        'pid_file': os.path.join(PID_DIR, 'lightrag_monitor.pid'),
        'patterns': ['unified_monitor', 'improved_monitor', 'monitor_projects'],
        'service_name': 'Monitor de Projetos'
    }
}

# Processos antigos que devem ser encerrados se encontrados
LEGACY_PATTERNS = [
    'monitor_projects.py',
    'improved_monitor.py',
    'lightrag_ui.py',
    'ui.py',
    'ui/app.py'
]

def read_pid_file(pid_file):
    """Lê um arquivo PID e retorna o número do processo"""
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
                if pid and pid.isdigit():
                    return int(pid)
    except Exception as e:
        logger.error(f"Erro ao ler arquivo PID {pid_file}: {e}")
    return None

def is_process_running(pid):
    """Verifica se um processo está em execução pelo PID"""
    try:
        if pid is None or pid <= 0:
            return False
        
        # Verificar se o processo existe
        process = psutil.Process(pid)
        
        # Verificar se o processo está realmente em execução
        if process.status() in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
            return False
            
        return True
    except psutil.NoSuchProcess:
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar processo {pid}: {e}")
        return False

def check_process_name(pid, patterns):
    """Verifica se o processo pertence ao LightRAG baseado no nome/comando"""
    try:
        process = psutil.Process(pid)
        cmd = ' '.join(process.cmdline()).lower()
        
        # Verificar se contém 'python' ou 'python3' e algum dos padrões
        if 'python' in cmd or 'python3' in cmd:
            for pattern in patterns:
                if pattern.lower() in cmd:
                    return True
        return False
    except psutil.NoSuchProcess:
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar nome do processo {pid}: {e}")
        return False

def find_all_lightrag_processes():
    """Encontra todos os processos relacionados ao LightRAG em execução"""
    lightrag_processes = {}
    
    # Processos registrados por tipo (server, ui, monitor)
    for process_type, config in LIGHTRAG_PROCESSES.items():
        lightrag_processes[process_type] = {
            'registered': None,  # Processo registrado em arquivo PID
            'running': [],       # Processos em execução que correspondem aos padrões
            'pid_file': config['pid_file'],
            'patterns': config['patterns'],
            'service_name': config['service_name']
        }
        
        # Verificar arquivo PID
        pid = read_pid_file(config['pid_file'])
        if pid and is_process_running(pid):
            if check_process_name(pid, config['patterns']):
                lightrag_processes[process_type]['registered'] = pid
    
    # Encontrar todos os processos Python em execução
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = ' '.join(proc.cmdline()).lower() if proc.cmdline() else ''
            if 'python' in cmd or 'python3' in cmd:
                pid = proc.pid
                
                # Verificar se corresponde a algum tipo de processo LightRAG
                for process_type, config in LIGHTRAG_PROCESSES.items():
                    for pattern in config['patterns']:
                        if pattern.lower() in cmd:
                            # Adicionar apenas se ainda não estiver na lista
                            if pid not in lightrag_processes[process_type]['running']:
                                lightrag_processes[process_type]['running'].append(pid)
                
                # Verificar padrões legados que devem ser encerrados
                for legacy_pattern in LEGACY_PATTERNS:
                    if legacy_pattern.lower() in cmd:
                        if 'legacy' not in lightrag_processes:
                            lightrag_processes['legacy'] = {
                                'registered': None,
                                'running': [],
                                'pid_file': None,
                                'patterns': LEGACY_PATTERNS,
                                'service_name': 'Processos Legados'
                            }
                        if pid not in lightrag_processes['legacy']['running']:
                            lightrag_processes['legacy']['running'].append(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as e:
            logger.error(f"Erro ao analisar processo: {e}")
    
    return lightrag_processes

def kill_process(pid, force=False):
    """Tenta encerrar um processo de forma segura primeiro, depois força se necessário"""
    try:
        process = psutil.Process(pid)
        process_name = ' '.join(process.cmdline())
        
        logger.info(f"Tentando encerrar processo {pid}: {process_name}")
        
        if not force:
            # Tenta encerramento normal primeiro (SIGTERM)
            process.terminate()
            
            # Dá um tempo para o processo ser encerrado
            gone, alive = psutil.wait_procs([process], timeout=5)
            if process in alive:
                logger.warning(f"Processo {pid} não respondeu ao SIGTERM, tentando SIGKILL")
                force = True
        
        if force:
            # Força encerramento (SIGKILL)
            process.kill()
            
            # Verifica novamente
            time.sleep(0.5)
            if is_process_running(pid):
                logger.error(f"Falha ao encerrar processo {pid} mesmo com SIGKILL")
                return False
        
        logger.info(f"Processo {pid} encerrado com sucesso")
        return True
    
    except psutil.NoSuchProcess:
        logger.info(f"Processo {pid} já não existe")
        return True
    except Exception as e:
        logger.error(f"Erro ao encerrar processo {pid}: {e}")
        return False

def update_pid_file(process_type, pid):
    """Atualiza o arquivo PID para o tipo de processo especificado"""
    try:
        pid_file = LIGHTRAG_PROCESSES[process_type]['pid_file']
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)
        
        with open(pid_file, 'w') as f:
            f.write(str(pid))
        
        logger.info(f"Arquivo PID para {process_type} atualizado: {pid_file} (PID: {pid})")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar arquivo PID para {process_type}: {e}")
        return False

def remove_pid_file(pid_file):
    """Remove um arquivo PID"""
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
            logger.info(f"Arquivo PID removido: {pid_file}")
        return True
    except Exception as e:
        logger.error(f"Erro ao remover arquivo PID {pid_file}: {e}")
        return False

def print_process_info(processes_info, verbose=False):
    """Imprime informações sobre processos de forma organizada"""
    print("\n=== Status dos Processos LightRAG ===\n")
    
    for process_type, info in processes_info.items():
        if process_type == 'legacy':
            print(f"\n{info['service_name']}:")
        else:
            print(f"\n{info['service_name']} ({process_type}):")
        
        # Verificar processo registrado no arquivo PID
        if info['registered']:
            print(f"  ✅ Registrado (PID: {info['registered']})")
        else:
            if os.path.exists(info.get('pid_file', '')):
                print(f"  ❌ Arquivo PID existe mas processo não está rodando: {info['pid_file']}")
            else:
                print(f"  ⚠️  Não registrado (arquivo PID não existe)")
        
        # Listar processos em execução
        if info['running']:
            if len(info['running']) == 1 and info['running'][0] == info['registered']:
                print(f"  ✅ Uma instância em execução (PID: {info['running'][0]})")
            else:
                print(f"  ⚠️  {len(info['running'])} instâncias em execução: {', '.join(map(str, info['running']))}")
                
                # Destacar duplicatas
                if info['registered'] and len(info['running']) > 1:
                    duplicates = [pid for pid in info['running'] if pid != info['registered']]
                    if duplicates:
                        print(f"  ❗ Processos duplicados detectados: {', '.join(map(str, duplicates))}")
        else:
            print(f"  ❌ Nenhuma instância em execução")
        
        # Informações detalhadas em modo verbose
        if verbose and info['running']:
            print("\n  Detalhes dos processos:")
            for pid in info['running']:
                try:
                    process = psutil.Process(pid)
                    cmd = ' '.join(process.cmdline())
                    created = datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')
                    memory = process.memory_info().rss / (1024 * 1024)  # MB
                    cpu = process.cpu_percent(interval=0.1)
                    
                    print(f"  · PID {pid}:")
                    print(f"    - Comando: {cmd}")
                    print(f"    - Iniciado em: {created}")
                    print(f"    - Uso de memória: {memory:.2f} MB")
                    print(f"    - Uso de CPU: {cpu:.1f}%")
                    print()
                except Exception as e:
                    print(f"  · PID {pid}: Erro ao obter detalhes ({e})")

def clean_duplicate_processes(processes_info, force=False):
    """Limpa processos duplicados e inválidos"""
    print("\n=== Limpeza de Processos Duplicados ===\n")
    
    for process_type, info in processes_info.items():
        if process_type == 'legacy':
            # Processos legados devem ser todos encerrados
            for pid in info['running']:
                print(f"Encerrando processo legado {pid}...")
                kill_process(pid, force)
            continue
                
        # Se não há processos em execução, remover arquivo PID
        if not info['running'] and os.path.exists(info['pid_file']):
            print(f"Removendo arquivo PID inválido: {info['pid_file']}")
            remove_pid_file(info['pid_file'])
            continue
            
        # Se há múltiplos processos do mesmo tipo
        if len(info['running']) > 1:
            registered_pid = info['registered']
            
            # Se há um processo registrado, mantê-lo e encerrar os outros
            if registered_pid:
                for pid in info['running']:
                    if pid != registered_pid:
                        print(f"Encerrando {info['service_name']} duplicado (PID: {pid})...")
                        kill_process(pid, force)
            
            # Se não há processo registrado, manter o mais antigo
            else:
                oldest_pid = None
                oldest_time = float('inf')
                
                # Encontrar o processo mais antigo
                for pid in info['running']:
                    try:
                        process = psutil.Process(pid)
                        if process.create_time() < oldest_time:
                            oldest_time = process.create_time()
                            oldest_pid = pid
                    except:
                        continue
                
                # Registrar o processo mais antigo e encerrar os outros
                if oldest_pid:
                    print(f"Mantendo {info['service_name']} mais antigo (PID: {oldest_pid})")
                    update_pid_file(process_type, oldest_pid)
                    
                    for pid in info['running']:
                        if pid != oldest_pid:
                            print(f"Encerrando {info['service_name']} mais recente (PID: {pid})...")
                            kill_process(pid, force)
        
        # Se há apenas um processo em execução mas não está registrado
        elif len(info['running']) == 1 and info['running'][0] != info['registered']:
            print(f"Atualizando registro de {info['service_name']} (PID: {info['running'][0]})")
            update_pid_file(process_type, info['running'][0])
    
    print("\nLimpeza concluída.")

def verify_system_integrity():
    """Verifica a integridade geral do sistema LightRAG"""
    issues = []
    
    # Verificar existência de diretório PID
    if not os.path.exists(PID_DIR):
        issues.append(f"Diretório de PIDs não existe: {PID_DIR}")
    
    # Verificar permissões do diretório PID
    if os.path.exists(PID_DIR) and not os.access(PID_DIR, os.W_OK):
        issues.append(f"Sem permissão de escrita no diretório de PIDs: {PID_DIR}")
    
    # Verificar arquivos PID antigos
    old_pid_files = glob.glob(os.path.join(SCRIPT_DIR, "*.pid"))
    old_pid_files.extend(glob.glob(os.path.join(SCRIPT_DIR, ".*.pid")))
    
    if old_pid_files:
        issues.append(f"Encontrados {len(old_pid_files)} arquivos PID antigos fora do diretório centralizado")
    
    # Verificar processos
    processes_info = find_all_lightrag_processes()
    
    # Verificar processos essenciais
    essential_processes = ['server', 'ui', 'monitor']
    for proc_type in essential_processes:
        info = processes_info.get(proc_type, {})
        if not info.get('running'):
            issues.append(f"{LIGHTRAG_PROCESSES[proc_type]['service_name']} não está em execução")
        elif len(info.get('running', [])) > 1:
            issues.append(f"Múltiplas instâncias de {LIGHTRAG_PROCESSES[proc_type]['service_name']} em execução")
    
    # Verificar processos legados
    if 'legacy' in processes_info and processes_info['legacy']['running']:
        issues.append(f"Processos legados em execução: {len(processes_info['legacy']['running'])}")
    
    return issues

def run_clean_pids():
    """Executa o script clean_pids.sh para organizar os arquivos PID"""
    clean_pids_script = os.path.join(SCRIPT_DIR, "clean_pids.sh")
    
    if not os.path.exists(clean_pids_script):
        logger.error(f"Script clean_pids.sh não encontrado em {clean_pids_script}")
        return False
    
    try:
        logger.info(f"Executando script clean_pids.sh...")
        subprocess.run(['bash', clean_pids_script], check=True)
        logger.info("Script clean_pids.sh executado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao executar clean_pids.sh: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao executar clean_pids.sh: {e}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Gerenciador de Processos LightRAG')
    
    # Opções de comando
    parser.add_argument('--status', action='store_true', help='Mostrar status dos processos')
    parser.add_argument('--clean', action='store_true', help='Limpar processos duplicados')
    parser.add_argument('--verify', action='store_true', help='Verificar integridade do sistema')
    parser.add_argument('--force', action='store_true', help='Forçar o encerramento de processos (SIGKILL)')
    parser.add_argument('--verbose', action='store_true', help='Mostrar informações detalhadas')
    
    # Analisar argumentos
    args = parser.parse_args()
    
    # Se nenhuma opção foi fornecida, mostrar ajuda
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)
    
    # Executar clean_pids.sh primeiro para garantir organização
    run_clean_pids()
    
    # Encontrar processos LightRAG
    processes_info = find_all_lightrag_processes()
    
    # Executar ações conforme solicitado
    if args.status:
        print_process_info(processes_info, args.verbose)
        
    if args.verify:
        issues = verify_system_integrity()
        
        print("\n=== Verificação de Integridade do Sistema ===\n")
        if issues:
            print(f"⚠️  Encontrados {len(issues)} problemas:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            print("\nRecomendação: Execute com a opção --clean para resolver automaticamente")
        else:
            print("✅ Sistema íntegro. Nenhum problema encontrado.")
    
    if args.clean:
        clean_duplicate_processes(processes_info, args.force)
        
        # Verificar novamente após limpeza
        if args.verbose:
            print("\n=== Status após limpeza ===")
            processes_info = find_all_lightrag_processes()
            print_process_info(processes_info, False)

if __name__ == "__main__":
    main()