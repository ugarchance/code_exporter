from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

@dataclass
class FileInfo:
    """Taranan dosyaların bilgilerini tutan sınıf."""
    
    path: Path                      # Dosyanın tam yolu
    name: str                       # Dosya adı
    extension: str                  # Dosya uzantısı
    parent_folder: str             # Üst klasör adı
    layer_name: Optional[str]      # Katman adı (.NET/Java projeleri için)
    is_selected: bool = False      # Dosyanın seçili olup olmadığı
    
    @classmethod
    def from_path(cls, file_path: str | Path) -> 'FileInfo':
        """Dosya yolundan FileInfo nesnesi oluşturur."""
        path = Path(file_path)
        return cls(
            path=path,
            name=path.name,
            extension=path.suffix.lower(),
            parent_folder=path.parent.name,
            layer_name=cls._detect_layer_name(path),
            is_selected=False
        )
    
    @staticmethod
    def _detect_layer_name(path: Path) -> Optional[str]:
        """Dosya yolundan katman adını tespit eder."""
        # .NET ve Java projelerinde yaygın katman isimleri
        layer_keywords = {
            'controller', 'service', 'repository', 'model', 
            'entity', 'dao', 'dto', 'util', 'helper',
            'domain', 'infrastructure', 'application'
        }
        
        # Dosya yolundaki her klasörü kontrol et
        parts = path.parts
        for part in parts:
            part_lower = part.lower()
            # Klasör adı bir katman anahtar kelimesi içeriyorsa
            if any(keyword in part_lower for keyword in layer_keywords):
                return part
        
        return None
    
    def matches_search(self, search_term: str) -> bool:
        """Dosyanın arama terimiyle eşleşip eşleşmediğini kontrol eder."""
        search_term = search_term.lower()
        return (search_term in self.name.lower() or
                search_term in str(self.path).lower() or
                (self.layer_name and search_term in self.layer_name.lower()))
    
    def get_content(self) -> str:
        """Dosya içeriğini UTF-8 formatında okur."""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Dosya okuma hatası: {str(e)}"
    
    def __str__(self) -> str:
        """Dosya bilgilerinin string gösterimi."""
        return f"{self.name} ({self.parent_folder})"