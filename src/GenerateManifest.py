#!/usr/bin/env python3
import urllib.request
import urllib.error
import urllib.parse
import json
import html.parser
import re
import sys
from pathlib import Path

def fetch_html(url, timeout=15):
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
        request = urllib.request.Request(url)
        response = opener.open(request, timeout=timeout)
        html_content = response.read().decode('utf-8', errors='ignore')
        return html_content
        
    except urllib.error.URLError as e:
        print(f"❌ Error de URL: {e}")
        return None
    except Exception as e:
        print(f"❌ Error al obtener la página: {e}")
        return None

class OptiFineHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.manifest_data = []
        self.current_minecraft_version = None
        self.in_download_table = False
        self.current_row_data = {}
        self.current_cell_type = None
        self.in_table_row = False
        self.capture_data = False
        self.in_h2 = False
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Buscar encabezados h2 con versiones de Minecraft
        if tag == 'h2':
            self.in_h2 = True
            self.capture_data = True
        
        # Buscar tablas de descarga
        elif tag == 'table':
            if 'class' in attrs_dict:
                classes = attrs_dict['class'].split()
                if 'downloadTable' in classes:
                    self.in_download_table = True
        
        # Dentro de la tabla de descarga
        elif self.in_download_table:
            if tag == 'tr':
                self.in_table_row = True
                self.current_row_data = {}
            
            elif tag == 'td' and self.in_table_row:
                if 'class' in attrs_dict:
                    self.current_cell_type = attrs_dict['class']
                    self.capture_data = True
            
            elif tag == 'a' and self.in_table_row and self.current_cell_type:
                if 'href' in attrs_dict:
                    href = attrs_dict['href']
                    if self.current_cell_type == 'colMirror':
                        self.current_row_data['mirror_url'] = href
                    elif self.current_cell_type == 'colChangelog':
                        self.current_row_data['changelog_url'] = href
    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        
        # Capturar versión de Minecraft desde h2
        if self.in_h2 and self.capture_data and 'Minecraft' in data:
            version_text = data.replace('Minecraft', '').strip()
            if version_text:
                self.current_minecraft_version = version_text
        
        # Capturar datos dentro de las celdas de la tabla
        elif self.in_table_row and self.capture_data and self.current_cell_type:
            if self.current_cell_type == 'colFile':
                self.current_row_data['optifine_version'] = data
            elif self.current_cell_type == 'colForge':
                self.current_row_data['forge_version'] = data if data else 'N/A'
            elif self.current_cell_type == 'colDate':
                self.current_row_data['release_date'] = data if data else 'N/A'
    
    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_h2 = False
            self.capture_data = False
        
        elif tag == 'table' and self.in_download_table:
            self.in_download_table = False
            self.in_table_row = False
        
        elif tag == 'tr' and self.in_table_row:
            self.in_table_row = False
            
            # Agregar la fila procesada al manifiesto si tiene los datos necesarios
            if (self.current_minecraft_version and 
                'optifine_version' in self.current_row_data and 
                'mirror_url' in self.current_row_data):
                
                entry = {
                    'minecraft_version': self.current_minecraft_version,
                    'optifine_version': self.current_row_data['optifine_version'],
                    'mirror_url': self.current_row_data['mirror_url'],
                    'forge_version': self.current_row_data.get('forge_version', 'N/A'),
                    'release_date': self.current_row_data.get('release_date', 'N/A')
                }
                
                # Extraer nombre de archivo del parámetro 'f' en la URL
                parsed_url = urllib.parse.urlparse(self.current_row_data['mirror_url'])
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'f' in query_params:
                    entry['filename'] = query_params['f'][0]
                
                # Extraer changelog si existe
                if 'changelog_url' in self.current_row_data:
                    entry['changelog_url'] = self.current_row_data['changelog_url']
                
                self.manifest_data.append(entry)
            
            self.current_row_data = {}
        
        elif tag == 'td':
            self.current_cell_type = None
            self.capture_data = False

def scrape_optifine_manifest_v2():
    url = "https://optifine.net/downloads"
    
    print("🔍 Obteniendo página de descargas de OptiFine...")
    html_content = fetch_html(url)
    
    if not html_content:
        print("❌ No se pudo obtener el contenido de la página")
        return None
    
    print("📋 Analizando contenido HTML...")
    
    manifest_data = []
    current_minecraft_version = None
    
    # Dividir el contenido en líneas para procesar más fácilmente
    lines = html_content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Buscar versión de Minecraft (en h2)
        if '<h2>' in line and 'Minecraft' in line:
            # Extraer la versión usando regex
            match = re.search(r'<h2[^>]*>(?:<u>)?Minecraft\s*([^<]+)', line, re.IGNORECASE)
            if match:
                current_minecraft_version = match.group(1).strip()
                print(f"📦 Versión encontrada: Minecraft {current_minecraft_version}")
        
        # Buscar tablas de descarga
        elif 'downloadTable' in line and 'table' in line:
            # Procesar las siguientes líneas hasta encontrar el cierre de la tabla
            for j in range(i, min(i + 100, len(lines))):
                row_line = lines[j].strip()
                
                # Buscar filas de la tabla
                if '<tr>' in row_line:
                    # Extraer datos de esta fila
                    row_data = extract_row_data(row_line, current_minecraft_version)
                    if row_data and current_minecraft_version:
                        manifest_data.append(row_data)
    
    return manifest_data

