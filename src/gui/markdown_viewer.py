from PyQt6.QtWidgets import QTextBrowser
from PyQt6.QtCore import Qt
import markdown
import re

class MarkdownViewer(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setStyleSheet("""
            QTextBrowser {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                padding: 10px;
            }
        """)
        
        # Özel CSS stilleri
        self.css = """
            <style>
                body {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 10px;
                }
                h1 { color: #61afef; font-size: 24px; margin-top: 20px; }
                h2 { color: #c678dd; font-size: 20px; margin-top: 15px; }
                h3 { color: #98c379; font-size: 16px; margin-top: 10px; }
                code {
                    background-color: #3b3b3b;
                    color: #e5c07b;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }
                pre {
                    background-color: #3b3b3b;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
                pre code {
                    background-color: transparent;
                    padding: 0;
                }
                blockquote {
                    border-left: 4px solid #61afef;
                    margin: 0;
                    padding-left: 10px;
                    color: #abb2bf;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 10px 0;
                }
                th, td {
                    border: 1px solid #3b3b3b;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #3b3b3b;
                }
                a { color: #61afef; text-decoration: none; }
                a:hover { text-decoration: underline; }
                hr { border: 1px solid #3b3b3b; }
                ul, ol { padding-left: 20px; }
                li { margin: 5px 0; }
                .method { 
                    background-color: #32363b;
                    border-left: 4px solid #98c379;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 0 5px 5px 0;
                }
                .class {
                    background-color: #32363b;
                    border-left: 4px solid #61afef;
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 0 5px 5px 0;
                }
                .parameter {
                    color: #e5c07b;
                    font-style: italic;
                }
                .return-type {
                    color: #c678dd;
                    font-weight: bold;
                }
            </style>
        """
        
    def set_markdown(self, text: str):
        # Markdown'ı HTML'e çevir
        html = markdown.markdown(
            text,
            extensions=['fenced_code', 'tables', 'codehilite']
        )
        
        # Kod bloklarını özelleştir
        html = re.sub(
            r'<pre><code>(.*?)</code></pre>',
            r'<pre><code class="highlight">\1</code></pre>',
            html,
            flags=re.DOTALL
        )
        
        # Metod ve sınıf bölümlerini özelleştir
        html = re.sub(
            r'<h3>Method: (.*?)</h3>',
            r'<div class="method"><h3>\1</h3>',
            html
        )
        html = html.replace('</pre></div>', '</pre></div></div>')
        
        # Sınıf bölümlerini özelleştir
        html = re.sub(
            r'<h2>Class: (.*?)</h2>',
            r'<div class="class"><h2>\1</h2>',
            html
        )
        
        # Parametre ve dönüş tiplerini özelleştir
        html = re.sub(
            r'Parameters: (.*?)<br>',
            r'<span class="parameter">Parameters:</span> \1<br>',
            html
        )
        html = re.sub(
            r'Returns: (.*?)<br>',
            r'<span class="return-type">Returns:</span> \1<br>',
            html
        )
        
        # CSS ve HTML'i birleştir
        full_html = f"{self.css}<body>{html}</body>"
        self.setHtml(full_html) 