
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton)
from typing import Dict, Any, List
from src.models.file_info import FileInfo
from src.gui.file_list_frame import FileListFrame


class StatisticsDialog(QDialog):
    """İstatistikler Dialog penceresi."""
    
    def __init__(self, file_list_frame: FileListFrame, parent=None):
        super().__init__(parent)
        self.file_list_frame = file_list_frame
        self.init_ui()
    
    def init_ui(self):
        """Dialog arayüzünü oluşturur."""
        self.setWindowTitle("İstatistikler")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # İstatistikleri hesapla
        stats = self.calculate_statistics()
        
        # İstatistikleri göster
        for label, value in stats.items():
            stat_layout = QHBoxLayout()
            stat_layout.addWidget(QLabel(f"{label}:"))
            stat_layout.addWidget(QLabel(str(value)))
            layout.addLayout(stat_layout)
        
        # Kapat düğmesi
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def calculate_statistics(self) -> Dict[str, Any]:
        """İstatistikleri hesaplar."""
        files = self.file_list_frame.get_files()
        selected = self.file_list_frame.get_selected_files()
        
        stats = {
            "Toplam Dosya Sayısı": len(files),
            "Seçili Dosya Sayısı": len(selected),
            "Toplam Boyut": self.format_total_size(files),
            "Seçili Dosyaların Boyutu": self.format_total_size(selected),
        }
        
        # Dosya türlerine göre dağılım
        extension_stats = {}
        for file in files:
            ext = file.extension.lower()
            extension_stats[ext] = extension_stats.get(ext, 0) + 1
        
        for ext, count in extension_stats.items():
            stats[f"{ext} Dosya Sayısı"] = count
        
        return stats
    
    def format_total_size(self, files: List['FileInfo']) -> str:
        """Toplam boyutu formatlar."""
        total_size = sum(f.path.stat().st_size for f in files)
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024:
                return f"{total_size:.1f} {unit}"
            total_size /= 1024
            
        return f"{total_size:.1f} TB"