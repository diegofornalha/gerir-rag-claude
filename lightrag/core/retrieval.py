#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LightRAG - Módulo de Recuperação
Este módulo implementa os algoritmos de busca e relevância
"""

import re
from typing import Dict, List, Any, Optional, Union

class RetrievalEngine:
    """
    Motor de recuperação e cálculo de relevância do LightRAG
    
    Esta classe implementa os algoritmos de busca e relevância para recuperar
    documentos da base de conhecimento com base em consultas.
    """
    
    @staticmethod
    def calculate_relevance_basic(query: str, content: str) -> float:
        """
        Calcula a relevância básica entre uma consulta e um conteúdo (algoritmo original)
        
        Esta é a implementação original do algoritmo de relevância, mantida
        para compatibilidade e comparação.
        
        Args:
            query: Texto da consulta
            content: Conteúdo do documento
            
        Retorna:
            float: Relevância entre 0.0 e 1.0
        """
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Verificar correspondência exata
        if query_lower in content_lower:
            return 0.9  # Alta relevância para correspondência exata
        
        # Verificar palavras individuais
        query_words = set(re.findall(r'\w+', query_lower))
        content_words = set(re.findall(r'\w+', content_lower))
        
        if not query_words:
            return 0
        
        # Calcular interseção de palavras
        common_words = query_words.intersection(content_words)
        if not common_words:
            return 0
        
        # Calcular relevância pela proporção de palavras correspondentes
        return len(common_words) / len(query_words) * 0.8
    
    @staticmethod
    def calculate_relevance_improved(query: str, content: str) -> float:
        """
        Calcula relevância melhorada entre uma consulta e um conteúdo
        
        Esta implementação melhora o algoritmo original de várias maneiras:
        1. Considera a posição das palavras no documento (proximidade)
        2. Dá peso extra para frases completas que correspondem
        3. Considera a frequência das palavras-chave
        4. Normaliza melhor os resultados
        
        Args:
            query: Texto da consulta
            content: Conteúdo do documento
            
        Retorna:
            float: Relevância entre 0.0 e 1.0
        """
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 1. Verificar correspondência exata de frases (peso alto)
        if query_lower in content_lower:
            # Quanto mais curto o documento, mais significativa é a correspondência
            doc_length_factor = min(1.0, 1000 / max(len(content_lower), 1))
            return 0.9 + (doc_length_factor * 0.1)  # Entre 0.9 e 1.0
        
        # 2. Extrair palavras normalizadas
        query_words = set(re.findall(r'\w+', query_lower))
        if not query_words:
            return 0
        
        content_words = re.findall(r'\w+', content_lower)
        content_words_set = set(content_words)
        
        # 3. Calcular interseção
        common_words = query_words.intersection(content_words_set)
        if not common_words:
            return 0
        
        # 4. Calcular score base a partir da proporção de palavras correspondentes
        base_score = len(common_words) / len(query_words) * 0.7
        
        # 5. Analisar frequência das palavras-chave (palavras importantes aparecem mais)
        word_freq_bonus = 0
        for word in common_words:
            frequency = content_words.count(word) / max(len(content_words), 1)
            # Limitar bônus por palavra para evitar textos que apenas repetem termos
            word_freq_bonus += min(frequency, 0.1)
        
        # Normalizar bônus de frequência para um máximo de 0.15
        freq_factor = min(0.15, word_freq_bonus / max(len(common_words), 1))
        
        # 6. Analisar frases compostas da consulta
        query_bigrams = set()
        query_words_list = list(query_words)
        for i in range(len(query_words_list) - 1):
            bigram = f"{query_words_list[i]} {query_words_list[i+1]}"
            if bigram.lower() in content_lower:
                query_bigrams.add(bigram)
        
        # Bônus para n-gramas encontrados (peso maior para frases completas)
        ngram_factor = min(0.15, len(query_bigrams) * 0.05)
        
        # Combinar fatores para pontuação final
        final_score = base_score + freq_factor + ngram_factor
        
        # Garantir que o resultado esteja no intervalo [0, 1]
        return min(1.0, final_score)
    
    @staticmethod
    def rank_documents(query: str, documents: List[Dict], 
                        max_results: int = 5, 
                        mode: str = "hybrid") -> List[Dict]:
        """
        Classifica documentos por relevância para uma consulta
        
        Args:
            query: Texto da consulta
            documents: Lista de documentos para classificar
            max_results: Número máximo de resultados a retornar
            mode: Modo de busca (hybrid, semantic, keyword)
            
        Retorna:
            List[Dict]: Documentos relevantes com score de relevância
        """
        if not query or not documents:
            return []
        
        # Definir função de cálculo de relevância conforme o modo
        if mode == "keyword":
            relevance_func = RetrievalEngine.calculate_relevance_basic
        else:
            # Para "semantic" e "hybrid", usamos o algoritmo melhorado
            relevance_func = RetrievalEngine.calculate_relevance_improved
        
        # Calcular relevância para cada documento
        docs_with_relevance = [
            {"doc": doc, "relevance": relevance_func(query, doc["content"])}
            for doc in documents
        ]
        
        # Filtrar documentos com alguma relevância
        relevant_docs = [
            item for item in docs_with_relevance 
            if item["relevance"] > 0
        ]
        
        # Ordenar por relevância (mais relevante primeiro)
        relevant_docs.sort(key=lambda x: x["relevance"], reverse=True)
        
        # Limitar número de resultados
        return relevant_docs[:max_results]
    
    @staticmethod
    def format_results(query: str, ranked_docs: List[Dict]) -> Dict:
        """
        Formata os resultados da busca no formato da resposta
        
        Args:
            query: Texto da consulta original
            ranked_docs: Lista de documentos classificados
            
        Retorna:
            Dict: Resposta formatada com contextos
        """
        response = {
            "response": f'Resposta para: "{query}"',
            "context": []
        }
        
        # Se encontramos documentos relevantes
        if ranked_docs:
            # Extrair e formatar contextos
            response["context"] = [
                {
                    "content": doc["doc"]["content"],
                    "source": doc["doc"].get("source", "desconhecido"),
                    "document_id": doc["doc"].get("id", "doc_desconhecido"),
                    "relevance": doc["relevance"]
                } for doc in ranked_docs
            ]
            
            # Mensagem mais informativa
            response["response"] = f'Com base no conhecimento disponível, aqui está a resposta para: "{query}"'
        
        return response