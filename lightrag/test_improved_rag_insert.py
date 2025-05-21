#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste da implementação melhorada de inserção de arquivo no LightRAG
"""

import os
import json
import sys
from improved_rag_insert_file import rag_insert_file, check_content_similarity, calculate_file_hash

def test_content_similarity():
    """Teste da função de similaridade de conteúdo"""
    print("\n=== Teste de similaridade de conteúdo ===")
    
    test_cases = [
        # Textos idênticos
        ("Este é um teste", "Este é um teste", True),
        # Textos com pequenas variações
        ("Este é um teste de similaridade", "Este é um teste para similaridade", True),
        # Textos com espaços diferentes
        ("LightRAG é um sistema  de RAG simplificado", "LightRAG é  um sistema de RAG simplificado", True),
        # Textos completamente diferentes
        ("LightRAG é um sistema de RAG", "Claude é um assistente de IA", False),
        # Um texto é substring do outro
        ("LightRAG sistema", "O LightRAG sistema é útil para consultas", True),
        # Textos vazios
        ("", "", False),
        ("Texto não vazio", "", False)
    ]
    
    for text1, text2, expected in test_cases:
        result = check_content_similarity(text1, text2)
        print(f"Textos: '{text1[:20]}...' e '{text2[:20]}...'")
        print(f"Esperado: {expected}, Obtido: {result}")
        if result == expected:
            print("✅ Teste passou")
        else:
            print("❌ Teste falhou")
        print()

def test_hash_calculation():
    """Teste da função de cálculo de hash"""
    print("\n=== Teste de cálculo de hash de arquivo ===")
    
    # Criar arquivos temporários para teste
    temp_files = []
    
    try:
        # Arquivo 1
        temp_file1 = "/tmp/test_lightrag_file1.txt"
        with open(temp_file1, 'w') as f:
            f.write("Conteúdo de teste para LightRAG")
        temp_files.append(temp_file1)
        
        # Arquivo 2 (mesmo conteúdo)
        temp_file2 = "/tmp/test_lightrag_file2.txt"
        with open(temp_file2, 'w') as f:
            f.write("Conteúdo de teste para LightRAG")
        temp_files.append(temp_file2)
        
        # Arquivo 3 (conteúdo diferente)
        temp_file3 = "/tmp/test_lightrag_file3.txt"
        with open(temp_file3, 'w') as f:
            f.write("Conteúdo diferente para teste de hash")
        temp_files.append(temp_file3)
        
        # Calcular hashes
        hash1 = calculate_file_hash(temp_file1)
        hash2 = calculate_file_hash(temp_file2)
        hash3 = calculate_file_hash(temp_file3)
        
        print(f"Hash do arquivo 1: {hash1}")
        print(f"Hash do arquivo 2: {hash2}")
        print(f"Hash do arquivo 3: {hash3}")
        
        # Verificar resultados
        if hash1 == hash2:
            print("✅ Hash igual para arquivos com mesmo conteúdo")
        else:
            print("❌ Hash diferente para arquivos com mesmo conteúdo")
        
        if hash1 != hash3:
            print("✅ Hash diferente para arquivos com conteúdo diferente")
        else:
            print("❌ Hash igual para arquivos com conteúdo diferente")
    
    finally:
        # Limpar arquivos temporários
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def test_file_insertion(file_path=None):
    """Teste da função principal de inserção de arquivo"""
    print("\n=== Teste de inserção de arquivo ===")
    
    if not file_path:
        # Tentar encontrar um arquivo JSONL para teste
        projects_dir = "/Users/agents/.claude/projects/-Users-agents--claude"
        if os.path.exists(projects_dir):
            import glob
            jsonl_files = glob.glob(f"{projects_dir}/*.jsonl")
            if jsonl_files:
                file_path = jsonl_files[0]
    
    if not file_path or not os.path.exists(file_path):
        print("❌ Nenhum arquivo de teste disponível")
        return
    
    print(f"Usando arquivo: {file_path}")
    
    # Primeira inserção (sem força)
    print("\n1. Primeira inserção (deve ter sucesso):")
    result1 = rag_insert_file(file_path)
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    
    # Segunda inserção (sem força - deve detectar duplicação)
    print("\n2. Segunda inserção sem força (deve detectar duplicação):")
    result2 = rag_insert_file(file_path)
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    
    # Terceira inserção (com força - deve inserir mesmo sendo duplicado)
    print("\n3. Terceira inserção com força (deve inserir mesmo duplicado):")
    result3 = rag_insert_file(file_path, force=True)
    print(json.dumps(result3, indent=2, ensure_ascii=False))
    
    # Verificar resultados
    if result1.get("success", False):
        print("✅ Primeira inserção teve sucesso")
    else:
        print("❌ Primeira inserção falhou")
    
    if not result2.get("success", False) and "duplicado" in result2.get("error", ""):
        print("✅ Segunda inserção detectou duplicação corretamente")
    else:
        print("❌ Segunda inserção não detectou duplicação")
    
    if result3.get("success", False) and result3.get("is_duplicate", False):
        print("✅ Terceira inserção com força teve sucesso apesar da duplicação")
    else:
        print("❌ Terceira inserção com força falhou")

def main():
    print("=== Testes da implementação melhorada de inserção de arquivo no LightRAG ===")
    
    # Testar funções auxiliares
    test_content_similarity()
    test_hash_calculation()
    
    # Testar inserção de arquivo
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_file_insertion(file_path)

if __name__ == "__main__":
    main()