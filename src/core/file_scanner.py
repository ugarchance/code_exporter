import os
from pathlib import Path
from typing import List, Set, Generator, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
from queue import Queue
import logging
from ..models.file_info import FileInfo


class FileScanner:
    """Dosya sistemi tarama ve filtreleme işlemlerini yöneten sınıf."""
    
    def __init__(self, config_manager=None, extension_manager=None):
        self._scanned_files: List[FileInfo] = []
        self._excluded_dirs: Set[str] = {'.git', 'node_modules', 'bin', 'obj', 'build', 'dist'}
        self._lock = Lock()
        self._file_queue = Queue(maxsize=1000)
        self._processed_count = 0
        self._total_files = 0
        self.config_manager = config_manager

        from .extension_manager import ExtensionManager
        if extension_manager is None:
            exts = None
            if self.config_manager:
                exts = self.config_manager.get('supported_extensions', None)
            self.extension_manager = ExtensionManager(exts)
        else:
            self.extension_manager = extension_manager
    
    def refresh_extensions(self):
        """Desteklenen uzantıları yeniden yükler."""
        exts = None
        if self.config_manager:
            exts = self.config_manager.get('supported_extensions', None)
        self.extension_manager = type(self.extension_manager)(exts)
        
    @property
    def scanned_files(self) -> List[FileInfo]:
        """Taranan dosyaların listesini döndürür."""
        return self._scanned_files
    
    def _should_skip_directory(self, dir_name: str) -> bool:
        """Klasörün atlanıp atlanmayacağını kontrol eder."""
        return dir_name.startswith('.') or dir_name in self._excluded_dirs
    

    def _is_supported_file(self, file_path: Path) -> bool:
        """Dosyanın desteklenen bir uzantıya sahip olup olmadığını kontrol eder."""
        return self.extension_manager.is_supported(file_path.suffix)
    
    def _scan_directory_fast(self, directory: Path) -> None:
        """Verilen klasörü ve alt klasörlerini hızlı bir şekilde tarar."""
        try:
            for entry in os.scandir(directory):
                try:
                    if entry.is_file():
                        # Dosya uzantısını kontrol et
                        if self._is_supported_file(Path(entry.name)):
                            self._file_queue.put(entry.path)
                            self._total_files += 1
                    elif entry.is_dir() and not self._should_skip_directory(entry.name):
                        # Alt klasörleri tara
                        self._scan_directory_fast(Path(entry.path))
                except PermissionError:
                    continue
        except PermissionError:
            logging.warning(f"Erişim hatası: {directory}")
        except Exception as e:
            logging.error(f"Tarama hatası ({directory}): {str(e)}")
    
    def _process_file(self, file_path: str) -> FileInfo:
        """Dosya bilgilerini işler."""
        return FileInfo.from_path(file_path)
    
    def _process_files_batch(self, file_paths: List[str]) -> List[FileInfo]:
        """Dosya grubunu işler."""
        return [self._process_file(fp) for fp in file_paths]
    
    def scan(self, root_directory: str | Path, 
             max_workers: int = 4, 
             batch_size: int = 50,
             progress_callback=None) -> List[FileInfo]:
        """
        Belirtilen klasörü tarar ve desteklenen dosyaları bulur.
        
        Args:
            root_directory: Taranacak ana klasör
            max_workers: Paralel işlem sayısı
            batch_size: Her seferde işlenecek dosya sayısı
            progress_callback: İlerleme durumu için geri çağırım fonksiyonu
            
        Returns:
            List[FileInfo]: Bulunan dosyaların listesi
        """
        root_path = Path(root_directory)
        if not root_path.exists() or not root_path.is_dir():
            raise ValueError(f"Geçersiz klasör yolu: {root_directory}")
        
        # Önceki tarama sonuçlarını temizle
        self._scanned_files.clear()
        self._processed_count = 0
        self._total_files = 0
        
        # Dosyaları bul (hızlı tarama)
        self._scan_directory_fast(root_path)
        total_files = self._total_files
        
        # İşlenecek dosyaları grupla
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            current_batch = []
            
            while not self._file_queue.empty() or current_batch:
                # Batch'i doldur
                while len(current_batch) < batch_size and not self._file_queue.empty():
                    try:
                        current_batch.append(self._file_queue.get_nowait())
                    except:
                        break
                
                # Batch işlemeye gönder
                if current_batch:
                    futures.append(executor.submit(self._process_files_batch, current_batch))
                    current_batch = []
                
                # Tamamlanan işlemleri kontrol et
                completed = []
                for future in list(futures):
                    if future.done():
                        try:
                            results = future.result()
                            with self._lock:
                                self._scanned_files.extend(results)
                                self._processed_count += len(results)
                                
                                # İlerleme durumunu bildir
                                if progress_callback and total_files > 0:
                                    progress = (self._processed_count / total_files) * 100
                                    progress_callback(progress)
                                    
                            futures.remove(future)
                        except Exception as e:
                            logging.error(f"Dosya işleme hatası: {str(e)}")
                            futures.remove(future)
                
                # Kısa bir bekleme ile CPU kullanımını azalt
                if not self._file_queue.empty():
                    time.sleep(0.001)
        
        return self._scanned_files
    
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
    
    def get_file_by_path(self, file_path: str | Path) -> FileInfo | None:
        """Belirtilen yoldaki dosyayı bulur."""
        path_str = str(Path(file_path))
        for file_info in self._scanned_files:
            if str(file_info.path) == path_str:
                return file_info
        return None
    
    def select_all(self, selected: bool = True) -> None:
        """Tüm dosyaları seçer veya seçimi kaldırır."""
        for file_info in self._scanned_files:
            file_info.is_selected = selected
    
    def get_selected_files(self) -> List[FileInfo]:
        """Seçili dosyaları döndürür."""
        return [f for f in self._scanned_files if f.is_selected]
