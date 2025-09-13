#!/usr/bin/env python3
"""
PDF Processing and Embedding Script
Processes the Economics PDF and stores embeddings in NeonDB with pgvector
"""

import os
import logging
import time
from typing import List, Tuple
import hashlib

import PyPDF2
import tiktoken
from openai import OpenAI
import streamlit as st
from app.db.database_connection import connect_to_db, insert_ingested_file, update_ingested_file_status

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFEmbeddingProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = 800
        self.model = "text-embedding-ada-002"
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    text += f"\n\n--- Page {page_num + 1} ---\n"
                    text += page_text
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
                    
        logger.info(f"Successfully extracted text from {len(pdf_reader.pages)} pages")
        return text.strip()
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks of max_tokens using tiktoken"""
        logger.info("Chunking text into smaller pieces...")
        
        # Tokenize the entire text
        tokens = self.encoding.encode(text)
        
        chunks = []
        current_chunk_tokens = []
        
        # Split into sentences first for better chunking
        sentences = text.split('. ')
        current_tokens = 0
        current_text = ""
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            if current_tokens + sentence_tokens > self.max_tokens and current_text:
                # Save current chunk and start new one
                chunks.append(current_text.strip())
                current_text = sentence + ". "
                current_tokens = sentence_tokens
            else:
                current_text += sentence + ". "
                current_tokens += sentence_tokens
        
        # Add the last chunk
        if current_text.strip():
            chunks.append(current_text.strip())
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def get_embedding_with_retry(self, text: str, max_retries: int = 3) -> List[float]:
        """Get embedding with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                return response.data[0].embedding
                
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
    
    def create_content_hash(self, content: str) -> str:
        """Create hash of content to prevent duplicates"""
        return hashlib.md5(content.encode()).hexdigest()

    def create_file_hash(self, file_path: str) -> str:
        """Create hash of entire file to track ingested files"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def initialize_rag_table(self):
        """Initialize the RAG chunks table with pgvector support"""
        logger.info("Initializing RAG table...")
        
        conn = connect_to_db()
        if conn is None:
            raise Exception("Failed to connect to database")
        
        try:
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Create the RAG table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS rag_chunks (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding VECTOR(1536),
                        content_hash VARCHAR(32) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create index for similarity search
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS rag_chunks_embedding_idx 
                    ON rag_chunks USING ivfflat (embedding vector_cosine_ops);
                """)
                
                conn.commit()
                logger.info("RAG table initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize RAG table: {e}")
            raise
        finally:
            conn.close()
    
    def chunk_exists(self, content_hash: str) -> bool:
        """Check if a chunk already exists in the database"""
        conn = connect_to_db()
        if conn is None:
            return False
            
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM rag_chunks WHERE content_hash = %s", (content_hash,))
                return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking chunk existence: {e}")
            return False
        finally:
            conn.close()
    
    def store_chunk_embedding(self, content: str, embedding: List[float]):
        """Store chunk and embedding in database"""
        content_hash = self.create_content_hash(content)
        
        # Skip if already exists
        if self.chunk_exists(content_hash):
            logger.debug("Chunk already exists, skipping...")
            return
        
        conn = connect_to_db()
        if conn is None:
            raise Exception("Failed to connect to database")
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO rag_chunks (content, embedding, content_hash)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (content_hash) DO NOTHING
                """, (content, embedding, content_hash))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store chunk: {e}")
            raise
        finally:
            conn.close()
    
    def process_pdf(self, pdf_path: str):
        """Main processing function"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Get file info for tracking
        file_name = os.path.basename(pdf_path)
        file_size = os.path.getsize(pdf_path)
        file_hash = self.create_file_hash(pdf_path)

        logger.info(f"Processing file: {file_name} ({file_size} bytes)")

        # Create ingested file record
        file_id = insert_ingested_file(file_name, pdf_path, file_size, file_hash, 'processing')

        if not file_id:
            logger.error("Failed to create ingested file record")
            raise Exception("Database error: could not track file ingestion")

        try:
            # Initialize database
            self.initialize_rag_table()

            # Extract and chunk text
            text = self.extract_text_from_pdf(pdf_path)
            chunks = self.chunk_text(text)

            logger.info(f"Processing {len(chunks)} chunks...")

            successful_chunks = 0
            failed_chunks = 0

            for i, chunk in enumerate(chunks):
                try:
                    logger.info(f"Processing chunk {i + 1}/{len(chunks)}")

                    # Get embedding
                    embedding = self.get_embedding_with_retry(chunk)

                    # Store in database
                    self.store_chunk_embedding(chunk, embedding)

                    successful_chunks += 1

                    # Rate limiting - be respectful to OpenAI API
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Failed to process chunk {i + 1}: {e}")
                    failed_chunks += 1
                    continue

            # Update file status to completed
            if failed_chunks == 0:
                update_ingested_file_status(file_id, 'completed', chunks_count=successful_chunks)
                logger.info(f"Processing complete! All {successful_chunks} chunks processed successfully")
            else:
                error_msg = f"Partial failure: {failed_chunks} chunks failed"
                update_ingested_file_status(file_id, 'completed', chunks_count=successful_chunks, error_message=error_msg)
                logger.warning(f"Processing complete with warnings! Success: {successful_chunks}, Failed: {failed_chunks}")

            return successful_chunks, failed_chunks

        except Exception as e:
            # Update file status to failed
            update_ingested_file_status(file_id, 'failed', error_message=str(e))
            logger.error(f"File processing failed: {e}")
            raise


def main():
    """Main execution function"""
    pdf_path = "2025 H2 Economics - Market Failure and Govt Intervention Lect Notes and Tut Package.pdf"
    
    processor = PDFEmbeddingProcessor()
    
    try:
        successful, failed = processor.process_pdf(pdf_path)
        print(f"✅ PDF processing completed successfully!")
        print(f"📊 Processed chunks: {successful} successful, {failed} failed")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"❌ Processing failed: {e}")


if __name__ == "__main__":
    main()