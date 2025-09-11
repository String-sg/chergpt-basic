"""
RAG (Retrieval Augmented Generation) Handler
Handles similarity search and context retrieval from embedded PDF chunks
"""

import logging
from typing import List, Tuple, Optional
import tiktoken
from openai import OpenAI
import streamlit as st
from app.db.database_connection import connect_to_db

logger = logging.getLogger(__name__)

class RAGHandler:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.embedding_model = "text-embedding-ada-002"
        self.max_context_tokens = 4000  # Reserve tokens for context
        
    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for user query"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=query
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to get query embedding: {e}")
            raise
    
    def similarity_search(self, query_embedding: List[float], limit: int = 5) -> List[Tuple[str, float]]:
        """
        Perform similarity search using cosine similarity
        Returns list of (content, similarity_score) tuples
        """
        conn = connect_to_db()
        if conn is None:
            logger.error("Failed to connect to database for similarity search")
            return []
        
        try:
            with conn.cursor() as cur:
                # Use pgvector's cosine similarity operator
                cur.execute("""
                    SELECT content, (1 - (embedding <=> %s::vector)) as similarity
                    FROM rag_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
                
                results = cur.fetchall()
                return [(content, float(similarity)) for content, similarity in results]
                
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
        finally:
            conn.close()
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def build_context(self, relevant_chunks: List[Tuple[str, float]], 
                     similarity_threshold: float = 0.7) -> str:
        """
        Build context from relevant chunks, respecting token limits
        """
        context_parts = []
        total_tokens = 0
        
        # Add header
        header = "# Relevant Context from Economics Materials:\n\n"
        header_tokens = self.count_tokens(header)
        
        if header_tokens > self.max_context_tokens:
            return ""
        
        total_tokens += header_tokens
        context_parts.append(header)
        
        # Add chunks within token limit and above similarity threshold
        for i, (chunk, similarity) in enumerate(relevant_chunks):
            if similarity < similarity_threshold:
                logger.debug(f"Skipping chunk {i} with low similarity: {similarity:.3f}")
                continue
                
            chunk_text = f"**Source {i+1}** (relevance: {similarity:.1%}):\n{chunk}\n\n"
            chunk_tokens = self.count_tokens(chunk_text)
            
            if total_tokens + chunk_tokens > self.max_context_tokens:
                logger.info(f"Token limit reached. Added {i} chunks to context.")
                break
                
            context_parts.append(chunk_text)
            total_tokens += chunk_tokens
            
        if len(context_parts) == 1:  # Only header added
            return ""
            
        context = "".join(context_parts)
        context += "---\n\nPlease answer the question using the above context when relevant. If the context doesn't contain relevant information, you may use your general knowledge but indicate this clearly.\n\n"
        
        logger.info(f"Built context with {len(context_parts)-1} chunks, {total_tokens} tokens")
        return context
    
    def retrieve_context(self, query: str, top_k: int = 5, 
                        similarity_threshold: float = 0.7) -> Optional[str]:
        """
        Main retrieval function - get relevant context for a query
        """
        try:
            # Get query embedding
            query_embedding = self.get_query_embedding(query)
            
            # Perform similarity search
            relevant_chunks = self.similarity_search(query_embedding, limit=top_k)
            
            if not relevant_chunks:
                logger.info("No relevant chunks found")
                return None
                
            # Log similarity scores
            logger.info(f"Found {len(relevant_chunks)} chunks with similarities: " + 
                       ", ".join([f"{sim:.3f}" for _, sim in relevant_chunks]))
            
            # Build context
            context = self.build_context(relevant_chunks, similarity_threshold)
            
            return context if context.strip() else None
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return None
    
    def is_economics_related(self, query: str) -> bool:
        """
        Simple heuristic to determine if query is economics-related
        You can make this more sophisticated later
        """
        economics_keywords = [
            'market', 'supply', 'demand', 'price', 'cost', 'revenue', 'profit',
            'competition', 'monopoly', 'oligopoly', 'consumer', 'producer',
            'economics', 'economic', 'economy', 'gdp', 'inflation', 'government',
            'intervention', 'regulation', 'externality', 'externalities', 'public goods',
            'market failure', 'efficiency', 'equity', 'welfare', 'subsidy',
            'tax', 'taxation', 'elasticity', 'surplus', 'deadweight loss',
            'fiscal', 'monetary', 'policy', 'trade', 'international'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in economics_keywords)
    
    def get_rag_stats(self) -> dict:
        """Get statistics about the RAG database"""
        conn = connect_to_db()
        if conn is None:
            return {"error": "Cannot connect to database"}
        
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM rag_chunks")
                chunk_count = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT AVG(LENGTH(content)), MIN(LENGTH(content)), MAX(LENGTH(content))
                    FROM rag_chunks
                """)
                avg_len, min_len, max_len = cur.fetchone()
                
                return {
                    "total_chunks": chunk_count,
                    "avg_chunk_length": int(avg_len) if avg_len else 0,
                    "min_chunk_length": min_len or 0,
                    "max_chunk_length": max_len or 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get RAG stats: {e}")
            return {"error": str(e)}
        finally:
            conn.close()


# Global RAG handler instance
rag_handler = RAGHandler()