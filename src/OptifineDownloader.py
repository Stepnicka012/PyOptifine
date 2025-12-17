#!/usr/bin/env python3

import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json
import os
import re
import time
import threading
import queue
import html.parser
import gzip
import io
import sys

# Configuración por defecto (puede ser modificada externamente)
CONFIG = {
    'MIN_VERSION': "1.7.10",
    'MAX_THREADS': 15,
    'BASE_DIR': "PyOptifine",
    'DOWNLOAD_PREVIEWS': True,
    'DOWNLOAD_CHANGELOGS': True
}

def set_config(**kwargs):
    """Permite configurar el módulo externamente"""
    for key, value in kwargs.items():
        if key.upper() in CONFIG:
            CONFIG[key.upper()] = value

def get_directories():
    """Retorna los directorios configurados"""
    base_dir = CONFIG['BASE_DIR']
    jar_dir = os.path.join(base_dir, "Jar")
    changelog_dir = os.path.join(base_dir, "Changelogs")
    return base_dir, jar_dir, changelog_dir

def ensure_directories():
    """Crea los directorios necesarios"""
    base_dir, jar_dir, changelog_dir = get_directories()
    os.makedirs(jar_dir, exist_ok=True)
    os.makedirs(changelog_dir, exist_ok=True)

def version_to_tuple(version_str):
    try:
        return tuple(map(int, version_str.split('.')))
    except ValueError:
        return ()

def is_version_in_range(version_str, min_ver):
    if not version_str:
        return False
    ver_tuple = version_to_tuple(version_str)
    min_tuple = version_to_tuple(min_ver)
    if not ver_tuple or not min_tuple:
        return True
    return ver_tuple >= min_tuple

