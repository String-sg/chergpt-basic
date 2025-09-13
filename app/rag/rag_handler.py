"""
RAG (Retrieval Augmented Generation) Handler
Handles similarity search and context retrieval from embedded PDF chunks
"""

import logging
from typing import List, Tuple, Optional
import tiktoken
from openai import OpenAI
import streamlit as st
from app.db.database_connection import connect_to_db, get_ingested_files, delete_ingested_file, get_selected_file_ids, get_user_file_selections, update_user_file_selection

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
    
    def similarity_search(self, query_embedding: List[float], limit: int = 5, user_name: str = None) -> List[Tuple[str, float]]:
        """
        Perform similarity search using cosine similarity
        Returns list of (content, similarity_score) tuples
        Filters by user's selected files if user_name is provided
        """
        conn = connect_to_db()
        if conn is None:
            logger.error("Failed to connect to database for similarity search")
            return []

        try:
            with conn.cursor() as cur:
                if user_name:
                    # Get selected file IDs for this user
                    selected_file_ids = get_selected_file_ids(user_name)

                    if not selected_file_ids:
                        logger.info(f"No files selected for user {user_name}")
                        return []

                    # Use pgvector's cosine similarity operator with file filtering
                    placeholders = ','.join(['%s'] * len(selected_file_ids))
                    query = f"""
                        SELECT content, (1 - (embedding <=> %s::vector)) as similarity
                        FROM rag_chunks
                        WHERE file_id IN ({placeholders})
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """
                    params = [query_embedding] + selected_file_ids + [query_embedding, limit]
                    cur.execute(query, params)
                else:
                    # Original query without filtering
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
                        similarity_threshold: float = 0.7, user_name: str = None) -> Optional[str]:
        """
        Main retrieval function - get relevant context for a query
        """
        try:
            # Get query embedding
            query_embedding = self.get_query_embedding(query)

            # Perform similarity search with user filtering
            relevant_chunks = self.similarity_search(query_embedding, limit=top_k, user_name=user_name)

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

    def get_ingested_files_list(self) -> List[dict]:
        """Get list of all ingested files for admin interface"""
        return get_ingested_files()

    def remove_ingested_file(self, file_id: int) -> bool:
        """Remove an ingested file record"""
        return delete_ingested_file(file_id)

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def get_user_file_selections(self, user_name: str) -> List[dict]:
        """Get user's file selections for UI"""
        return get_user_file_selections(user_name)

    def update_user_file_selection(self, user_name: str, file_id: int, is_selected: bool) -> bool:
        """Update user's file selection"""
        return update_user_file_selection(user_name, file_id, is_selected)

    def process_uploaded_files(self, uploaded_files: list) -> dict:
        """
        Process uploaded files securely from Streamlit file uploader
        Returns processing results with security measures
        """
        from process_pdf import PDFEmbeddingProcessor

        results = {
            'total_files': len(uploaded_files),
            'successful_files': 0,
            'failed_files': 0,
            'total_chunks': 0,
            'errors': [],
            'warnings': [],
            'details': []
        }

        processor = PDFEmbeddingProcessor()

        for uploaded_file in uploaded_files:
            file_result = {
                'filename': uploaded_file.name,
                'status': 'processing',
                'chunks': 0,
                'error': None,
                'warnings': []
            }

            try:
                # Read file content from Streamlit's UploadedFile object
                file_content = uploaded_file.read()

                # Security validation first
                validation = processor.validate_uploaded_file(file_content, uploaded_file.name)

                if not validation['valid']:
                    file_result['status'] = 'failed'
                    file_result['error'] = validation['error']
                    results['errors'].append(f"{uploaded_file.name}: {validation['error']}")
                    results['failed_files'] += 1
                else:
                    # Add warnings
                    file_result['warnings'] = validation['warnings']
                    results['warnings'].extend([f"{uploaded_file.name}: {w}" for w in validation['warnings']])

                    # Process the file
                    successful_chunks, failed_chunks = processor.process_uploaded_file(file_content, uploaded_file.name)

                    file_result['chunks'] = successful_chunks
                    file_result['status'] = 'completed' if failed_chunks == 0 else 'partial'

                    if failed_chunks > 0:
                        file_result['error'] = f"{failed_chunks} chunks failed to process"

                    results['successful_files'] += 1
                    results['total_chunks'] += successful_chunks

            except Exception as e:
                file_result['status'] = 'failed'
                file_result['error'] = str(e)
                results['errors'].append(f"{uploaded_file.name}: {str(e)}")
                results['failed_files'] += 1

            finally:
                # Security cleanup - ensure file content is cleared
                file_content = None
                uploaded_file.seek(0)  # Reset file pointer for Streamlit

            results['details'].append(file_result)

        return results


# Global RAG handler instance
rag_handler = RAGHandler()