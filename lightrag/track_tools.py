#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para rastrear e analisar o uso de ferramentas (tool_use e tool_result)
conforme documentado no formato JSONL do Claude Code
"""

import json
import argparse
import os
import sys
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Tuple

class ToolTracker:
    """Rastreador de uso de ferramentas do Claude"""
    
    def __init__(self):
        self.tool_uses = []
        self.tool_results = []
        self.tool_pairs = []  # Pares de tool_use -> tool_result
        self.tool_stats = defaultdict(lambda: {
            'count': 0,
            'success': 0,
            'errors': 0,
            'total_duration_ms': 0,
            'input_sizes': [],
            'output_sizes': []
        })
        self.tool_sequences = []
        self.current_sequence = []
        
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Processa um arquivo JSONL para extrair informações de ferramentas"""
        file_info = {
            'file_path': file_path,
            'tool_use_count': 0,
            'tool_result_count': 0,
            'unique_tools': set(),
            'tool_sequences': [],
            'errors': []
        }
        
        # Mapa temporário para correlacionar tool_use com tool_result
        pending_tools = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line.strip())
                        
                        # Processar mensagens do assistente (tool_use)
                        if entry.get('type') == 'assistant':
                            content = entry.get('message', {}).get('content', [])
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                                        tool_info = {
                                            'id': item.get('id'),
                                            'name': item.get('name'),
                                            'input': item.get('input'),
                                            'timestamp': entry.get('timestamp'),
                                            'uuid': entry.get('uuid'),
                                            'cost_usd': entry.get('costUSD', 0),
                                            'duration_ms': entry.get('durationMs', 0)
                                        }
                                        
                                        self.tool_uses.append(tool_info)
                                        file_info['tool_use_count'] += 1
                                        file_info['unique_tools'].add(tool_info['name'])
                                        
                                        # Adicionar ao mapa de pendentes
                                        if tool_info['id']:
                                            pending_tools[tool_info['id']] = tool_info
                                        
                                        # Adicionar à sequência atual
                                        self.current_sequence.append({
                                            'type': 'tool_use',
                                            'name': tool_info['name'],
                                            'timestamp': tool_info['timestamp']
                                        })
                                        
                                        # Atualizar estatísticas
                                        stats = self.tool_stats[tool_info['name']]
                                        stats['count'] += 1
                                        
                                        # Tamanho do input
                                        if tool_info['input']:
                                            input_size = len(json.dumps(tool_info['input']))
                                            stats['input_sizes'].append(input_size)
                        
                        # Processar mensagens do usuário (tool_result)
                        elif entry.get('type') == 'user':
                            content = entry.get('message', {}).get('content', [])
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'tool_result':
                                        result_info = {
                                            'tool_use_id': item.get('tool_use_id'),
                                            'content': item.get('content'),
                                            'timestamp': entry.get('timestamp'),
                                            'uuid': entry.get('uuid')
                                        }
                                        
                                        # Informações adicionais do toolUseResult
                                        tool_use_result = entry.get('toolUseResult', {})
                                        if tool_use_result:
                                            result_info['extra_data'] = tool_use_result
                                        
                                        self.tool_results.append(result_info)
                                        file_info['tool_result_count'] += 1
                                        
                                        # Correlacionar com tool_use
                                        if result_info['tool_use_id'] in pending_tools:
                                            tool_use = pending_tools[result_info['tool_use_id']]
                                            
                                            # Criar par tool_use -> tool_result
                                            pair = {
                                                'tool_name': tool_use['name'],
                                                'tool_use': tool_use,
                                                'tool_result': result_info,
                                                'success': self._is_success(result_info)
                                            }
                                            self.tool_pairs.append(pair)
                                            
                                            # Atualizar estatísticas
                                            stats = self.tool_stats[tool_use['name']]
                                            if pair['success']:
                                                stats['success'] += 1
                                            else:
                                                stats['errors'] += 1
                                            
                                            # Tamanho do output
                                            if result_info['content']:
                                                output_size = len(result_info['content'])
                                                stats['output_sizes'].append(output_size)
                                            
                                            # Remover do mapa de pendentes
                                            del pending_tools[result_info['tool_use_id']]
                                        
                                        # Adicionar à sequência atual
                                        self.current_sequence.append({
                                            'type': 'tool_result',
                                            'success': self._is_success(result_info),
                                            'timestamp': result_info['timestamp']
                                        })
                            
                            # Verificar se é o fim de uma sequência
                            if self.current_sequence and not content:
                                file_info['tool_sequences'].append(self.current_sequence.copy())
                                self.tool_sequences.append(self.current_sequence.copy())
                                self.current_sequence = []
                    
                    except json.JSONDecodeError as e:
                        error_msg = f"Erro JSON na linha {line_num}: {e}"
                        file_info['errors'].append(error_msg)
                    except Exception as e:
                        error_msg = f"Erro na linha {line_num}: {e}"
                        file_info['errors'].append(error_msg)
            
            # Converter set para list para serialização
            file_info['unique_tools'] = list(file_info['unique_tools'])
            
            return file_info
            
        except Exception as e:
            file_info['errors'].append(f"Erro ao abrir arquivo: {e}")
            return file_info
    
    def _is_success(self, result_info: Dict[str, Any]) -> bool:
        """Determina se um tool_result indica sucesso"""
        content = result_info.get('content', '').lower()
        
        # Palavras que indicam erro
        error_indicators = ['error', 'failed', 'exception', 'not found', 'denied', 'invalid']
        
        for indicator in error_indicators:
            if indicator in content:
                return False
        
        return True
    
    def generate_report(self) -> str:
        """Gera relatório detalhado sobre uso de ferramentas"""
        report_lines = [
            "=" * 80,
            "🔧 RELATÓRIO DE ANÁLISE DE USO DE FERRAMENTAS",
            "=" * 80,
            f"\n📊 RESUMO GERAL:",
            f"  • Total de tool_use: {len(self.tool_uses)}",
            f"  • Total de tool_result: {len(self.tool_results)}",
            f"  • Pares correlacionados: {len(self.tool_pairs)}",
            f"  • Ferramentas únicas: {len(self.tool_stats)}",
        ]
        
        # Taxa de sucesso geral
        if self.tool_pairs:
            success_count = sum(1 for pair in self.tool_pairs if pair['success'])
            success_rate = success_count / len(self.tool_pairs) * 100
            report_lines.append(f"  • Taxa de sucesso geral: {success_rate:.1f}%")
        
        # Estatísticas por ferramenta
        report_lines.extend([
            f"\n📈 ESTATÍSTICAS POR FERRAMENTA:",
        ])
        
        for tool_name, stats in sorted(self.tool_stats.items(), 
                                      key=lambda x: x[1]['count'], 
                                      reverse=True):
            report_lines.append(f"\n  🔨 {tool_name}:")
            report_lines.append(f"    • Usos: {stats['count']}")
            
            total_tracked = stats['success'] + stats['errors']
            if total_tracked > 0:
                success_rate = stats['success'] / total_tracked * 100
                report_lines.append(f"    • Taxa de sucesso: {success_rate:.1f}% ({stats['success']}/{total_tracked})")
            
            if stats['input_sizes']:
                avg_input = sum(stats['input_sizes']) / len(stats['input_sizes'])
                report_lines.append(f"    • Tamanho médio de input: {avg_input:.0f} bytes")
            
            if stats['output_sizes']:
                avg_output = sum(stats['output_sizes']) / len(stats['output_sizes'])
                report_lines.append(f"    • Tamanho médio de output: {avg_output:.0f} bytes")
        
        # Sequências de ferramentas mais comuns
        if self.tool_sequences:
            report_lines.extend([
                f"\n🔄 SEQUÊNCIAS DE FERRAMENTAS MAIS COMUNS:",
            ])
            
            # Extrair padrões de sequências
            sequence_patterns = []
            for seq in self.tool_sequences:
                pattern = [item['name'] for item in seq if item['type'] == 'tool_use']
                if pattern:
                    sequence_patterns.append(' → '.join(pattern))
            
            pattern_counter = Counter(sequence_patterns)
            for pattern, count in pattern_counter.most_common(5):
                report_lines.append(f"  • {pattern}: {count} vezes")
        
        # Ferramentas com mais erros
        error_tools = [(name, stats['errors']) 
                      for name, stats in self.tool_stats.items() 
                      if stats['errors'] > 0]
        
        if error_tools:
            report_lines.extend([
                f"\n⚠️  FERRAMENTAS COM ERROS:",
            ])
            
            for tool_name, error_count in sorted(error_tools, 
                                               key=lambda x: x[1], 
                                               reverse=True)[:5]:
                report_lines.append(f"  • {tool_name}: {error_count} erros")
        
        return "\n".join(report_lines)
    
    def export_detailed_analysis(self, output_file: str):
        """Exporta análise detalhada em JSON"""
        analysis = {
            'summary': {
                'total_tool_uses': len(self.tool_uses),
                'total_tool_results': len(self.tool_results),
                'correlated_pairs': len(self.tool_pairs),
                'unique_tools': len(self.tool_stats)
            },
            'tool_statistics': {},
            'tool_sequences': self.tool_sequences,
            'top_error_messages': [],
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Converter estatísticas para formato serializável
        for tool_name, stats in self.tool_stats.items():
            analysis['tool_statistics'][tool_name] = {
                'count': stats['count'],
                'success': stats['success'],
                'errors': stats['errors'],
                'success_rate': stats['success'] / (stats['success'] + stats['errors']) * 100 
                               if (stats['success'] + stats['errors']) > 0 else 0,
                'avg_input_size': sum(stats['input_sizes']) / len(stats['input_sizes']) 
                                 if stats['input_sizes'] else 0,
                'avg_output_size': sum(stats['output_sizes']) / len(stats['output_sizes']) 
                                  if stats['output_sizes'] else 0
            }
        
        # Extrair mensagens de erro comuns
        error_messages = []
        for pair in self.tool_pairs:
            if not pair['success']:
                content = pair['tool_result'].get('content', '')
                if content:
                    error_messages.append({
                        'tool': pair['tool_name'],
                        'message': content[:200]  # Primeiros 200 caracteres
                    })
        
        # Top 10 mensagens de erro
        analysis['top_error_messages'] = error_messages[:10]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Análise detalhada exportada para: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Rastreia e analisa uso de ferramentas em conversas Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Analisar um arquivo específico
  python track_tools.py /path/to/conversation.jsonl
  
  # Analisar múltiplos arquivos
  python track_tools.py file1.jsonl file2.jsonl file3.jsonl
  
  # Exportar análise detalhada
  python track_tools.py /path/to/file.jsonl --export tools_analysis.json
        """
    )
    
    parser.add_argument("files", nargs='+', help="Arquivos JSONL para analisar")
    parser.add_argument("--export", "-e", metavar="FILE",
                        help="Exportar análise detalhada para arquivo JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Modo verboso - mostrar detalhes de processamento")
    
    args = parser.parse_args()
    
    # Criar rastreador
    tracker = ToolTracker()
    
    # Processar cada arquivo
    total_files = len(args.files)
    for i, file_path in enumerate(args.files, 1):
        if not os.path.exists(file_path):
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            continue
        
        if args.verbose:
            print(f"[{i}/{total_files}] Processando: {file_path}...", end='', flush=True)
        
        file_info = tracker.process_file(file_path)
        
        if args.verbose:
            print(f" ✓ ({file_info['tool_use_count']} uses, {file_info['tool_result_count']} results)")
        
        if file_info['errors'] and args.verbose:
            print(f"  ⚠️  {len(file_info['errors'])} erros encontrados")
    
    # Gerar e mostrar relatório
    report = tracker.generate_report()
    print("\n" + report)
    
    # Exportar se solicitado
    if args.export:
        tracker.export_detailed_analysis(args.export)
    
    print(f"\n✅ Análise concluída!")

if __name__ == "__main__":
    main()