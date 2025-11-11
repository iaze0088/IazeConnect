"""
Sistema de RAG (Retrieval Augmented Generation) para Instruções Grandes
Divide o arquivo em chunks e busca apenas partes relevantes
"""
import os
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class InstructionsRAG:
    """
    Sistema de busca inteligente para instruções grandes
    """
    
    def __init__(self):
        self.chunks_cache = {}
    
    def split_into_chunks(self, text: str, chunk_size: int = 2000) -> List[Dict]:
        """
        Divide texto em chunks menores com overlap
        """
        chunks = []
        
        # Dividir por seções (usando separadores)
        sections = re.split(r'═{3,}|─{3,}|\n\n\n+', text)
        
        current_chunk = ""
        chunk_id = 0
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Se seção é pequena, adiciona ao chunk atual
            if len(current_chunk) + len(section) < chunk_size:
                current_chunk += "\n\n" + section
            else:
                # Salvar chunk atual
                if current_chunk:
                    chunks.append({
                        "id": chunk_id,
                        "content": current_chunk.strip(),
                        "keywords": self._extract_keywords(current_chunk)
                    })
                    chunk_id += 1
                
                # Iniciar novo chunk
                current_chunk = section
        
        # Adicionar último chunk
        if current_chunk:
            chunks.append({
                "id": chunk_id,
                "content": current_chunk.strip(),
                "keywords": self._extract_keywords(current_chunk)
            })
        
        logger.info(f"✅ Arquivo dividido em {len(chunks)} chunks")
        return chunks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrai palavras-chave importantes do texto
        """
        # Palavras comuns em instruções de IPTV
        keywords = []
        
        text_lower = text.lower()
        
        # Aparelhos
        if any(word in text_lower for word in ['tv box', 'tvbox', 'box']):
            keywords.append('tv_box')
        if any(word in text_lower for word in ['smart tv', 'smarttv', 'smart']):
            keywords.append('smart_tv')
        if any(word in text_lower for word in ['fire stick', 'firestick', 'fire']):
            keywords.append('fire_stick')
        if 'celular' in text_lower or 'mobile' in text_lower or 'android' in text_lower:
            keywords.append('celular')
        
        # Ações
        if any(word in text_lower for word in ['teste', 'test', 'gratis', 'gratuito']):
            keywords.append('teste_gratis')
        if 'instala' in text_lower or 'baixar' in text_lower or 'download' in text_lower:
            keywords.append('instalacao')
        if 'usuário' in text_lower or 'usuario' in text_lower or 'senha' in text_lower:
            keywords.append('login')
        if 'erro' in text_lower or 'problema' in text_lower or 'não funciona' in text_lower:
            keywords.append('suporte')
        
        # Apps
        if 'assist plus' in text_lower or 'assistplus' in text_lower:
            keywords.append('assist_plus')
        if 'lazer play' in text_lower or 'lazerplay' in text_lower:
            keywords.append('lazer_play')
        if 'hades' in text_lower:
            keywords.append('hades_play')
        
        return keywords
    
    def search_relevant_chunks(self, chunks: List[Dict], query: str, max_chunks: int = 1) -> List[Dict]:
        """
        Busca chunks mais relevantes para a query
        """
        query_lower = query.lower()
        scored_chunks = []
        
        for chunk in chunks:
            score = 0
            
            # Pontuação por palavras-chave
            for keyword in chunk['keywords']:
                keyword_text = keyword.replace('_', ' ')
                if keyword_text in query_lower:
                    score += 10
            
            # Pontuação por palavras da query presentes no chunk
            query_words = query_lower.split()
            content_lower = chunk['content'].lower()
            
            for word in query_words:
                if len(word) > 3:  # Ignorar palavras muito curtas
                    if word in content_lower:
                        score += 1
            
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Ordenar por score e pegar os top N
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for score, chunk in scored_chunks[:max_chunks]]
        
        logger.info(f"🔍 Busca: '{query[:50]}...' → {len(top_chunks)} chunks relevantes")
        
        return top_chunks
    
    def load_and_prepare(self, filepath: str) -> bool:
        """
        Carrega arquivo e prepara chunks
        """
        try:
            if filepath in self.chunks_cache:
                logger.info(f"📦 Usando chunks em cache: {filepath}")
                return True
            
            if not os.path.exists(filepath):
                logger.error(f"❌ Arquivo não encontrado: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = self.split_into_chunks(content)
            self.chunks_cache[filepath] = chunks
            
            logger.info(f"✅ Arquivo preparado: {len(chunks)} chunks | {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao preparar arquivo: {e}")
            return False
    
    def get_relevant_instructions(self, filepath: str, user_message: str) -> str:
        """
        Retorna apenas as instruções relevantes para a mensagem do usuário
        """
        try:
            # Preparar chunks se necessário
            if filepath not in self.chunks_cache:
                if not self.load_and_prepare(filepath):
                    return ""
            
            chunks = self.chunks_cache[filepath]
            relevant_chunks = self.search_relevant_chunks(chunks, user_message, max_chunks=3)
            
            if not relevant_chunks:
                # Se não achou nada específico, retorna chunk inicial (geralmente tem contexto geral)
                relevant_chunks = chunks[:2]
                logger.warning("⚠️ Nenhum chunk específico encontrado, usando chunks iniciais")
            
            # Combinar chunks relevantes
            combined = "\n\n═══════════════════════════════════════════\n\n".join(
                chunk['content'] for chunk in relevant_chunks
            )
            
            return combined
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar instruções relevantes: {e}")
            return ""

# Instância global
instructions_rag = InstructionsRAG()
