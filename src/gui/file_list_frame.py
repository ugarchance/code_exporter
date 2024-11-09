import logging
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QProgressDialog, QApplication,
                             QCheckBox, QRadioButton)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import os
from pathlib import Path
import time
from PyQt6.QtGui import QIcon, QColor
from src.core.git.git_manager import GitManager
from src.core.git.git_exceptions import GitException
from src.core.git.git_types import GitFileStatus

class FileListFrame(QFrame):
    """Basitleştirilmiş dosya listesi görünümü."""
    
    # Seçili dosyalar sinyali
    selection_changed = pyqtSignal(list)
    
    def __init__(self, file_scanner=None, git_manager=None):
        super().__init__()
        self.file_scanner = file_scanner  # file_scanner'ı sakla
        self.git_manager = git_manager
        self.current_directory = None
        self.git_status = {} 
        self.total_files = 0
        self.selected_files = set()
        self.visible_rows = set()  # Görünür satırları takip etmek için
        self.setup_ui()
        
        self.table.setColumnCount(6)  # 5'ten 6'ya çıkarıldı
        self.table.setHorizontalHeaderLabels(
        ["", "Dosya Adı", "Uzantı", "Klasör", "Boyut", "Git"]  # Git sütunu en sonda
    )

    def update_git_status(self, status: dict):
        """Git durumunu günceller ve tabloyu yeniler."""
        self.git_status = status
        
        # Git değişikliklerini say
        modified_count = sum(1 for s in status.values() if s == GitFileStatus.MODIFIED)
        added_count = sum(1 for s in status.values() if s == GitFileStatus.ADDED)
        deleted_count = sum(1 for s in status.values() if s == GitFileStatus.DELETED)
        untracked_count = sum(1 for s in status.values() if s == GitFileStatus.UNTRACKED)
        
        # Tablo görünümünü güncelle
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            if name_item is None:
                continue
                
            file_path_data = name_item.data(Qt.ItemDataRole.UserRole)
            if file_path_data is None:
                continue
                
            try:
                file_path = Path(file_path_data)
                if file_path in self.git_status:
                    self._set_git_status_cell(row, self.git_status[file_path])
            except Exception as e:
                logging.warning(f"Git durumu güncellenirken hata: {e}")
        
        # Bilgi etiketini güncelle
        status_info = (
            f"Git değişiklikleri: "
            f"{modified_count} değişen, "
            f"{added_count} yeni, "
            f"{deleted_count} silinen, "
            f"{untracked_count} takip edilmeyen"
        )
        self.update_info_label(status_info)
        
    def _set_git_status_cell(self, row: int, status: GitFileStatus):
        """Git durumu hücresini ayarlar."""
        item = QTableWidgetItem()
        
        if status == GitFileStatus.MODIFIED:
            item.setText("✎ M")  # Kalem emoji ile Modified
            item.setBackground(QColor(255, 255, 150))  # Daha belirgin sarı
            item.setToolTip("Modified - Dosya değiştirildi")
        elif status == GitFileStatus.ADDED:
            item.setText("+ A")  # Plus işareti ile Added
            item.setBackground(QColor(150, 255, 150))  # Daha belirgin yeşil
            item.setToolTip("Added - Dosya eklendi")
        elif status == GitFileStatus.DELETED:
            item.setText("- D")  # Eksi işareti ile Deleted
            item.setBackground(QColor(255, 150, 150))  # Daha belirgin kırmızı
            item.setToolTip("Deleted - Dosya silindi")
        elif status == GitFileStatus.UNTRACKED:
            item.setText("? U")  # Soru işareti ile Untracked
            item.setBackground(QColor(200, 200, 200))  # Gri
            item.setToolTip("Untracked - Git tarafından takip edilmiyor")
        
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 5, item)  # Git durumu en sonda

        
    def setup_ui(self):
        """Kullanıcı arayüzünü oluşturur."""
        layout = QVBoxLayout(self)
        
        # Üst Bar
        top_bar = QHBoxLayout()
        
        # Dosya Arama
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Dosya ara... (En az 3 karakter)")
        self.search_box.textChanged.connect(self.filter_files)
        top_bar.addWidget(self.search_box)
        
        # Seçim Butonları Grubu için Container
        selection_buttons = QHBoxLayout()

         # Git Yenile Butonu
        refresh_btn = QPushButton("Git Durumunu Yenile")
        refresh_btn.clicked.connect(self.refresh_git_status)
        top_bar.addWidget(refresh_btn)
            
        # Arama Sonuçlarını Seç
        select_results_btn = QPushButton("Sonuçları Seç")
        select_results_btn.clicked.connect(lambda: self.toggle_search_results_selection(True))
        selection_buttons.addWidget(select_results_btn)
        
        # Arama Sonuçlarının Seçimini Kaldır
        deselect_results_btn = QPushButton("Sonuçların Seçimini Kaldır")
        deselect_results_btn.clicked.connect(lambda: self.toggle_search_results_selection(False))
        selection_buttons.addWidget(deselect_results_btn)
        
        # Tümünü Seç
        select_all_btn = QPushButton("Hepsini Seç")
        select_all_btn.clicked.connect(lambda: self.toggle_all_selection(True))
        selection_buttons.addWidget(select_all_btn)
        
        # Seçimi Temizle
        clear_btn = QPushButton("Seçimi Temizle")
        clear_btn.clicked.connect(lambda: self.toggle_all_selection(False))
        selection_buttons.addWidget(clear_btn)
        
        # Butonları ana layout'a ekle
        top_bar.addLayout(selection_buttons)
        layout.addLayout(top_bar)
        
        # Bilgi Etiketi
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: gray;")
        layout.addWidget(self.info_label)
        
        # Dosya Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["", "Dosya Adı", "Uzantı", "Klasör", "Boyut", "Git"]  # Git sütunu en sonda
        )
      # Tablo Ayarları
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Dosya adı
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Uzantı
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Klasör
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Boyut
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Git durumut
            
        self.table.setColumnWidth(0, 30)  # Checkbox
        self.table.setColumnWidth(2, 70)  # Uzantı
        self.table.setColumnWidth(4, 100)  # Boyut
        self.table.setColumnWidth(5, 40)  # Git durumu
        
        layout.addWidget(self.table)
        
        filter_group = QHBoxLayout()
    
        # Git filtre butonları
        self.filter_all = QRadioButton("Tümü")
        self.filter_modified = QRadioButton("Değişenler")
        self.filter_added = QRadioButton("Yeniler") 
        self.filter_deleted = QRadioButton("Silinenler")  # Eksik olan buton
        self.filter_untracked = QRadioButton("Takip Edilmeyenler")
        
        self.filter_all.setChecked(True)
        
        filter_group.addWidget(QLabel("Git Filtresi:"))
        filter_group.addWidget(self.filter_all)
        filter_group.addWidget(self.filter_modified)
        filter_group.addWidget(self.filter_added)
        filter_group.addWidget(self.filter_deleted)  # Yeni eklenen
        filter_group.addWidget(self.filter_untracked)
        
        # Signal bağlantıları
        self.filter_all.toggled.connect(self.apply_git_filter)
        self.filter_modified.toggled.connect(self.apply_git_filter)
        self.filter_added.toggled.connect(self.apply_git_filter)
        self.filter_deleted.toggled.connect(self.apply_git_filter)  # Yeni eklenen
        self.filter_untracked.toggled.connect(self.apply_git_filter)
        
        layout.addLayout(filter_group)
   
    def refresh_git_status(self):
        """Git durumunu manuel olarak yeniler."""
        if self.git_manager and self.current_directory:
            try:
                logging.info(f"Git durumu yenileniyor: {self.current_directory}")
                status = self.git_manager.check_changes(Path(self.current_directory))
                
                logging.info(f"Git durumu alındı: {status}")
                self.update_git_status(status)
                
                # Değişiklik sayılarını hesapla
                modified_count = sum(1 for s in status.values() if s == GitFileStatus.MODIFIED)
                added_count = sum(1 for s in status.values() if s == GitFileStatus.ADDED)
                deleted_count = sum(1 for s in status.values() if s == GitFileStatus.DELETED)
                
                status_info = (f"Git değişiklikleri: "
                            f"{modified_count} modified, "
                            f"{added_count} added, "
                            f"{deleted_count} deleted")
                logging.info(status_info)
                self.update_info_label(status_info)
                
            except GitException as e:
                logging.error(f"Git durumu alınamadı: {e}")
                self.update_info_label(f"Git hatası: {str(e)}")
    def format_size(self, size):
        """Dosya boyutunu formatlar."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def scan_directory(self, directory: str | Path):
        """Klasörü tarar ve dosyaları listeler."""
        
        # İlerleme Dialogu
        progress = QProgressDialog(
            "Dosyalar taranıyor...", "İptal", 0, 0, self
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        try:
            start_time = time.time()
            logging.info(f"Klasör taraması başlıyor: {directory}")
            if (Path(directory) / '.git').exists():
                logging.info("Git repository tespit edildi")  
            directory = Path(directory)
            self.current_directory = directory
           
            if self.git_manager:
                try:
                    status = self.git_manager.check_changes(self.current_directory)
                    self.update_git_status(status)
                except GitException as e:
                    logging.warning(f"Git durumu alınamadı: {e}")
            # Tabloyu temizle
            self.table.setRowCount(0)
            self.selected_files.clear()
            self.visible_rows.clear()
            
            # Desteklenen uzantılar
            valid_extensions = {'.cs', '.java', '.js', '.jsx', '.ts', '.tsx','.py'}
            skip_folders = {'.git', 'node_modules', 'bin', 'obj', 'build', 'dist'}
            
            # Dosyaları topla
            files_data = []
            
            for root, dirs, files in os.walk(str(directory)):
                # Atlanacak klasörleri filtrele
                dirs[:] = [d for d in dirs if d not in skip_folders and not d.startswith('.')]
                
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in valid_extensions:
                        try:
                            rel_path = file_path.relative_to(directory)
                            size = os.path.getsize(file_path)
                            
                            files_data.append({
                                'name': file_path.name,
                                'ext': file_path.suffix[1:].upper(),
                                'folder': str(rel_path.parent),
                                'size': size,
                                'path': str(file_path)
                            })
                            
                            # Her 100 dosyada bir ilerlemeyi güncelle
                            if len(files_data) % 100 == 0:
                                progress.setLabelText(f"{len(files_data)} dosya bulundu...")
                                QApplication.processEvents()
                                
                        except Exception as e:
                            print(f"Hata: {file_path} - {e}")
            
            # Tabloyu doldur
            self.table.setRowCount(len(files_data))
            for row, data in enumerate(files_data):
                # Checkbox
                   # Checkbox
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                self.table.setItem(row, 0, checkbox)
                
                # Dosya bilgileri (eski sıra)
                self.table.setItem(row, 1, QTableWidgetItem(data['name']))  # Dosya adı
                self.table.setItem(row, 2, QTableWidgetItem(data['ext']))   # Uzantı
                self.table.setItem(row, 3, QTableWidgetItem(data['folder'])) # Klasör
                self.table.setItem(row, 4, QTableWidgetItem(self.format_size(data['size']))) # Boyut
                
                # Git durumu sütununu en sona ekleyelim (yeni sütun)
                self.table.setItem(row, 5, QTableWidgetItem(""))  # Git durumu için boş hücre
                
                # Dosya yolunu gizli data olarak sakla (eski yerinde kalsın)
                self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, data['path'])
                
                # Her 1000 satırda bir UI'ı güncelle
                if row % 1000 == 0:
                    QApplication.processEvents()
            if self.git_manager and self.current_directory:
                try:
                    status = self.git_manager.check_changes(self.current_directory)
                    self.update_git_status(status)
                except GitException as e:
                    logging.warning(f"Git durumu alınamadı: {e}")        
            # İstatistikleri güncelle
            duration = time.time() - start_time
            self.total_files = len(files_data)
            self.update_info_label(f"Tarama süresi: {duration:.1f} saniye")
            
            # Tüm satırları görünür olarak işaretle
            self.visible_rows = set(range(self.total_files))
            
            # Sütunları otomatik boyutlandır
            self.table.resizeColumnsToContents()
            
        finally:
            progress.close()
            
        # Tablo sinyallerini bağla
        self.table.itemChanged.connect(self.on_item_changed)
    
    def filter_files(self, text: str):
        """Dosyaları filtreler."""
        search_text = text.lower().strip()
        self.visible_rows.clear()
        
        # 3 karakterden kısa aramaları ignore et
        if len(search_text) < 3:
            # Tüm satırları göster
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
                self.visible_rows.add(row)
            return
            
        # Her satırı kontrol et
        for row in range(self.table.rowCount()):
            file_name = self.table.item(row, 1).text().lower()
            folder = self.table.item(row, 3).text().lower()
            
            match = search_text in file_name or search_text in folder
            self.table.setRowHidden(row, not match)
            if match:
                self.visible_rows.add(row)
                
        # İstatistikleri güncelle
        self.update_info_label()
    
    def toggle_search_results_selection(self, select: bool):
        """Arama sonuçlarını seçer/seçimini kaldırır."""
        state = Qt.CheckState.Checked if select else Qt.CheckState.Unchecked
        
        # Sinyal bağlantısını geçici olarak kaldır
        self.table.itemChanged.disconnect(self.on_item_changed)
        
        # Sadece görünür satırların seçimini değiştir
        for row in self.visible_rows:
            item = self.table.item(row, 0)
            item.setCheckState(state)
            
            file_path = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            if select:
                self.selected_files.add(file_path)
            else:
                self.selected_files.discard(file_path)
        
        # Sinyal bağlantısını geri ekle
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Seçim değişikliğini bildir
        self.selection_changed.emit(list(self.selected_files))
        self.update_info_label()
    
    def toggle_all_selection(self, select: bool):
        """Tüm görünür öğeleri seçer/seçimi kaldırır."""
        state = Qt.CheckState.Checked if select else Qt.CheckState.Unchecked
        
        # Sinyal bağlantısını geçici olarak kaldır
        self.table.itemChanged.disconnect(self.on_item_changed)
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            item.setCheckState(state)
            
            file_path = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            if select:
                self.selected_files.add(file_path)
            else:
                self.selected_files.discard(file_path)
        
        # Sinyal bağlantısını geri ekle
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Seçim değişikliğini bildir
        self.selection_changed.emit(list(self.selected_files))
        self.update_info_label()
    
    def on_item_changed(self, item):
        """Öğe değişikliklerini işler."""
        if item.column() == 0:  # Checkbox sütunu
            row = item.row()
            file_path = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            
            if item.checkState() == Qt.CheckState.Checked:
                self.selected_files.add(file_path)
            else:
                self.selected_files.discard(file_path)
            
            self.selection_changed.emit(list(self.selected_files))
            self.update_info_label()
    
    def update_info_label(self, extra_info: str = ""):
        """Bilgi etiketini günceller."""
        visible_count = len(self.visible_rows) if self.visible_rows else self.table.rowCount()
        
        info_text = (f"Toplam: {self.total_files} dosya | "
                    f"Görünen: {visible_count} | "
                    f"Seçili: {len(self.selected_files)}")
                    
        if extra_info:
            info_text += f" | {extra_info}"
            
        self.info_label.setText(info_text)
    
    def get_selected_files(self) -> list:
        """Seçili dosya yollarını döndürür."""
        return list(self.selected_files)

    def apply_git_filter(self):
        """Git durumuna göre dosyaları filtreler"""
        self.visible_rows.clear()
        
        # Git durumlarını say
        status_counts = {
            GitFileStatus.MODIFIED: 0,
            GitFileStatus.ADDED: 0,
            GitFileStatus.DELETED: 0,
            GitFileStatus.UNTRACKED: 0
        }
        
        for row in range(self.table.rowCount()):
            file_path = Path(self.table.item(row, 1).data(Qt.ItemDataRole.UserRole))
            show_row = False
            
            if self.filter_all.isChecked():
                # Tümü seçiliyse her dosyayı göster
                show_row = True
            else:
                # Dosya Git durumuna sahipse ve ilgili filtre seçiliyse göster
                if file_path in self.git_status:
                    status = self.git_status[file_path]
                    if ((self.filter_modified.isChecked() and status == GitFileStatus.MODIFIED) or
                        (self.filter_added.isChecked() and status == GitFileStatus.ADDED) or
                        (self.filter_deleted.isChecked() and status == GitFileStatus.DELETED) or
                        (self.filter_untracked.isChecked() and status == GitFileStatus.UNTRACKED)):
                        show_row = True
            
            # Git durumlarını say
            if file_path in self.git_status:
                status = self.git_status[file_path]
                if status in status_counts:
                    status_counts[status] += 1
            
            # Satırı göster/gizle
            self.table.setRowHidden(row, not show_row)
            if show_row:
                self.visible_rows.add(row)
        
        # Filtre butonlarının etiketlerini güncelle
        self.filter_modified.setText(f"Değişenler ({status_counts[GitFileStatus.MODIFIED]})")
        self.filter_added.setText(f"Yeniler ({status_counts[GitFileStatus.ADDED]})")
        self.filter_deleted.setText(f"Silinenler ({status_counts[GitFileStatus.DELETED]})")
        self.filter_untracked.setText(f"Takip Edilmeyenler ({status_counts[GitFileStatus.UNTRACKED]})")
        
        # Bilgi etiketini güncelle
        self.update_info_label()