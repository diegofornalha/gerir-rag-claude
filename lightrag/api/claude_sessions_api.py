#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Claude Sessions API
API focada na integração entre conversas e todos do Claude
"""

from flask import Flask, request, jsonify
import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Diretórios base
CLAUDE_BASE = "/Users/agents/.claude"
PROJECTS_DIR = os.path.join(CLAUDE_BASE, "projects")
TODOS_DIR = os.path.join(CLAUDE_BASE, "todos")

# Criar aplicação Flask
app = Flask(__name__)

class SessionManager:
    """Gerencia sessões Claude (conversas + todos)"""
    
    @staticmethod
    def get_all_sessions() -> List[Dict]:
        """Retorna todas as sessões com seus todos associados"""
        sessions = []
        
        # Buscar todos os arquivos de todos
        todo_files = glob.glob(os.path.join(TODOS_DIR, "*.json"))
        
        for todo_file in todo_files:
            session_id = os.path.basename(todo_file).replace('.json', '')
            
            # Buscar conversa correspondente
            conversation_files = glob.glob(os.path.join(PROJECTS_DIR, "*", f"{session_id}.jsonl"))
            
            session_info = {
                "sessionId": session_id,
                "todos": todo_file,
                "conversation": conversation_files[0] if conversation_files else None,
                "hasConversation": len(conversation_files) > 0,
                "lastModified": datetime.fromtimestamp(os.path.getmtime(todo_file)).isoformat()
            }
            
            # Adicionar contagem de todos
            try:
                with open(todo_file, 'r') as f:
                    todos = json.load(f)
                    session_info["todoCount"] = len(todos)
                    session_info["pendingCount"] = sum(1 for t in todos if t.get("status") == "pending")
                    session_info["completedCount"] = sum(1 for t in todos if t.get("status") == "completed")
            except:
                session_info["todoCount"] = 0
                session_info["pendingCount"] = 0
                session_info["completedCount"] = 0
            
            sessions.append(session_info)
        
        return sorted(sessions, key=lambda x: x["lastModified"], reverse=True)
    
    @staticmethod
    def get_session_details(session_id: str) -> Optional[Dict]:
        """Retorna detalhes completos de uma sessão"""
        todo_file = os.path.join(TODOS_DIR, f"{session_id}.json")
        
        if not os.path.exists(todo_file):
            return None
        
        # Buscar conversa
        conversation_files = glob.glob(os.path.join(PROJECTS_DIR, "*", f"{session_id}.jsonl"))
        
        result = {
            "sessionId": session_id,
            "todos": [],
            "conversation": [],
            "metadata": {}
        }
        
        # Ler todos
        try:
            with open(todo_file, 'r') as f:
                result["todos"] = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao ler todos: {e}")
        
        # Ler conversa (primeiras e últimas mensagens)
        if conversation_files:
            try:
                with open(conversation_files[0], 'r') as f:
                    lines = f.readlines()
                    
                # Pegar primeira mensagem com summary
                for line in lines[:10]:
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "summary":
                            result["metadata"]["summary"] = entry.get("summary", "")
                            break
                    except:
                        continue
                
                # Pegar algumas mensagens para contexto
                for i, line in enumerate(lines[:20]):
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "user" and entry.get("message"):
                            result["conversation"].append({
                                "index": i,
                                "type": "user",
                                "content": entry["message"].get("content", "")[:200] + "...",
                                "timestamp": entry.get("timestamp")
                            })
                    except:
                        continue
                        
            except Exception as e:
                logger.error(f"Erro ao ler conversa: {e}")
        
        return result

# Endpoints da API

@app.route('/api/claude-sessions', methods=['GET'])
def get_sessions():
    """Lista todas as sessões"""
    try:
        sessions = SessionManager.get_all_sessions()
        return jsonify({
            "success": True,
            "count": len(sessions),
            "sessions": sessions
        })
    except Exception as e:
        logger.error(f"Erro ao listar sessões: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/claude-sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Retorna detalhes de uma sessão"""
    try:
        session = SessionManager.get_session_details(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": "Sessão não encontrada"
            }), 404
        
        return jsonify({
            "success": True,
            "session": session
        })
    except Exception as e:
        logger.error(f"Erro ao buscar sessão: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/claude-sessions/<session_id>/todos', methods=['GET'])
def get_session_todos(session_id):
    """Retorna apenas os todos de uma sessão"""
    try:
        todo_file = os.path.join(TODOS_DIR, f"{session_id}.json")
        if not os.path.exists(todo_file):
            return jsonify({
                "success": False,
                "error": "Todos não encontrados"
            }), 404
        
        with open(todo_file, 'r') as f:
            todos = json.load(f)
        
        return jsonify({
            "success": True,
            "sessionId": session_id,
            "todos": todos,
            "stats": {
                "total": len(todos),
                "pending": sum(1 for t in todos if t.get("status") == "pending"),
                "inProgress": sum(1 for t in todos if t.get("status") == "in_progress"),
                "completed": sum(1 for t in todos if t.get("status") == "completed")
            }
        })
    except Exception as e:
        logger.error(f"Erro ao buscar todos: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/claude-sessions/active', methods=['GET'])
def get_active_sessions():
    """Retorna apenas sessões com todos não completados"""
    try:
        all_sessions = SessionManager.get_all_sessions()
        active_sessions = [s for s in all_sessions if s.get("pendingCount", 0) > 0]
        
        return jsonify({
            "success": True,
            "count": len(active_sessions),
            "sessions": active_sessions
        })
    except Exception as e:
        logger.error(f"Erro ao buscar sessões ativas: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# WebSocket será implementado posteriormente com Socket.IO

# CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

if __name__ == '__main__':
    logger.info("Iniciando Claude Sessions API na porta 5555")
    app.run(host='0.0.0.0', port=5555, debug=True)