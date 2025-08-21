import pytest
from app.startup import chunk_text_robust

def test_chunk_text_robust_short_text():
    """Teste qu'un texte plus court que la taille du chunk n'est pas modifié."""
    content = "Ceci est un texte court."
    chunks = chunk_text_robust(content, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == content

def test_chunk_text_robust_long_text():
    """Teste qu'un long texte est correctement découpé en plusieurs chunks."""
    content = "a" * 2500
    chunks = chunk_text_robust(content, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 4
    assert chunks[0] == "a" * 1000
    assert len(chunks[1]) == 1000
    assert chunks[1].startswith("a" * 200) 

def test_chunk_text_robust_empty_string():
    """Teste qu'une chaîne vide retourne une liste vide."""
    content = ""
    chunks = chunk_text_robust(content, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 0

def test_chunk_text_robust_whitespace_string():
    """Teste qu'une chaîne avec seulement des espaces retourne une liste vide."""
    content = "   \t\n  "
    chunks = chunk_text_robust(content, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 0
    
def test_chunk_text_robust_with_paragraphs():
    """Teste le découpage basé sur les paragraphes."""
    content = "Premier paragraphe.\n\nDeuxième paragraphe qui est un peu plus long pour voir."
    chunks = chunk_text_robust(content, chunk_size=1000, chunk_overlap=200)
    assert len(chunks) == 2
    assert chunks[0] == "Premier paragraphe."
    assert chunks[1] == "Deuxième paragraphe qui est un peu plus long pour voir."