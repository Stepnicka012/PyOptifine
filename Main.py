#!/usr/bin/env python3
"""
PyOptifine - Main Script
Integra todos los módulos del proyecto
"""

import os
import sys
import argparse
from pathlib import Path

# Añadir src al path para importar módulos
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def show_banner():
    """Muestra el banner del proyecto"""
    banner = """
        ╔════════════════════════════════════════════════════════════════════════════════════════╗
        ║ ██████╗ ██╗   ██╗     ██████╗  ██████╗  ████████╗ ██╗ ███████╗ ██╗ ███╗   ██╗ ███████╗ ║
        ║ ██   ██╗╚██╗ ██╔╝    ██╔═══██╗ ██   ██╗ ╚══██╔══╝ ██║ ██╔════╝ ██║ ████╗  ██║ ██╔════╝ ║
        ║ ██████╔╝ ╚████╔╝     ██║   ██║ ██████╔╝    ██║    ██║ █████╗   ██║ ██╔██╗ ██║ █████╗   ║
        ║ ██╔═══╝   ╚██╔╝      ██║   ██║ ██╔═══╝     ██║    ██║ ██╔══╝   ██║ ██║╚██╗██║ ██╔══╝   ║
        ║ ██║        ██║       ╚██████╔╝ ██║         ██║    ██║ ██║      ██║ ██║ ╚████║ ███████╗ ║
        ║ ╚═╝        ╚═╝        ╚═════╝  ╚═╝         ╚═╝    ╚═╝ ╚═╝      ╚═╝ ╚═╝  ╚═══╝ ╚══════╝ ║
        ║                                                                                        ║
        ║ P Y O P T I F I N E   M A N A G E R                                                    ║
        ║ Author : NovaStepStudios                                                               ║
        ╚════════════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def run_downloader(min_version="1.7.10", no_previews=False, threads=15):
    """Ejecuta el módulo de descarga con la configuración especificada"""
    print("🔽 Módulo de descarga de OptiFine")
    print()
    
    try:
        import OptifineDownloader
        
        # Configurar el módulo antes de ejecutarlo
        OptifineDownloader.set_config(
            MIN_VERSION=min_version,
            MAX_THREADS=threads,
            DOWNLOAD_PREVIEWS=not no_previews,
            DOWNLOAD_CHANGELOGS=True
        )
        
        # Ejecutar el descargador
        OptifineDownloader.main()
        return True
    except ImportError as e:
        print(f"\n❌ Error: No se pudo importar OptifineDownloader")
        print(f"   Asegúrate de que el archivo esté en src/OptifineDownloader.py")
        print(f"   Detalle: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error ejecutando el descargador: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_generate_manifest():
    """Ejecuta el módulo de generación de manifiesto"""
    print("📄 Módulo de generación del manifiesto")
    print()
    
    try:
        import GenerateManifest
        
        if hasattr(GenerateManifest, 'main'):
            GenerateManifest.main()
        else:
            manifest = GenerateManifest.scrape_optifine_manifest()
            
            if manifest:
                output_filename = 'optifine_mirror_manifest.json'
                with open(output_filename, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                
                print(f"\n✅ Manifiesto creado: '{output_filename}'")
                print(f"📊 Enlaces encontrados: {len(manifest)}")
            else:
                print("\n⚠️  No se encontraron datos")
        
        return True
    except ImportError as e:
        print(f"\n❌ Error: No se pudo importar GenerateManifest")
        print(f"   Asegúrate de que el archivo esté en src/GenerateManifest.py")
        print(f"   Detalle: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error generando el manifiesto: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_help():
    """Muestra el mensaje de ayuda completo"""
    help_text = """
        ╔════════════════════════════════════════════════════════════════════════════════════════╗
        ║ ██████╗ ██╗   ██╗     ██████╗  ██████╗  ████████╗ ██╗ ███████╗ ██╗ ███╗   ██╗ ███████╗ ║
        ║ ██   ██╗╚██╗ ██╔╝    ██╔═══██╗ ██   ██╗ ╚══██╔══╝ ██║ ██╔════╝ ██║ ████╗  ██║ ██╔════╝ ║
        ║ ██████╔╝ ╚████╔╝     ██║   ██║ ██████╔╝    ██║    ██║ █████╗   ██║ ██╔██╗ ██║ █████╗   ║
        ║ ██╔═══╝   ╚██╔╝      ██║   ██║ ██╔═══╝     ██║    ██║ ██╔══╝   ██║ ██║╚██╗██║ ██╔══╝   ║
        ║ ██║        ██║       ╚██████╔╝ ██║         ██║    ██║ ██║      ██║ ██║ ╚████║ ███████╗ ║
        ║ ╚═╝        ╚═╝        ╚═════╝  ╚═╝         ╚═╝    ╚═╝ ╚═╝      ╚═╝ ╚═╝  ╚═══╝ ╚══════╝ ║
        ║                                                                                        ║
        ║ P Y O P T I F I N E   M A N A G E R                                                    ║
        ║ Author : NovaStepStudios                                                               ║
        ╚════════════════════════════════════════════════════════════════════════════════╗    ╔══╝
        ╔════════════════════════════════════════════════════════════════════════════════╝    ╚══╗
        ║ PyOptifine Manager                                                                     ║
        ║ Gestor completo de descargas OptiFine                                                  ║
        ╚════════════════════════════════════════════════════════════════════════════════════════╝

        COMANDOS DISPONIBLES:

        download    - Descarga todas las versiones de OptiFine
                        Descarga los archivos .jar de OptiFine en el directorio PyOptifine/Jar/

        manifest    - Genera un manifiesto de versiones disponibles
                        Crea un archivo JSON con todas las versiones encontradas en optifine.net

        all         - Ejecuta ambos módulos (download y manifest)
                        Primero descarga y luego genera el manifiesto

        help        - Muestra este mensaje de ayuda

        OPCIONES ADICIONALES:

        --min-version VERSION  - Versión mínima de Minecraft a descargar
                                (ejemplo: --min-version 1.16, por defecto: 1.7.10)

        --no-previews         - No descargar versiones preview/beta
                                Solo descarga versiones estables

        --threads NUMERO      - Número máximo de hilos para descargas paralelas
                                (por defecto: 15, máximo recomendado: 50)

        EJEMPLOS DE USO:

        # Descargar todas las versiones desde Minecraft 1.16
        python3 Main.py download --min-version 1.16

        # Descargar sin versiones preview, desde 1.12, con 10 hilos
        python3 Main.py download --min-version 1.12 --no-previews --threads 10

        # Generar solo el manifiesto sin descargar
        python3 Main.py manifest

        # Ejecutar todo con configuración personalizada
        python3 Main.py all --min-version 1.12 --no-previews --threads 10

        # Mostrar ayuda
        python3 Main.py help

        ESTRUCTURA DE DIRECTORIOS:

        PyOptifine/
        ├── Jar/                          # Archivos .jar descargados
        ├── Changelogs/                   # Archivos de changelog (.txt)
        └── PyOptifine_Manifest.json      # Manifiesto con info de descargas

        NOTAS:

        - El script detecta automáticamente archivos ya descargados y los omite
        - Usa multithreading para descargas más rápidas
        - Extrae URLs reales desde las páginas mirror de OptiFine
        - Genera un manifiesto JSON con metadata de todas las descargas
    """
    print(help_text)

def show_interactive_menu():
    """Muestra un menú interactivo cuando no se pasan argumentos"""
    print("\n" + "=" * 60)
    print("MENÚ PRINCIPAL")
    print("=" * 60)
    print("\n1. 📥 Descargar versiones de OptiFine")
    print("2. 📄 Generar manifiesto de versiones")
    print("3. 🔄 Hacer ambos (Descargar + Manifiesto)")
    print("4. ❓ Mostrar ayuda completa")
    print("5. 🚪 Salir")
    print()
    
    while True:
        try:
            choice = input("Selecciona una opción [1-5]: ").strip()
            
            if choice == '1':
                return configure_and_run('download')
            elif choice == '2':
                return 'manifest', {}
            elif choice == '3':
                return configure_and_run('all')
            elif choice == '4':
                show_help()
                return None, {}
            elif choice == '5':
                print("\n👋 ¡Hasta luego!")
                return None, {}
            else:
                print("❌ Opción inválida. Por favor elige 1-5.")
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            return None, {}
        except EOFError:
            print("\n\n👋 ¡Hasta luego!")
            return None, {}

def configure_and_run(command):
    """Configura opciones para download o all"""
    print("\n" + "=" * 60)
    print("CONFIGURACIÓN DE DESCARGA")
    print("=" * 60)
    
    # Versión mínima
    print("\n📦 Versión mínima de Minecraft [default: 1.7.10]:")
    print("   Ejemplos: 1.16, 1.12, 1.8")
    min_version = input("   Versión: ").strip() or "1.7.10"
    
    # Incluir previews
    print("\n🔍 ¿Incluir versiones preview/beta? [S/n]:")
    include_previews = input("   Incluir: ").strip().lower()
    no_previews = include_previews == 'n'
    
    # Número de hilos
    print("\n⚡ Número de hilos de descarga [default: 15]:")
    print("   Rango recomendado: 5-50")
    threads_input = input("   Hilos: ").strip()
    try:
        threads = int(threads_input) if threads_input else 15
        threads = max(1, min(threads, 100))  # Limitar entre 1 y 100
    except ValueError:
        threads = 15
        print("   ⚠️  Valor inválido, usando 15 hilos")
    
    # Confirmación
    print("\n" + "=" * 60)
    print("RESUMEN DE CONFIGURACIÓN:")
    print("=" * 60)
    print(f"   • Comando: {command}")
    print(f"   • Versión mínima: Minecraft {min_version}")
    print(f"   • Incluir previews: {'No' if no_previews else 'Sí'}")
    print(f"   • Hilos: {threads}")
    print("=" * 60)
    
    confirm = input("\n¿Continuar con esta configuración? [S/n]: ").strip().lower()
    if confirm == 'n':
        print("\n❌ Operación cancelada")
        return None, {}
    
    config = {
        'min_version': min_version,
        'no_previews': no_previews,
        'threads': threads
    }
    
    return command, config

def main():
    # Si se pasa 'help' como argumento directo, mostrar ayuda
    if len(sys.argv) > 1 and sys.argv[1] == 'help':
        show_help()
        return
    
    show_banner()
    
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(
        description='PyOptifine Manager - Gestor completo de descargas OptiFine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        default=None,  # Cambiar a None para detectar cuando no se pasa comando
        choices=['download', 'manifest', 'all', 'help'],
        help='Comando a ejecutar'
    )
    
    parser.add_argument(
        '--min-version',
        default='1.7.10',
        help='Versión mínima de Minecraft a descargar (default: %(default)s)'
    )
    
    parser.add_argument(
        '--no-previews',
        action='store_true',
        help='No descargar versiones preview'
    )
    
    parser.add_argument(
        '--threads',
        type=int,
        default=15,
        help='Número máximo de hilos (default: %(default)s)'
    )
    
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Mostrar mensaje de ayuda'
    )
    
    args = parser.parse_args()
    
    # Mostrar ayuda si se solicita
    if args.help:
        show_help()
        return
    
    # Si no se pasó ningún comando, mostrar menú interactivo
    if args.command is None:
        command, config = show_interactive_menu()
        if command is None:
            return
        
        # Aplicar configuración del menú interactivo
        if config:
            args.min_version = config.get('min_version', args.min_version)
            args.no_previews = config.get('no_previews', args.no_previews)
            args.threads = config.get('threads', args.threads)
        
        args.command = command
    
    # Si el comando es help, mostrar ayuda
    if args.command == 'help':
        show_help()
        return
    
    # Mostrar configuración
    print(f"\n📁 Directorio de trabajo: {os.getcwd()}")
    
    print(f"\n⚙️  CONFIGURACIÓN:")
    print(f"   • Comando: {args.command}")
    print(f"   • Versión mínima: Minecraft {args.min_version}")
    print(f"   • Incluir previews: {'No' if args.no_previews else 'Sí'}")
    print(f"   • Hilos de descarga: {args.threads}")
    print()
    
    success = True
    
    # Ejecutar comando de descarga
    if args.command == 'download' or args.command == 'all':
        print("=" * 60)
        success = run_downloader(
            min_version=args.min_version,
            no_previews=args.no_previews,
            threads=args.threads
        ) and success
        
        if args.command == 'all':
            print("\n" + "=" * 60)
    
    # Ejecutar comando de manifiesto
    if args.command == 'manifest' or args.command == 'all':
        print("=" * 60)
        success = run_generate_manifest() and success
    
    # Mostrar resultado final
    print("\n" + "=" * 60)
    if success:
        print("✨ ¡Proceso completado exitosamente!")
    else:
        print("⚠️  El proceso completó con algunos errores")
    
    print("\n💡 Para más información ejecuta: python3 Main.py help")
    print("=" * 60)

if __name__ == "__main__":
    main()