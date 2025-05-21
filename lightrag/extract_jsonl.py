#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para extrair conteúdo de arquivos JSONL e inserir no LightRAG
"""

import json
import argparse
import urllib.request
import urllib.parse
import sys
import os

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

def extract_jsonl_content(file_path, max_lines=100):
    """Extrai conteúdo relevante de um arquivo JSONL"""
    try:
        content = []
        with open(file_path, 'r', encoding='utf-8') as f:
            # Ler primeira linha para pegar o resumo
            first_line = f.readline().strip()
            summary = "Arquivo JSONL"
            
            if first_line.startswith('{'):
                try:
                    data = json.loads(first_line)
                    if 'summary' in data:
                        summary = data['summary']
                except:
                    pass
            
            # Ler linhas restantes
            line_count = 1
            for line in f:
                if line_count >= max_lines:
                    break
                
                try:
                    data = json.loads(line.strip())
                    if 'message' in data:
                        msg = data['message']
                        if 'content' in msg:
                            if isinstance(msg['content'], str):
                                content.append(msg['content'])
                            elif isinstance(msg['content'], list):
                                for item in msg['content']:
                                    if isinstance(item, dict) and 'text' in item:
                                        content.append(item['text'])
                except:
                    pass
                
                line_count += 1
        
        # Montar texto completo
        full_text = f"RESUMO: {summary}\n\n" + "\n\n".join(content)
        return full_text, summary, os.path.basename(file_path)
    
    except Exception as e:
        print(f"Erro ao extrair conteúdo do arquivo {file_path}: {e}")
        return None, None, None

def main():
    parser = argparse.ArgumentParser(description="Extrai conteúdo de JSONL e insere no LightRAG")
    parser.add_argument("file_path", help="Caminho para o arquivo JSONL")
    parser.add_argument("--max", type=int, default=100, help="Número máximo de linhas")
    args = parser.parse_args()
    
    # Verificar arquivo
    if not os.path.exists(args.file_path):
        print(f"Arquivo não encontrado: {args.file_path}")
        sys.exit(1)
    
    # Extrair conteúdo
    print(f"Extraindo conteúdo de {args.file_path}...")
    text, summary, source_id = extract_jsonl_content(args.file_path, args.max)
    
    if not text:
        print("Falha ao extrair conteúdo.")
        sys.exit(1)
    
    # Inserir no LightRAG
    print(f"Inserindo conteúdo no LightRAG (tamanho: {len(text)} caracteres)...")
    result = insert_to_lightrag(text, summary, source_id)
    
    if result.get("success", False):
        print(f"✅ Conteúdo inserido com sucesso! ID: {result.get('documentId')}")
    else:
        print(f"❌ Falha ao inserir conteúdo: {result.get('error', 'Erro desconhecido')}")

if __name__ == "__main__":
    main()