def format_bar(percent, width=40):
    filled = int(width * percent // 100)
    return '█' * filled + '░' * (width - filled)

class SilentConsole:
    """Consola silenciosa que solo muestra la barra de progreso"""
    def __init__(self):
        self._last_len = 0
        self.start_time = time.time()
        self.last_update = 0
        self.messages = []
        self.errors = []
    
    def add_message(self, message):
        """Agrega un mensaje para mostrar al final"""
        self.messages.append(message)
    
    def add_error(self, error):
        """Agrega un error para mostrar al final"""
        self.errors.append(error)
    
    def clear(self):
        sys.stdout.write('\r' + ' ' * self._last_len + '\r')
        sys.stdout.flush()
    
    def write(self, text, newline=False, clear_first=False):
        """Solo escribe si es la barra de progreso, de lo contrario guarda el mensaje"""
        if '[' in text and ']' in text and ('█' in text or '░' in text):
            if clear_first:
                self.clear()
            if newline:
                print(text)
                self._last_len = 0
            else:
                sys.stdout.write('\r' + ' ' * self._last_len + '\r')
                sys.stdout.write(text)
                self._last_len = len(text)
                sys.stdout.flush()
        else:
            if text.strip():
                self.add_message(text)
    
    def progress(self, current, total, prefix="", suffix=""):
        now = time.time()
        if now - self.last_update < 0.1 and current != total:
            return
        self.last_update = now
        
        percent = (current / total * 100) if total > 0 else 0
        elapsed = time.time() - self.start_time
        eta = (elapsed / current * (total - current)) if current > 0 else 0
        
        bar = format_bar(percent)
        eta_str = f"ETA: {eta:.0f}s" if eta > 0 and current < total else ""
        
        text = f"{prefix} [{bar}] {current}/{total} ({percent:.1f}%) {eta_str} {suffix}".strip()
        self.write(text)
        
        if current == total:
            self.write(f"{prefix} [{bar}] {current}/{total} (100%) ✓", newline=True)
    
    def print_all_messages(self):
        """Muestra todos los mensajes guardados"""
        if self.messages:
            print("\n" + "=" * 60)
            print("📋 MENSAJES DEL PROCESO:")
            for msg in self.messages:
                print(msg)
        
        if self.errors:
            print("\n" + "=" * 60)
            print("❌ ERRORES ENCONTRADOS:")
            print("=" * 60)
            for error in self.errors:
                print(f"  • {error}")

class OptiFineParser(html.parser.HTMLParser):
    def __init__(self, console):
        super().__init__()
        self.console = console
        self.manifest = []
        self._current_version = ""
        self._in_table = False
        self._current = {}
        self._cell_type = ""
        self._is_preview = False
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'h2':
            pass
        elif tag == 'table' and 'downloadTable' in attrs_dict.get('class', ''):
            self._in_table = True
            self._current = {}
            self._is_preview = 'mainTable' not in attrs_dict.get('class', '')
        elif self._in_table and tag == 'td':
            self._cell_type = attrs_dict.get('class', '')
        elif self._in_table and tag == 'a':
            href = attrs_dict.get('href', '')
            if self._cell_type == 'colMirror':
                self._current['mirror_url'] = href
            elif self._cell_type == 'colChangelog':
                self._current['changelog_url'] = href
    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if data.startswith('Minecraft'):
            self._current_version = data.replace('Minecraft', '').strip()
        elif self._in_table and self._current_version:
            if 'colFile' in self._cell_type:
                self._current['optifine_version'] = data
            elif 'colForge' in self._cell_type:
                self._current['forge_version'] = data
            elif 'colDate' in self._cell_type:
                self._current['release_date'] = data
    
    def handle_endtag(self, tag):
        if tag == 'table' and self._in_table:
            self._in_table = False
            if self._current and 'mirror_url' in self._current:
                if CONFIG['DOWNLOAD_PREVIEWS'] or not self._is_preview:
                    self._current['minecraft_version'] = self._current_version
                    self._current['is_preview'] = self._is_preview
                    
                    parsed = urllib.parse.urlparse(self._current['mirror_url'])
                    query = urllib.parse.parse_qs(parsed.query)
                    if 'f' in query:
                        self._current['filename'] = query['f'][0]
                        self.manifest.append(self._current.copy())
            self._current = {}
            self._is_preview = False

def fetch_html(url, timeout=15):
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        request = urllib.request.Request(url)
        response = opener.open(request, timeout=timeout)
        
        if response.info().get('Content-Encoding') == 'gzip':
            buf = io.BytesIO(response.read())
            with gzip.GzipFile(fileobj=buf) as f:
                return f.read().decode('utf-8', errors='ignore')
        return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def generate_manifest(console):
    console.add_message("🔍 Obteniendo lista de versiones...")
    
    html_content = fetch_html("https://optifine.net/downloads")
    if not html_content:
        console.add_error("No se pudo obtener la página de descargas")
        return []
    
    parser = OptiFineParser(console)
    parser.feed(html_content)
    
    filtered = []
    min_version = CONFIG['MIN_VERSION']
    for entry in parser.manifest:
        if is_version_in_range(entry.get('minecraft_version', ''), min_version):
            filtered.append(entry)
    
    preview_count = sum(1 for e in filtered if e.get('is_preview', False))
    
    console.add_message(f"✅ Encontradas {len(filtered)} versiones de OptiFine")
    if not CONFIG['DOWNLOAD_PREVIEWS'] and preview_count:
        console.add_message(f"📊 (excluyendo {preview_count} versiones preview)")
    
    return filtered

class DownloadManager:
    def __init__(self, console):
        self.console = console
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        
        self.queue = queue.Queue()
        self.stats = {
            'total': 0, 'downloaded': 0, 'skipped': 0, 
            'failed': 0, 'bytes': 0, 'changelogs': 0
        }
        self.lock = threading.Lock()
        self.results = []
        self.download_details = []
    
    def extract_download_url_from_html(self, html_content, mirror_url):
        """
        Extrae la URL real de descarga del HTML de la página mirror.
        Busca patrones como: downloadx?f=preview_OptiFine_1.21.10_HD_U_J7_pre9.jar&x=...
        """
        try:
            # Buscar el patrón href='downloadx?f=...&x=...'
            pattern = r"href=['\"]?(downloadx\?f=[^'\">\s]+)['\"]?"
            match = re.search(pattern, html_content, re.IGNORECASE)
            
            if match:
                download_path = match.group(1)
                
                # Construir la URL completa
                parsed_mirror = urllib.parse.urlparse(mirror_url)
                base_url = f"{parsed_mirror.scheme}://{parsed_mirror.netloc}"
                
                # Si el path no empieza con /, añadirlo
                if not download_path.startswith('/'):
                    download_path = '/' + download_path
                
                final_url = base_url + download_path
                return final_url
            
            # Fallback: buscar cualquier enlace con .jar
            pattern_jar = r"href=['\"]?([^'\">\s]*\.jar[^'\">\s]*)['\"]?"
            match_jar = re.search(pattern_jar, html_content, re.IGNORECASE)
            
            if match_jar:
                jar_path = match_jar.group(1)
                parsed_mirror = urllib.parse.urlparse(mirror_url)
                base_url = f"{parsed_mirror.scheme}://{parsed_mirror.netloc}"
                
                if jar_path.startswith('http'):
                    return jar_path
                elif jar_path.startswith('/'):
                    return base_url + jar_path
                else:
                    return base_url + '/' + jar_path
            
            return None
            
        except Exception as e:
            self.console.add_error(f"Error extrayendo URL de descarga: {str(e)}")
            return None
    
    def get_final_url(self, mirror_url):
        """
        Obtiene la URL final del JAR desde la página mirror.
        1. Descarga el HTML del mirror
        2. Extrae la URL real de descarga
        """
        try:
            # Construir la URL completa del mirror si es necesario
            if not mirror_url.startswith('http'):
                mirror_url = f"https://optifine.net/{mirror_url}"
            
            # Descargar el HTML de la página mirror
            request = urllib.request.Request(mirror_url)
            response = self.opener.open(request, timeout=15)
            html = response.read().decode('utf-8', errors='ignore')
            
            # Extraer la URL real de descarga
            download_url = self.extract_download_url_from_html(html, mirror_url)
            
            if download_url:
                return download_url
            else:
                self.console.add_error(f"No se encontró URL de descarga en {mirror_url}")
                return None
                
        except Exception as e:
            self.console.add_error(f"Error obteniendo URL final de {mirror_url}: {str(e)}")
            return None
    
    def download_file(self, url, filepath, referer=""):
        try:
            if os.path.exists(filepath):
                return True, os.path.getsize(filepath), True
            
            request = urllib.request.Request(url)
            if referer:
                request.add_header('Referer', referer)
            
            response = self.opener.open(request, timeout=30)
            file_size = 0
            
            with open(filepath, 'wb') as f:
                while True:
                    chunk = response.read(16384)
                    if not chunk:
                        break
                    f.write(chunk)
                    file_size += len(chunk)
            
            return True, file_size, False
        except Exception as e:
            self.console.add_error(f"Error descargando {url}: {str(e)}")
            return False, 0, False
    
    def download_changelog(self, entry):
        if not CONFIG['DOWNLOAD_CHANGELOGS'] or 'changelog_url' not in entry:
            return False, 0
        
        changelog_url = entry['changelog_url']
        if not changelog_url.startswith('http'):
            changelog_url = f"https://optifine.net/{changelog_url}"
        
        filename = entry.get('filename', 'unknown.jar').replace('.jar', '.txt')
        _, _, changelog_dir = get_directories()
        changelog_path = os.path.join(changelog_dir, filename)
        
        success, size, existed = self.download_file(changelog_url, changelog_path)
        return success, size
    
    def worker(self):
        _, jar_dir, _ = get_directories()
        
        while True:
            try:
                entry = self.queue.get_nowait()
            except queue.Empty:
                break
            
            filename = entry.get('filename', 'unknown.jar')
            jar_path = os.path.join(jar_dir, filename)
            
            try:
                # Paso 1: Obtener la URL real del JAR desde el mirror
                mirror_url = entry['mirror_url']
                if not mirror_url.startswith('http'):
                    mirror_url = f"https://optifine.net/{mirror_url}"
                
                final_url = self.get_final_url(mirror_url)
                
                if not final_url:
                    with self.lock:
                        self.stats['failed'] += 1
                        entry['downloaded'] = False
                        self.results.append(entry)
                        self.download_details.append({
                            'filename': filename,
                            'status': 'failed',
                            'error': 'No se pudo extraer URL de descarga del mirror'
                        })
                    self.queue.task_done()
                    continue
                
                # Paso 2: Descargar el JAR real
                success, jar_size, existed = self.download_file(final_url, jar_path, mirror_url)
                
                # Paso 3: Descargar changelog si está habilitado
                changelog_success = False
                changelog_size = 0
                if CONFIG['DOWNLOAD_CHANGELOGS'] and 'changelog_url' in entry:
                    changelog_success, changelog_size = self.download_changelog(entry)
                
                with self.lock:
                    if existed:
                        self.stats['skipped'] += 1
                        status = 'skipped'
                    elif success:
                        self.stats['downloaded'] += 1
                        self.stats['bytes'] += jar_size
                        entry['downloaded'] = True
                        entry['file_size'] = jar_size
                        entry['local_path'] = jar_path
                        status = 'downloaded'
                    else:
                        self.stats['failed'] += 1
                        entry['downloaded'] = False
                        status = 'failed'
                    
                    if changelog_success:
                        self.stats['changelogs'] += 1
                    
                    self.results.append(entry)
                    
                    self.download_details.append({
                        'filename': filename,
                        'status': status,
                        'size_mb': jar_size / (1024 * 1024) if jar_size > 0 else 0
                    })
                
            except Exception as e:
                with self.lock:
                    self.stats['failed'] += 1
                    entry['downloaded'] = False
                    self.results.append(entry)
                    self.download_details.append({
                        'filename': filename,
                        'status': 'failed',
                        'error': str(e)
                    })
            finally:
                self.queue.task_done()
    
    def download_all(self, manifest):
        for entry in manifest:
            self.queue.put(entry)
        self.stats['total'] = len(manifest)
        
        self.console.add_message(f"🚀 Iniciando descarga de {len(manifest)} archivos...")
        
        max_threads = CONFIG['MAX_THREADS']
        threads = []
        for i in range(min(max_threads, len(manifest))):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            threads.append(t)
        
        last_progress = 0
        while any(t.is_alive() for t in threads) or not self.queue.empty():
            with self.lock:
                processed = (self.stats['downloaded'] + 
                           self.stats['failed'] + 
                           self.stats['skipped'])
            
            if processed != last_progress:
                self.console.progress(processed, self.stats['total'], 
                                    prefix="📦 Descargas", 
                                    suffix=f"📄 {self.stats['changelogs']} changelogs")
                last_progress = processed
            
            time.sleep(0.1)
        
        self.console.progress(self.stats['total'], self.stats['total'],
                            prefix="📦 Descargas",
                            suffix=f"📄 {self.stats['changelogs']} changelogs")
        
        final = []
        for original in manifest:
            for result in self.results:
                if result.get('mirror_url') == original.get('mirror_url'):
                    merged = original.copy()
                    merged.update({
                        'downloaded': result.get('downloaded', False),
                        'file_size': result.get('file_size', 0),
                        'local_path': result.get('local_path', '')
                    })
                    final.append(merged)
                    break
        
        return final
    
    def print_summary(self, console):
        total_mb = self.stats['bytes'] / (1024 * 1024)
        _, jar_dir, changelog_dir = get_directories()
        
        console.add_message("📊 Resumen de la descarga")
        console.add_message("=" * 60)
        
        summary_lines = [
            f"   📦 Total archivos:    {self.stats['total']}",
            f"   ✅ Descargados:      {self.stats['downloaded']}",
            f"   ⏭️  Saltados:        {self.stats['skipped']}",
            f"   ❌ Fallidos:         {self.stats['failed']}",
            f"   📄 Changelogs:       {self.stats['changelogs']}",
            f"   💾 Total datos:      {total_mb:.1f} MB"
        ]
        
        for line in summary_lines:
            console.add_message(line)
        
        console.add_message(f"   📂 Jar:             {jar_dir}/")
        if CONFIG['DOWNLOAD_CHANGELOGS']:
            console.add_message(f"   📂 Changelogs:      {changelog_dir}/")
        
        failed_downloads = [d for d in self.download_details if d['status'] == 'failed']
        skipped_downloads = [d for d in self.download_details if d['status'] == 'skipped']
        
        if failed_downloads:
            console.add_message("\n❌ DESCARGAS FALLADAS:")
            for d in failed_downloads[:10]:
                error_msg = f" - {d.get('error', 'Error desconocido')}" if 'error' in d else ""
                console.add_message(f"   • {d['filename']}{error_msg}")
            if len(failed_downloads) > 10:
                console.add_message(f"   ... y {len(failed_downloads) - 10} más")
        
        if skipped_downloads:
            console.add_message("\n⏭️  ARCHIVOS EXISTENTES (SALTADOS):")
            for d in skipped_downloads[:5]:
                console.add_message(f"   • {d['filename']}")
            if len(skipped_downloads) > 5:
                console.add_message(f"   ... y {len(skipped_downloads) - 5} más")

def main():
    print(f"⚙️  CONFIGURACIÓN INICIAL:")
    print(f"   • Versión mínima: Minecraft {CONFIG['MIN_VERSION']}")
    print(f"   • Incluir previews: {'Sí' if CONFIG['DOWNLOAD_PREVIEWS'] else 'No'}")
    print(f"   • Descargar changelogs: {'Sí' if CONFIG['DOWNLOAD_CHANGELOGS'] else 'No'}")
    print(f"   • Hilos máximos: {CONFIG['MAX_THREADS']}")
    print()
    
    ensure_directories()
    console = SilentConsole()
    
    manifest = generate_manifest(console)
    if not manifest:
        console.add_error("❌ No se encontraron versiones para descargar.")
        console.print_all_messages()
        return
    
    downloader = DownloadManager(console)
    final_manifest = downloader.download_all(manifest)
    
    base_dir, _, _ = get_directories()
    manifest_file = os.path.join(base_dir, 'PyOptifine_Manifest.json')
    try:
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(final_manifest, f, indent=2, ensure_ascii=False)
        console.add_message(f"💾 Manifest guardado en: {manifest_file}")
    except Exception as e:
        console.add_error(f"Error guardando manifest: {str(e)}")
    
    downloader.print_summary(console)
    console.print_all_messages()

if __name__ == "__main__":
    main()