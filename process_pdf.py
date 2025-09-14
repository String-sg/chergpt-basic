#!/usr/bin/env python3
"""
PDF Processing and Embedding Script
Processes the Economics PDF and stores embeddings in NeonDB with pgvector
"""

import os
import logging
import time
import sys
import argparse
import glob
import gc
import io
from typing import List, Tuple, Optional
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

        # Security limits
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.max_pages = 1000  # Maximum pages to process
        
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

    def validate_uploaded_file(self, file_content: bytes, filename: str) -> dict:
        """Validate uploaded file for security and format compliance"""
        validation_result = {
            'valid': False,
            'error': None,
            'warnings': []
        }

        try:
            # Check file size
            file_size = len(file_content)
            if file_size > self.max_file_size:
                validation_result['error'] = f"File too large ({file_size / 1024 / 1024:.1f}MB). Maximum allowed: {self.max_file_size / 1024 / 1024}MB"
                return validation_result

            if file_size == 0:
                validation_result['error'] = "File is empty"
                return validation_result

            # Check file extension
            if not filename.lower().endswith('.pdf'):
                validation_result['error'] = "File must be a PDF"
                return validation_result

            # Validate PDF format by trying to read it
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))

            # Check page count
            page_count = len(pdf_reader.pages)
            if page_count > self.max_pages:
                validation_result['error'] = f"PDF has too many pages ({page_count}). Maximum allowed: {self.max_pages}"
                return validation_result

            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                validation_result['error'] = "Encrypted PDFs are not supported for security reasons"
                return validation_result

            # Warnings for large files
            if file_size > 10 * 1024 * 1024:  # 10MB
                validation_result['warnings'].append(f"Large file ({file_size / 1024 / 1024:.1f}MB) - processing may take longer")

            if page_count > 100:
                validation_result['warnings'].append(f"Large PDF ({page_count} pages) - processing may take longer")

            validation_result['valid'] = True
            return validation_result

        except Exception as e:
            validation_result['error'] = f"Invalid PDF file: {str(e)}"
            return validation_result

    def extract_text_from_memory(self, file_content: bytes, filename: str) -> str:
        """Extract text from PDF in memory without saving to disk"""
        logger.info(f"Extracting text from uploaded file: {filename}")

        try:
            # Create PDF reader from memory buffer
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
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

        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {e}")
            raise Exception(f"Text extraction failed: {str(e)}")

    def create_file_hash_from_content(self, file_content: bytes) -> str:
        """Create hash from file content in memory"""
        return hashlib.sha256(file_content).hexdigest()

    def process_uploaded_file(self, file_content: bytes, filename: str) -> tuple[int, int]:
        """
        Securely process uploaded PDF from memory
        Returns (successful_chunks, failed_chunks)
        """
        try:
            # Security validation
            validation = self.validate_uploaded_file(file_content, filename)
            if not validation['valid']:
                raise Exception(validation['error'])

            # Log warnings
            for warning in validation['warnings']:
                logger.warning(warning)

            # Get file info for tracking
            file_size = len(file_content)
            file_hash = self.create_file_hash_from_content(file_content)

            logger.info(f"Processing uploaded file: {filename} ({file_size} bytes)")

            # Check if already processed
            if self.is_already_processed_by_hash(file_hash):
                raise Exception(f"File {filename} has already been processed")

            # Create ingested file record
            file_id = insert_ingested_file(filename, f"uploaded://{filename}", file_size, file_hash, 'processing')

            if not file_id:
                raise Exception("Database error: could not track file ingestion")

            try:
                # Initialize database
                self.initialize_rag_table()

                # Extract text from memory
                text = self.extract_text_from_memory(file_content, filename)

                # Immediately clear file content from memory for security
                file_content = None
                gc.collect()

                # Chunk text
                chunks = self.chunk_text(text)

                # Clear original text for security
                text = None
                gc.collect()

                logger.info(f"Processing {len(chunks)} chunks...")

                successful_chunks = 0
                failed_chunks = 0

                for i, chunk in enumerate(chunks):
                    try:
                        # Get embedding
                        embedding = self.get_embedding_with_retry(chunk)

                        # Store in database
                        self.store_chunk_embedding(chunk, embedding, file_id)

                        successful_chunks += 1

                        # Rate limiting
                        time.sleep(0.1)

                    except Exception as e:
                        logger.error(f"Failed to process chunk {i + 1}: {e}")
                        failed_chunks += 1
                        continue

                # Update file status
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

        finally:
            # Ensure cleanup
            file_content = None
            gc.collect()

    def is_already_processed_by_hash(self, file_hash: str) -> bool:
        """Check if file hash has already been processed successfully"""
        conn = connect_to_db()
        if conn is None:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status FROM ingested_files
                    WHERE file_hash = %s AND status = 'completed'
                """, (file_hash,))
                result = cur.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking if file is processed: {e}")
            return False
        finally:
            conn.close()
    
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
                        file_id INTEGER REFERENCES ingested_files(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Add file_id column if it doesn't exist (for existing databases)
                cur.execute("""
                    DO $$
                    BEGIN
                        BEGIN
                            ALTER TABLE rag_chunks ADD COLUMN file_id INTEGER REFERENCES ingested_files(id) ON DELETE CASCADE;
                        EXCEPTION
                            WHEN duplicate_column THEN
                            -- Column already exists, do nothing
                        END;
                    END $$;
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
    
    def store_chunk_embedding(self, content: str, embedding: List[float], file_id: int):
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
                    INSERT INTO rag_chunks (content, embedding, content_hash, file_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (content_hash) DO NOTHING
                """, (content, embedding, content_hash, file_id))
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
                    self.store_chunk_embedding(chunk, embedding, file_id)

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

    def is_already_processed(self, file_path: str) -> bool:
        """Check if file has already been processed successfully"""
        file_hash = self.create_file_hash(file_path)
        conn = connect_to_db()
        if conn is None:
            return False

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status FROM ingested_files
                    WHERE file_hash = %s AND status = 'completed'
                """, (file_hash,))
                result = cur.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking if file is processed: {e}")
            return False
        finally:
            conn.close()

    def process_directory(self, directory_path: str, force_reprocess: bool = False):
        """Process all PDF files in a directory"""
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        # Find all PDF files
        pdf_pattern = os.path.join(directory_path, "*.pdf")
        pdf_files = glob.glob(pdf_pattern)

        if not pdf_files:
            print(f"⚠️  No PDF files found in {directory_path}")
            return

        print(f"📁 Found {len(pdf_files)} PDF file(s) in {directory_path}")

        # Initialize database once
        self.initialize_rag_table()

        total_successful = 0
        total_failed = 0
        processed_count = 0
        skipped_count = 0

        for i, pdf_path in enumerate(pdf_files, 1):
            file_name = os.path.basename(pdf_path)
            print(f"\n{'='*60}")
            print(f"Processing file {i}/{len(pdf_files)}: {file_name}")
            print(f"{'='*60}")

            try:
                # Skip if already processed and not forcing reprocess
                if not force_reprocess and self.is_already_processed(pdf_path):
                    print(f"⏭️  Skipping {file_name} (already processed)")
                    skipped_count += 1
                    continue

                successful, failed = self.process_pdf(pdf_path)
                total_successful += successful
                total_failed += failed
                processed_count += 1

                print(f"✅ {file_name}: {successful} chunks processed, {failed} failed")

            except Exception as e:
                print(f"❌ Failed to process {file_name}: {e}")
                total_failed += 1

        # Final summary
        print(f"\n{'='*60}")
        print(f"📊 BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Files processed: {processed_count}")
        print(f"Files skipped: {skipped_count}")
        print(f"Total chunks successful: {total_successful}")
        print(f"Total chunks failed: {total_failed}")

        if total_successful > 0:
            print(f"🎉 Successfully processed {total_successful} chunks across {processed_count} files!")
        if total_failed > 0:
            print(f"⚠️  {total_failed} chunks failed processing")


