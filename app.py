import sys
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from yt_dlp import YoutubeDL
import threading
import queue
import concurrent.futures
import json
import datetime
from plyer import notification
import urllib.request
import time

class MediaDownloaderPro(QMainWindow):
    # Definir sinais personalizados
    update_video_info_signal = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaDownloader Pro v2.0")
        self.setMinimumSize(1000, 800)
        
        # Configurar estilo
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0d6efd;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            QLineEdit {
                padding: 8px;
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                color: white;
            }
            QComboBox {
                padding: 8px;
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #2d2d2d;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                color: white;
                selection-background-color: #0d6efd;
            }
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0d6efd;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header com logo e título
        header_layout = QHBoxLayout()
        logo_label = QLabel("🎬")
        logo_label.setStyleSheet("font-size: 48px;")
        header_layout.addWidget(logo_label)
        
        title_label = QLabel("MediaDownloader Pro")
        title_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Botão de tema
        self.theme_button = QPushButton("🌙 Tema Escuro")
        self.theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_button)
        layout.addLayout(header_layout)
        
        # URL input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole o URL do vídeo aqui...")
        url_layout.addWidget(self.url_input)
        
        self.check_url_button = QPushButton("Verificar URL")
        self.check_url_button.clicked.connect(self.check_url)
        url_layout.addWidget(self.check_url_button)
        layout.addLayout(url_layout)
        
        # Informações do vídeo
        self.info_group = QGroupBox("Informações do Vídeo")
        info_layout = QVBoxLayout()
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.thumbnail_label)
        
        self.title_label = QLabel()
        self.duration_label = QLabel()
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.duration_label)
        
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        # Formato
        format_group = QGroupBox("Formato")
        format_layout = QVBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "MP4 - 1080p", 
            "MP4 - 720p", 
            "MP4 - 480p",
            "MP3 - 320kbps", 
            "MP3 - 128kbps",
            "WAV - Alta Qualidade",
            "WEBM - 1080p", 
            "WEBM - 720p"
        ])
        format_layout.addWidget(self.format_combo)
        format_group.setLayout(format_layout)
        controls_layout.addWidget(format_group)
        
        # Downloads simultâneos
        concurrent_group = QGroupBox("Downloads Simultâneos")
        concurrent_layout = QVBoxLayout()
        self.concurrent_combo = QComboBox()
        self.concurrent_combo.addItems(["1", "2", "3", "4", "5"])
        self.concurrent_combo.setCurrentText("3")
        concurrent_layout.addWidget(self.concurrent_combo)
        concurrent_group.setLayout(concurrent_layout)
        controls_layout.addWidget(concurrent_group)
        
        # Frame para seleção de diretório
        directory_group = QGroupBox("Diretório de Download")
        directory_layout = QVBoxLayout()
        
        self.directory_label = QLabel(os.path.join(os.path.expanduser("~"), "Downloads"))
        directory_layout.addWidget(self.directory_label)
        
        self.directory_button = QPushButton("📁 Escolher Pasta")
        self.directory_button.clicked.connect(self.choose_directory)
        directory_layout.addWidget(self.directory_button)
        
        directory_group.setLayout(directory_layout)
        controls_layout.addWidget(directory_group)
        
        layout.addLayout(controls_layout)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        self.download_button = QPushButton("⬇️ Download")
        self.download_button.clicked.connect(self.start_download)
        self.pause_button = QPushButton("⏸️ Pausar")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.cancel_button = QPushButton("⏹️ Cancelar")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_download)
        
        buttons_layout.addWidget(self.download_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab de Downloads Ativos
        self.queue_tab = QWidget()
        queue_layout = QVBoxLayout()
        self.queue_text = QTextEdit()
        self.queue_text.setReadOnly(True)
        queue_layout.addWidget(self.queue_text)
        self.queue_tab.setLayout(queue_layout)
        tabs.addTab(self.queue_tab, "Downloads Ativos")
        
        # Tab de Histórico
        self.history_tab = QWidget()
        history_layout = QVBoxLayout()
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)
        clear_history_button = QPushButton("Limpar Histórico")
        clear_history_button.clicked.connect(self.clear_history)
        history_layout.addWidget(clear_history_button)
        self.history_tab.setLayout(history_layout)
        tabs.addTab(self.history_tab, "Histórico")
        
        # Tab de Favoritos
        self.favorites_tab = QWidget()
        favorites_layout = QVBoxLayout()
        self.favorites_text = QTextEdit()
        self.favorites_text.setReadOnly(True)
        favorites_layout.addWidget(self.favorites_text)
        
        fav_buttons_layout = QHBoxLayout()
        add_favorite_button = QPushButton("Adicionar aos Favoritos")
        add_favorite_button.clicked.connect(self.add_favorite)
        remove_favorite_button = QPushButton("Remover Favorito")
        remove_favorite_button.clicked.connect(self.remove_favorite)
        
        fav_buttons_layout.addWidget(add_favorite_button)
        fav_buttons_layout.addWidget(remove_favorite_button)
        favorites_layout.addLayout(fav_buttons_layout)
        
        self.favorites_tab.setLayout(favorites_layout)
        tabs.addTab(self.favorites_tab, "Favoritos")
        
        layout.addWidget(tabs)
        
        # Variáveis de controle
        self.download_paused = False
        self.download_cancelled = False
        self.current_download = None
        self.download_queue = queue.Queue()
        self.active_downloads = []
        self.download_pool = None
        
        # Adicionar variável para armazenar o diretório
        self.download_directory = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Carregar dados
        self.history = self.load_data('historico.json')
        self.favorites = self.load_data('favoritos.json')
        self.update_history_ui()
        self.update_favorites_ui()
        
        # Tema inicial
        self.dark_theme = True
        
        # Conectar sinal ao slot
        self.update_video_info_signal.connect(self.update_video_info)

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        if self.dark_theme:
            self.theme_button.setText("🌙 Tema Escuro")
            self.setStyleSheet("""
                QMainWindow { background-color: #1e1e1e; }
                QWidget { color: #ffffff; }
                QPushButton {
                    background-color: #0d6efd;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #0b5ed7;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
                QLineEdit {
                    padding: 8px;
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    color: white;
                }
                QComboBox {
                    padding: 8px;
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    color: white;
                }
                QComboBox::drop-down {
                    border: none;
                    background-color: #2d2d2d;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid white;
                    margin-right: 8px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    color: white;
                    selection-background-color: #0d6efd;
                }
                QProgressBar {
                    border: 2px solid #404040;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #2d2d2d;
                }
                QProgressBar::chunk {
                    background-color: #0d6efd;
                    border-radius: 3px;
                }
                QTabWidget::pane {
                    border: 1px solid #404040;
                    background-color: #1e1e1e;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #0d6efd;
                }
                QTextEdit {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
            """)
        else:
            self.theme_button.setText("☀️ Tema Claro")
            self.setStyleSheet("""
                QMainWindow { background-color: #ffffff; }
                QWidget { color: #000000; }
                QPushButton {
                    background-color: #0d6efd;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QLineEdit {
                    padding: 8px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    color: black;
                }
                QComboBox {
                    padding: 8px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    color: black;
                }
                QComboBox::drop-down {
                    border: none;
                    background-color: #f8f9fa;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid black;
                    margin-right: 8px;
                }
                QComboBox QAbstractItemView {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    color: black;
                    selection-background-color: #0d6efd;
                }
                QProgressBar {
                    border: 2px solid #dee2e6;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #f8f9fa;
                }
                QTabWidget::pane {
                    border: 1px solid #dee2e6;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #f8f9fa;
                    padding: 8px 16px;
                    margin-right: 2px;
                    color: black;
                }
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    color: black;
                }
            """)

    def check_url(self):
        url = self.url_input.text()
        if not url:
            self.status_label.setText("Por favor, insira uma URL válida!")
            return
            
        self.status_label.setText("Obtendo informações do vídeo...")
        threading.Thread(target=self._fetch_video_info, args=(url,)).start()

    def _fetch_video_info(self, url):
        try:
            with YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)
                # Usar o sinal em vez de emit diretamente
                self.update_video_info_signal.emit(info)
        except Exception as e:
            # Usar QTimer para atualizar a interface da thread principal
            QTimer.singleShot(0, lambda: self.status_label.setText(f"Erro ao obter informações: {str(e)}"))

    def update_video_info(self, info):
        try:
            # Atualizar título
            title = info.get('title', 'Sem título')
            self.title_label.setText(f"Título: {title}")
            
            # Atualizar duração
            duration = info.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            self.duration_label.setText(f"Duração: {minutes}:{seconds:02d}")
            
            # Carregar e exibir miniatura
            thumbnail_url = info.get('thumbnail', '')
            if thumbnail_url:
                data = urllib.request.urlopen(thumbnail_url).read()
                image = QImage()
                image.loadFromData(data)
                pixmap = QPixmap(image).scaled(400, 225, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_label.setPixmap(pixmap)
                
            self.status_label.setText("Informações carregadas com sucesso!")
        except Exception as e:
            self.status_label.setText(f"Erro ao atualizar informações: {str(e)}")

    def start_download(self):
        url = self.url_input.text()
        if not url:
            self.status_label.setText("Por favor, insira uma URL válida!")
            return
            
        formato = self.format_combo.currentText()
        self.download_queue.put((url, formato))
        self.update_queue_text(f"Adicionado: {url} ({formato})")
        
        if self.download_pool is None:
            max_workers = int(self.concurrent_combo.currentText())
            self.download_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
            threading.Thread(target=self.process_download_queue).start()

    def process_download_queue(self):
        while True:
            try:
                url, formato = self.download_queue.get_nowait()
                future = self.download_pool.submit(self.execute_download, url, formato)
                self.active_downloads.append(future)
                self.active_downloads = [f for f in self.active_downloads if not f.done()]
            except queue.Empty:
                if len(self.active_downloads) == 0:
                    self.download_pool.shutdown(wait=False)
                    self.download_pool = None
                    break
            time.sleep(0.1)

    def update_queue_text(self, text):
        self.queue_text.append(text)

    def load_data(self, filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_data(self, data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f)

    def update_history_ui(self):
        self.history_text.clear()
        for item in self.history:
            self.history_text.append(
                f"[{item['data']}] {item['url']} - {item['formato']} ({item['status']})"
            )

    def update_favorites_ui(self):
        self.favorites_text.clear()
        for item in self.favorites:
            self.favorites_text.append(f"[{item['data']}] {item['url']}")

    def clear_history(self):
        self.history = []
        self.save_data(self.history, 'historico.json')
        self.update_history_ui()

    def add_favorite(self):
        url = self.url_input.text()
        if not url:
            self.status_label.setText("Insira uma URL para favoritar!")
            return
            
        if url not in [f['url'] for f in self.favorites]:
            self.favorites.append({
                'url': url,
                'data': datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            })
            self.save_data(self.favorites, 'favoritos.json')
            self.update_favorites_ui()
            self.status_label.setText("URL adicionada aos favoritos!")

    def remove_favorite(self):
        url = self.url_input.text()
        self.favorites = [f for f in self.favorites if f['url'] != url]
        self.save_data(self.favorites, 'favoritos.json')
        self.update_favorites_ui()
        self.status_label.setText("URL removida dos favoritos!")

    def toggle_pause(self):
        self.download_paused = not self.download_paused
        self.pause_button.setText("▶️ Continuar" if self.download_paused else "⏸️ Pausar")

    def cancel_download(self):
        self.download_cancelled = True
        self.status_label.setText("Cancelando download...")

    def execute_download(self, url, formato):
        try:
            formato_config = self._get_format_config(formato)
            
            ydl_opts = {
                'outtmpl': os.path.join(self.download_directory, '%(title)s.%(ext)s'),  # Usar diretório escolhido
                'progress_hooks': [self.update_progress],
                **formato_config
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                self.current_download = ydl
                if not self.download_cancelled:
                    ydl.download([url])
                    
            if not self.download_cancelled:
                QTimer.singleShot(0, lambda: self.status_label.setText("Download concluído com sucesso!"))
                self.add_to_history(url, formato, "Concluído")
                self.show_notification("Download Concluído", f"O download de {url} foi concluído com sucesso!")
                
        except Exception as e:
            if not self.download_cancelled:
                QTimer.singleShot(0, lambda: self.status_label.setText(f"Erro: {str(e)}"))
                self.add_to_history(url, formato, "Erro")
                self.show_notification("Erro no Download", f"Ocorreu um erro no download de {url}")
        finally:
            self.current_download = None
            QTimer.singleShot(0, lambda: self.pause_button.setEnabled(False))
            QTimer.singleShot(0, lambda: self.cancel_button.setEnabled(False))

    def _get_format_config(self, formato):
        formato_lower = formato.lower()
        
        if "mp3" in formato_lower:
            quality = "320" if "320" in formato else "128"
            return {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
                'ffmpeg_location': self._get_ffmpeg_path()
            }
        elif "wav" in formato_lower:
            return {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                }],
                'ffmpeg_location': self._get_ffmpeg_path()
            }
        elif "webm" in formato_lower:
            resolution = formato.split(" - ")[1].replace("p", "")
            return {
                'format': f'best[height<={resolution}][ext=webm]',
                'ffmpeg_location': self._get_ffmpeg_path()
            }
        else:  # MP4 (default)
            resolution = formato.split(" - ")[1].replace("p", "")
            return {
                # Simplificado para baixar direto em MP4
                'format': f'best[height<={resolution}][ext=mp4]/best[ext=mp4]/best',
                'ffmpeg_location': self._get_ffmpeg_path()
            }

    def _get_ffmpeg_path(self):
        if os.name == 'nt':  # Windows
            return r"C:\ffmpeg\bin\ffmpeg.exe"
        else:  # Linux/Mac
            return "ffmpeg"

    def update_progress(self, d):
        if d['status'] == 'downloading':
            # Verifica se o download foi cancelado
            if self.download_cancelled:
                if self.current_download:
                    self.current_download.cancel_download()
                return
                
            # Sistema de pausa
            while self.download_paused and not self.download_cancelled:
                time.sleep(0.1)
                continue
                
            try:
                p = d['downloaded_bytes'] / d['total_bytes']
                QTimer.singleShot(0, lambda: self.progress_bar.setValue(int(p * 100)))
                
                # Calcula velocidade em MB/s
                speed = d.get('speed', 0) / 1024 / 1024
                status = f"Baixando: {d['_percent_str']} de {d['_total_bytes_str']} ({speed:.1f} MB/s)"
                QTimer.singleShot(0, lambda: self.status_label.setText(status))
            except:
                QTimer.singleShot(0, lambda: self.status_label.setText("Baixando..."))

    def add_to_history(self, url, formato, status):
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.history.insert(0, {
            'data': now,
            'url': url,
            'formato': formato,
            'status': status
        })
        if len(self.history) > 100:
            self.history.pop()
        self.save_data(self.history, 'historico.json')
        QTimer.singleShot(0, self.update_history_ui)

    def show_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_icon=None,
                timeout=10,
            )
        except:
            print(f"Não foi possível mostrar notificação: {title} - {message}")

    def choose_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Escolher Pasta de Download",
            self.download_directory,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.download_directory = directory
            # Mostrar caminho reduzido se for muito longo
            display_path = directory
            if len(display_path) > 40:
                display_path = "..." + display_path[-37:]
            self.directory_label.setText(display_path)
            self.status_label.setText(f"Pasta de download alterada: {directory}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MediaDownloaderPro()
    window.show()
    sys.exit(app.exec()) 
