import requests
import json
import os
from pathlib import Path
import logging
from packaging import version
import sys
import subprocess
from typing import Optional, Tuple

class AutoUpdater:
    def __init__(self, github_repo: str, current_version: str):
        self.github_repo = github_repo
        self.current_version = current_version
        self.github_api = f"https://api.github.com/repos/{github_repo}/releases/latest"
        
    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Güncellemeleri kontrol eder.
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
            (güncelleme_var_mı, yeni_sürüm, indirme_linki)
        """
        try:
            response = requests.get(self.github_api)
            response.raise_for_status()
            
            latest_release = response.json()
            latest_version = latest_release['tag_name'].lstrip('v')
            
            if version.parse(latest_version) > version.parse(self.current_version):
                # Windows için exe dosyasını bul
                for asset in latest_release['assets']:
                    if asset['name'].endswith('.exe'):
                        return True, latest_version, asset['browser_download_url']
                        
            return False, None, None
            
        except Exception as e:
            logging.error(f"Güncelleme kontrolü başarısız: {e}")
            return False, None, None
            
    def download_and_install_update(self, download_url: str) -> bool:
        """Güncellemeyi indirir ve yükler."""
        try:
            # Geçici dizini oluştur
            temp_dir = Path.home() / '.code_exporter' / 'updates'
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Yeni exe'yi indir
            new_exe_path = temp_dir / 'CodeExporter_new.exe'
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Güncelleme betiği oluştur
            update_script = temp_dir / 'update.bat'
            current_exe = sys.executable
            
            with open(update_script, 'w') as f:
                f.write(f'''@echo off
timeout /t 2 /nobreak
del "{current_exe}"
move "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
''')
            
            # Güncelleme betiğini çalıştır
            subprocess.Popen([update_script], shell=True)
            sys.exit(0)
            
            return True
            
        except Exception as e:
            logging.error(f"Güncelleme yüklenirken hata: {e}")
            return False 