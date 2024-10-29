from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QProgressDialog, QApplication,
                             QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import os
from pathlib import Path
import time

class FileListFrame(QFrame):
    """Basitleştirilmiş dosya listesi görünümü."""
    
    # Seçili dosyalar sinyali
    selection_changed = pyqtSignal(list)
    
    def __init__(self, file_scanner=None):
        super().__init__()
        self.file_scanner = file_scanner  # file_scanner'ı sakla
        self.total_files = 0
        self.selected_files = set()
        self.visible_rows = set()  # Görünür satırları takip etmek için
        self.setup_ui()

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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Dosya Adı", "Uzantı", "Klasör", "Boyut"])
        
        # Tablo Ayarları
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Dosya
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Uzantı
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Klasör
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Boyut
        
        self.table.setColumnWidth(0, 30)  # Checkbox
        self.table.setColumnWidth(2, 70)  # Uzantı
        self.table.setColumnWidth(4, 100)  # Boyut
        
        # Tablo Performans Ayarları
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
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
            directory = Path(directory)
            self.current_directory = directory
            
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
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                self.table.setItem(row, 0, checkbox)
                
                # Dosya bilgileri
                self.table.setItem(row, 1, QTableWidgetItem(data['name']))
                self.table.setItem(row, 2, QTableWidgetItem(data['ext']))
                self.table.setItem(row, 3, QTableWidgetItem(data['folder']))
                self.table.setItem(row, 4, QTableWidgetItem(self.format_size(data['size'])))
                
                # Dosya yolunu gizli data olarak sakla
                self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, data['path'])
                
                # Her 1000 satırda bir UI'ı güncelle
                if row % 1000 == 0:
                    QApplication.processEvents()
            
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