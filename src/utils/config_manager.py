import json
from pathlib import Path
from typing import Any, Dict, Optional
import os

class ConfigManager:
    """Program ayarlarını yöneten sınıf."""
    
    DEFAULT_CONFIG = {
        'last_directory': '',
        'export_directory': '',
        'max_workers': 4,
        'batch_size': 1000,
        'excluded_directories': ['.git', 'node_modules', 'bin', 'obj', 'build', 'dist'],
        'supported_extensions': ['.java', '.cs', '.js', '.jsx', '.ts', '.tsx','.py'],
        'default_encoding': 'utf-8',
        'window_size': {'width': 1024, 'height': 768},
        'window_position': {'x': 100, 'y': 100},
        'recent_projects': [],
        'recent_templates': [],
        'dark_mode': False
    }
    
    def __init__(self, config_dir: str | Path):
        """
        Args:
            config_dir: Ayarların saklanacağı klasör
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / 'config.json'
        
        # Varsayılan ayarlar
        self.config: Dict[str, Any] = {
            'excluded_directories': ['.git', 'node_modules', 'bin', 'obj', 'build', 'dist'],
            'supported_extensions': ['.java', '.cs', '.js', '.jsx', '.ts', '.tsx','.py'],
            'max_workers': 4,
            'batch_size': 1000,
            'default_encoding': 'utf-8',
            'dark_mode': False
        }
        
        # Yapılandırma klasörünü oluştur
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.ensure_app_dirs()
    
    def load_config(self) -> None:
        """Kayıtlı ayarları yükler."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Varsayılan ayarları güncelle
                    self.config.update(loaded_config)
        except Exception as e:
            print(f"Ayar yükleme hatası: {str(e)}")
    
    def save_config(self) -> None:
        """Ayarları kaydeder."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ayar kaydetme hatası: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Ayar değerini döndürür.
        
        Args:
            key: Ayar anahtarı
            default: Varsayılan değer
            
        Returns:
            Any: Ayar değeri
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Ayar değerini günceller ve kaydeder.
        
        Args:
            key: Ayar anahtarı
            value: Yeni değer
        """
        self.config[key] = value
        self.save_config()
    
    def add_recent_project(self, project_path: str) -> None:
        """Son kullanılan projelere yeni proje ekler."""
        recent = self.config.get('recent_projects', [])
        
        # Zaten varsa listeden çıkar
        if project_path in recent:
            recent.remove(project_path)
            
        # Başa ekle
        recent.insert(0, project_path)
        
        # Maksimum 10 proje tut
        self.config['recent_projects'] = recent[:10]
        self.save_config()
    
    def add_recent_template(self, template_name: str) -> None:
        """Son kullanılan şablonlara yeni şablon ekler."""
        recent = self.config.get('recent_templates', [])
        
        # Zaten varsa listeden çıkar
        if template_name in recent:
            recent.remove(template_name)
            
        # Başa ekle
        recent.insert(0, template_name)
        
        # Maksimum 10 şablon tut
        self.config['recent_templates'] = recent[:10]
        self.save_config()
    
    def get_app_dirs(self) -> Dict[str, Path]:
        """Uygulama klasörlerini döndürür."""
        return {
            'config': self.config_dir,
            'templates': self.config_dir / 'templates',
            'exports': self.config_dir / 'exports',
            'logs': self.config_dir / 'logs'
        }
    
    def ensure_app_dirs(self) -> None:
        """Uygulama klasörlerinin varlığını kontrol eder ve oluşturur."""
        for dir_path in self.get_app_dirs().values():
            dir_path.mkdir(parents=True, exist_ok=True)