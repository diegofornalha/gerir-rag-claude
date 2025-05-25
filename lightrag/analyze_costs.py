#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para análise detalhada de custos e métricas de conversas Claude
Baseado nos exemplos da documentação JSONL
"""

import json
import argparse
import glob
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
import sys

# Custos aproximados por modelo (em USD por milhão de tokens)
MODEL_COSTS = {
    'claude-3-5-sonnet-20241022': {'input': 3.00, 'output': 15.00},
    'claude-3-5-haiku-20241022': {'input': 0.80, 'output': 4.00},
    'claude-3-opus-20240229': {'input': 15.00, 'output': 75.00},
    'claude-opus-4-20250514': {'input': 15.00, 'output': 75.00},
    'claude-3-sonnet-20240229': {'input': 3.00, 'output': 15.00},
    'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25}
}

class CostAnalyzer:
    """Analisador de custos e métricas para conversas Claude"""
    
    def __init__(self):
        self.total_cost = 0.0
        self.costs_by_model = defaultdict(float)
        self.token_usage = defaultdict(int)
        self.tool_usage = defaultdict(int)
        self.sessions_analyzed = 0
        self.messages_processed = 0
        self.errors = []
        
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analisa um arquivo JSONL específico"""
        file_metrics = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'total_cost': 0.0,
            'messages': 0,
            'duration_ms': 0,
            'token_usage': defaultdict(int),
            'tool_usage': defaultdict(int),
            'models_used': set(),
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line.strip())
                        
                        if entry.get('type') == 'assistant':
                            file_metrics['messages'] += 1
                            self.messages_processed += 1
                            
                            # Custo
                            if 'costUSD' in entry:
                                cost = entry['costUSD']
                                file_metrics['total_cost'] += cost
                                self.total_cost += cost
                                
                                # Por modelo
                                model = entry.get('message', {}).get('model', 'unknown')
                                file_metrics['models_used'].add(model)
                                self.costs_by_model[model] += cost
                            
                            # Duração
                            if 'durationMs' in entry:
                                file_metrics['duration_ms'] += entry['durationMs']
                            
                            # Uso de tokens
                            usage = entry.get('message', {}).get('usage', {})
                            if usage:
                                for key, value in usage.items():
                                    if key in ['input_tokens', 'output_tokens', 
                                              'cache_creation_input_tokens', 'cache_read_input_tokens']:
                                        file_metrics['token_usage'][key] += value
                                        self.token_usage[key] += value
                            
                            # Uso de ferramentas
                            content = entry.get('message', {}).get('content', [])
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                                        tool_name = item.get('name', 'unknown')
                                        file_metrics['tool_usage'][tool_name] += 1
                                        self.tool_usage[tool_name] += 1
                    
                    except json.JSONDecodeError as e:
                        error_msg = f"Erro JSON na linha {line_num}: {e}"
                        file_metrics['errors'].append(error_msg)
                        self.errors.append(f"{file_path}: {error_msg}")
                    except Exception as e:
                        error_msg = f"Erro na linha {line_num}: {e}"
                        file_metrics['errors'].append(error_msg)
                        self.errors.append(f"{file_path}: {error_msg}")
            
            self.sessions_analyzed += 1
            
            # Converter sets e defaultdicts para tipos serializáveis
            file_metrics['models_used'] = list(file_metrics['models_used'])
            file_metrics['token_usage'] = dict(file_metrics['token_usage'])
            file_metrics['tool_usage'] = dict(file_metrics['tool_usage'])
            
            return file_metrics
            
        except Exception as e:
            error_msg = f"Erro ao abrir arquivo: {e}"
            self.errors.append(f"{file_path}: {error_msg}")
            file_metrics['errors'].append(error_msg)
            return file_metrics
    
    def analyze_directory(self, directory: str, pattern: str = "*.jsonl") -> List[Dict[str, Any]]:
        """Analisa todos os arquivos JSONL em um diretório"""
        files = glob.glob(os.path.join(directory, pattern))
        results = []
        
        print(f"Encontrados {len(files)} arquivos para análise em {directory}")
        
        for file_path in sorted(files):
            print(f"Analisando: {os.path.basename(file_path)}...", end='', flush=True)
            result = self.analyze_file(file_path)
            results.append(result)
            print(f" ✓ (${result['total_cost']:.4f})")
        
        return results
    
    def generate_report(self) -> str:
        """Gera relatório completo de análise"""
        report_lines = [
            "=" * 80,
            "📊 RELATÓRIO DE ANÁLISE DE CUSTOS E MÉTRICAS CLAUDE",
            "=" * 80,
            f"\n📈 RESUMO EXECUTIVO:",
            f"  • Sessões analisadas: {self.sessions_analyzed}",
            f"  • Mensagens processadas: {self.messages_processed}",
            f"  • Custo total: ${self.total_cost:.4f}",
        ]
        
        if self.sessions_analyzed > 0:
            avg_cost_per_session = self.total_cost / self.sessions_analyzed
            report_lines.append(f"  • Custo médio por sessão: ${avg_cost_per_session:.4f}")
        
        if self.messages_processed > 0:
            avg_cost_per_message = self.total_cost / self.messages_processed
            report_lines.append(f"  • Custo médio por mensagem: ${avg_cost_per_message:.4f}")
        
        # Custos por modelo
        report_lines.extend([
            f"\n💰 CUSTOS POR MODELO:",
        ])
        for model, cost in sorted(self.costs_by_model.items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / self.total_cost * 100) if self.total_cost > 0 else 0
            report_lines.append(f"  • {model}: ${cost:.4f} ({percentage:.1f}%)")
        
        # Uso de tokens
        report_lines.extend([
            f"\n🔢 USO DE TOKENS:",
        ])
        
        total_input = self.token_usage.get('input_tokens', 0)
        total_output = self.token_usage.get('output_tokens', 0)
        cache_created = self.token_usage.get('cache_creation_input_tokens', 0)
        cache_read = self.token_usage.get('cache_read_input_tokens', 0)
        
        report_lines.extend([
            f"  • Tokens de entrada: {total_input:,}",
            f"  • Tokens de saída: {total_output:,}",
            f"  • Tokens para criar cache: {cache_created:,}",
            f"  • Tokens lidos do cache: {cache_read:,}",
        ])
        
        # Eficiência do cache
        if cache_created > 0:
            cache_efficiency = cache_read / cache_created
            cache_savings = self._estimate_cache_savings(cache_read)
            report_lines.extend([
                f"\n📊 EFICIÊNCIA DO CACHE:",
                f"  • Taxa de reutilização: {cache_efficiency:.1%}",
                f"  • Economia estimada: ${cache_savings:.4f}",
            ])
        
        # Uso de ferramentas
        if self.tool_usage:
            report_lines.extend([
                f"\n🔧 USO DE FERRAMENTAS (Top 10):",
            ])
            for tool, count in sorted(self.tool_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
                report_lines.append(f"  • {tool}: {count} vezes")
        
        # Erros
        if self.errors:
            report_lines.extend([
                f"\n⚠️  ERROS ENCONTRADOS: {len(self.errors)}",
            ])
            for error in self.errors[:5]:  # Mostrar apenas os primeiros 5 erros
                report_lines.append(f"  • {error}")
            if len(self.errors) > 5:
                report_lines.append(f"  • ... e {len(self.errors) - 5} erros adicionais")
        
        return "\n".join(report_lines)
    
    def _estimate_cache_savings(self, cache_read_tokens: int) -> float:
        """Estima economia com uso de cache"""
        # Usar custo médio de entrada do modelo mais comum
        avg_input_cost = 3.00 / 1_000_000  # $3 por milhão de tokens
        return cache_read_tokens * avg_input_cost
    
    def export_json(self, output_file: str, file_results: List[Dict[str, Any]]):
        """Exporta resultados completos em JSON"""
        export_data = {
            'summary': {
                'total_cost': self.total_cost,
                'sessions_analyzed': self.sessions_analyzed,
                'messages_processed': self.messages_processed,
                'costs_by_model': dict(self.costs_by_model),
                'token_usage': dict(self.token_usage),
                'tool_usage': dict(self.tool_usage),
                'errors_count': len(self.errors)
            },
            'file_results': file_results,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Resultados exportados para: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Analisa custos e métricas de conversas Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Analisar um arquivo específico
  python analyze_costs.py /path/to/conversation.jsonl
  
  # Analisar todos os arquivos em um diretório
  python analyze_costs.py /Users/agents/.claude/projects/ --directory
  
  # Exportar resultados em JSON
  python analyze_costs.py /path/to/files/ --directory --export results.json
        """
    )
    
    parser.add_argument("path", help="Caminho para arquivo JSONL ou diretório")
    parser.add_argument("--directory", "-d", action="store_true", 
                        help="Analisar todos os arquivos JSONL no diretório")
    parser.add_argument("--pattern", "-p", default="*.jsonl",
                        help="Padrão de arquivos para buscar (padrão: *.jsonl)")
    parser.add_argument("--export", "-e", metavar="FILE",
                        help="Exportar resultados para arquivo JSON")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Modo silencioso - apenas mostrar relatório final")
    
    args = parser.parse_args()
    
    # Verificar se o caminho existe
    if not os.path.exists(args.path):
        print(f"❌ Erro: Caminho não encontrado: {args.path}")
        sys.exit(1)
    
    # Criar analisador
    analyzer = CostAnalyzer()
    
    # Analisar arquivos
    if args.directory:
        if not os.path.isdir(args.path):
            print(f"❌ Erro: {args.path} não é um diretório")
            sys.exit(1)
        
        file_results = analyzer.analyze_directory(args.path, args.pattern)
    else:
        if not os.path.isfile(args.path):
            print(f"❌ Erro: {args.path} não é um arquivo")
            sys.exit(1)
        
        if not args.quiet:
            print(f"Analisando arquivo: {args.path}")
        
        result = analyzer.analyze_file(args.path)
        file_results = [result]
    
    # Gerar e mostrar relatório
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Exportar se solicitado
    if args.export:
        analyzer.export_json(args.export, file_results)
    
    # Mostrar estatísticas finais
    if analyzer.sessions_analyzed > 0:
        print(f"\n✅ Análise concluída com sucesso!")
    else:
        print(f"\n⚠️  Nenhuma sessão foi analisada.")

if __name__ == "__main__":
    main()