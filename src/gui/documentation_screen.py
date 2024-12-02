from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTextEdit, QComboBox, QLabel, QProgressBar, QMessageBox,
                               QTreeView, QSplitter, QFileDialog, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDir
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from .markdown_viewer import MarkdownViewer
import google.generativeai as genai
import os
import time
from typing import List, Dict, Any
import ast
import re
from datetime import datetime

class FileSystemModel(QStandardItemModel):
    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = root_path
        self.setHorizontalHeaderLabels(['Dosya/Klasör'])
        self.refresh()
        
    def refresh(self):
        self.clear()
        self.setHorizontalHeaderLabels(['Dosya/Klasör'])
        root_item = self.invisibleRootItem()
        self._populate_model(self.root_path, root_item)
        
    def _populate_model(self, path: str, parent_item: QStandardItem):
        dir_items = []
        file_items = []
        
        for entry in os.scandir(path):
            if entry.name.startswith('.'):
                continue
                
            item = QStandardItem(entry.name)
            item.setData(entry.path, Qt.ItemDataRole.UserRole)
            
            if entry.is_dir():
                self._populate_model(entry.path, item)
                dir_items.append(item)
            else:
                # Sadece desteklenen uzantılara sahip dosyaları göster
                if any(entry.name.endswith(ext) for ext in SupportedLanguages.get_all_extensions()):
                    file_items.append(item)
        
        # Önce klasörleri, sonra dosyaları ekle (alfabetik sıralı)
        for item in sorted(dir_items, key=lambda x: x.text().lower()):
            parent_item.appendRow(item)
        for item in sorted(file_items, key=lambda x: x.text().lower()):
            parent_item.appendRow(item)

