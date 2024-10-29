from pathlib import Path
from typing import List, Dict, Optional
import json
import shutil
from datetime import datetime
from ..models.template import Template
from ..models.file_info import FileInfo

class TemplateManager:
    """Şablon yönetimi işlemlerini yöneten sınıf."""
    
    def __init__(self, templates_dir: str | Path):
        """
        Args:
            templates_dir: Şablonların saklanacağı klasör yolu
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._templates: Dict[str, Template] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Kayıtlı şablonları yükler."""
        for template_file in self.templates_dir.glob("*.json"):
            try:
                template = Template.load_from_file(template_file)
                self._templates[template.name] = template
            except Exception as e:
                print(f"Şablon yükleme hatası ({template_file}): {str(e)}")
    
    def get_templates(self) -> List[Template]:
        """Tüm şablonları döndürür."""
        return list(self._templates.values())
    
    def get_template(self, name: str) -> Optional[Template]:
        """İsme göre şablon döndürür."""
        return self._templates.get(name)
    
    def create_template(
        self,
        name: str,
        description: str,
        selected_files: List[FileInfo],
        export_settings: Dict = None
    ) -> Template:
        """
        Yeni şablon oluşturur ve kaydeder.
        
        Args:
            name: Şablon adı
            description: Şablon açıklaması
            selected_files: Seçili dosyalar
            export_settings: Dışa aktarma ayarları
            
        Returns:
            Template: Oluşturulan şablon
        """
        if name in self._templates:
            raise ValueError(f"'{name}' adında bir şablon zaten var")
        
        # Dosya desenlerini çıkar
        file_patterns = {file.extension for file in selected_files}
        
        # Klasör desenlerini çıkar
        folder_patterns = {file.parent_folder for file in selected_files 
                         if file.parent_folder}
        
        # Katman desenlerini çıkar
        layer_patterns = {file.layer_name for file in selected_files 
                        if file.layer_name}
        
        # Varsayılan dışa aktarma ayarları
        if export_settings is None:
            export_settings = {
                'group_by': None,
                'custom_naming': False
            }
        
        # Şablonu oluştur
        template = Template(
            name=name,
            description=description,
            file_patterns=list(file_patterns),
            folder_patterns=list(folder_patterns),
            layer_patterns=list(layer_patterns),
            export_settings=export_settings
        )
        
        # Şablonu kaydet
        template_path = self.templates_dir / f"{name}.json"
        template.save_to_file(template_path)
        
        # Şablonu yöneticiye ekle
        self._templates[name] = template
        return template
    
    def update_template(
        self,
        name: str,
        description: Optional[str] = None,
        selected_files: Optional[List[FileInfo]] = None,
        export_settings: Optional[Dict] = None
    ) -> Template:
        """Var olan şablonu günceller."""
        if name not in self._templates:
            raise ValueError(f"'{name}' adında bir şablon bulunamadı")
        
        template = self._templates[name]
        
        # Güncelleme yapılacak alanları kontrol et
        if description is not None:
            template.description = description
        
        if selected_files is not None:
            template.file_patterns = list({f.extension for f in selected_files})
            template.folder_patterns = list({f.parent_folder for f in selected_files 
                                          if f.parent_folder})
            template.layer_patterns = list({f.layer_name for f in selected_files 
                                         if f.layer_name})
        
        if export_settings is not None:
            template.export_settings = export_settings
        
        # Güncellenmiş şablonu kaydet
        template_path = self.templates_dir / f"{name}.json"
        template.save_to_file(template_path)
        
        return template
    
    def delete_template(self, name: str) -> None:
        """Şablonu siler."""
        if name not in self._templates:
            raise ValueError(f"'{name}' adında bir şablon bulunamadı")
        
        # Şablon dosyasını sil
        template_path = self.templates_dir / f"{name}.json"
        if template_path.exists():
            template_path.unlink()
        
        # Şablonu yöneticiden kaldır
        del self._templates[name]
    
    def export_template(self, name: str, export_path: str | Path) -> None:
        """
        Şablonu belirtilen konuma dışa aktarır.
        
        Args:
            name: Şablon adı
            export_path: Dışa aktarma yolu
        """
        if name not in self._templates:
            raise ValueError(f"'{name}' adında bir şablon bulunamadı")
        
        template_path = self.templates_dir / f"{name}.json"
        shutil.copy2(template_path, export_path)
    
    def import_template(self, import_path: str | Path) -> Template:
        """
        Şablonu içe aktarır.
        
        Args:
            import_path: İçe aktarılacak şablon dosyasının yolu
            
        Returns:
            Template: İçe aktarılan şablon
        """
        # Şablonu yükle
        template = Template.load_from_file(import_path)
        
        # Aynı isimde şablon varsa yeni isim oluştur
        original_name = template.name
        counter = 1
        while template.name in self._templates:
            template.name = f"{original_name}_{counter}"
            counter += 1
        
        # Şablonu kaydet
        template_path = self.templates_dir / f"{template.name}.json"
        template.save_to_file(template_path)
        
        # Şablonu yöneticiye ekle
        self._templates[template.name] = template
        return template
    
    def find_matching_files(self, template: Template, files: List[FileInfo]) -> List[FileInfo]:
        """
        Şablonla eşleşen dosyaları bulur.
        
        Args:
            template: Kontrol edilecek şablon
            files: Dosya listesi
            
        Returns:
            List[FileInfo]: Eşleşen dosyalar
        """
        return [file for file in files if template.matches_file(file)]