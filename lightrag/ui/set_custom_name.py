#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para definir nomes personalizados para chats no LightRAG
"""

import json
import os
import sys
import argparse

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

def save_custom_name(chat_id, custom_name):
    """Salva um nome personalizado para um chat"""
    if not chat_id:
        print("ID do chat não fornecido")
        return False
        
    # Carregar nomes existentes
    custom_names = load_custom_names()
    
    # Atualizar ou adicionar o nome personalizado
    custom_names[chat_id] = custom_name
    
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
            
        print(f"Nome personalizado salvo: {chat_id} = {custom_name}")
        return True
    except Exception as e:
        print(f"Erro ao salvar nome personalizado: {e}")
        return False

def list_custom_names():
    """Lista todos os nomes personalizados"""
    custom_names = load_custom_names()
    
    if not custom_names:
        print("Nenhum nome personalizado encontrado")
        return
    
    print(f"Nomes personalizados ({len(custom_names)}):")
    for chat_id, name in custom_names.items():
        print(f"  {chat_id}: {name}")

def list_chat_files():
    """Lista os arquivos de chat disponíveis"""
    projects_dir = os.path.join(os.path.dirname(BASE_DIR), "projects", "-Users-agents--claude-lightrag-ui")
    if not os.path.exists(projects_dir):
        print(f"Diretório de projetos não encontrado: {projects_dir}")
        return []
    
    # Listar arquivos .jsonl no diretório de projetos
    chat_files = [f for f in os.listdir(projects_dir) if f.endswith('.jsonl')]
    return chat_files

def main():
    parser = argparse.ArgumentParser(description="Gerenciador de nomes personalizados para chats LightRAG")
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")
    
    # Comando list
    list_parser = subparsers.add_parser("list", help="Listar nomes personalizados")
    list_parser.add_argument("--chats", action="store_true", help="Listar chats disponíveis")
    
    # Comando set
    set_parser = subparsers.add_parser("set", help="Definir nome personalizado")
    set_parser.add_argument("chat_id", help="ID do chat")
    set_parser.add_argument("nome", help="Nome personalizado")
    
    # Comando delete
    delete_parser = subparsers.add_parser("delete", help="Remover nome personalizado")
    delete_parser.add_argument("chat_id", help="ID do chat")
    
    args = parser.parse_args()
    
    if args.comando == "list":
        if args.chats:
            chat_files = list_chat_files()
            if chat_files:
                print(f"Chats disponíveis ({len(chat_files)}):")
                for chat_file in chat_files:
                    chat_id = chat_file.split('.')[0]
                    custom_names = load_custom_names()
                    custom_name = custom_names.get(chat_id, "")
                    if custom_name:
                        print(f"  {chat_id} - Nome: {custom_name}")
                    else:
                        print(f"  {chat_id}")
            else:
                print("Nenhum chat encontrado")
        else:
            list_custom_names()
    
    elif args.comando == "set":
        if save_custom_name(args.chat_id, args.nome):
            print(f"Nome personalizado definido com sucesso!")
        else:
            print("Falha ao definir nome personalizado.")
    
    elif args.comando == "delete":
        custom_names = load_custom_names()
        if args.chat_id in custom_names:
            del custom_names[args.chat_id]
            
            try:
                with open(CUSTOM_NAMES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(custom_names, f, indent=2, ensure_ascii=False)
                print(f"Nome personalizado removido: {args.chat_id}")
            except Exception as e:
                print(f"Erro ao remover nome personalizado: {e}")
        else:
            print(f"Chat ID não encontrado: {args.chat_id}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()