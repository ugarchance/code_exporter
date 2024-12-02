from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QFont, QBrush, QPen
import os
import logging
import random

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        self.setFixedSize(600, 400)  # Sabit boyut
        
        # Timer'ı baştan oluştur
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_opacity)
        self.opacity = 0.0
        self.fade_in = True
        
        # Animasyon için değişkenler
        self.angle = 0
        self.lines = []
        for _ in range(5):
            self.lines.append({
                'x': random.randint(0, 600),
                'y': random.randint(0, 400),
                'length': random.randint(50, 150),
                'speed': random.randint(2, 5)
            })
        
        # Logo dosyasının yolunu belirle
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                "resources", "icons", "added.png")
        
        # Ana pixmap'i oluştur
        self.base_pixmap = QPixmap(600, 400)
        self.base_pixmap.fill(Qt.GlobalColor.transparent)
        
        # Logo pixmap'ini yükle
        if os.path.exists(logo_path):
            self.logo = QPixmap(logo_path)
            if self.logo.isNull():
                self.logo = None
        else:
            self.logo = None
            
        # Efekt timer'ı
        self.effect_timer = QTimer()
        self.effect_timer.timeout.connect(self.update_effects)
        self.effect_timer.start(50)
        
        # Pencereyi yarı saydam yap
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | 
                          Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(0.0)
        
    def update_effects(self):
        self.angle = (self.angle + 2) % 360
        
        # Arka planı güncelle
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Siyah arka plan
        painter.fillRect(0, 0, 600, 400, QColor(0, 0, 0))
        
        # Neon çizgiler
        for line in self.lines:
            pen = QPen(QColor(0, 255, 255, 100))  # Siber mavi
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(line['x'], line['y'], 
                           line['x'] + line['length'], line['y'])
            
            # Çizgileri hareket ettir
            line['x'] -= line['speed']
            if line['x'] + line['length'] < 0:
                line['x'] = 600
                line['y'] = random.randint(0, 400)
        
        # Grid efekti
        pen = QPen(QColor(0, 255, 255, 30))
        pen.setWidth(1)
        painter.setPen(pen)
        for i in range(0, 600, 30):
            painter.drawLine(i, 0, i, 400)
        for i in range(0, 400, 30):
            painter.drawLine(0, i, 600, i)
        
        # Logo ekle
        if self.logo:
            scaled_logo = self.logo.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
            logo_x = (600 - scaled_logo.width()) // 2
            logo_y = (400 - scaled_logo.height()) // 2
            
            # Logo'nun etrafına neon efekti
            glow = QPen(QColor(0, 255, 255, 50))
            glow.setWidth(10)
            painter.setPen(glow)
            painter.drawRect(logo_x-5, logo_y-5, 
                           scaled_logo.width()+10, scaled_logo.height()+10)
            
            painter.drawPixmap(logo_x, logo_y, scaled_logo)
        
        # Fütüristik yazı
        font = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Neon yazı efekti
        glow = QPen(QColor(0, 255, 255, 100))
        painter.setPen(glow)
        painter.drawText(QRect(0, 300, 600, 50), 
                        Qt.AlignmentFlag.AlignCenter, 
                        "CODE EXPORTER")
        
        painter.end()
        self.setPixmap(pixmap)
        
    def update_opacity(self):
        if self.fade_in:
            self.opacity += 0.05
            if self.opacity >= 1.0:
                self.opacity = 1.0
                self.fade_in = False
        else:
            self.opacity -= 0.05
            if self.opacity <= 0.0:
                self.opacity = 0.0
                self.timer.stop()
                self.effect_timer.stop()
                self.close()
                
        self.setWindowOpacity(self.opacity)
    
    def start_animation(self):
        self.show()
        self.timer.start(50)  # Her 50ms'de bir güncelle