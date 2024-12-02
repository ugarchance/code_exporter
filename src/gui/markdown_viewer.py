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
                background-color: #252525;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                padding: 15px;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
        """)
        
        # Özel CSS stilleri
        self.css = """
            <style>
                body {
                    background-color: #252525;
                    color: #e0e0e0;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 15px;
                }
                h1 { 
                    color: #61afef;
                    font-size: 24px;
                    margin-top: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #3a3a3a;
                }
                h2 { 
                    color: #c678dd;
                    font-size: 20px;
                    margin-top: 15px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #3a3a3a;
                }
                h3 { 
                    color: #98c379;
                    font-size: 16px;
                    margin-top: 10px;
                }
                code {
                    background-color: #1a1a1a;
                    color: #e5c07b;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
                    font-size: 13px;
                }
                pre {
                    background-color: #1a1a1a;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #3a3a3a;
                    overflow-x: auto;
                    margin: 15px 0;
                }
                pre code {
                    background-color: transparent;
                    padding: 0;
                    border: none;
                }
                blockquote {
                    border-left: 4px solid #2d5a88;
                    margin: 15px 0;
                    padding: 10px 20px;
                    background-color: #1a1a1a;
                    border-radius: 0 5px 5px 0;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                    background-color: #1a1a1a;
                    border-radius: 5px;
                    overflow: hidden;
                }
                th, td {
                    border: 1px solid #3a3a3a;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background-color: #2d5a88;
                    color: white;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #2a2a2a;
                }
                a { 
                    color: #61afef;
                    text-decoration: none;
                    border-bottom: 1px dotted #61afef;
                    padding-bottom: 2px;
                }
                a:hover {
                    border-bottom: 1px solid #61afef;
                }
                hr {
                    border: none;
                    height: 1px;
                    background-color: #3a3a3a;
                    margin: 20px 0;
                }
                ul, ol {
                    padding-left: 25px;
                    margin: 10px 0;
                }
                li {
                    margin: 8px 0;
                }
                .method { 
                    background-color: #1a1a1a;
                    border-left: 4px solid #98c379;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 0 5px 5px 0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                }
                .class {
                    background-color: #1a1a1a;
                    border-left: 4px solid #61afef;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 0 5px 5px 0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                }
                .parameter {
                    color: #e5c07b;
                    font-style: italic;
                    background-color: #2a2a2a;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 13px;
                }
                .return-type {
                    color: #c678dd;
                    font-weight: bold;
                    background-color: #2a2a2a;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 13px;
                }
                .highlight {
                    background-color: #2d5a88;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
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