from dataclasses import dataclass
from typing import List, Dict
import json
from pathlib import Path

@dataclass
class Template:
    """Şablon bilgilerini tutan sınıf."""
    
    name: str                       # Şablon adı
    description: str                # Şablon açıklaması
    file_patterns: List[str]        # Dosya uzantıları (.java, .cs vb.)
    folder_patterns: List[str]      # Klasör desenleri
    layer_patterns: List[str]       # Katman desenleri
    export_settings: Dict           # Dışa aktarma ayarları
    
    def to_json(self) -> str:
        """Şablonu JSON formatına dönüştürür."""
        return json.dumps({
            'name': self.name,
            'description': self.description,
            'file_patterns': self.file_patterns,
            'folder_patterns': self.folder_patterns,
            'layer_patterns': self.layer_patterns,
            'export_settings': self.export_settings
        }, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Template':
        """JSON formatından Template nesnesi oluşturur."""
        data = json.loads(json_str)
        return cls(
            name=data['name'],
            description=data['description'],
            file_patterns=data['file_patterns'],
            folder_patterns=data['folder_patterns'],
            layer_patterns=data['layer_patterns'],
            export_settings=data['export_settings']
        )
    
    def save_to_file(self, file_path: str | Path) -> None:
        """Şablonu dosyaya kaydeder."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, file_path: str | Path) -> 'Template':
        """Dosyadan şablon yükler."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())
    
    def matches_file(self, file_info) -> bool:
        """Verilen dosyanın bu şablonla eşleşip eşleşmediğini kontrol eder."""
        # Dosya uzantısı kontrolü
        if not any(file_info.extension.endswith(pattern) for pattern in self.file_patterns):
            return False
            
        # Klasör deseni kontrolü
        if self.folder_patterns and not any(
            pattern in str(file_info.path) for pattern in self.folder_patterns
        ):
            return False
            
        # Katman kontrolü
        if self.layer_patterns and file_info.layer_name and not any(
            pattern in file_info.layer_name for pattern in self.layer_patterns
        ):
            return False
            
        return True