class SupportedLanguages:
    LANGUAGES = {
        'Python': {
            'extensions': ['.py', '.pyw'],
            'comment': '#',
            'method_patterns': [
                r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]'
            ]
        },
        'JavaScript': {
            'extensions': ['.js', '.jsx', '.ts', '.tsx'],
            'comment': '//',
            'method_patterns': [
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*function\s*\(',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*function\s*\(',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\([^)]*\)\s*=>'
            ]
        },
        'Java': {
            'extensions': ['.java'],
            'comment': '//',
            'method_patterns': [
                r'(public|private|protected|static|\s) +[\w\<\>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^\)]*\)\s*\{'
            ]
        },
        'C#': {
            'extensions': ['.cs'],
            'comment': '//',
            'method_patterns': [
                r'(public|private|protected|static|\s) +[\w\<\>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^\)]*\)\s*\{'
            ]
        },
        'PHP': {
            'extensions': ['.php'],
            'comment': '//',
            'method_patterns': [
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'public|private|protected\s+function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            ]
        },
        'Ruby': {
            'extensions': ['.rb'],
            'comment': '#',
            'method_patterns': [
                r'def\s+([a-zA-Z_][a-zA-Z0-9_?!]*)'
            ]
        },
        'Go': {
            'extensions': ['.go'],
            'comment': '//',
            'method_patterns': [
                r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            ]
        }
    }

    @classmethod
    def get_all_extensions(cls) -> List[str]:
        extensions = []
        for lang in cls.LANGUAGES.values():
            extensions.extend(lang['extensions'])
        return extensions

    @classmethod
    def get_language_by_extension(cls, file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        for lang_name, lang_info in cls.LANGUAGES.items():
            if ext in lang_info['extensions']:
                return {'name': lang_name, **lang_info}
        return None

class MethodExtractor:
    @staticmethod
    def extract_methods(content: str, language: str) -> List[Dict[str, Any]]:
        if language == 'Python':
            return MethodExtractor._extract_python_methods(content)
        elif language in ['JavaScript', 'TypeScript']:
            return MethodExtractor._extract_js_methods(content)
        elif language in ['Java', 'C#']:
            return MethodExtractor._extract_java_like_methods(content)
        else:
            return MethodExtractor._extract_generic_methods(content)

    @staticmethod
    def _extract_python_methods(content: str) -> List[Dict[str, Any]]:
        methods = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method = {
                        'name': node.name,
                        'start': node.lineno,
                        'end': node.end_lineno,
                        'type': 'async_function' if isinstance(node, ast.AsyncFunctionDef) else 'function',
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [ast.unparse(d) for d in node.decorator_list]
                    }
                    methods.append(method)
                elif isinstance(node, ast.ClassDef):
                    method = {
                        'name': node.name,
                        'start': node.lineno,
                        'end': node.end_lineno,
                        'type': 'class',
                        'methods': []
                    }
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            class_method = {
                                'name': f"{node.name}.{item.name}",
                                'start': item.lineno,
                                'end': item.end_lineno,
                                'type': 'method',
                                'args': [arg.arg for arg in item.args.args],
                                'decorators': [ast.unparse(d) for d in item.decorator_list]
                            }
                            method['methods'].append(class_method)
                    methods.append(method)
        except Exception as e:
            print(f"Python metod çıkarma hatası: {str(e)}")
        return methods

    @staticmethod
    def _extract_js_methods(content: str) -> List[Dict[str, Any]]:
        methods = []
        patterns = [
            # Normal fonksiyonlar
            r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\((.*?)\)',
            # Ok fonksiyonları
            r'(?:const|let|var)?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:\(.*?\)|[^=]*?)\s*=>\s*{',
            # Sınıf metodları
            r'(?:async\s+)?(?:static\s+)?([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\((.*?)\)\s*{',
            # Getter/Setter
            r'(?:get|set)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\((.*?)\)\s*{'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                method = {
                    'name': match.group(1),
                    'start': content.count('\n', 0, match.start()) + 1,
                    'end': content.count('\n', 0, match.end()) + 1,
                    'type': 'function',
                    'args': [arg.strip() for arg in (match.group(2).split(',') if len(match.groups()) > 1 else [])]
                }
                methods.append(method)
        return methods

    @staticmethod
    def _extract_java_like_methods(content: str) -> List[Dict[str, Any]]:
        methods = []
        pattern = r'(?:public|private|protected|static|\s) +[\w\<\>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^\)]*)\)\s*(?:throws\s+[\w\s,]+\s*)?{'
        
        matches = re.finditer(pattern, content)
        for match in matches:
            method = {
                'name': match.group(1),
                'start': content.count('\n', 0, match.start()) + 1,
                'end': content.count('\n', 0, match.end()) + 1,
                'type': 'method',
                'args': [arg.strip().split()[-1] for arg in match.group(2).split(',') if arg.strip()]
            }
            methods.append(method)
        return methods

    @staticmethod
    def _extract_generic_methods(content: str) -> List[Dict[str, Any]]:
        methods = []
        # Genel metod kalıpları
        patterns = [
            r'(?:function|func|def|method|procedure)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^\)]*)\)',
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*function\s*\(([^\)]*)\)',
            r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*function\s*\(([^\)]*)\)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                method = {
                    'name': match.group(1),
                    'start': content.count('\n', 0, match.start()) + 1,
                    'end': content.count('\n', 0, match.end()) + 1,
                    'type': 'function',
                    'args': [arg.strip() for arg in match.group(2).split(',') if arg.strip()]
                }
                methods.append(method)
        return methods

class DocumentationGenerator(QThread):
    progress_updated = pyqtSignal(int)
    documentation_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key: str, code_content: str, mode: str, language: str = None):
        super().__init__()
        self.api_key = api_key
        self.code_content = code_content
        self.mode = mode
        self.language = language
        self.rate_limit_delay = 1

    def run(self):
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""Lütfen aşağıdaki {self.language if self.language else ''} kodunu analiz ederek teknik dokümantasyon oluştur:
            
            {self.code_content}
            
            Lütfen şu başlıkları içeren bir dokümantasyon oluştur:
            1. Genel Bakış
            2. Metodlar ve Fonksiyonlar
            3. Parametreler ve Dönüş Değerleri
            4. Kullanım Örnekleri
            5. Önemli Notlar
            """
            
            response = model.generate_content(prompt)
            self.documentation_ready.emit(response.text)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class DocumentationScreen(QWidget):
    def __init__(self, project_path=None):
        super().__init__()
        self.api_key = ""
        self.project_path = project_path or os.getcwd()
        if not os.path.exists(self.project_path):
            self.project_path = os.getcwd()
        
        self.selected_methods = []
        self.current_language = None
        self.current_documentation = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Ana stil
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTreeView {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 5px;
            }
            QTreeView::item {
                padding: 5px;
                border-radius: 3px;
            }
            QTreeView::item:hover {
                background-color: #353535;
            }
            QTreeView::item:selected {
                background-color: #2d5a88;
            }
            QComboBox {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 5px;
                min-height: 25px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down-arrow.png);
            }
            QTextEdit {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 5px;
                selection-background-color: #2d5a88;
            }
            QPushButton {
                background-color: #2d5a88;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #366ba2;
            }
            QPushButton:pressed {
                background-color: #244b73;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: bold;
            }
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #252525;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2d5a88;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                background-color: #252525;
            }
            QTabBar::tab {
                background-color: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #252525;
                border-bottom: 2px solid #2d5a88;
            }
            QTabBar::tab:hover {
                background-color: #303030;
            }
            QSplitter::handle {
                background-color: #3a3a3a;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #252525;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        # API Ayarları
        api_layout = QHBoxLayout()
        api_label = QLabel("API Anahtarı")
        self.api_input = QTextEdit()
        self.api_input.setMaximumHeight(35)
        self.api_input.setPlaceholderText("Gemini API anahtarınızı buraya girin...")
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_input)
        main_layout.addLayout(api_layout)
        
        # Ana içerik bölümü
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(1)
        
        # Sol panel - Dosya gezgini
        file_panel = QWidget()
        file_layout = QVBoxLayout(file_panel)
        file_layout.setContentsMargins(0, 0, 0, 0)
        
        file_header = QLabel("📁 Dosya Gezgini")
        file_layout.addWidget(file_header)
        
        self.file_tree = QTreeView()
        self.file_model = FileSystemModel(self.project_path)
        self.file_tree.setModel(self.file_model)
        self.file_tree.clicked.connect(self.on_file_selected)
        self.file_tree.setHeaderHidden(True)
        file_layout.addWidget(self.file_tree)
        
        # Orta panel - Metod listesi
        method_panel = QWidget()
        method_layout = QVBoxLayout(method_panel)
        method_layout.setContentsMargins(5, 0, 5, 0)
        
        self.language_label = QLabel("💻 Dil: -")
        method_layout.addWidget(self.language_label)
        
        method_header = QLabel("🔧 Metodlar")
        method_layout.addWidget(method_header)
        
        self.method_combo = QComboBox()
        self.method_combo.currentTextChanged.connect(self.on_method_selected)
        method_layout.addWidget(self.method_combo)
        
        # Sağ panel - Kod ve çıktı
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Dokümantasyon Modu
        mode_layout = QHBoxLayout()
        mode_label = QLabel("🎯 Mod:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Metod Bazlı", "Dosya Bazlı", "Klasör Bazlı"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        right_layout.addLayout(mode_layout)
        
        # Kod Görüntüleme
        code_header = QLabel("📝 Kod")
        right_layout.addWidget(code_header)
        
        self.code_display = QTextEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setPlaceholderText("Seçilen kod burada görüntülenecek...")
        right_layout.addWidget(self.code_display)
        
        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setTextVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # Dokümantasyon çıktısı
        doc_header = QLabel("📄 Dokümantasyon")
        right_layout.addWidget(doc_header)
        
        self.output_tabs = QTabWidget()
        self.markdown_viewer = MarkdownViewer()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        
        self.output_tabs.addTab(self.markdown_viewer, "✨ Markdown")
        self.output_tabs.addTab(self.output_text, "📝 Düz Metin")
        right_layout.addWidget(self.output_tabs)
        
        # Panelleri splitter'a ekle
        content_splitter.addWidget(file_panel)
        content_splitter.addWidget(method_panel)
        content_splitter.addWidget(right_panel)
        
        # Splitter boyutlarını ayarla
        content_splitter.setSizes([200, 150, 450])
        main_layout.addWidget(content_splitter)
        
        # Kontrol butonları
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        self.generate_btn = QPushButton("✨ Dokümantasyon Oluştur")
        self.generate_btn.clicked.connect(self.generate_documentation)
        
        self.save_md_btn = QPushButton("💾 Markdown Kaydet")
        self.save_md_btn.clicked.connect(self.save_as_markdown)
        self.save_md_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("🗑️ Temizle")
        self.clear_btn.clicked.connect(self.clear_all)
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.save_md_btn)
        button_layout.addWidget(self.clear_btn)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        self.setWindowTitle("✨ Teknik Dokümantasyon Oluşturucu")
        self.resize(1200, 800)

    def on_file_selected(self, index):
        file_path = self.file_model.data(index, Qt.ItemDataRole.UserRole)
        if not file_path:
            return
            
        language_info = SupportedLanguages.get_language_by_extension(file_path)
        if language_info:
            self.current_file = file_path
            self.current_language = language_info['name']
            self.language_label.setText(f"💻 Dil: {self.current_language}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.code_display.setPlainText(content)
                
                # Metodları çıkar ve combo box'a ekle
                methods = MethodExtractor.extract_methods(content, self.current_language)
                self.method_combo.clear()
                
                for method in methods:
                    if method['type'] == 'class':
                        self.method_combo.addItem(f"📦 {method['name']} (Sınıf)")
                        for class_method in method['methods']:
                            self.method_combo.addItem(f"  🔧 {class_method['name']}")
                    else:
                        self.method_combo.addItem(f"⚡ {method['name']}")

    def on_method_selected(self, method_text):
        if not method_text:
            return
            
        # Metod adını temizle
        method_name = method_text.split()[-1].replace('(Sınıf)', '').strip()
        if method_name.startswith('🔧'):
            method_name = method_name[2:].strip()
        elif method_name.startswith('⚡'):
            method_name = method_name[2:].strip()
        elif method_name.startswith('📦'):
            method_name = method_name[2:].strip()
            
        with open(self.current_file, 'r', encoding='utf-8') as f:
            content = f.read()
            methods = MethodExtractor.extract_methods(content, self.current_language)
            
            # Metodu bul
            selected_method = None
            for method in methods:
                if method['name'] == method_name:
                    selected_method = method
                    break
                elif method['type'] == 'class':
                    for class_method in method['methods']:
                        if class_method['name'] == method_name:
                            selected_method = class_method
                            break
            
            if selected_method:
                lines = content.split('\n')
                method_code = '\n'.join(lines[selected_method['start']-1:selected_method['end']])
                self.code_display.setPlainText(method_code)

    def save_as_markdown(self):
        if not self.current_documentation:
            QMessageBox.warning(self, "Hata", "Önce dokümantasyon oluşturmalısınız.")
            return
            
        file_name = f"documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Markdown Olarak Kaydet",
            os.path.join(os.getcwd(), file_name),
            "Markdown Dosyaları (*.md)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Başlık ve meta bilgileri ekle
                    header = f"""# Teknik Dokümantasyon

Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Dil: {self.current_language if self.current_language else 'Belirtilmemiş'}
Mod: {self.mode_combo.currentText()}

