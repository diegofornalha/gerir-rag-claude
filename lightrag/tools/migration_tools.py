#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Ferramentas de Migração e Manutenção
Script consolidado para migrações, correções e atualizações
"""

import os
import sys
import json
import re
import glob
import argparse
import shutil
import hashlib
import datetime
import time
from typing import Dict, List, Any, Optional, Tuple, Set

# Garantir que o diretório raiz esteja no PYTHONPATH
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BASE_DIR)

# Utilitários de log
def log_info(msg):
    """Log de informação"""
    print(f"[INFO] {msg}")

def log_warning(msg):
    """Log de aviso"""
    print(f"[AVISO] {msg}")

def log_error(msg):
    """Log de erro"""
    print(f"[ERRO] {msg}")

def log_success(msg):
    """Log de sucesso"""
    print(f"[SUCESSO] {msg}")

# Funções utilitárias
def backup_file(file_path):
    """Cria um backup de um arquivo"""
    if not os.path.exists(file_path):
        log_warning(f"Arquivo não encontrado para backup: {file_path}")
        return None
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{file_path}.bak.{timestamp}"
    try:
        shutil.copy2(file_path, backup_path)
        log_info(f"Backup criado: {backup_path}")
        return backup_path
    except Exception as e:
        log_error(f"Erro ao criar backup de {file_path}: {e}")
        return None

def file_checksum(file_path):
    """Calcula o checksum de um arquivo"""
    if not os.path.exists(file_path):
        return None
        
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        log_error(f"Erro ao calcular checksum de {file_path}: {e}")
        return None

# Migração para IDs baseados em UUID
class UUIDMigration:
    """Classe para migração para IDs baseados em UUID"""
    
    def __init__(self, db_path=None):
        """Inicializa a migração"""
        self.db_path = db_path or os.path.join(BASE_DIR, "lightrag_db.json")
        self.custom_names_path = os.path.join(BASE_DIR, "custom_project_names.json")
        self.uuid_pattern = re.compile(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')
        
    def extract_uuid(self, text):
        """Extrai UUID de qualquer texto"""
        match = self.uuid_pattern.search(text)
        return match.group(1) if match else None
        
    def get_custom_names(self):
        """Carrega nomes personalizados existentes"""
        if os.path.exists(self.custom_names_path):
            try:
                with open(self.custom_names_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log_error(f"Erro ao carregar nomes personalizados: {e}")
        return {}
        
    def save_custom_names(self, names):
        """Salva nomes personalizados"""
        try:
            with open(self.custom_names_path, 'w', encoding='utf-8') as f:
                json.dump(names, f, indent=2)
            return True
        except Exception as e:
            log_error(f"Erro ao salvar nomes personalizados: {e}")
            return False
    
    def get_database(self):
        """Carrega a base de dados"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log_error(f"Erro ao carregar base de dados: {e}")
        return {"documents": [], "lastUpdated": ""}
    
    def save_database(self, db):
        """Salva a base de dados"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=2)
            return True
        except Exception as e:
            log_error(f"Erro ao salvar base de dados: {e}")
            return False
    
    def migrate_ids(self):
        """Migra IDs temporais para UUIDs"""
        log_info("Iniciando migração para UUIDs...")
        
        # Fazer backup do banco e nomes personalizados
        backup_file(self.db_path)
        backup_file(self.custom_names_path)
        
        # Carregar dados
        db = self.get_database()
        custom_names = self.get_custom_names()
        
        # Novos dicionários
        new_custom_names = {}
        
        # Contar documentos processados
        processed = 0
        migrated = 0
        
        for doc in db.get("documents", []):
            processed += 1
            old_id = doc.get("id", "")
            
            # Verificar se o ID já é um UUID ou contém um
            uuid = None
            if self.uuid_pattern.match(old_id):
                uuid = old_id
            else:
                # Tentar extrair UUID do conteúdo ou source
                for field in ["content", "source"]:
                    if field in doc:
                        uuid = self.extract_uuid(doc[field])
                        if uuid:
                            break
            
            # Se encontrou um UUID, atualizar o ID
            if uuid and uuid != old_id:
                # Verificar se o nome personalizado deve ser migrado
                if old_id in custom_names:
                    new_custom_names[uuid] = custom_names[old_id]
                
                # Atualizar ID do documento
                doc["id"] = uuid
                migrated += 1
                
                log_info(f"Documento migrado: {old_id} -> {uuid}")
        
        # Atualizar timestamp
        db["lastUpdated"] = datetime.datetime.now().isoformat()
        
        # Salvar alterações
        if migrated > 0:
            log_info(f"Salvando alterações no banco de dados ({migrated} documentos migrados)...")
            self.save_database(db)
            
            # Atualizar nomes personalizados
            if new_custom_names:
                # Mesclar com nomes existentes
                for uuid, name in new_custom_names.items():
                    custom_names[uuid] = name
                    
                log_info(f"Salvando {len(new_custom_names)} nomes personalizados migrados...")
                self.save_custom_names(custom_names)
            
            log_success(f"Migração concluída. {migrated} de {processed} documentos migrados.")
        else:
            log_info("Nenhum documento precisou ser migrado.")
        
        return migrated

# Remoção de duplicatas
class DuplicateRemoval:
    """Classe para remoção de documentos duplicados"""
    
    def __init__(self, db_path=None):
        """Inicializa a remoção de duplicatas"""
        self.db_path = db_path or os.path.join(BASE_DIR, "lightrag_db.json")
        
    def get_database(self):
        """Carrega a base de dados"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log_error(f"Erro ao carregar base de dados: {e}")
        return {"documents": [], "lastUpdated": ""}
    
    def save_database(self, db):
        """Salva a base de dados"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=2)
            return True
        except Exception as e:
            log_error(f"Erro ao salvar base de dados: {e}")
            return False
    
    def calculate_content_hash(self, doc):
        """Calcula hash do conteúdo de um documento"""
        content = doc.get("content", "")
        if not content:
            return None
            
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def find_duplicates(self):
        """Encontra documentos duplicados"""
        db = self.get_database()
        documents = db.get("documents", [])
        
        # Dicionário para mapear hashes de conteúdo para documentos
        content_hashes = {}
        duplicates = []
        
        for doc in documents:
            content_hash = self.calculate_content_hash(doc)
            if not content_hash:
                continue
                
            if content_hash in content_hashes:
                # Encontrou duplicata
                duplicates.append((doc, content_hashes[content_hash]))
            else:
                content_hashes[content_hash] = doc
        
        return duplicates
    
    def remove_duplicates(self, keep_newer=True):
        """Remove documentos duplicados"""
        log_info("Buscando documentos duplicados...")
        
        # Fazer backup do banco
        backup_file(self.db_path)
        
        # Encontrar duplicatas
        duplicates = self.find_duplicates()
        
        if not duplicates:
            log_info("Nenhum documento duplicado encontrado.")
            return 0
            
        log_info(f"Encontrados {len(duplicates)} documentos duplicados.")
        
        # Carregar o banco completo
        db = self.get_database()
        documents = db.get("documents", [])
        
        # IDs para remover
        ids_to_remove = set()
        
        for dup, orig in duplicates:
            dup_id = dup.get("id", "")
            orig_id = orig.get("id", "")
            
            # Determinar qual documento manter com base na data de criação
            if keep_newer:
                dup_created = dup.get("created", "")
                orig_created = orig.get("created", "")
                
                if dup_created > orig_created:
                    # Duplicata é mais recente, remover original
                    ids_to_remove.add(orig_id)
                    log_info(f"Removendo documento mais antigo: {orig_id} (manterá {dup_id})")
                else:
                    # Original é mais recente ou igual, remover duplicata
                    ids_to_remove.add(dup_id)
                    log_info(f"Removendo duplicata: {dup_id} (manterá {orig_id})")
            else:
                # Sempre manter o original
                ids_to_remove.add(dup_id)
                log_info(f"Removendo duplicata: {dup_id} (manterá {orig_id})")
        
        # Remover documentos
        if ids_to_remove:
            new_docs = [doc for doc in documents if doc.get("id", "") not in ids_to_remove]
            
            # Verificar quantos foram removidos
            removed = len(documents) - len(new_docs)
            
            # Atualizar banco
            db["documents"] = new_docs
            db["lastUpdated"] = datetime.datetime.now().isoformat()
            
            # Salvar alterações
            log_info(f"Salvando alterações (removendo {removed} documentos)...")
            self.save_database(db)
            
            log_success(f"Remoção concluída. {removed} documentos duplicados removidos.")
            return removed
        
        return 0

# Aplicação de patches
class PatchApplier:
    """Classe para aplicação de patches"""
    
    def __init__(self):
        """Inicializa o aplicador de patches"""
        self.patches_applied = []
    
    def apply_patch(self, file_path, search_text, replace_text):
        """Aplica um patch em um arquivo"""
        if not os.path.exists(file_path):
            log_error(f"Arquivo não encontrado: {file_path}")
            return False
            
        # Fazer backup
        backup_file(file_path)
        
        try:
            # Ler conteúdo atual
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificar se o texto a ser substituído existe
            if search_text not in content:
                log_warning(f"Texto não encontrado em {file_path}")
                return False
                
            # Substituir texto
            new_content = content.replace(search_text, replace_text)
            
            # Se não houve alterações, não fazer nada
            if new_content == content:
                log_warning(f"Nenhuma alteração necessária em {file_path}")
                return False
                
            # Salvar novo conteúdo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            log_info(f"Patch aplicado com sucesso em {file_path}")
            self.patches_applied.append(file_path)
            return True
            
        except Exception as e:
            log_error(f"Erro ao aplicar patch em {file_path}: {e}")
            return False
    
    def apply_ui_patches(self):
        """Aplica patches na interface UI"""
        # Patches da interface UI
        ui_patches = [
            {
                "file": os.path.join(BASE_DIR, "ui", "ui.py"),
                "search": "def load_memory_summary(self):\n        \"\"\"\n        Carrega o arquivo de resumo da integração com Memory MCP\n        ",
                "replace": "def load_memory_summary(self):\n        \"\"\"\n        Carrega o arquivo de resumo da integração com Memory e Model Context Protocol (MCP)\n        "
            },
            {
                "file": os.path.join(BASE_DIR, "ui", "lightrag_ui.py"),
                "search": "        st.caption(\"Desenvolvido com Streamlit e Flask | Integração com Memory MCP\")",
                "replace": "        st.caption(\"Desenvolvido com Streamlit e Flask | Integração com Memory e Model Context Protocol (MCP)\")"
            }
        ]
        
        applied = 0
        for patch in ui_patches:
            if self.apply_patch(patch["file"], patch["search"], patch["replace"]):
                applied += 1
                
        log_info(f"Aplicados {applied} de {len(ui_patches)} patches UI")
        return applied
    
    def apply_app_patches(self):
        """Aplica patches no app principal"""
        # Patches do app principal
        app_patches = [
            {
                "file": os.path.join(BASE_DIR, "app.py"),
                "search": "        # Cabeçalho com logo e título\n        st.title(\"🔍 LightRAG - Sistema de RAG\")\n        st.caption(\"Retrieval Augmented Generation\")",
                "replace": "        # Cabeçalho com logo e título\n        st.title(\"🔍 LightRAG - Sistema de RAG\")\n        st.caption(\"Retrieval Augmented Generation integrado com Memory e Model Context Protocol (MCP)\")"
            },
            {
                "file": os.path.join(BASE_DIR, "app.py"),
                "search": "def render_memory_tab(self):\n        \"\"\"Renderiza a aba de integração com Memory MCP\"\"\"",
                "replace": "def render_memory_tab(self):\n        \"\"\"Renderiza a aba de integração com Memory e Model Context Protocol (MCP)\"\"\""
            }
        ]
        
        applied = 0
        for patch in app_patches:
            if self.apply_patch(patch["file"], patch["search"], patch["replace"]):
                applied += 1
                
        log_info(f"Aplicados {applied} de {len(app_patches)} patches App")
        return applied
    
    def apply_database_patches(self):
        """Aplica patches no módulo de banco de dados"""
        # Patches do módulo de banco de dados
        db_patches = [
            {
                "file": os.path.join(BASE_DIR, "core", "database.py"),
                "search": "    def insert_document(self, content, summary=None, source=None, metadata=None):",
                "replace": "    def insert_document(self, content, summary=None, source=None, metadata=None, custom_id=None):"
            },
            {
                "file": os.path.join(BASE_DIR, "core", "database.py"),
                "search": "        # Gerar ID do documento\n        doc_id = f\"doc_{int(time.time())}\"",
                "replace": "        # Gerar ID do documento\n        if custom_id:\n            doc_id = custom_id\n        else:\n            doc_id = f\"doc_{int(time.time())}\""
            }
        ]
        
        applied = 0
        for patch in db_patches:
            if self.apply_patch(patch["file"], patch["search"], patch["replace"]):
                applied += 1
                
        log_info(f"Aplicados {applied} de {len(db_patches)} patches Database")
        return applied
    
    def apply_all_patches(self):
        """Aplica todos os patches"""
        log_info("Aplicando todos os patches...")
        
        total = 0
        total += self.apply_ui_patches()
        total += self.apply_app_patches()
        total += self.apply_database_patches()
        
        if total > 0:
            log_success(f"Total de {total} patches aplicados com sucesso.")
        else:
            log_info("Nenhum patch aplicado. Sistema já está atualizado.")
            
        return total

# Função principal
def main():
    """Função principal do script"""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description="Ferramentas de migração e manutenção do LightRAG")
    
    # Comandos
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")
    
    # Comando de migração para UUID
    parser_uuid = subparsers.add_parser("migrate-uuid", help="Migrar para IDs baseados em UUID")
    
    # Comando de remoção de duplicatas
    parser_dedup = subparsers.add_parser("remove-duplicates", help="Remover documentos duplicados")
    parser_dedup.add_argument("--keep-newer", action="store_true", help="Manter documentos mais recentes em caso de duplicatas")
    
    # Comando de aplicação de patches
    parser_patch = subparsers.add_parser("apply-patches", help="Aplicar patches")
    parser_patch.add_argument("--type", choices=["all", "ui", "app", "database"], default="all", help="Tipo de patches a aplicar")
    
    # Comando para executar todas as operações
    parser_all = subparsers.add_parser("all", help="Executar todas as operações (migração, remoção de duplicatas e patches)")
    
    # Comando de backup
    parser_backup = subparsers.add_parser("backup", help="Criar backup da base de dados")
    
    # Processar argumentos
    args = parser.parse_args()
    
    # Executar comando
    if args.command == "migrate-uuid":
        migration = UUIDMigration()
        migration.migrate_ids()
        
    elif args.command == "remove-duplicates":
        dedup = DuplicateRemoval()
        dedup.remove_duplicates(keep_newer=args.keep_newer)
        
    elif args.command == "apply-patches":
        patcher = PatchApplier()
        
        if args.type == "all":
            patcher.apply_all_patches()
        elif args.type == "ui":
            patcher.apply_ui_patches()
        elif args.type == "app":
            patcher.apply_app_patches()
        elif args.type == "database":
            patcher.apply_database_patches()
            
    elif args.command == "all":
        # Executar tudo em sequência
        # 1. Migração para UUID
        migration = UUIDMigration()
        migration.migrate_ids()
        
        # 2. Remover duplicatas
        dedup = DuplicateRemoval()
        dedup.remove_duplicates(keep_newer=True)
        
        # 3. Aplicar patches
        patcher = PatchApplier()
        patcher.apply_all_patches()
        
        log_success("Todas as operações de manutenção concluídas com sucesso!")
        
    elif args.command == "backup":
        # Criar backup da base de dados
        db_path = os.path.join(BASE_DIR, "lightrag_db.json")
        backup_path = backup_file(db_path)
        
        if backup_path:
            log_success(f"Backup criado com sucesso: {backup_path}")
        else:
            log_error("Falha ao criar backup da base de dados")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    # Criar diretório tools se não existir
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Executar função principal
    main()