def extract_row_data(html_line, minecraft_version):
    
    # Buscar todas las celdas td en la línea
    td_matches = re.findall(r'<td[^>]*>(.*?)</td>', html_line, re.DOTALL)
    
    if len(td_matches) < 4:  # Necesitamos al menos 4 celdas
        return None
    
    # Procesar cada celda
    optifine_version = None
    mirror_url = None
    forge_version = 'N/A'
    release_date = 'N/A'
    
    for i, td_content in enumerate(td_matches):
        # Limpiar el contenido
        clean_content = re.sub(r'<[^>]+>', '', td_content).strip()
        
        # Celda 0: Nombre del archivo (colFile)
        if i == 0 and clean_content:
            optifine_version = clean_content
        
        # Celda 1: Enlace de descarga (colMirror)
        elif i == 1:
            # Buscar enlace href
            href_match = re.search(r'href="([^"]+)"', td_content)
            if href_match:
                mirror_url = href_match.group(1)
        
        # Celda 2: Versión de Forge (colForge)
        elif i == 2 and clean_content:
            forge_version = clean_content
        
        # Celda 3: Fecha (colDate)
        elif i == 3 and clean_content:
            release_date = clean_content
    
    # Validar que tenemos los datos mínimos
    if optifine_version and mirror_url and minecraft_version:
        entry = {
            'minecraft_version': minecraft_version,
            'optifine_version': optifine_version,
            'mirror_url': mirror_url,
            'forge_version': forge_version,
            'release_date': release_date
        }
        
        # Extraer nombre de archivo del parámetro 'f' en la URL
        try:
            parsed_url = urllib.parse.urlparse(mirror_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'f' in query_params:
                entry['filename'] = query_params['f'][0]
        except:
            pass
        
        return entry
    
    return None

def scrape_optifine_manifest():
    url = "https://optifine.net/downloads"
    
    print("🔍 Obteniendo página de descargas de OptiFine...")
    html_content = fetch_html(url)
    
    if not html_content:
        print("❌ No se pudo obtener el contenido de la página")
        return None
    
    print("📋 Analizando contenido HTML con parser...")
    
    # Usar el parser HTML
    parser = OptiFineHTMLParser()
    parser.feed(html_content)
    
    if parser.manifest_data:
        print(f"✅ Encontradas {len(parser.manifest_data)} entradas")
        return parser.manifest_data
    else:
        print("⚠️  No se encontraron datos con el parser, intentando método alternativo...")
        return scrape_optifine_manifest_v2()

def main():
    manifest = scrape_optifine_manifest()
    
    if manifest:
        # Guardar el manifiesto en un archivo JSON
        output_filename = 'optifine_mirror_manifest.json'
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print()
        print("=" * 80)
        print("✅ ¡MANIFIESTO GENERADO EXITOSAMENTE!")
        print("=" * 80)
        print(f"📄 Archivo creado: '{output_filename}'")
        print(f"📊 Total de entradas: {len(manifest)}")
        print()

        versions_count = {}
        for entry in manifest:
            version = entry.get('minecraft_version', 'Desconocida')
            versions_count[version] = versions_count.get(version, 0) + 1
        
        print("📈 Resumen por versión de Minecraft:")
        for version, count in sorted(versions_count.items()):
            print(f"   • Minecraft {version}: {count} versiones de OptiFine")
        
        # Mostrar algunos ejemplos
        print()
        print("📋 Ejemplos de entradas encontradas:")
        for i, entry in enumerate(manifest[:3]):  # Mostrar solo las primeras 3
            print(f"   {i+1}. Minecraft {entry['minecraft_version']} - {entry['optifine_version']}")
        
        if len(manifest) > 3:
            print(f"   ... y {len(manifest) - 3} más")
    
    else:
        print()
        print("❌ NO SE PUDO GENERAR EL MANIFIESTO")
        print("=" * 80)
        print("Posibles causas:")
        print("   • Problemas de conexión a internet")
        print("   • La página de OptiFine cambió su estructura")
        print("   • El sitio está temporalmente fuera de línea")
        print()
        print("💡 Sugerencias:")
        print("   • Verifica tu conexión a internet")
        print("   • Intenta nuevamente más tarde")
        print("   • Revisa si optifine.net está accesible desde tu navegador")

if __name__ == "__main__":
    main()