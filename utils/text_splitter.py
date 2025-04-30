from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

class DocumentSplitter:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        separators: List[str] = None
    ):
        """
        Initialize the document splitter with custom parameters.
        
        Args:
            chunk_size (int): Maximum size of each chunk in characters
            chunk_overlap (int): Number of characters to overlap between chunks
            separators (List[str]): Custom separators for splitting text
        """
        if separators is None:
            separators = [
                "\n\n",
                "\n",
                ". ",
                "! ",
                "? ",
                " ",
                ""
            ]
            
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators
        )
        
    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split the input text into chunks with metadata.
        
        Args:
            text (str): Input text to split
            
        Returns:
            List[Dict[str, Any]]: List of chunks with metadata
        """
        # First, identify section headers
        sections = self._identify_sections(text)
        
        # Split the text into chunks
        chunks = self.splitter.split_text(text)
        
        # Add metadata to chunks
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Find which section this chunk belongs to
            section = self._find_section_for_chunk(chunk, sections)
            
            processed_chunks.append({
                "text": chunk,
                "chunk_id": i,
                "section": section,
                "metadata": {
                    "length": len(chunk),
                    "has_section_header": bool(section)
                }
            })
            
        return processed_chunks
    
    def _identify_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify section headers in the text.
        
        Args:
            text (str): Input text
            
        Returns:
            List[Dict[str, Any]]: List of sections with their positions
        """
        # Common section header patterns
        patterns = [
            r"\n\d+\.\s+[A-Za-z\s]+",  # 1. Section Name
            r"\n[A-Z]+\s+[A-Za-z\s]+",  # SECTION NAME
            r"\n[A-Z][a-z]+\s+[A-Za-z\s]+"  # Section Name
        ]
        
        sections = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                sections.append({
                    "title": match.group().strip(),
                    "start": match.start(),
                    "end": match.end()
                })
                
        return sorted(sections, key=lambda x: x["start"])
    
    def _find_section_for_chunk(self, chunk: str, sections: List[Dict[str, Any]]) -> str:
        """
        Find which section a chunk belongs to.
        
        Args:
            chunk (str): Text chunk
            sections (List[Dict[str, Any]]): List of sections
            
        Returns:
            str: Section title or empty string
        """
        chunk_start = 0  # Simplified for this example
        
        for section in sections:
            if section["start"] <= chunk_start:
                return section["title"]
                
        return "" 