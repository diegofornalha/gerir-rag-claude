#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Módulo de Banco de Dados
Implementa o acesso e gerenciamento da base de conhecimento
"""

import json
import os
import datetime
import hashlib
from typing import Dict, List, Any, Optional, Union

# Importar configurações centralizadas
from core.settings import DB_FILE

class LightRAGDatabase:
    """
    Gerenciador da base de conhecimento do LightRAG
    
    Esta classe implementa o padrão Singleton para garantir que apenas uma
    instância do banco de dados seja criada durante a execução da aplicação.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LightRAGDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa o banco de dados carregando-o do arquivo"""
        if self._initialized:
            return
            
        self.db_file = DB_FILE
        self.knowledge_base = {
            "documents": [],
            "lastUpdated": datetime.datetime.now().isoformat()
        }
        
        # Carregar base de conhecimento
        self.load()
        
        self._initialized = True
    
    def load(self) -> bool:
        """
        Carrega a base de conhecimento do arquivo
        
        Retorna:
            bool: True se carregado com sucesso, False caso contrário
        """
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
                print(f"Base de conhecimento carregada com {len(self.knowledge_base['documents'])} documentos")
                return True
            except Exception as e:
                print(f"Erro ao carregar base de conhecimento: {str(e)}")
        return False
    
    def save(self) -> bool:
        """
        Salva a base de conhecimento no arquivo
        
        Retorna:
            bool: True se salvo com sucesso, False caso contrário
        """
        try:
            # Atualizar timestamp
            self.knowledge_base["lastUpdated"] = datetime.datetime.now().isoformat()
            
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar base de conhecimento: {str(e)}")
            return False
    
    def create_backup(self) -> Optional[str]:
        """
        Cria um backup da base de conhecimento
        
        Retorna:
            Optional[str]: Caminho do arquivo de backup ou None se falhar
        """
        try:
            backup_file = f"{self.db_file}.bak.{int(datetime.datetime.now().timestamp())}"
            with open(self.db_file, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            return backup_file
        except Exception as e:
            print(f"Erro ao criar backup: {str(e)}")
            return None
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """
        Busca um documento pelo ID
        
        Args:
            doc_id: ID do documento
            
        Retorna:
            Optional[Dict]: Documento encontrado ou None
        """
        for doc in self.knowledge_base["documents"]:
            if doc.get("id") == doc_id:
                return doc
        return None
    
    def get_document_by_hash(self, content_hash: str) -> Optional[Dict]:
        """
        Busca um documento pelo hash do conteúdo
        
        Args:
            content_hash: Hash SHA-256 do conteúdo
            
        Retorna:
            Optional[Dict]: Documento encontrado ou None
        """
        for doc in self.knowledge_base["documents"]:
            # Verificar nos metadados
            metadata = doc.get("metadata", {})
            if metadata.get("content_hash") == content_hash:
                return doc
                
            # Se não existir nos metadados, calcular na hora
            if "content" in doc:
                doc_hash = hashlib.sha256(doc["content"].encode('utf-8')).hexdigest()
                if doc_hash == content_hash:
                    return doc
                    
        return None
    
    def insert_document(self, content: str, source: str = "manual", 
                        summary: Optional[str] = None, 
                        metadata: Optional[Dict] = None) -> Dict:
        """
        Insere um novo documento na base de conhecimento
        
        Args:
            content: Conteúdo do documento
            source: Fonte do documento
            summary: Resumo do documento
            metadata: Metadados adicionais (opcional)
            
        Retorna:
            Dict: Resultado da operação com ID do documento
        """
        if not content:
            return {"success": False, "error": "Conteúdo vazio"}
        
        # Gerar ID único baseado no timestamp
        doc_id = f"doc_{int(datetime.datetime.now().timestamp() * 1000)}"
        
        # Preparar o documento com metadados
        document = {
            "id": doc_id,
            "content": content,
            "source": source,
            "summary": summary or "Documento sem resumo",
            "created": datetime.datetime.now().isoformat()
        }
        
        # Adicionar metadados se fornecidos
        if metadata:
            document["metadata"] = metadata
        else:
            # Calcular hash do conteúdo como metadado padrão
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            document["metadata"] = {"content_hash": content_hash}
        
        # Adicionar à base de conhecimento
        self.knowledge_base["documents"].append(document)
        
        # Salvar alterações
        if self.save():
            return {
                "success": True,
                "message": "Documento inserido com sucesso",
                "documentId": doc_id
            }
        else:
            return {
                "success": False,
                "error": "Erro ao salvar documento"
            }
    
    def delete_document(self, doc_id: str) -> Dict:
        """
        Remove um documento da base de conhecimento
        
        Args:
            doc_id: ID do documento a ser removido
            
        Retorna:
            Dict: Resultado da operação
        """
        if not doc_id:
            return {"success": False, "error": "ID não fornecido"}
        
        # Verificar se o documento existe
        original_count = len(self.knowledge_base["documents"])
        documents_filtered = [doc for doc in self.knowledge_base["documents"] if doc.get("id") != doc_id]
        
        if len(documents_filtered) == original_count:
            return {
                "success": False,
                "error": f"Documento com ID '{doc_id}' não encontrado"
            }
        
        # Atualizar base de conhecimento
        self.knowledge_base["documents"] = documents_filtered
        
        # Salvar alterações
        if self.save():
            return {
                "success": True,
                "message": f"Documento '{doc_id}' removido com sucesso"
            }
        else:
            return {
                "success": False,
                "error": "Erro ao salvar alterações"
            }
    
    def clear_database(self, create_backup: bool = True) -> Dict:
        """
        Limpa todos os documentos da base de conhecimento
        
        Args:
            create_backup: Se True, cria um backup antes de limpar
            
        Retorna:
            Dict: Resultado da operação
        """
        # Criar backup se solicitado
        backup_file = None
        if create_backup:
            backup_file = self.create_backup()
            if not backup_file:
                return {
                    "success": False,
                    "error": "Falha ao criar backup antes de limpar"
                }
        
        # Contar documentos antes de limpar
        doc_count = len(self.knowledge_base["documents"])
        
        # Limpar base
        self.knowledge_base["documents"] = []
        
        # Salvar alterações
        if self.save():
            result = {
                "success": True,
                "message": f"Base de conhecimento limpa. {doc_count} documentos removidos."
            }
            
            if backup_file:
                result["backup"] = backup_file
                
            return result
        else:
            return {
                "success": False,
                "error": "Erro ao salvar base vazia"
            }
    
    def get_all_documents(self) -> List[Dict]:
        """
        Retorna todos os documentos na base de conhecimento
        
        Retorna:
            List[Dict]: Lista de documentos
        """
        return self.knowledge_base.get("documents", [])
    
    def get_status(self) -> Dict:
        """
        Retorna informações sobre o estado atual da base de conhecimento
        
        Retorna:
            Dict: Status da base de conhecimento
        """
        return {
            "status": "online",
            "documents": len(self.knowledge_base.get("documents", [])),
            "lastUpdated": self.knowledge_base.get("lastUpdated")
        }