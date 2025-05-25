#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script aprimorado para extrair TODOS os campos documentados de arquivos JSONL
e inserir no LightRAG com análise completa de métricas
"""

import json
import argparse
import urllib.request
import urllib.parse
import sys
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

def insert_to_lightrag(text, summary, source="jsonl_extract"):
    """Insere texto no servidor LightRAG"""
    base_url = "http://127.0.0.1:5000"
    
    data = {
        "text": text,
        "summary": summary,
        "source": source
    }
    
    try:
        encoded_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/insert",
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Erro ao inserir no LightRAG: {e}")
        return {"success": False, "error": str(e)}

def extract_jsonl_complete(file_path: str) -> Dict[str, Any]:
    """Extrai TODOS os campos documentados de um arquivo JSONL"""
    metrics = {
        'summary': '',
        'session_id': '',
        'total_messages': 0,
        'user_messages': 0,
        'assistant_messages': 0,
        'tool_uses': defaultdict(int),
        'tool_results': defaultdict(int),
        'total_cost_usd': 0.0,
        'costs_by_model': defaultdict(float),
        'total_duration_ms': 0,
        'token_usage': {
            'input_tokens': 0,
            'output_tokens': 0,
            'cache_creation_tokens': 0,
            'cache_read_tokens': 0
        },
        'messages': [],
        'start_timestamp': None,
        'end_timestamp': None,
        'models_used': set(),
        'stop_reasons': defaultdict(int),
        'error_count': 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())
                    
                    # Processar summary
                    if entry.get('type') == 'summary':
                        metrics['summary'] = entry.get('summary', '')
                        metrics['session_id'] = entry.get('leafUuid', '')
                    
                    # Processar mensagens do usuário
                    elif entry.get('type') == 'user':
                        metrics['user_messages'] += 1
                        metrics['total_messages'] += 1
                        
                        # Capturar timestamp
                        timestamp = entry.get('timestamp')
                        if timestamp:
                            if not metrics['start_timestamp']:
                                metrics['start_timestamp'] = timestamp
                            metrics['end_timestamp'] = timestamp
                        
                        # Processar tool results
                        content = entry.get('message', {}).get('content', [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'tool_result':
                                    tool_id = item.get('tool_use_id', '')
                                    metrics['tool_results'][tool_id] += 1
                        
                        # Capturar informações da mensagem
                        message_info = {
                            'type': 'user',
                            'uuid': entry.get('uuid'),
                            'timestamp': timestamp,
                            'content': extract_message_content(entry)
                        }
                        metrics['messages'].append(message_info)
                    
                    # Processar mensagens do assistente
                    elif entry.get('type') == 'assistant':
                        metrics['assistant_messages'] += 1
                        metrics['total_messages'] += 1
                        
                        # Capturar métricas de custo e desempenho
                        if 'costUSD' in entry:
                            metrics['total_cost_usd'] += entry['costUSD']
                        
                        if 'durationMs' in entry:
                            metrics['total_duration_ms'] += entry['durationMs']
                        
                        message = entry.get('message', {})
                        model = message.get('model', '')
                        if model:
                            metrics['models_used'].add(model)
                            if 'costUSD' in entry:
                                metrics['costs_by_model'][model] += entry['costUSD']
                        
                        # Capturar stop reason
                        stop_reason = message.get('stop_reason')
                        if stop_reason:
                            metrics['stop_reasons'][stop_reason] += 1
                        
                        # Capturar uso de tokens
                        usage = message.get('usage', {})
                        if usage:
                            metrics['token_usage']['input_tokens'] += usage.get('input_tokens', 0)
                            metrics['token_usage']['output_tokens'] += usage.get('output_tokens', 0)
                            metrics['token_usage']['cache_creation_tokens'] += usage.get('cache_creation_input_tokens', 0)
                            metrics['token_usage']['cache_read_tokens'] += usage.get('cache_read_input_tokens', 0)
                        
                        # Processar tool uses
                        content = message.get('content', [])
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'tool_use':
                                    tool_name = item.get('name', 'unknown')
                                    metrics['tool_uses'][tool_name] += 1
                        
                        # Capturar informações da mensagem
                        message_info = {
                            'type': 'assistant',
                            'uuid': entry.get('uuid'),
                            'timestamp': entry.get('timestamp'),
                            'model': model,
                            'cost_usd': entry.get('costUSD', 0),
                            'duration_ms': entry.get('durationMs', 0),
                            'content': extract_message_content(entry)
                        }
                        metrics['messages'].append(message_info)
                
                except json.JSONDecodeError as e:
                    metrics['error_count'] += 1
                    print(f"Erro ao decodificar linha {line_num}: {e}")
                except Exception as e:
                    metrics['error_count'] += 1
                    print(f"Erro ao processar linha {line_num}: {e}")
        
        # Converter sets para listas para serialização JSON
        metrics['models_used'] = list(metrics['models_used'])
        metrics['tool_uses'] = dict(metrics['tool_uses'])
        metrics['tool_results'] = dict(metrics['tool_results'])
        metrics['costs_by_model'] = dict(metrics['costs_by_model'])
        metrics['stop_reasons'] = dict(metrics['stop_reasons'])
        
        # Calcular duração total da sessão
        if metrics['start_timestamp'] and metrics['end_timestamp']:
            start_dt = datetime.fromisoformat(metrics['start_timestamp'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(metrics['end_timestamp'].replace('Z', '+00:00'))
            metrics['session_duration_seconds'] = (end_dt - start_dt).total_seconds()
        
        # Calcular eficiência do cache
        if metrics['token_usage']['cache_creation_tokens'] > 0:
            metrics['cache_efficiency'] = (
                metrics['token_usage']['cache_read_tokens'] / 
                metrics['token_usage']['cache_creation_tokens']
            )
        else:
            metrics['cache_efficiency'] = 0.0
        
        return metrics
    
    except Exception as e:
        print(f"Erro ao processar arquivo {file_path}: {e}")
        return None

def extract_message_content(entry: Dict[str, Any]) -> str:
    """Extrai conteúdo textual de uma mensagem"""
    content_parts = []
    
    message = entry.get('message', {})
    content = message.get('content', '')
    
    if isinstance(content, str):
        content_parts.append(content)
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    content_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    content_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                elif item.get('type') == 'tool_result':
                    result_content = item.get('content', '')
                    if len(result_content) > 200:
                        result_content = result_content[:197] + "..."
                    content_parts.append(f"[Tool Result: {result_content}]")
            elif isinstance(item, str):
                content_parts.append(item)
    
    return ' '.join(content_parts)

def format_metrics_report(metrics: Dict[str, Any]) -> str:
    """Formata um relatório detalhado das métricas"""
    if not metrics:
        return "Nenhuma métrica disponível"
    
    report_lines = [
        f"📋 RELATÓRIO DE MÉTRICAS - {metrics.get('summary', 'Sem resumo')}",
        "=" * 60,
        f"\n📊 RESUMO GERAL:",
        f"  • Session ID: {metrics.get('session_id', 'N/A')}",
        f"  • Total de mensagens: {metrics.get('total_messages', 0)}",
        f"  • Mensagens do usuário: {metrics.get('user_messages', 0)}",
        f"  • Mensagens do assistente: {metrics.get('assistant_messages', 0)}",
    ]
    
    # Duração da sessão
    if 'session_duration_seconds' in metrics:
        duration = metrics['session_duration_seconds']
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        report_lines.append(f"  • Duração da sessão: {hours}h {minutes}m {seconds}s")
    
    # Custos
    report_lines.extend([
        f"\n💰 CUSTOS:",
        f"  • Custo total: ${metrics.get('total_cost_usd', 0):.4f}"
    ])
    
    if metrics.get('costs_by_model'):
        report_lines.append("  • Custo por modelo:")
        for model, cost in metrics['costs_by_model'].items():
            report_lines.append(f"    - {model}: ${cost:.4f}")
    
    # Uso de tokens
    token_usage = metrics.get('token_usage', {})
    if token_usage:
        report_lines.extend([
            f"\n🔢 USO DE TOKENS:",
            f"  • Tokens de entrada: {token_usage.get('input_tokens', 0):,}",
            f"  • Tokens de saída: {token_usage.get('output_tokens', 0):,}",
            f"  • Tokens para criar cache: {token_usage.get('cache_creation_tokens', 0):,}",
            f"  • Tokens lidos do cache: {token_usage.get('cache_read_tokens', 0):,}",
            f"  • Eficiência do cache: {metrics.get('cache_efficiency', 0):.1%}"
        ])
    
    # Uso de ferramentas
    if metrics.get('tool_uses'):
        report_lines.append(f"\n🔧 USO DE FERRAMENTAS:")
        for tool, count in sorted(metrics['tool_uses'].items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  • {tool}: {count} vezes")
    
    # Modelos utilizados
    if metrics.get('models_used'):
        report_lines.extend([
            f"\n🤖 MODELOS UTILIZADOS:",
            "  • " + ", ".join(metrics['models_used'])
        ])
    
    # Stop reasons
    if metrics.get('stop_reasons'):
        report_lines.append(f"\n🛑 RAZÕES DE PARADA:")
        for reason, count in metrics['stop_reasons'].items():
            report_lines.append(f"  • {reason}: {count} vezes")
    
    # Performance
    if metrics.get('total_duration_ms', 0) > 0:
        avg_duration = metrics['total_duration_ms'] / metrics.get('assistant_messages', 1)
        report_lines.extend([
            f"\n⚡ PERFORMANCE:",
            f"  • Tempo total de processamento: {metrics.get('total_duration_ms', 0):,} ms",
            f"  • Tempo médio por resposta: {avg_duration:.0f} ms"
        ])
    
    return "\n".join(report_lines)

def main():
    parser = argparse.ArgumentParser(description="Extrai métricas completas de JSONL e insere no LightRAG")
    parser.add_argument("file_path", help="Caminho para o arquivo JSONL")
    parser.add_argument("--analyze-only", action="store_true", help="Apenas analisar, não inserir no RAG")
    parser.add_argument("--format", choices=['json', 'text'], default='text', help="Formato de saída")
    args = parser.parse_args()
    
    # Verificar arquivo
    if not os.path.exists(args.file_path):
        print(f"Arquivo não encontrado: {args.file_path}")
        sys.exit(1)
    
    # Extrair métricas completas
    print(f"Extraindo métricas completas de {args.file_path}...")
    metrics = extract_jsonl_complete(args.file_path)
    
    if not metrics:
        print("Falha ao extrair métricas.")
        sys.exit(1)
    
    # Mostrar relatório ou JSON
    if args.format == 'json':
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:
        print(format_metrics_report(metrics))
    
    # Inserir no LightRAG se não for apenas análise
    if not args.analyze_only:
        # Preparar texto para inserção
        text_content = format_metrics_report(metrics) + "\n\n--- MENSAGENS ---\n\n"
        
        # Adicionar conteúdo das mensagens
        for msg in metrics.get('messages', [])[:50]:  # Limitar a 50 mensagens
            timestamp = msg.get('timestamp', '')
            msg_type = msg.get('type', '')
            content = msg.get('content', '')
            
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    timestamp_str = timestamp
            else:
                timestamp_str = 'N/A'
            
            text_content += f"\n[{timestamp_str}] {msg_type.upper()}: {content}\n"
        
        print(f"\nInserindo conteúdo no LightRAG (tamanho: {len(text_content)} caracteres)...")
        result = insert_to_lightrag(
            text_content, 
            metrics.get('summary', 'Análise JSONL'), 
            os.path.basename(args.file_path)
        )
        
        if result.get("success", False):
            print(f"✅ Conteúdo inserido com sucesso! ID: {result.get('documentId')}")
        else:
            print(f"❌ Falha ao inserir conteúdo: {result.get('error', 'Erro desconhecido')}")

if __name__ == "__main__":
    main()