from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QMenuBar, QMenu, QMessageBox, QFileDialog,
                             QStatusBar, QDialog, QLabel, QLineEdit, QPushButton,
                             QCheckBox)

from src.core import file_scanner
from src.core.git.git_exceptions import GitException, GitInitError
from src.core.git.git_manager import GitManager
from src.gui.dialogs.git_settings_dialog import GitSettingsDialog
from src.gui.dialogs.settings_dialog import SettingsDialog
from src.gui.dialogs.statistics_dialog import StatisticsDialog
from ..models.file_info import FileInfo
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from pathlib import Path
import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

from src.utils.config_manager import ConfigManager
from src.gui.file_list_frame import FileListFrame
from src.gui.export_frame import ExportFrame


class MainWindow(QMainWindow):
    """Ana program penceresi."""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager 
        logging.info("Git manager başlatılıyor...")
        self.git_manager = GitManager()
        logging.info("Git manager başlatıldı")
        self.file_list = None
        # Pencere başlığı ve boyutu
        self.setWindowTitle("Kod Dışa Aktarma Aracı")
        self.setMinimumSize(1024, 768)
        
        # Merkezi widget'ı oluştur
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Ana layout
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Menü çubuğunu oluştur
        self.create_menu_bar()
        
        # Splitter ve panelleri oluştur
        self.create_panels()
        
        # Durum çubuğunu oluştur
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Pencere ayarlarını yükle
        self.load_window_settings()
    
    def create_menu_bar(self):
        """Menü çubuğunu oluşturur."""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")
        
         # Git menüsü
        git_menu = menubar.addMenu("Git")
    
        # Repository yenile
        refresh_action = QAction("Repository Yenile", self)
        refresh_action.setShortcut("Ctrl+R")
        refresh_action.triggered.connect(self.refresh_git_status)
        git_menu.addAction(refresh_action)
        
        # Branch değiştir
        branch_menu = QMenu("Branch Değiştir", self)
        git_menu.addMenu(branch_menu)
        
        # Git ayarları
        git_settings_action = QAction("Git Ayarları", self)
        git_settings_action.triggered.connect(self.show_git_settings)
        git_menu.addAction(git_settings_action)
        
        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")     

        # Klasör Aç
        open_action = QAction("Klasör Aç...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.select_directory)
        file_menu.addAction(open_action)
        
        # Son kullanılanlar
        self.recent_menu = QMenu("Son Kullanılanlar", self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        # Ayarlar
        settings_action = QAction("Ayarlar", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction("Çıkış", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")
        
        # İstatistikler
        stats_action = QAction("İstatistikler", self)
        stats_action.triggered.connect(self.show_statistics)
        view_menu.addAction(stats_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")
        
        # Hakkında
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_panels(self):
        """Panel yerleşimini oluşturur."""
        # Splitter oluştur
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Core bileşenleri oluştur
        from src.core.file_scanner import FileScanner
        from src.core.file_exporter import FileExporter
        from src.core.template_manager import TemplateManager
        
        file_scanner = FileScanner()
        file_exporter = FileExporter()
        template_manager = TemplateManager(
            self.config_manager.get_app_dirs()['templates']
        )
        
        # Dosya listesi paneli
        self.file_list = FileListFrame(file_scanner, git_manager=self.git_manager)
        self.splitter.addWidget(self.file_list)
        
        # Dışa aktarma paneli
        self.export_frame = ExportFrame(
            file_exporter=file_exporter,
            template_manager=template_manager,
            config_manager=self.config_manager
        )
        self.splitter.addWidget(self.export_frame)
        
        # Splitter'ı ana layout'a ekle
        self.main_layout.addWidget(self.splitter)
        
        # Panel boyutlarını ayarla
        self.splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])
        
        # Paneller arası sinyal bağlantıları
        self.file_list.selection_changed.connect(self.export_frame.update_selected_files)
        self.export_frame.export_started.connect(self.on_export_started)
        self.export_frame.export_completed.connect(self.on_export_completed)
        self.export_frame.export_failed.connect(self.on_export_failed)
    
    
    def show_git_settings(self):
        """Git ayarları penceresini gösterir."""
        # Git ayarları dialog'unu göster
        dialog = GitSettingsDialog(self.config_manager, self)
        dialog.exec()
        
    def refresh_git_status(self):
        """Git durumunu yeniler."""
        if self.git_manager:
            try:
                current_dir = self.file_list.current_directory
                if current_dir:
                    changes = self.git_manager.check_changes(Path(current_dir))
                    self.file_list.update_git_status(changes)
            except GitException as e:
                QMessageBox.warning(
                    self,
                    "Git Hatası",
                    f"Git durumu güncellenirken hata oluştu:\n{str(e)}"
                )

    def select_directory(self):
        """Klasör seçme dialogunu açar."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Proje Klasörünü Seç",
            str(Path.home())  # Her zaman kullanıcının home dizininden başla
        )
        
        if directory:
            self.open_directory(directory)
    
    def open_directory(self, directory: str):
        """Seçilen klasörü açar."""
        try:
            # Klasörü tara
            self.file_list.scan_directory(directory)
            
            # Son kullanılan klasörlere ekle
            self.add_recent_directory(directory)
            
            # Durum çubuğunu güncelle
            self.status_bar.showMessage(f"'{directory}' klasörü tarandı.")
            
        except Exception as e:
            logging.error(f"Klasör açma hatası: {e}")
            QMessageBox.critical(
                self,
                "Hata",
                f"Klasör açılırken hata oluştu:\n{str(e)}"
            )
    
    def add_recent_directory(self, directory: str):
        """Son kullanılan klasörlere yeni klasör ekler."""
        recent_dirs = self.config_manager.get('recent_directories', [])
        
        # Zaten varsa listeden çıkar
        if directory in recent_dirs:
            recent_dirs.remove(directory)
        
        # Başa ekle
        recent_dirs.insert(0, directory)
        
        # Maksimum 10 klasör tut
        recent_dirs = recent_dirs[:10]
        
        # Ayarları güncelle
        self.config_manager.set('recent_directories', recent_dirs)
        self.config_manager.set('last_directory', directory)
        
        # Menüyü güncelle
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """Son kullanılanlar menüsünü günceller."""
        self.recent_menu.clear()
        recent_dirs = self.config_manager.get('recent_directories', [])
        
        for directory in recent_dirs:
            action = QAction(directory, self)
            action.triggered.connect(lambda d=directory: self.open_directory(d))
            self.recent_menu.addAction(action)
    
    def show_settings(self):
        """Ayarlar penceresini gösterir."""
        dialog = SettingsDialog(self.config_manager, self)
        dialog.exec()
    
    def show_git_settings(self):
        """Git ayarları penceresini gösterir."""
        dialog = GitSettingsDialog(self.config_manager, self)
        dialog.exec()
    
    def show_statistics(self):
        """İstatistikler penceresini gösterir."""
        dialog = StatisticsDialog(self.file_list, self)
        dialog.exec()
    
    def show_about(self):
        """Hakkında penceresini gösterir."""
        QMessageBox.about(
            self,
            "Hakkında",
            "Kod Dışa Aktarma Aracı\n\n"
            "Sürüm: 1.0.0\n\n"
            "Bu program, proje dosyalarını kolayca dışa aktarmak ve "
            "yönetmek için tasarlanmıştır.\n\n"
            "© 2024 Tüm hakları saklıdır."
        )
    
    def on_export_started(self):
        """Dışa aktarma başladığında çağrılır."""
        self.status_bar.showMessage("Dosyalar dışa aktarılıyor...")
    
    def on_export_completed(self, file_count: int):
        """Dışa aktarma tamamlandığında çağrılır."""
        self.status_bar.showMessage(
            f"{file_count} dosya başarıyla dışa aktarıldı.",
            5000  # 5 saniye göster
        )
    
    def on_export_failed(self, error_msg: str):
        """Dışa aktarma başarısız olduğunda çağrılır."""
        self.status_bar.showMessage("Dışa aktarma başarısız oldu!")
        QMessageBox.critical(
            self,
            "Dışa Aktarma Hatası",
            f"Dosyalar dışa aktarılırken hata oluştu:\n{error_msg}"
        )
    
    def load_window_settings(self):
        """Pencere ayarlarını yükler."""
        settings = self.config_manager.get('window_settings', {})
        
        if 'geometry' in settings:
            self.restoreGeometry(bytes.fromhex(settings['geometry']))
        if 'state' in settings:
            self.restoreState(bytes.fromhex(settings['state']))
        if 'splitter' in settings:
            self.splitter.restoreState(bytes.fromhex(settings['splitter']))
    
    def save_window_settings(self):
        """Pencere ayarlarını kaydeder."""
        settings = {
            'geometry': self.saveGeometry().hex(),
            'state': self.saveState().hex(),
            'splitter': self.splitter.saveState().hex()
        }
        self.config_manager.set('window_settings', settings)
    
    def closeEvent(self, event):
        """Program kapatılırken çağrılır."""
        # Pencere ayarlarını kaydet
        self.save_window_settings()
        event.accept()