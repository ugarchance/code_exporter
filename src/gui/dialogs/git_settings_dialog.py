from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QMessageBox)
from src.utils.config_manager import ConfigManager

class GitSettingsDialog(QDialog):
    """Git ayarları Dialog penceresi."""
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()
    
    def init_ui(self):
        """Dialog arayüzünü oluşturur."""
        self.setWindowTitle("Git Ayarları")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Git ayarları
        # Git desteği
        self.git_enabled_cb = QCheckBox("Git Desteği")
        self.git_enabled_cb.setChecked(self.config_manager.get_git_config()['enabled'])
        layout.addWidget(self.git_enabled_cb)
        
        # Otomatik tarama
        self.git_autoscan_cb = QCheckBox("Otomatik Git Tarama")
        self.git_autoscan_cb.setChecked(self.config_manager.get_git_config()['auto_scan'])
        layout.addWidget(self.git_autoscan_cb)
        
        # Cache timeout
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(QLabel("Cache Süresi (saniye):"))
        self.cache_timeout_edit = QLineEdit()
        self.cache_timeout_edit.setText(str(self.config_manager.get_git_config()['cache_timeout']))
        cache_layout.addWidget(self.cache_timeout_edit)
        layout.addLayout(cache_layout)
        
        # Diff boyutu
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Maksimum Diff Boyutu (MB):"))
        self.max_diff_edit = QLineEdit()
        self.max_diff_edit.setText(str(self.config_manager.get_git_config()['max_diff_size'] / (1024 * 1024)))
        diff_layout.addWidget(self.max_diff_edit)
        layout.addLayout(diff_layout)
        
        # Yoksayılan branch'ler
        branches_layout = QVBoxLayout()
        branches_layout.addWidget(QLabel("Yoksayılan Branch'ler:"))
        self.excluded_branches_edit = QLineEdit()
        current_branches = self.config_manager.get_git_config()['excluded_branches']
        self.excluded_branches_edit.setText(','.join(current_branches))
        branches_layout.addWidget(self.excluded_branches_edit)
        layout.addLayout(branches_layout)
        
        # Butonlar
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
            git_config = self.config_manager.get_git_config()
            
            # Temel ayarlar
            git_config['enabled'] = self.git_enabled_cb.isChecked()
            git_config['auto_scan'] = self.git_autoscan_cb.isChecked()
            
            # Cache timeout
            cache_timeout = int(self.cache_timeout_edit.text())
            if cache_timeout > 0:
                git_config['cache_timeout'] = cache_timeout
            
            # Diff boyutu
            max_diff = float(self.max_diff_edit.text()) * 1024 * 1024  # MB to bytes
            if max_diff > 0:
                git_config['max_diff_size'] = int(max_diff)
            
            # Yoksayılan branch'ler
            excluded_branches = [b.strip() for b in self.excluded_branches_edit.text().split(',') if b.strip()]
            git_config['excluded_branches'] = excluded_branches
            
            # Ayarları kaydet
            self.config_manager.set_git_config(git_config)
            
            # Dialog'u kapat
            self.accept()
            
            QMessageBox.information(
                self,
                "Ayarlar Kaydedildi",
                "Git ayarları başarıyla kaydedildi."
            )
            
        except (ValueError, TypeError) as e:
            QMessageBox.warning(
                self,
                "Hata",
                f"Ayarlar kaydedilirken hata oluştu:\n{str(e)}"
            )