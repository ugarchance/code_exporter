from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class FileExporter:
    """Dosya dışa aktarma işlemlerini yöneten sınıf."""
    
    def __init__(self):
        self.export_format = """Path: {file_path}
Code:
{file_content}
{separator}
"""
        self.separator = "\n" + "=" * 80 + "\n"
    
    def _create_export_file(self, output_path: Path) -> None:
        """Dışa aktarma dosyasını oluşturur ve UTF-8 BOM ekler."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
    
    def _append_to_file(self, file_path: Path, content: str) -> None:
        """Dosyaya içerik ekler."""
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def _format_display_path(self, file_path: str | Path, ref_path: Path) -> str:
        """Görüntülenecek yolu formatlar."""
        try:
            # Path'i referans noktadan sonrasını alacak şekilde formatla
            parts = Path(file_path).parts[len(ref_path.parts)-1:]
            return "\\" + "\\".join(parts)
        except Exception:
            # Herhangi bir hata durumunda orijinal path'i döndür
            return str(file_path)
    
    def _process_java_content(self, content: str) -> str:
        """Java dosyasındaki import ve package satırlarını filtreler."""
        lines = content.splitlines()
        filtered_lines = [
            line for line in lines
            if not line.strip().startswith(("import ", "package "))
        ]
        return "\n".join(filtered_lines)

    def export_files(
        self,
        files: List[str],
        output_dir: str | Path,
        group_by: Optional[str] = None,
        custom_name: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Dosyaları dışa aktarır.
        
        Args:
            files: Dışa aktarılacak dosyaların yolları
            output_dir: Çıktı klasörü
            group_by: Gruplandırma türü ('layer', 'folder' veya None)
            custom_name: Özel dosya adı
            
        Returns:
            Dict[str, Path]: Oluşturulan dosyaların grup adı ve yolları
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Dosyaları gruplara ayır
        if group_by == 'folder':
            groups = self._group_by_folder(files)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = custom_name or f"export_{timestamp}"
            groups = {name: files}
        
        exported_files = {}
        
        # Her grup için ayrı dosya oluştur
        for group_name, group_files in groups.items():
            if not group_files:  # Boş grupları atla
                continue
                
            # Dosya adını oluştur
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                              for c in group_name)
            export_path = output_path / f"{safe_name}.txt"
            
            # Dosyayı oluştur ve BOM ekle
            self._create_export_file(export_path)
            
            # İlk dosyanın klasör yolunu al (referans için)
            ref_path = Path(group_files[0]).parent.parent
            
            # Dosyaları aktar
            for file_path in group_files:
                try:
                    # Dosya içeriğini oku
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Java dosyası ise içeriği filtrele
                    if str(file_path).lower().endswith('.java'):
                        content = self._process_java_content(content)
                    
                    # Path'i formatla
                    display_path = self._format_display_path(file_path, ref_path)
                    
                    # İçeriği formatla ve dosyaya ekle
                    content = self.export_format.format(
                        file_path=display_path,
                        file_content=content,
                        separator=self.separator
                    )
                    self._append_to_file(export_path, content)
                    
                except Exception as e:
                    error_content = self.export_format.format(
                        file_path=str(file_path),
                        file_content=f"Dosya okuma hatası: {str(e)}",
                        separator=self.separator
                    )
                    self._append_to_file(export_path, error_content)
            
            exported_files[group_name] = export_path
        
        return exported_files
    
    def _group_by_folder(self, files: List[str]) -> Dict[str, List[str]]:
        """Dosyaları üst klasörlere göre gruplar."""
        groups: Dict[str, List[str]] = {}
        
        for file_path in files:
            path = Path(file_path)
            folder = path.parent.name or 'root'
            
            if folder not in groups:
                groups[folder] = []
            groups[folder].append(file_path)
        
        return groups
    
    def _group_by_layer(self, files: List[str]) -> Dict[str, List[str]]:
        """Dosyaları katmanlara göre gruplar."""
        groups: Dict[str, List[str]] = {}
        
        # Yaygın katman isimleri
        layer_keywords = {
            'controller', 'service', 'repository', 'model', 
            'entity', 'dao', 'dto', 'util', 'helper',
            'domain', 'infrastructure', 'application'
        }
        
        for file_path in files:
            path = Path(file_path)
            layer = 'other'
            
            # Path içinde katman ismi ara
            for part in path.parts:
                part_lower = part.lower()
                if any(keyword in part_lower for keyword in layer_keywords):
                    layer = part
                    break
            
            if layer not in groups:
                groups[layer] = []
            groups[layer].append(file_path)
        
        return groups