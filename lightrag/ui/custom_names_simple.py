#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema simplificado para gestão de nomes personalizados
"""

import json
import os
import sys

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUSTOM_NAMES_FILE = os.path.join(BASE_DIR, "custom_project_names.json")

def load_custom_names():
    """Carrega os nomes personalizados do arquivo JSON"""
    if os.path.exists(CUSTOM_NAMES_FILE):
        try:
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar nomes personalizados: {e}")
    return {}

def save_custom_name(doc_id, custom_name):
    """Salva um nome personalizado para um documento"""
    if not doc_id:
        print("ID do documento não fornecido")
        return False
        
    # Carregar nomes existentes
    custom_names = load_custom_names()
    
    # Atualizar ou adicionar o nome personalizado
    custom_names[doc_id] = custom_name
    
    try:
        # Criar backup do arquivo antes de modificar
        if os.path.exists(CUSTOM_NAMES_FILE):
            backup_path = f"{CUSTOM_NAMES_FILE}.bak"
            with open(CUSTOM_NAMES_FILE, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dest:
                    dest.write(src.read())
        
        # Salvar os nomes atualizados
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_names, f, indent=2, ensure_ascii=False)
            
        print(f"Nome personalizado salvo: {doc_id} = {custom_name}")
        return True
    except Exception as e:
        print(f"Erro ao salvar nome personalizado: {e}")
        return False

def delete_custom_name(doc_id):
    """Remove um nome personalizado"""
    if not doc_id:
        print("ID do documento não fornecido")
        return False
        
    # Carregar nomes existentes
    custom_names = load_custom_names()
    
    # Verificar se o documento existe
    if doc_id not in custom_names:
        print(f"Documento {doc_id} não encontrado")
        return False
    
    # Remover o nome personalizado
    del custom_names[doc_id]
    
    try:
        # Salvar os nomes atualizados
        with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(custom_names, f, indent=2, ensure_ascii=False)
            
        print(f"Nome personalizado removido: {doc_id}")
        return True
    except Exception as e:
        print(f"Erro ao remover nome personalizado: {e}")
        return False

def get_custom_name(doc_id):
    """Obtém o nome personalizado de um documento específico"""
    if not doc_id:
        return None
        
    # Carregar nomes existentes
    custom_names = load_custom_names()
    
    # Retornar o nome personalizado se existir
    return custom_names.get(doc_id)

def list_custom_names():
    """Lista todos os nomes personalizados"""
    custom_names = load_custom_names()
    
    if not custom_names:
        print("Nenhum nome personalizado encontrado")
        return
    
    print(f"Nomes personalizados ({len(custom_names)}):")
    for doc_id, name in custom_names.items():
        print(f"  {doc_id}: {name}")

# Função principal para uso em linha de comando
def main():
    if len(sys.argv) < 2:
        print("Uso: python custom_names_simple.py [list|get|set|delete] [args]")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        list_custom_names()
    
    elif command == "get" and len(sys.argv) >= 3:
        doc_id = sys.argv[2]
        name = get_custom_name(doc_id)
        if name:
            print(f"Nome personalizado para {doc_id}: {name}")
        else:
            print(f"Nenhum nome personalizado encontrado para {doc_id}")
    
    elif command == "set" and len(sys.argv) >= 4:
        doc_id = sys.argv[2]
        custom_name = sys.argv[3]
        if save_custom_name(doc_id, custom_name):
            print(f"Nome personalizado definido com sucesso!")
            # Verificar se foi salvo corretamente
            saved_name = get_custom_name(doc_id)
            if saved_name == custom_name:
                print("✓ Verificado: nome salvo corretamente.")
            else:
                print(f"⚠ Alerta: Verificação falhou. Nome atual: {saved_name}")
        else:
            print("Falha ao definir nome personalizado.")
    
    elif command == "delete" and len(sys.argv) >= 3:
        doc_id = sys.argv[2]
        if delete_custom_name(doc_id):
            print("Nome personalizado removido com sucesso!")
        else:
            print("Falha ao remover nome personalizado.")
    
    else:
        print("Comando inválido ou argumentos insuficientes.")
        print("Uso: python custom_names_simple.py [list|get|set|delete] [args]")

if __name__ == "__main__":
    main()