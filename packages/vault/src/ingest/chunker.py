"""
Chunking strategies for text import.
"""
from typing import List, Tuple


def chunk_by_size(text: str, chunk_size: int = 1024, overlap: int = 256) -> List[Tuple[str, int, int]]:
    """
    Chunk text by fixed size with overlap.
    Returns list of (chunk_text, byte_offset, byte_length) tuples.
    """
    chunks = []
    text_bytes = text.encode('utf-8')
    total_bytes = len(text_bytes)
    
    offset = 0
    while offset < total_bytes:
        end = min(offset + chunk_size, total_bytes)
        chunk_bytes = text_bytes[offset:end]
        
        # Try to break at word boundary
        if end < total_bytes:
            # Search backward for last space
            try:
                chunk_text = chunk_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # If we hit a multi-byte character, trim to safe boundary
                while end > offset and end < total_bytes:
                    try:
                        chunk_bytes = text_bytes[offset:end]
                        chunk_text = chunk_bytes.decode('utf-8')
                        break
                    except UnicodeDecodeError:
                        end -= 1
                else:
                    chunk_text = chunk_bytes.decode('utf-8', errors='replace')
            
            # Break at word boundary
            last_space = chunk_text.rfind(' ')
            if last_space > len(chunk_text) * 0.5:  # Don't break too early
                end = offset + len(chunk_text[:last_space].encode('utf-8'))
                chunk_bytes = text_bytes[offset:end]
                chunk_text = chunk_bytes.decode('utf-8')
        else:
            chunk_text = chunk_bytes.decode('utf-8')
        
        chunks.append((chunk_text, offset, len(chunk_bytes)))
        
        # Move forward with overlap
        offset = end - overlap if end - overlap > offset else end
    
    return chunks


def chunk_by_paragraphs(text: str, min_size: int = 512, max_size: int = 2048) -> List[Tuple[str, int, int]]:
    """
    Chunk text by paragraphs (double newline), respecting size limits.
    Returns list of (chunk_text, byte_offset, byte_length) tuples.
    """
    chunks = []
    paragraphs = text.split('\n\n')
    
    current_chunk = []
    current_offset = 0
    
    byte_pos = 0
    for i, para in enumerate(paragraphs):
        para_bytes = para.encode('utf-8')
        para_size = len(para_bytes)
        
        # Build test chunk with this paragraph
        test_chunk = current_chunk + [para]
        test_text = '\n\n'.join(test_chunk)
        test_size = len(test_text.encode('utf-8'))
        
        if test_size > max_size:
            # Flush current chunk without this paragraph (if not empty)
            if current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunk_bytes = len(chunk_text.encode('utf-8'))
                chunks.append((chunk_text, current_offset, chunk_bytes))
            
            # Start new chunk with current paragraph (even if it exceeds max_size when alone)
            current_chunk = [para]
            current_offset = byte_pos
        else:
            current_chunk.append(para)
        
        byte_pos += para_size + (2 if i < len(paragraphs) - 1 else 0)
    
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append((chunk_text, current_offset, len(chunk_text.encode('utf-8'))))
    
    return chunks
