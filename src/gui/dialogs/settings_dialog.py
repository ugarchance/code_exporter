from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QMessageBox)
from src.core.git.git_manager import GitManager
from src.utils.config_manager import ConfigManager

class SettingsDialog(QDialog):
    """Ayarlar Dialog penceresi."""
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.git_manager = GitManager()
        self.init_ui()
    
    def init_ui(self):
        """Dialog arayüzünü oluşturur."""
        self.setWindowTitle("Ayarlar")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Tema seçimi
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Tema:"))
        self.dark_mode_cb = QCheckBox("Koyu Tema")
        self.dark_mode_cb.setChecked(self.config_manager.get('dark_mode', False))
        theme_layout.addWidget(self.dark_mode_cb)
        layout.addLayout(theme_layout)

        # Git ayarları
        git_layout = QVBoxLayout()
        git_layout.addWidget(QLabel("Git Ayarları:"))
        
        # Git desteği
        self.git_enabled_cb = QCheckBox("Git Desteği")
        self.git_enabled_cb.setChecked(self.config_manager.get_git_config()['enabled'])
        git_layout.addWidget(self.git_enabled_cb)
        
        # Otomatik tarama
        self.git_autoscan_cb = QCheckBox("Otomatik Git Tarama")
        self.git_autoscan_cb.setChecked(self.config_manager.get_git_config()['auto_scan'])
        git_layout.addWidget(self.git_autoscan_cb)
        
        layout.addLayout(git_layout)
        
        # Paralel işlem sayısı
        workers_layout = QHBoxLayout()
        workers_layout.addWidget(QLabel("Paralel İşlem Sayısı:"))
        self.workers_edit = QLineEdit()
        self.workers_edit.setText(str(self.config_manager.get('max_workers', 4)))
        workers_layout.addWidget(self.workers_edit)
        layout.addLayout(workers_layout)
        
        # Yoksayılacak klasörler
        excluded_layout = QVBoxLayout()
        excluded_layout.addWidget(QLabel("Yoksayılacak Klasörler:"))
        self.excluded_edit = QLineEdit()
        current_excluded = self.config_manager.get('excluded_directories', [])
        self.excluded_edit.setText(','.join(current_excluded))
        excluded_layout.addWidget(self.excluded_edit)
        layout.addLayout(excluded_layout)
        
        # Desteklenen dosya uzantıları
        extensions_layout = QVBoxLayout()
        extensions_layout.addWidget(QLabel("Desteklenen Dosya Uzantıları:"))
        self.extensions_edit = QLineEdit()
        current_extensions = self.config_manager.get('supported_extensions', [])
        self.extensions_edit.setText(','.join(current_extensions))
        extensions_layout.addWidget(self.extensions_edit)
        layout.addLayout(extensions_layout)
        
        # Kaydetme düğmesi
        button_box = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)
    
    def save_settings(self):
        """Ayarları kaydeder."""
        try:
            # Tema ayarı
            self.config_manager.set('dark_mode', self.dark_mode_cb.isChecked())
            
            # Git ayarları
            git_config = self.config_manager.get_git_config()
            git_config['enabled'] = self.git_enabled_cb.isChecked()
            git_config['auto_scan'] = self.git_autoscan_cb.isChecked()
            self.config_manager.set_git_config(git_config)
            
            # Paralel işlem sayısı
            workers = int(self.workers_edit.text())
            if 1 <= workers <= 16:
                self.config_manager.set('max_workers', workers)
            
            # Yoksayılan klasörler
            excluded = [d.strip() for d in self.excluded_edit.text().split(',') if d.strip()]
            self.config_manager.set('excluded_directories', excluded)
            
            # Dosya uzantıları
            extensions = [e.strip() for e in self.extensions_edit.text().split(',') if e.strip()]
            self.config_manager.set('supported_extensions', extensions)
            
            # Dialog'u kapat
            self.accept()
            
            # Ayarların kaydedildiğini bildir
            QMessageBox.information(
                self,
                "Ayarlar Kaydedildi",
                "Ayarlar başarıyla kaydedildi ve uygulanacak."
            )
        except ValueError as e:
            QMessageBox.warning(self, "Hata", str(e))