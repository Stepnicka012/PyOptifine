<div align="center">
<pre>
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
</pre>
</div>

**PyOptifine** es un **gestor avanzado de descargas de OptiFine** escrito en **Python**, diseñado para automatizar, organizar y centralizar la obtención de todas las versiones disponibles de OptiFine directamente desde sus mirrors oficiales.

El proyecto está pensado tanto para **usuarios avanzados** como para **desarrolladores de launchers**, scripts o herramientas que necesiten **control total sobre las versiones de OptiFine**, sin depender de descargas manuales.

---

## 🚀 Características principales

* 📥 **Descarga automática de OptiFine**

  * Descarga todas las versiones disponibles desde OptiFine.net
  * Soporta versiones **estables y preview/beta**
  * Permite definir una **versión mínima de Minecraft**

* ⚡ **Descargas en paralelo**

  * Uso de **multithreading** configurable
  * Mucho más rápido que descargas secuenciales

* 📄 **Generación de manifiesto JSON**

  * Crea un archivo con metadata completa de todas las versiones encontradas
  * Ideal para integrarlo en launchers o sistemas externos

* 🧠 **Detección inteligente**

  * Omite archivos ya descargados
  * Evita duplicados automáticamente

* 🖥️ **CLI + menú interactivo**

  * Modo línea de comandos para automatización
  * Menú interactivo si no se pasan argumentos

* 📦 **Arquitectura modular**

  * Downloader y generador de manifiesto desacoplados
  * Fácil de extender o integrar en otros proyectos

---

## 🛠️ Requisitos

* Python **3.8+**
* Sistema operativo: **Linux / Windows / macOS**
* Conexión a internet

No requiere dependencias externas pesadas.

---

## ▶️ Uso básico

### Mostrar ayuda

```bash
python3 Main.py help
```

### Descargar todas las versiones desde Minecraft 1.16

```bash
python3 Main.py download --min-version 1.16
```

### Descargar sin previews (solo versiones estables)

```bash
python3 Main.py download --no-previews
```

### Descargar usando 10 hilos

```bash
python3 Main.py download --threads 10
```

### Generar solo el manifiesto

```bash
python3 Main.py manifest
```

### Ejecutar todo (descarga + manifiesto)

```bash
python3 Main.py all --min-version 1.12 --threads 20
```

---

## 🧭 Menú interactivo

Si ejecutás el script **sin argumentos**, PyOptifine muestra un menú interactivo:

```bash
python3 Main.py
```

Desde ahí podés:

* Configurar versión mínima
* Elegir si incluir previews
* Ajustar número de hilos
* Ejecutar todo sin escribir comandos

---

## 📄 Manifiesto JSON

El manifiesto generado incluye:

* Versión de Minecraft
* Versión de OptiFine
* Tipo (estable / preview)
* URLs reales de descarga
* Información útil para launchers

Ideal para:

* Launchers personalizados
* Mirrors
* Sistemas de cache
* Automatización

```json
[
  {
    "minecraft_version": "1.21.10",
    "optifine_version": "OptiFine HD U J7 pre11",
    "mirror_url": "http://optifine.net/adloadx?f=preview_OptiFine_1.21.10_HD_U_J7_pre11.jar",
    "forge_version": "Forge 60.1.0",
    "release_date": "03.12.2025",
    "filename": "preview_OptiFine_1.21.10_HD_U_J7_pre11.jar",
    "changelog_url": "changelog?f=preview_OptiFine_1.21.10_HD_U_J7_pre11.jar"
  },
  {
    "minecraft_version": "1.21.10",
    "optifine_version": "OptiFine HD U J7 pre10",
    "mirror_url": "http://optifine.net/adloadx?f=preview_OptiFine_1.21.10_HD_U_J7_pre10.jar",
    "forge_version": "Forge 60.1.0",
    "release_date": "02.12.2025",
    "filename": "preview_OptiFine_1.21.10_HD_U_J7_pre10.jar",
    "changelog_url": "changelog?f=preview_OptiFine_1.21.10_HD_U_J7_pre10.jar"
  },
    Etc...
```


---

## ⚠️ Notas importantes

* PyOptifine **NO modifica** los archivos `.jar`
* **NO parchea** OptiFine
* **NO instala** OptiFine en Minecraft

👉 Su función es **descargar, organizar y exponer información**, dejando la instalación al launcher o herramienta que lo consuma.

---

## 📜 Licencia

Uso educativo y de desarrollo.
OptiFine es propiedad de sus respectivos autores.