"""
                    f.write(header + self.current_documentation)
                    
                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Dokümantasyon başarıyla kaydedildi:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Dokümantasyon kaydedilirken hata oluştu:\n{str(e)}"
                )

    def show_documentation(self, text):
        self.current_documentation = text
        self.output_text.setPlainText(text)
        self.markdown_viewer.set_markdown(text)
        self.generate_btn.setEnabled(True)
        self.save_md_btn.setEnabled(True)
        self.progress_bar.setValue(100)

    def on_mode_changed(self, mode):
        if mode == "Metod Bazlı":
            self.method_combo.setEnabled(True)
        else:
            self.method_combo.setEnabled(False)
            if hasattr(self, 'current_file'):
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    self.code_display.setPlainText(f.read())

    def generate_documentation(self):
        if not self.api_input.toPlainText().strip():
            QMessageBox.warning(self, "Hata", "Lütfen Gemini API anahtarını girin.")
            return
            
        mode = self.mode_combo.currentText()
        code_content = ""
        
        if mode == "Metod Bazlı":
            code_content = self.code_display.toPlainText()
        elif mode == "Dosya Bazlı":
            if hasattr(self, 'current_file'):
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    code_content = f.read()
        elif mode == "Klasör Bazlı":
            selected_index = self.file_tree.currentIndex()
            if selected_index.isValid():
                folder_path = self.file_model.filePath(selected_index)
                if os.path.isdir(folder_path):
                    code_content = self.get_folder_content(folder_path)
        
        if not code_content:
            QMessageBox.warning(self, "Hata", "Lütfen analiz edilecek kodu seçin.")
            return
            
        self.progress_bar.setValue(0)
        self.generate_btn.setEnabled(False)
        
        self.generator = DocumentationGenerator(
            api_key=self.api_input.toPlainText().strip(),
            code_content=code_content,
            mode=mode,
            language=self.current_language
        )
        
        self.generator.progress_updated.connect(self.update_progress)
        self.generator.documentation_ready.connect(self.show_documentation)
        self.generator.error_occurred.connect(self.show_error)
        
        self.generator.start()

    def get_folder_content(self, folder_path: str) -> str:
        content = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                language_info = SupportedLanguages.get_language_by_extension(file_path)
                if language_info:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content.append(f"# {file} ({language_info['name']})\n{f.read()}\n\n")
                    except Exception as e:
                        print(f"Dosya okuma hatası ({file}): {str(e)}")
        return '\n'.join(content)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_error(self, error_message):
        QMessageBox.critical(self, "Hata", f"Dokümantasyon oluşturulurken bir hata oluştu: {error_message}")
        self.generate_btn.setEnabled(True)
        self.progress_bar.setValue(0)

    def clear_all(self):
        self.code_display.clear()
        self.output_text.clear()
        self.markdown_viewer.setHtml("")
        self.progress_bar.setValue(0)
        self.save_md_btn.setEnabled(False)
  