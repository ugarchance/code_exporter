import os
from pathlib import Path
from typing import List, Set
import chardet

def get_file_encoding(file_path: str | Path) -> str:
    """
    Dosyanın karakter kodlamasını tespit eder.
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        str: Tespit edilen kodlama (örn: 'utf-8', 'windows-1254')
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'

def safe_read_file(file_path: str | Path, encoding: str = None) -> str:
    """
    Dosyayı güvenli bir şekilde okur, kodlama hatası durumunda alternatif kodlamaları dener.
    
    Args:
        file_path: Dosya yolu
        encoding: Kullanılacak kodlama (None ise otomatik tespit edilir)
        
    Returns:
        str: Dosya içeriği
    """
    try:
        # Belirtilen kodlama ile okumayı dene
        if encoding:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        
        # Kodlamayı tespit et ve oku
        detected_encoding = get_file_encoding(file_path)
        with open(file_path, 'r', encoding=detected_encoding) as f:
            return f.read()
            
    except UnicodeDecodeError:
        # Yaygın kodlamaları dene
        encodings = ['utf-8', 'windows-1254', 'iso-8859-9', 'latin1']
        
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
                
        # Hiçbir kodlama işe yaramadıysa binary modda oku
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='replace')

def create_unique_filename(base_path: str | Path, name: str, extension: str = '.txt') -> Path:
    """
    Belirtilen klasörde benzersiz bir dosya adı oluşturur.
    
    Args:
        base_path: Ana klasör yolu
        name: Temel dosya adı
        extension: Dosya uzantısı
        
    Returns:
        Path: Benzersiz dosya yolu
    """
    base_path = Path(base_path)
    counter = 1
    
    # Uzantıyı düzenle
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    # İlk deneme
    file_path = base_path / f"{name}{extension}"
    
    # Dosya varsa yeni isim dene
    while file_path.exists():
        file_path = base_path / f"{name}_{counter}{extension}"
        counter += 1
    
    return file_path

def get_relative_path(file_path: str | Path, base_path: str | Path) -> str:
    """
    Dosyanın baz klasöre göre göreceli yolunu döndürür.
    
    Args:
        file_path: Dosya yolu
        base_path: Baz klasör yolu
        
    Returns:
        str: Göreceli yol
    """
    try:
        return str(Path(file_path).relative_to(base_path))
    except ValueError:
        return str(file_path)

def get_common_parent_path(paths: List[str | Path]) -> Path:
    """
    Verilen yolların ortak üst klasörünü bulur.
    
    Args:
        paths: Yol listesi
        
    Returns:
        Path: Ortak üst klasör
    """
    if not paths:
        return Path()
    
    paths = [Path(p).resolve() for p in paths]
    common_path = paths[0].parent
    
    while common_path != common_path.parent:
        if all(str(p).startswith(str(common_path)) for p in paths):
            return common_path

def format_file_size(size_in_bytes: int) -> str:
    """
    Dosya boyutunu insan okunabilir formata dönüştürür.
    
    Args:
        size_in_bytes: Bayt cinsinden boyut
        
    Returns:
        str: Formatlanmış boyut (örn: '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} PB"

def count_lines(content: str) -> int:
    """
    Metin içeriğindeki satır sayısını sayar (boş satırlar dahil).
    
    Args:
        content: Metin içeriği
        
    Returns:
        int: Satır sayısı
    """
    return len(content.splitlines())

def is_binary_file(file_path: str | Path) -> bool:
    """
    Dosyanın binary olup olmadığını kontrol eder.
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        bool: Dosya binary ise True
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return False
    except UnicodeDecodeError:
        return True
        common_path = common_path.parent
        
    return common_path