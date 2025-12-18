#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path

# Añadir src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from src.OptifineExecuting import execute_optifine
except ImportError:
    execute_optifine = None

def show_banner():
    print("""
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
        ╚════════════════════════════════════════════════════════════════╗                    ╔══╝
        ╔════════════════════════════════════════════════════════════════╝                    ╚══╗
        ║ PyOptifine Manager                                                                     ║
        ║ Gestor completo de descargas OptiFine                                                  ║
        ╚════════════════════════════════════════════════════════════════════════════════════════╝
        """)

def run_downloader(min_version="1.7.10", no_previews=False, threads=15):
    print("🔽 Descargando versiones de OptiFine...\n")
    try:
        import OptifineDownloader
        OptifineDownloader.set_config(
            MIN_VERSION=min_version,
            MAX_THREADS=threads,
            DOWNLOAD_PREVIEWS=not no_previews,
            DOWNLOAD_CHANGELOGS=True
        )
        OptifineDownloader.main()
        return True
    except ImportError as e:
        print(f"\n❌ No se pudo importar OptifineDownloader: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error en el descargador: {e}")
        import traceback; traceback.print_exc()
        return False

def run_generate_manifest():
    print("📄 Generando manifiesto de versiones...\n")
    try:
        import GenerateManifest
        if hasattr(GenerateManifest, 'main'):
            GenerateManifest.main()
        else:
            manifest = GenerateManifest.scrape_optifine_manifest()
            if manifest:
                import json
                with open('optifine_mirror_manifest.json', 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                print(f"\n✅ Manifiesto creado: 'optifine_mirror_manifest.json' ({len(manifest)} enlaces)")
            else:
                print("\n⚠️ No se encontraron datos")
        return True
    except ImportError as e:
        print(f"\n❌ No se pudo importar GenerateManifest: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error generando manifiesto: {e}")
        import traceback; traceback.print_exc()
        return False

def show_help():
    print("""
PyOptifine Manager - Gestor completo de descargas OptiFine

COMANDOS DISPONIBLES:
  download    - Descargar versiones de OptiFine
  manifest    - Generar manifiesto de versiones
  all         - Ejecutar ambos (download + manifest)
  patch       - Parchear y ejecutar OptiFine installer
  help        - Mostrar ayuda

OPCIONES:
  --min-version VERSION  - Versión mínima de Minecraft (default: 1.7.10)
  --no-previews          - No descargar versiones preview
  --threads NUMERO       - Máx. hilos de descarga (default: 15)
""")

def show_interactive_menu():
    print("\n" + "="*60)
    print("MENÚ PRINCIPAL")
    print("="*60)
    print("1. 📥 Descargar versiones de OptiFine")
    print("2. 📄 Generar manifiesto de versiones")
    print("3. 🔄 Descargar + Generar manifiesto")
    print("4. ⚙️ Parchear y ejecutar OptiFine")
    print("5. ❓ Mostrar ayuda")
    print("6. 🚪 Salir\n")
    
    while True:
        try:
            choice = input("Selecciona una opción [1-6]: ").strip()
            if choice == '1': return configure_and_run('download')
            elif choice == '2': return 'manifest', {}
            elif choice == '3': return configure_and_run('all')
            elif choice == '4': return 'patch', {}
            elif choice == '5': show_help(); return None, {}
            elif choice == '6': print("\n👋 ¡Hasta luego!"); return None, {}
            else: print("❌ Opción inválida, elige 1-6.")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 ¡Hasta luego!"); return None, {}

def configure_and_run(command):
    min_version = input("\n📦 Versión mínima de Minecraft [default: 1.7.10]: ").strip() or "1.7.10"
    include_previews = input("🔍 ¿Incluir versiones preview/beta? [S/n]: ").strip().lower()
    no_previews = include_previews == 'n'
    threads_input = input("⚡ Número de hilos [default: 15]: ").strip()
    
    try: threads = int(threads_input) if threads_input else 15; threads = max(1, min(threads, 100))
    except ValueError: threads = 15; print("⚠️ Valor inválido, usando 15 hilos")
    
    print("\nResumen de configuración:")
    print(f"• Comando: {command}, Versión mínima: {min_version}, Previews: {'No' if no_previews else 'Sí'}, Hilos: {threads}")
    
    confirm = input("¿Continuar? [S/n]: ").strip().lower()
    if confirm == 'n': print("\n❌ Operación cancelada"); return None, {}
    
    return command, {'min_version': min_version, 'no_previews': no_previews, 'threads': threads}

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'help': show_help(); return
    show_banner()
    
    parser = argparse.ArgumentParser(description='PyOptifine Manager', add_help=False)
    parser.add_argument('command', nargs='?', choices=['download','manifest','all','patch','help'])
    parser.add_argument('--min-version', default='1.7.10')
    parser.add_argument('--no-previews', action='store_true')
    parser.add_argument('--threads', type=int, default=15)
    parser.add_argument('-h','--help', action='store_true')
    args = parser.parse_args()
    
    if args.help: show_help(); return
    
    if args.command is None:
        command, config = show_interactive_menu()
        if command is None: return
        if config: args.min_version=config.get('min_version',args.min_version); args.no_previews=config.get('no_previews',args.no_previews); args.threads=config.get('threads',args.threads)
        args.command = command
    
    print(f"\n📁 Directorio de trabajo: {os.getcwd()}")
    print(f"\n⚙️ CONFIG: Comando={args.command}, MinVersion={args.min_version}, Previews={'No' if args.no_previews else 'Sí'}, Hilos={args.threads}\n")
    
    success = True
    if args.command in ['download','all']: success = run_downloader(args.min_version,args.no_previews,args.threads) and success
    if args.command in ['manifest','all']: success = run_generate_manifest() and success
    
    if args.command == 'patch':
        if execute_optifine is None: print("❌ OptifineExecutor no disponible"); return
        optifine_jar = input("Ruta al OptiFine installer (.jar): ").strip()
        minecraft_dir = input("Ruta al directorio .minecraft: ").strip()
        try: execute_optifine(optifine_jar, minecraft_dir); print("✅ OptiFine parcheado y ejecutado con éxito")
        except Exception as e: print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✨ ¡Proceso completado!" if success else "⚠️  Proceso con errores")
    print("\n💡 Para más info: python3 Main.py help")
    print("="*60)

if __name__ == "__main__":
    main()
