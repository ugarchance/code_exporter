import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from .git_repository import GitRepository
from .git_types import GitFileStatus, GitDiff
from .git_exceptions import *

class GitManager:
    """Git operasyonları yöneticisi."""
    
    def __init__(self):
        self.repositories: Dict[Path, GitRepository] = {}
        self.status_callbacks: List[Callable] = []
    
    def init_repository(self, path: Path) -> GitRepository:
        """Repository'yi başlat veya mevcut olanı getir."""
        if path not in self.repositories:
            try:
                repo = GitRepository(path)
                logging.info(f"Repository başarıyla başlatıldı: {path}")
                self.repositories[path] = repo
                return repo
            except GitException as e:
                raise GitInitError(f"Repository başlatılamadı: {str(e)}")
        return self.repositories[path]
    
    def get_repository(self, path: Path) -> Optional[GitRepository]:
        """Path için repository döndür."""
        return self.repositories.get(path)
    
    def watch_status(self, callback: Callable) -> None:
        """Durum değişikliklerini izle."""
        self.status_callbacks.append(callback)
    
    def check_changes(self, path: Path) -> Dict[Path, GitFileStatus]:
        """Değişiklikleri kontrol et."""
        logging.info(f"Git değişiklikleri kontrol ediliyor: {path}")

        # Repository'yi başlat veya mevcut olanı al
        repo = self.get_repository(path) or self.init_repository(path)
        
        if repo:
            try:
                # Git komutu çalıştırıp çıktıyı alalım
                logging.info("Git status komutu çalıştırılıyor...")
                import subprocess
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                        cwd=str(path), 
                                        capture_output=True, 
                                        text=True)
                logging.info(f"Git status çıktısı:\n{result.stdout}")
                
                changes = {}
                for line in result.stdout.splitlines():
                    if len(line) >= 3:  # En az "XY filename" formatında olmalı
                        status_code = line[:2].strip()  # Status kodu
                        file_path = Path(path) / line[3:].strip()  # Dosya yolu
                        
                        # Status kodunu analiz et
                        if status_code.startswith('M'):  # Modified
                            changes[file_path] = GitFileStatus.MODIFIED
                            logging.info(f"Modified dosya bulundu: {file_path}")
                        elif status_code.startswith('A'):  # Added
                            changes[file_path] = GitFileStatus.ADDED
                            logging.info(f"Added dosya bulundu: {file_path}")
                        elif status_code.startswith('D'):  # Deleted
                            changes[file_path] = GitFileStatus.DELETED
                            logging.info(f"Deleted dosya bulundu: {file_path}")
                        elif status_code.startswith('??'):  # Untracked
                            changes[file_path] = GitFileStatus.UNTRACKED
                            logging.info(f"Untracked dosya bulundu: {file_path}")
                
                logging.info(f"Toplam {len(changes)} değişiklik bulundu")
                return changes
                
            except Exception as e:
                logging.error(f"Git değişiklikleri kontrol edilirken hata: {e}")
                raise GitException(f"Git değişiklikleri kontrol edilemedi: {e}")
        return {}

    def get_file_diff(self, repo_path: Path, file_path: Path) -> Optional[GitDiff]:
        """Dosya diff'ini al."""
        repo = self.get_repository(repo_path)
        if repo:
            return repo.get_diff(file_path)
        return None