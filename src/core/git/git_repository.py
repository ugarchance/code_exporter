from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import git
import logging
from .git_types import GitFileStatus, GitDiff
from .git_exceptions import GitInitError, GitOperationError

@dataclass
class GitRepository:
   """Git repository wrapper sınıfı."""
   
   path: Path
   repo: Optional[git.Repo] = None
   
   def __post_init__(self):
       """Repository'yi başlat veya bağlan."""
       try:
           self.repo = git.Repo(self.path)
           logging.info(f"Git repository başarıyla açıldı: {self.path}")
       except git.exc.InvalidGitRepositoryError:
           raise GitInitError(f"Geçerli bir Git repository'si bulunamadı: {self.path}")
   
   def get_status(self) -> Dict[Path, GitFileStatus]:
       """Repository durumunu döndür."""
       try:
           status = {}
           if not self.repo:
               return status
               
           # Staged değişiklikleri kontrol et
           logging.info("Staged değişiklikler kontrol ediliyor...")
           diff_index = self.repo.index.diff('HEAD')
           for item in diff_index:
               file_path = Path(item.a_path)
               status[file_path] = self._convert_status(item)
               logging.debug(f"Staged değişiklik: {file_path} - {status[file_path]}")
               
           # Working directory değişiklikleri
           logging.info("Working directory değişiklikleri kontrol ediliyor...")
           diff_working = self.repo.index.diff(None)
           for item in diff_working:
               file_path = Path(item.a_path)
               status[file_path] = self._convert_status(item)
               logging.debug(f"Working değişiklik: {file_path} - {status[file_path]}")
               
           # Untracked dosyalar
           logging.info("Untracked dosyalar kontrol ediliyor...")
           for file_path in self.repo.untracked_files:
               status[Path(file_path)] = GitFileStatus.UNTRACKED
               logging.debug(f"Untracked dosya: {file_path}")
               
           logging.info(f"Repository durumu alındı: {len(status)} değişiklik")
           return status
           
       except Exception as e:
           logging.error(f"Repository durumu alınırken hata: {e}")
           raise GitOperationError(f"Durum alınamadı: {str(e)}")
   
   def get_diff(self, file_path: Path) -> GitDiff:
       """Belirli bir dosyanın diff'ini al."""
       try:
           # Diff işlemleri...
           logging.info(f"Diff alınıyor: {file_path}")
           if not self.repo:
               raise GitOperationError("Repository başlatılmamış")
               
           diff = self.repo.git.diff(file_path)
           logging.debug(f"Diff alındı: {len(diff)} karakter")
           return diff
           
       except Exception as e:
           logging.error(f"Diff alınırken hata: {e}")
           raise GitOperationError(f"Diff alınamadı: {str(e)}")
   
   def _convert_status(self, item) -> GitFileStatus:
       """Git durumunu internal duruma dönüştür."""
       try:
           if item.change_type == 'M':
               return GitFileStatus.MODIFIED
           elif item.change_type == 'A':
               return GitFileStatus.ADDED
           elif item.change_type == 'D':
               return GitFileStatus.DELETED
           elif item.change_type == 'R':
               return GitFileStatus.RENAMED
           elif item.change_type == 'C':
               return GitFileStatus.COPIED
           else:
               return GitFileStatus.UNMODIFIED
               
       except Exception as e:
           logging.error(f"Durum dönüştürme hatası: {e}")
           return GitFileStatus.UNMODIFIED