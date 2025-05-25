#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para análises práticas de conversas Claude conforme documentado
Implementa os exemplos práticos da documentação JSONL
"""

import json
import argparse
import os
import sys
import glob
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class PracticalAnalyzer:
    """Analisador prático para conversas Claude"""
    
    def __init__(self):
        self.sessions = []
        self.all_messages = []
        self.daily_stats = defaultdict(lambda: {
            'cost': 0.0,
            'messages': 0,
            'tokens': 0,
            'cache_hits': 0,
            'tools_used': 0
        })
        
    def analyze_session(self, file_path: str) -> Dict[str, Any]:
        """Analisa uma sessão completa"""
        session = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'summary': '',
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0,
            'total_cost': 0.0,
            'message_count': 0,
            'token_stats': defaultdict(int),
            'model_usage': defaultdict(int),
            'tool_usage': defaultdict(int),
            'hourly_activity': defaultdict(int),
            'cache_efficiency': 0.0,
            'avg_response_time_ms': 0,
            'messages': []
        }
        
        response_times = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Summary
                        if entry.get('type') == 'summary':
                            session['summary'] = entry.get('summary', '')
                        
                        # Timestamps
                        timestamp = entry.get('timestamp')
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            if not session['start_time']:
                                session['start_time'] = dt
                            session['end_time'] = dt
                            
                            # Hora do dia
                            hour = dt.hour
                            session['hourly_activity'][hour] += 1
                            
                            # Data para estatísticas diárias
                            date_key = dt.strftime('%Y-%m-%d')
                        
                        # Mensagens
                        if entry.get('type') in ['user', 'assistant']:
                            session['message_count'] += 1
                            
                            message_info = {
                                'type': entry['type'],
                                'timestamp': timestamp,
                                'content_preview': ''
                            }
                            
                            # Assistant metrics
                            if entry.get('type') == 'assistant':
                                # Custo
                                if 'costUSD' in entry:
                                    cost = entry['costUSD']
                                    session['total_cost'] += cost
                                    self.daily_stats[date_key]['cost'] += cost
                                
                                # Tempo de resposta
                                if 'durationMs' in entry:
                                    response_times.append(entry['durationMs'])
                                
                                # Modelo
                                model = entry.get('message', {}).get('model', 'unknown')
                                session['model_usage'][model] += 1
                                
                                # Tokens
                                usage = entry.get('message', {}).get('usage', {})
                                for key, value in usage.items():
                                    session['token_stats'][key] += value
                                    if key in ['input_tokens', 'output_tokens']:
                                        self.daily_stats[date_key]['tokens'] += value
                                
                                # Cache hits
                                if usage.get('cache_read_input_tokens', 0) > 0:
                                    self.daily_stats[date_key]['cache_hits'] += 1
                                
                                # Ferramentas
                                content = entry.get('message', {}).get('content', [])
                                if isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get('type') == 'tool_use':
                                            tool_name = item.get('name', 'unknown')
                                            session['tool_usage'][tool_name] += 1
                                            self.daily_stats[date_key]['tools_used'] += 1
                                        elif isinstance(item, dict) and item.get('type') == 'text':
                                            text = item.get('text', '')[:100]
                                            message_info['content_preview'] = text
                                
                                message_info.update({
                                    'model': model,
                                    'cost': entry.get('costUSD', 0),
                                    'duration_ms': entry.get('durationMs', 0)
                                })
                            
                            session['messages'].append(message_info)
                            self.all_messages.append(message_info)
                            self.daily_stats[date_key]['messages'] += 1
                    
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        continue
            
            # Calcular métricas derivadas
            if session['start_time'] and session['end_time']:
                session['duration_seconds'] = (session['end_time'] - session['start_time']).total_seconds()
            
            if response_times:
                session['avg_response_time_ms'] = sum(response_times) / len(response_times)
            
            # Eficiência do cache
            cache_created = session['token_stats'].get('cache_creation_input_tokens', 0)
            cache_read = session['token_stats'].get('cache_read_input_tokens', 0)
            if cache_created > 0:
                session['cache_efficiency'] = cache_read / cache_created
            
            # Converter defaultdicts para dicts normais
            session['token_stats'] = dict(session['token_stats'])
            session['model_usage'] = dict(session['model_usage'])
            session['tool_usage'] = dict(session['tool_usage'])
            session['hourly_activity'] = dict(session['hourly_activity'])
            
            self.sessions.append(session)
            return session
            
        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")
            return session
    
    def generate_insights(self) -> Dict[str, Any]:
        """Gera insights práticos dos dados analisados"""
        insights = {
            'total_sessions': len(self.sessions),
            'total_cost': sum(s['total_cost'] for s in self.sessions),
            'total_messages': sum(s['message_count'] for s in self.sessions),
            'avg_cost_per_session': 0,
            'avg_messages_per_session': 0,
            'most_used_models': Counter(),
            'most_used_tools': Counter(),
            'peak_hours': Counter(),
            'daily_trends': {},
            'cache_savings': 0,
            'recommendations': []
        }
        
        if not self.sessions:
            return insights
        
        # Médias
        insights['avg_cost_per_session'] = insights['total_cost'] / len(self.sessions)
        insights['avg_messages_per_session'] = insights['total_messages'] / len(self.sessions)
        
        # Agregações
        for session in self.sessions:
            for model, count in session['model_usage'].items():
                insights['most_used_models'][model] += count
            
            for tool, count in session['tool_usage'].items():
                insights['most_used_tools'][tool] += count
            
            for hour, count in session['hourly_activity'].items():
                insights['peak_hours'][hour] += count
        
        # Tendências diárias
        insights['daily_trends'] = dict(self.daily_stats)
        
        # Economia com cache
        total_cache_tokens = sum(
            s['token_stats'].get('cache_read_input_tokens', 0) 
            for s in self.sessions
        )
        # Assumir custo médio de $3 por milhão de tokens de entrada
        insights['cache_savings'] = (total_cache_tokens / 1_000_000) * 3.00
        
        # Recomendações baseadas em dados
        insights['recommendations'] = self._generate_recommendations(insights)
        
        return insights
    
    def _generate_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Gera recomendações práticas baseadas nos insights"""
        recommendations = []
        
        # Recomendação de modelo
        if insights['most_used_models']:
            top_model = insights['most_used_models'].most_common(1)[0][0]
            if 'opus' in top_model and insights['avg_cost_per_session'] > 1.0:
                recommendations.append(
                    "💡 Considere usar Claude 3.5 Sonnet para tarefas menos complexas - "
                    "pode reduzir custos em até 80% mantendo qualidade similar"
                )
        
        # Recomendação de cache
        cache_efficiency = sum(
            s['cache_efficiency'] for s in self.sessions
        ) / len(self.sessions) if self.sessions else 0
        
        if cache_efficiency < 0.5:
            recommendations.append(
                "💡 Baixa eficiência de cache detectada. Considere agrupar conversas "
                "relacionadas para melhor reuso de contexto"
            )
        
        # Recomendação de horário
        if insights['peak_hours']:
            peak_hour = insights['peak_hours'].most_common(1)[0][0]
            recommendations.append(
                f"💡 Maior atividade às {peak_hour}h. Considere agendar tarefas "
                "pesadas fora deste horário para melhor performance"
            )
        
        # Recomendação de ferramentas
        if insights['most_used_tools']:
            top_tool = insights['most_used_tools'].most_common(1)[0][0]
            if top_tool in ['Read', 'Write', 'Edit']:
                recommendations.append(
                    "💡 Alto uso de ferramentas de arquivo. Considere usar "
                    "MultiEdit para operações em lote e melhorar eficiência"
                )
        
        return recommendations
    
    def generate_visualizations(self, output_dir: str = "."):
        """Gera visualizações dos dados"""
        if not self.sessions:
            print("Sem dados para visualizar")
            return
        
        # Configurar matplotlib
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # 1. Gráfico de custos diários
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = sorted(self.daily_stats.keys())
        costs = [self.daily_stats[date]['cost'] for date in dates]
        
        ax.plot(dates, costs, marker='o', linewidth=2, markersize=8)
        ax.set_title('Custos Diários - Conversas Claude', fontsize=16)
        ax.set_xlabel('Data', fontsize=12)
        ax.set_ylabel('Custo (USD)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Formatar eixo X
        if len(dates) > 7:
            ax.xaxis.set_major_locator(plt.MaxNLocator(10))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'daily_costs.png'), dpi=300)
        plt.close()
        
        # 2. Gráfico de distribuição de modelos
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Pizza de uso de modelos
        model_counts = defaultdict(int)
        for session in self.sessions:
            for model, count in session['model_usage'].items():
                model_counts[model] += count
        
        if model_counts:
            models = list(model_counts.keys())
            counts = list(model_counts.values())
            
            ax1.pie(counts, labels=models, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Distribuição de Uso por Modelo', fontsize=14)
        
        # Barras de ferramentas mais usadas
        tool_counts = defaultdict(int)
        for session in self.sessions:
            for tool, count in session['tool_usage'].items():
                tool_counts[tool] += count
        
        if tool_counts:
            top_tools = dict(Counter(tool_counts).most_common(10))
            tools = list(top_tools.keys())
            counts = list(top_tools.values())
            
            ax2.barh(tools, counts)
            ax2.set_title('Top 10 Ferramentas Mais Usadas', fontsize=14)
            ax2.set_xlabel('Número de Usos')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'usage_distribution.png'), dpi=300)
        plt.close()
        
        # 3. Heatmap de atividade por hora
        fig, ax = plt.subplots(figsize=(10, 6))
        
        hourly_activity = defaultdict(int)
        for session in self.sessions:
            for hour, count in session['hourly_activity'].items():
                hourly_activity[hour] += count
        
        hours = list(range(24))
        activity = [hourly_activity.get(h, 0) for h in hours]
        
        bars = ax.bar(hours, activity, color='skyblue', edgecolor='navy', alpha=0.7)
        
        # Destacar horários de pico
        max_activity = max(activity) if activity else 0
        for i, (h, a) in enumerate(zip(hours, activity)):
            if a == max_activity and max_activity > 0:
                bars[i].set_color('orange')
        
        ax.set_title('Distribuição de Atividade por Hora do Dia', fontsize=16)
        ax.set_xlabel('Hora do Dia', fontsize=12)
        ax.set_ylabel('Número de Mensagens', fontsize=12)
        ax.set_xticks(hours)
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'hourly_activity.png'), dpi=300)
        plt.close()
        
        print(f"✅ Visualizações salvas em: {output_dir}")
    
    def export_report(self, output_file: str):
        """Exporta relatório completo em formato Markdown"""
        insights = self.generate_insights()
        
        report_lines = [
            "# Relatório de Análise Prática - Conversas Claude",
            f"\n*Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "\n## 📊 Resumo Executivo",
            f"- **Total de Sessões**: {insights['total_sessions']}",
            f"- **Total de Mensagens**: {insights['total_messages']:,}",
            f"- **Custo Total**: ${insights['total_cost']:.2f}",
            f"- **Custo Médio por Sessão**: ${insights['avg_cost_per_session']:.2f}",
            f"- **Mensagens Médias por Sessão**: {insights['avg_messages_per_session']:.1f}",
            f"- **Economia com Cache**: ${insights['cache_savings']:.2f}",
            "\n## 🤖 Modelos Mais Utilizados"
        ]
        
        for model, count in insights['most_used_models'].most_common(5):
            report_lines.append(f"1. **{model}**: {count} usos")
        
        report_lines.append("\n## 🔧 Ferramentas Mais Utilizadas")
        
        for tool, count in insights['most_used_tools'].most_common(10):
            report_lines.append(f"- **{tool}**: {count} usos")
        
        report_lines.append("\n## 📈 Tendências Diárias")
        report_lines.append("\n| Data | Custo | Mensagens | Tokens | Cache Hits |")
        report_lines.append("|------|-------|-----------|--------|------------|")
        
        for date in sorted(insights['daily_trends'].keys())[-7:]:  # Últimos 7 dias
            stats = insights['daily_trends'][date]
            report_lines.append(
                f"| {date} | ${stats['cost']:.2f} | {stats['messages']} | "
                f"{stats['tokens']:,} | {stats['cache_hits']} |"
            )
        
        report_lines.append("\n## 💡 Recomendações")
        
        for rec in insights['recommendations']:
            report_lines.append(f"\n{rec}")
        
        report_lines.append("\n## 📊 Visualizações")
        report_lines.append("\n- `daily_costs.png`: Evolução dos custos diários")
        report_lines.append("- `usage_distribution.png`: Distribuição de uso por modelo e ferramentas")
        report_lines.append("- `hourly_activity.png`: Padrão de atividade por hora do dia")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"📄 Relatório exportado para: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Análises práticas de conversas Claude com insights e visualizações",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("path", help="Arquivo JSONL ou diretório com arquivos")
    parser.add_argument("--directory", "-d", action="store_true",
                        help="Processar todos os arquivos JSONL no diretório")
    parser.add_argument("--output-dir", "-o", default=".",
                        help="Diretório para salvar visualizações (padrão: diretório atual)")
    parser.add_argument("--report", "-r", metavar="FILE",
                        help="Gerar relatório Markdown")
    parser.add_argument("--no-viz", action="store_true",
                        help="Pular geração de visualizações")
    
    args = parser.parse_args()
    
    # Verificar matplotlib
    if not args.no_viz:
        try:
            import matplotlib
        except ImportError:
            print("⚠️  matplotlib não instalado. Instale com: pip install matplotlib")
            print("   Continuando sem visualizações...")
            args.no_viz = True
    
    # Criar analisador
    analyzer = PracticalAnalyzer()
    
    # Processar arquivos
    if args.directory:
        if not os.path.isdir(args.path):
            print(f"❌ Erro: {args.path} não é um diretório")
            sys.exit(1)
        
        files = glob.glob(os.path.join(args.path, "**/*.jsonl"), recursive=True)
        print(f"Encontrados {len(files)} arquivos JSONL")
        
        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Processando: {os.path.basename(file_path)}...")
            analyzer.analyze_session(file_path)
    else:
        if not os.path.isfile(args.path):
            print(f"❌ Erro: {args.path} não é um arquivo")
            sys.exit(1)
        
        print(f"Processando: {args.path}")
        analyzer.analyze_session(args.path)
    
    # Gerar insights
    insights = analyzer.generate_insights()
    
    print(f"\n✅ Análise concluída!")
    print(f"   • Sessões analisadas: {insights['total_sessions']}")
    print(f"   • Custo total: ${insights['total_cost']:.2f}")
    print(f"   • Economia com cache: ${insights['cache_savings']:.2f}")
    
    # Gerar visualizações
    if not args.no_viz:
        print("\n📊 Gerando visualizações...")
        analyzer.generate_visualizations(args.output_dir)
    
    # Gerar relatório
    if args.report:
        analyzer.export_report(args.report)
    
    # Mostrar recomendações
    if insights['recommendations']:
        print("\n💡 Recomendações:")
        for rec in insights['recommendations']:
            print(f"   {rec}")

if __name__ == "__main__":
    main()