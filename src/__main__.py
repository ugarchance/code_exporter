#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
import logging
import argparse
from datetime import datetime

from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager

# Log yapılandırması
def setup_logging():
    """Loglama sistemini yapılandırır."""
    log_dir = Path.home() / '.code_exporter' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f'app_{datetime.now():%Y%m%d_%H%M%S}.log'
    
    # Root logger'ı yapılandır
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Formatlayıcı oluştur
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Dosya handler'ı
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Konsol handler'ı
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Handler'ları ekle
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Test log mesajı
    logging.info("Logging sistemi başlatıldı")
    logging.debug("Debug modu aktif")

def setup_dark_theme(app: QApplication) -> None:
    """Koyu tema renk şemasını ayarlar."""
    palette = QPalette()
    
    # Pencere arkaplanı
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    
    # Pencere metni
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    
    # Temel widget arkaplanı
    palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
    
    # Alternatif widget arkaplanı (örn: tablo satırları)
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
    
    # Araç ipucu arkaplanı
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
    
    # Araç ipucu metni
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    
    # Metin rengi
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    
    # Buton arkaplanı
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    
    # Buton metni
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    
    # Vurgu rengi
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    
    # Vurgulanan metin
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    # Devre dışı öğeler
    palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorGroup.Active,
                    QPalette.ColorRole.Text, QColor(128, 128, 128))
    palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorGroup.Active,
                    QPalette.ColorRole.ButtonText, QColor(128, 128, 128))
    
    # Paleti uygula
    app.setPalette(palette)

def parse_arguments():
    """Komut satırı argümanlarını işler."""
    parser = argparse.ArgumentParser(
        description='Kod dosyalarını dışa aktarma aracı'
    )
    
    parser.add_argument(
        '--dir',
        type=str,
        help='Başlangıçta taranacak klasör yolu'
    )
    
    parser.add_argument(
        '--theme',
        choices=['light', 'dark'],
        default='light',
        help='Uygulama teması (varsayılan: light)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Hata ayıklama modunu etkinleştirir'
    )
    
    return parser.parse_args()

def setup_exception_handler():
    """Global hata yakalayıcıyı ayarlar."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        logging.error("Beklenmeyen hata!", 
                     exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception

class CodeExporterApp:
    """Ana uygulama sınıfı."""
    
    def __init__(self, args):
        """
        Args:
            args: Komut satırı argümanları
        """
        self.args = args
        self.app = QApplication(sys.argv)
        self.setup_app()
        
        # Uygulama dizinlerini ayarla
        self.app_dir = Path.home() / '.code_exporter'
        self.app_dir.mkdir(parents=True, exist_ok=True)
        
        # Yapılandırma yöneticisini başlat
        self.config_manager = ConfigManager(self.app_dir)
        
        # Ana pencereyi oluştur
        self.main_window = MainWindow(self.config_manager)
        
        # Başlangıç klasörünü kontrol et
        self.check_initial_directory()
    
    def setup_app(self) -> None:
        """Uygulama ayarlarını yapılandırır."""
        # Organizasyon bilgilerini ayarla
        self.app.setOrganizationName("CodeExporter")
        self.app.setApplicationName("Code Exporter")
        
        # Tema ayarını kontrol et
        if self.args.theme == 'dark':
            setup_dark_theme(self.app)
        elif self.config_manager.get('dark_mode', False):
            setup_dark_theme(self.app)
        
        # Hata ayıklama modu
        if self.args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Hata ayıklama modu etkin")
    
    def check_initial_directory(self) -> None:
        """Başlangıç klasörünü kontrol eder ve gerekirse yükler."""
        initial_dir = None
        
        # Önce komut satırı argümanını kontrol et
        if self.args.dir:
            initial_dir = Path(self.args.dir)
            if not initial_dir.exists() or not initial_dir.is_dir():
                logging.warning(f"Belirtilen klasör bulunamadı: {initial_dir}")
                initial_dir = None
        
        # Komut satırında klasör belirtilmediyse son kullanılan klasörü dene
        if not initial_dir:
            last_dir = self.config_manager.get('last_directory')
            if last_dir and Path(last_dir).exists():
                initial_dir = Path(last_dir)
        
        # Başlangıç klasörü varsa yükle
        if initial_dir:
            try:
                logging.info(f"Başlangıç klasörü yükleniyor: {initial_dir}")
                self.main_window.open_directory(str(initial_dir))
            except Exception as e:
                logging.error(f"Başlangıç klasörü yüklenirken hata: {e}")
    
    def run(self) -> int:
        """
        Uygulamayı çalıştırır.
        
        Returns:
            int: Çıkış kodu
        """
        try:
            # Ana pencereyi göster
            self.main_window.show()
            
            # Uygulama döngüsünü başlat
            return self.app.exec()
            
        except Exception as e:
            logging.error(f"Uygulama çalıştırılırken hata: {e}")
            return 1
        
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Uygulama kapanırken temizlik işlemlerini yapar."""
        try:
            # Yapılandırmayı kaydet
            self.config_manager.save_config()
            
            # Log dosyalarını temizle (30 günden eski)
            self.cleanup_old_logs()
            
        except Exception as e:
            logging.error(f"Temizlik işlemleri sırasında hata: {e}")
    
    def cleanup_old_logs(self, days: int = 30) -> None:
        """Eski log dosyalarını temizler."""
        log_dir = self.app_dir / 'logs'
        if not log_dir.exists():
            return
            
        current_time = datetime.now()
        for log_file in log_dir.glob('app_*.log'):
            try:
                # Log dosyası tarihini al
                file_date_str = log_file.stem[4:12]  # "app_20240215_*.log"
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                
                # 30 günden eski ise sil
                if (current_time - file_date).days > days:
                    log_file.unlink()
                    logging.debug(f"Eski log dosyası silindi: {log_file}")
                    
            except Exception as e:
                logging.error(f"Log dosyası temizlenirken hata: {e}")

def main():
    """Uygulama başlangıç noktası."""
    # Log sistemini ayarla
    setup_logging()
    
    # Global hata yakalayıcıyı ayarla
    setup_exception_handler()
    
    try:
        # Komut satırı argümanlarını al
        args = parse_arguments()
        
        # Uygulamayı başlat
        app = CodeExporterApp(args)
        
        # Uygulamayı çalıştır ve çıkış kodunu döndür
        return app.run()
        
    except Exception as e:
        logging.error(f"Uygulama başlatılırken hata: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())