def main():
    """Main execution function with command line argument support"""
    parser = argparse.ArgumentParser(description="Process PDF files for RAG ingestion")
    parser.add_argument("path", nargs="?",
                       help="Path to PDF file or directory (defaults to current directory)")
    parser.add_argument("--force", "-f", action="store_true",
                       help="Force reprocess already ingested files")
    parser.add_argument("--file", action="store_true",
                       help="Treat path as a single file (default: auto-detect)")
    parser.add_argument("--dir", action="store_true",
                       help="Treat path as a directory (default: auto-detect)")

    args = parser.parse_args()

    # Default to current directory if no path provided
    target_path = args.path or "."

    processor = PDFEmbeddingProcessor()

    try:
        # Auto-detect if not explicitly specified
        if args.file:
            is_file = True
        elif args.dir:
            is_file = False
        else:
            is_file = os.path.isfile(target_path)

        if is_file:
            # Process single file
            if not target_path.lower().endswith('.pdf'):
                print(f"❌ Error: {target_path} is not a PDF file")
                sys.exit(1)

            print(f"📄 Processing single file: {target_path}")
            successful, failed = processor.process_pdf(target_path)
            print(f"✅ Processing completed!")
            print(f"📊 Chunks: {successful} successful, {failed} failed")

        else:
            # Process directory
            print(f"📁 Processing directory: {target_path}")
            processor.process_directory(target_path, force_reprocess=args.force)

    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"❌ Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()