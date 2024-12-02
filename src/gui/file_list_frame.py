import logging
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QProgressDialog, QApplication,
                             QCheckBox, QRadioButton, QTreeWidget, QTreeWidgetItem, QButtonGroup, QStackedWidget)
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
        self.file_scanner = file_scanner
        self.git_manager = git_manager
        self.current_directory = None
        self.git_status = {}
        self.total_files = 0
        self.selected_files = set()
        self.visible_rows = set()
        self.setup_ui()

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
        
        # Görünüm Kontrolleri
        layout.addLayout(self._setup_view_controls())
        
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

        # Liste görünümü ayarları
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["", "Dosya Adı", "Uzantı", "Klasör", "Boyut", "Git"]
        )
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 40)

        # Klasör görünümü ayarları
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["Dosya/Klasör", "Boyut", "Git"])
        self.folder_tree.itemChanged.connect(self._on_tree_item_changed)

        # Stack widget oluştur ve görünümleri ekle
        self.stack_widget = QStackedWidget()
        self.stack_widget.addWidget(self.table)
        self.stack_widget.addWidget(self.folder_tree)
        
        # Stack widget'ı layout'a ekle
        layout.addWidget(self.stack_widget)

        # Git filtre grubu
        filter_group = QHBoxLayout()
        
        self.filter_all = QRadioButton("Tümü")
        self.filter_modified = QRadioButton("Değişenler")
        self.filter_added = QRadioButton("Yeniler")
        self.filter_deleted = QRadioButton("Silinenler")
        self.filter_untracked = QRadioButton("Takip Edilmeyenler")
        
        self.filter_all.setChecked(True)
        
        filter_group.addWidget(QLabel("Git Filtresi:"))
        filter_group.addWidget(self.filter_all)
        filter_group.addWidget(self.filter_modified)
        filter_group.addWidget(self.filter_added)
        filter_group.addWidget(self.filter_deleted)
        filter_group.addWidget(self.filter_untracked)
        
        # Signal bağlantıları
        self.filter_all.toggled.connect(self.apply_git_filter)
        self.filter_modified.toggled.connect(self.apply_git_filter)
        self.filter_added.toggled.connect(self.apply_git_filter)
        self.filter_deleted.toggled.connect(self.apply_git_filter)
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
            directory = Path(directory)
            self.current_directory = directory
            
            logging.info(f"Klasör taraması başlıyor: {directory}")
            
            # Git repository kontrolü
            if (directory / '.git').exists():
                logging.info("Git repository tespit edildi")
            
            # Tabloları temizle
            self.table.setRowCount(0)
            self.selected_files.clear()
            self.visible_rows.clear()
            
            # Desteklenen uzantılar
            valid_extensions = {'.cs', '.java', '.js', '.jsx', '.ts', '.tsx', '.py'}
            skip_folders = {'.git', 'node_modules', 'bin', 'obj', 'build', 'dist'}
            
            # Dosyaları topla
            files_data = []
            
            # Dosyaları tara ve topla
            for root, dirs, files in os.walk(str(directory)):
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
                            
                            if len(files_data) % 100 == 0:
                                progress.setLabelText(f"{len(files_data)} dosya bulundu...")
                                QApplication.processEvents()
                                
                        except Exception as e:
                            print(f"Hata: {file_path} - {e}")
            
            # Klasör yapısını oluştur
            self._current_folder_structure = self._build_folder_structure(files_data)
            
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
                self.table.setItem(row, 5, QTableWidgetItem(""))  # Git durumu için boş hücre
                
                # Dosya yolunu sakla
                self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, data['path'])
                self._add_file_to_table(row, data)
                if row % 1000 == 0:
                    QApplication.processEvents()
            
            # Git durumunu güncelle
            if self.git_manager:
                try:
                    status = self.git_manager.check_changes(self.current_directory)
                    self.update_git_status(status)
                except GitException as e:
                    logging.warning(f"Git durumu alınamadı: {e}")
            
            # Görünüm güncellemesi
            if self.list_view_btn.isChecked():
                self._update_list_view()
            else:
                self._update_folder_view()
            
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
            name_item = self.table.item(row, 1)
            if name_item is None:  # Güvenlik kontrolü
                return
                
            file_path = name_item.data(Qt.ItemDataRole.UserRole)
            if file_path is None:  # Güvenlik kontrolü
                return
                
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
                # Tümü seçiliyse her dosyay göster
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

    def _setup_view_controls(self):
        """Görünüm kontrol butonlarını oluşturur."""
        view_controls = QHBoxLayout()
        
        # Görünüm seçimi için radio butonlar
        self.view_buttons = QButtonGroup(self)
        self.list_view_btn = QRadioButton("Liste Görünümü")
        self.folder_view_btn = QRadioButton("Klasör Görünümü")
        self.list_view_btn.setChecked(True)  # Varsayılan görünüm
        
        self.view_buttons.addButton(self.list_view_btn)
        self.view_buttons.addButton(self.folder_view_btn)
        
        view_controls.addWidget(self.list_view_btn)
        view_controls.addWidget(self.folder_view_btn)
        view_controls.addStretch()
        
        # Görünüm değişikliği bağlantısı
        self.list_view_btn.toggled.connect(self._on_view_changed)
        
        return view_controls

    def _on_view_changed(self, checked):
        """Görünüm değişikliğini yönetir."""
        try:
            if checked:  # Liste görünümü
                self.stack_widget.setCurrentWidget(self.table)
                if hasattr(self, '_current_folder_structure'):
                    self._update_list_view()
            else:  # Klasör görünümü
                self.stack_widget.setCurrentWidget(self.folder_tree)
                if hasattr(self, '_current_folder_structure'):
                    self._update_folder_view()
                    
            # Geçiş sırasında seçimleri koru
            if self.selected_files:
                if checked:  # Liste görünümüne geçiş
                    self._restore_list_selections()
                else:  # Klasör görünümüne geçiş
                    self._restore_tree_selections()
        except Exception as e:
            logging.error(f"Görünüm değiştirme hatası: {str(e)}")
   
    def _restore_tree_selections(self):
        """Ağaç görünümünde seçimleri geri yükler."""
        def restore_item(item):
            for i in range(item.childCount()):
                child = item.child(i)
                file_path = child.data(0, Qt.ItemDataRole.UserRole)
                if file_path and file_path in self.selected_files:
                    child.setCheckState(0, Qt.CheckState.Checked)
                if child.childCount() > 0:
                    restore_item(child)
        
        root = self.folder_tree.invisibleRootItem()
        restore_item(root)

    def _restore_list_selections(self):
        """Liste görünümünde seçimleri geri yükler."""
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            if name_item:
                file_path = name_item.data(Qt.ItemDataRole.UserRole)
                if file_path in self.selected_files:
                    checkbox = self.table.item(row, 0)
                    if checkbox:
                        checkbox.setCheckState(Qt.CheckState.Checked)
    def switch_view(self, view_type: str):
        """Belirli bir görünüme geçer."""
        if view_type == 'list':
            self.list_view_btn.setChecked(True)
        else:
            self.folder_view_btn.setChecked(True)

    def _build_folder_structure(self, files_data):
        """Klasör yapısını oluşturur."""
        folder_structure = {}
        for file_data in files_data:
            folder_path = Path(file_data['folder'])
            current_dict = folder_structure
            
            # Klasör hiyerarşisini oluştur
            for part in folder_path.parts:
                if part not in current_dict:
                    current_dict[part] = {'files': [], 'subfolders': {}}
                current_dict = current_dict[part]['subfolders']
            
            # Dosyayı son klasöre ekle
            if folder_path.parts:
                target_dict = folder_structure
                for part in folder_path.parts[:-1]:
                    target_dict = target_dict[part]['subfolders']
                target_dict[folder_path.parts[-1]]['files'].append(file_data)
            else:
                folder_structure.setdefault('root', {'files': [], 'subfolders': {}})
                folder_structure['root']['files'].append(file_data)
        
        return folder_structure

    def _update_folder_view(self):
        """Klasör görünümünü günceller."""
        if not hasattr(self, '_current_folder_structure'):
            return
        
        self.folder_tree.clear()
        self._populate_folder_tree(self.folder_tree.invisibleRootItem(), 
                                self._current_folder_structure)

    def _populate_folder_tree(self, parent_item, folder_dict):
        """Klasör ağacını doldurur."""
        for folder_name, content in folder_dict.items():
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, folder_name)
            folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            folder_item.setCheckState(0, Qt.CheckState.Unchecked)
            
            # Klasördeki dosyaları ekle
            for file_data in content['files']:
                file_item = QTreeWidgetItem(folder_item)
                file_item.setText(0, file_data['name'])
                file_item.setText(1, self.format_size(file_data['size']))
                file_item.setData(0, Qt.ItemDataRole.UserRole, file_data['path'])
                file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                
                # Eğer dosya seçili dosyalar listesindeyse işaretle
                if file_data['path'] in self.selected_files:
                    file_item.setCheckState(0, Qt.CheckState.Checked)
                else:
                    file_item.setCheckState(0, Qt.CheckState.Unchecked)
                
                # Git durumunu ekle
                if Path(file_data['path']) in self.git_status:
                    self._set_tree_item_git_status(file_item, 
                                                self.git_status[Path(file_data['path'])])
            
            # Alt klasörleri işle
            self._populate_folder_tree(folder_item, content['subfolders'])
            
            # Klasör durumunu güncelle
            self._update_folder_check_state(folder_item)

    def _update_list_view(self):
        """Liste görünümünü günceller."""
        if not hasattr(self, '_current_folder_structure'):
            return
            
        # Tabloyu temizle
        self.table.setRowCount(0)
        self.selected_files.clear()
        
        # Dosyaları düz liste halinde topla
        files_data = []
        def collect_files(structure, path=""):
            for folder_name, content in structure.items():
                if folder_name != 'files':
                    for file_data in content.get('files', []):
                        files_data.append(file_data)
                    if 'subfolders' in content:
                        new_path = f"{path}/{folder_name}" if path else folder_name
                        collect_files(content['subfolders'], new_path)
        
        collect_files(self._current_folder_structure)
        
        # Tabloyu doldur
        self.table.setRowCount(len(files_data))
        for row, data in enumerate(files_data):
            self._add_file_to_table(row, data)

    def _set_tree_item_git_status(self, item: QTreeWidgetItem, status: GitFileStatus):
        """Ağaç görünümünde Git durumunu ayarlar."""
        if status == GitFileStatus.MODIFIED:
            item.setText(2, "✎ M")
            item.setBackground(2, QColor(255, 255, 150))
            item.setToolTip(2, "Modified - Dosya değiştirildi")
        elif status == GitFileStatus.ADDED:
            item.setText(2, "+ A")
            item.setBackground(2, QColor(150, 255, 150))
            item.setToolTip(2, "Added - Dosya eklendi")
        elif status == GitFileStatus.DELETED:
            item.setText(2, "- D")
            item.setBackground(2, QColor(255, 150, 150))
            item.setToolTip(2, "Deleted - Dosya silindi")
        elif status == GitFileStatus.UNTRACKED:
            item.setText(2, "? U")
            item.setBackground(2, QColor(200, 200, 200))
            item.setToolTip(2, "Untracked - Git tarafından takip edilmiyor")

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int):
        """Ağaç görünümünde öğe değişikliklerini işler."""
        if column == 0:  # Checkbox sütunu
            # Sinyal bağlantısını geçici olarak kaldır
            self.folder_tree.itemChanged.disconnect(self._on_tree_item_changed)
            
            is_checked = item.checkState(0) == Qt.CheckState.Checked
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            
            if not file_path:  # Klasör öğesi
                # Alt öğelerin tümünü işaretle/işareti kaldır
                self._set_children_check_state(item, is_checked)
            else:  # Dosya öğesi
                if is_checked:
                    self.selected_files.add(file_path)
                else:
                    self.selected_files.discard(file_path)
            
            # Üst klasörün durumunu kontrol et
            self._update_parent_check_state(item.parent())
            
            # Sinyal bağlantısını geri ekle
            self.folder_tree.itemChanged.connect(self._on_tree_item_changed)
            
            # Seçim değişikliğini bildir
            self.selection_changed.emit(list(self.selected_files))
            self.update_info_label()

    def _update_parent_check_state(self, parent_item: QTreeWidgetItem):
        """Üst klasörün işaret durumunu alt öğelere göre günceller."""
        if not parent_item:
            return
            
        child_count = parent_item.childCount()
        checked_count = 0
        partial_check = False
        
        for i in range(child_count):
            child = parent_item.child(i)
            if child.checkState(0) == Qt.CheckState.Checked:
                checked_count += 1
            elif child.checkState(0) == Qt.CheckState.PartiallyChecked:
                partial_check = True
                break
        
        if partial_check or (0 < checked_count < child_count):
            parent_item.setCheckState(0, Qt.CheckState.PartiallyChecked)
        elif checked_count == child_count:
            parent_item.setCheckState(0, Qt.CheckState.Checked)
        else:
            parent_item.setCheckState(0, Qt.CheckState.Unchecked)
            
        # Üst klasörleri de güncelle
        self._update_parent_check_state(parent_item.parent())

    def _update_tree_view(self):
        """Ağaç görünümünü günceller."""
        self.folder_tree.clear()
        
        # Git durumunu güncelle
        if self.git_manager and self.current_directory:
            try:
                status = self.git_manager.check_changes(self.current_directory)
                self.update_git_status(status)
            except GitException as e:
                logging.warning(f"Git durumu alınamadı: {e}")
        
        # Ağacı doldur
        self._populate_folder_tree(self.folder_tree.invisibleRootItem(), self._current_folder_structure)

    def _add_file_to_table(self, row: int, data: dict):
        """Tabloya dosya ekler."""
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
        self.table.setItem(row, 5, QTableWidgetItem(""))  # Git durumu için boş hücre
        
        # Dosya yolunu gizli data olarak sakla
        self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, data['path'])

    def _set_children_check_state(self, item: QTreeWidgetItem, checked: bool):
        """Alt öğelerin seçim durumunu ayarlar."""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            
            # Dosya yolunu al
            file_path = child.data(0, Qt.ItemDataRole.UserRole)
            if file_path:
                if checked:
                    self.selected_files.add(file_path)
                else:
                    self.selected_files.discard(file_path)
            
            # Alt klasörleri de işle
            if child.childCount() > 0:
                self._set_children_check_state(child, checked)

    def _update_folder_check_state(self, folder_item: QTreeWidgetItem):
        """Klasör öğesinin seçim durumunu alt öğelere göre günceller."""
        if folder_item is None:
            return
        
        child_count = folder_item.childCount()
        checked_count = 0
        
        for i in range(child_count):
            child = folder_item.child(i)
            if child.checkState(0) == Qt.CheckState.Checked:
                checked_count += 1
        
        if checked_count == child_count:
            folder_item.setCheckState(0, Qt.CheckState.Checked)
        elif checked_count == 0:
            folder_item.setCheckState(0, Qt.CheckState.Unchecked)
        else:
            folder_item.setCheckState(0, Qt.CheckState.PartiallyChecked)