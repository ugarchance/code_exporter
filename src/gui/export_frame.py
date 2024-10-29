from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QRadioButton, QLineEdit, QFileDialog,
                             QMessageBox, QComboBox, QLabel, QProgressDialog,
                             QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import List, Optional
import os

from ..core.file_exporter import FileExporter
from ..core.template_manager import TemplateManager
from ..models.file_info import FileInfo
from ..models.template import Template
from ..utils.config_manager import ConfigManager

class ExportFrame(QFrame):
    """Dışa aktarma seçenekleri ve şablon yönetimi arayüzü."""
    
    # Sinyaller
    export_started = pyqtSignal()
    export_completed = pyqtSignal(int)  # Aktarılan dosya sayısı
    export_failed = pyqtSignal(str)     # Hata mesajı
    
    def __init__(self, file_exporter: FileExporter, 
                 template_manager: TemplateManager,
                 config_manager: ConfigManager):
        super().__init__()
        self.file_exporter = file_exporter
        self.template_manager = template_manager
        self.config_manager = config_manager
        
        self.selected_files: List[FileInfo] = []
        self.current_template: Optional[Template] = None
        
        self.init_ui()
    
    def init_ui(self) -> None:
        """Kullanıcı arayüzünü başlatır."""
        layout = QVBoxLayout(self)
        
        # Dışa aktarma seçenekleri grubu
        export_group = QGroupBox("Dışa Aktarma Seçenekleri")
        export_layout = QVBoxLayout(export_group)
        
        # Gruplandırma seçenekleri
        grouping_layout = QHBoxLayout()
        
        self.group_buttons = QButtonGroup(self)
        
        # Tek dosya
        self.single_file_radio = QRadioButton("Tek Dosya")
        self.single_file_radio.setChecked(True)
        self.group_buttons.addButton(self.single_file_radio)
        grouping_layout.addWidget(self.single_file_radio)
        
        # Katmana göre
        self.group_by_layer_radio = QRadioButton("Katmana Göre")
        self.group_buttons.addButton(self.group_by_layer_radio)
        grouping_layout.addWidget(self.group_by_layer_radio)
        
        # Klasöre göre
        self.group_by_folder_radio = QRadioButton("Klasöre Göre")
        self.group_buttons.addButton(self.group_by_folder_radio)
        grouping_layout.addWidget(self.group_by_folder_radio)
        
        export_layout.addLayout(grouping_layout)
        
        # Çıktı dosyası adı
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Dosya Adı:"))
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Varsayılan: export_YYYYMMDD_HHMMSS")
        name_layout.addWidget(self.name_edit)
        
        export_layout.addLayout(name_layout)
        
        # Çıktı klasörü
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Hedef Klasör:"))
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Çıktı klasörünü seç...")
        output_layout.addWidget(self.output_dir_edit)
        
        self.browse_btn = QPushButton("Gözat...")
        self.browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.browse_btn)
        
        export_layout.addLayout(output_layout)
        
        # İlerleme bilgisi
        self.progress_label = QLabel()
        export_layout.addWidget(self.progress_label)
        
        # Dışa aktar düğmesi
        self.export_btn = QPushButton("Dışa Aktar")
        self.export_btn.clicked.connect(self.export_files)
        self.export_btn.setEnabled(False)  # Başlangıçta devre dışı
        export_layout.addWidget(self.export_btn)
        
        layout.addWidget(export_group)
        
        # Başlangıç dizinini ayarla
        last_dir = self.config_manager.get('export_directory')
        if last_dir and os.path.exists(last_dir):
            self.output_dir_edit.setText(last_dir)
    
    def browse_output_dir(self) -> None:
        """Çıktı klasörü seçme dialogunu açar."""
        current_dir = self.output_dir_edit.text() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self,
            "Çıktı Klasörünü Seç",
            current_dir
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            self.config_manager.set('export_directory', directory)
    
    def update_selected_files(self, files: List[FileInfo]) -> None:
        """Seçili dosya listesini günceller."""
        self.selected_files = files
        self.export_btn.setEnabled(bool(files))
        
        # İlerleme bilgisini güncelle
        if files:
            self.progress_label.setText(f"{len(files)} dosya seçildi")
        else:
            self.progress_label.setText("Dosya seçilmedi")
    
    def export_files(self) -> None:
        """Seçili dosyaları dışa aktarır."""
        if not self.selected_files:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Dışa aktarılacak dosya seçilmedi!"
            )
            return
            
        # Çıktı klasörünü kontrol et
        output_dir = self.output_dir_edit.text()
        if not output_dir:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Lütfen çıktı klasörünü seçin!"
            )
            return
            
        output_path = Path(output_dir)
        
        try:
            # Klasörü oluştur
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Gruplandırma türünü belirle
            group_by = None
            if self.group_by_layer_radio.isChecked():
                group_by = 'layer'
            elif self.group_by_folder_radio.isChecked():
                group_by = 'folder'
            
            # Özel dosya adı
            custom_name = self.name_edit.text()
            
            # İlerleme dialogu
            progress = QProgressDialog(
                "Dosyalar dışa aktarılıyor...",
                "İptal",
                0,
                len(self.selected_files),
                self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            
            # Dışa aktarma başladı sinyali
            self.export_started.emit()
            
            # Dosyaları dışa aktar
            exported = self.file_exporter.export_files(
                self.selected_files,
                output_path,
                group_by=group_by,
                custom_name=custom_name
            )
            
            # Başarılı sinyal
            self.export_completed.emit(len(self.selected_files))
            
            # Son kullanılan klasörü kaydet
            self.config_manager.set('export_directory', output_dir)
            
            # Tamamlandı mesajı
            QMessageBox.information(
                self,
                "Başarılı",
                f"{len(exported)} dosya başarıyla dışa aktarıldı.\n"
                f"Konum: {output_dir}"
            )
            
        except Exception as e:
            # Hata sinyali
            self.export_failed.emit(str(e))
            
        finally:
            progress.close()
    
    def create_new_template(self) -> None:
        """Yeni şablon oluşturma dialogunu açar."""
        if not self.selected_files:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Şablon oluşturmak için önce dosya seçmelisiniz!"
            )
            return
        
        # Şablon adı al
        name, ok = QMessageBox.getText(
            self,
            "Yeni Şablon",
            "Şablon Adı:",
            QLineEdit.EchoMode.Normal
        )
        
        if ok and name:
            # Şablon zaten var mı kontrol et
            if self.template_manager.get_template(name):
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    f"'{name}' adında bir şablon zaten var!"
                )
                return
            
            # Açıklama al
            description, ok = QMessageBox.getText(
                self,
                "Şablon Açıklaması",
                "Açıklama:",
                QLineEdit.EchoMode.Normal
            )
            
            if ok:
                try:
                    # Mevcut dışa aktarma ayarlarını al
                    export_settings = {
                        'group_by': 'layer' if self.group_by_layer_radio.isChecked()
                                    else 'folder' if self.group_by_folder_radio.isChecked()
                                    else None,
                        'custom_naming': bool(self.name_edit.text())
                    }
                    
                    # Şablonu oluştur
                    template = self.template_manager.create_template(
                        name=name,
                        description=description,
                        selected_files=self.selected_files,
                        export_settings=export_settings
                    )
                    
                    # Son kullanılan şablonlara ekle
                    self.config_manager.add_recent_template(name)
                    
                    QMessageBox.information(
                        self,
                        "Başarılı",
                        f"'{name}' şablonu başarıyla oluşturuldu."
                    )
                    
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Hata",
                        f"Şablon oluşturulurken hata: {str(e)}"
                    )
    
    def load_template(self, template: Template) -> None:
        """Seçilen şablonu yükler."""
        try:
            self.current_template = template
            
            # Gruplandırma ayarını yükle
            group_by = template.export_settings.get('group_by')
            if group_by == 'layer':
                self.group_by_layer_radio.setChecked(True)
            elif group_by == 'folder':
                self.group_by_folder_radio.setChecked(True)
            else:
                self.single_file_radio.setChecked(True)
            
            # Özel isimlendirme ayarını yükle
            if template.export_settings.get('custom_naming'):
                self.name_edit.setText(template.name)
            
            # Eşleşen dosyaları bul ve seç
            matching_files = self.template_manager.find_matching_files(
                template, 
                self.selected_files
            )
            
            if matching_files:
                self.update_selected_files(matching_files)
            
            QMessageBox.information(
                self,
                "Şablon Yüklendi",
                f"'{template.name}' şablonu başarıyla yüklendi.\n"
                f"Eşleşen dosya sayısı: {len(matching_files)}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Hata",
                f"Şablon yüklenirken hata: {str(e)}"
            )
    
    def export_template(self) -> None:
        """Mevcut şablonu dışa aktarır."""
        if not self.current_template:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Dışa aktarılacak şablon seçilmedi!"
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Şablonu Kaydet",
            str(Path.home() / f"{self.current_template.name}.json"),
            "JSON Dosyaları (*.json)"
        )
        
        if file_path:
            try:
                self.template_manager.export_template(
                    self.current_template.name,
                    file_path
                )
                
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Şablon başarıyla dışa aktarıldı:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Şablon dışa aktarılırken hata: {str(e)}"
                )