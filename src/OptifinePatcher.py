import subprocess
import zipfile
import shutil
import re
from pathlib import Path

def patch_optifine_installer( optifine_jar: Path, output_jar: Path, cfr_jar: Path, workdir: Path | None = None ):
    optifine_jar = optifine_jar.resolve()
    output_jar = output_jar.resolve()
    cfr_jar = cfr_jar.resolve()

    work = workdir or Path(".optifine_patch_work")
    src = work / "src"
    bin = work / "bin"
    installer_class_path = "optifine/Installer.class"

    if work.exists():
        shutil.rmtree(work)
    src.mkdir(parents=True)
    bin.mkdir(parents=True)

    with zipfile.ZipFile(optifine_jar, "r") as jar:
        jar.extract(installer_class_path, work)
    installer_class = work / installer_class_path

    subprocess.run(
        ["java", "-jar", str(cfr_jar), str(installer_class),
         "--outputdir", str(src), "--silent", "true"],
        check=True
    )

    installer_java = src / "optifine" / "Installer.java"
    if not installer_java.exists():
        raise RuntimeError("CFR no generó Installer.java")

    code = installer_java.read_text(encoding="utf-8")

    if not re.search(r'^\s*package\s+optifine\s*;', code, re.MULTILINE):
        m = re.match(r'(\s*(/\*.*?\*/\s*)*)', code, re.DOTALL)
        insert_at = m.end() if m else 0
        code = code[:insert_at] + "\npackage optifine;\n\n" + code[insert_at:]

    pattern = re.compile(r'File\s+(\w+)\s*=\s*Utils\.getWorkingDirectory\s*\(\s*\)\s*;', re.MULTILINE)
    match = pattern.search(code)
    if not match:
        raise RuntimeError("No se encontró Utils.getWorkingDirectory()")
    var = match.group(1)

    replacement = f"""File {var} = null;
        for (int i = 0; i < args.length; i++) {{
            if (args[i].equals("--mcdir") && i + 1 < args.length) {{
                {var} = new File(args[++i]);
            }}
        }}
        if ({var} == null) {{
            {var} = Utils.getWorkingDirectory();
        }}
    """
    
    code = pattern.sub(replacement, code, count=1)
    installer_java.write_text(code, encoding="utf-8")

    subprocess.run(
        ["javac", "--release", "8", "-classpath", str(optifine_jar), "-d", str(bin), str(installer_java)],
        check=True
    )
    patched_class = bin / "optifine" / "Installer.class"
    if not patched_class.exists():
        raise RuntimeError("Falló la recompilación del Installer.class")

    with zipfile.ZipFile(optifine_jar, "r") as jar_in, zipfile.ZipFile(output_jar, "w") as jar_out:
        for item in jar_in.infolist():
            if item.filename == installer_class_path:
                continue
            jar_out.writestr(item, jar_in.read(item.filename))
        jar_out.write(patched_class, installer_class_path)

    shutil.rmtree(work)

def patch_manifest(jar_path: Path, new_main_class: str):
    jar_path = jar_path.resolve()
    manifest_path = "META-INF/MANIFEST.MF"

    with zipfile.ZipFile(jar_path, "r") as jar:
        try:
            manifest = jar.read(manifest_path).decode("utf-8")
        except KeyError:
            manifest = "Manifest-Version: 1.0\n"

        lines = manifest.splitlines()
        out = []
        replaced = False
        for line in lines:
            if line.startswith("Main-Class:"):
                out.append(f"Main-Class: {new_main_class}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            out.append(f"Main-Class: {new_main_class}")

        new_manifest = "\n".join(out).strip() + "\n"

    temp_jar = jar_path.with_suffix(".temp.jar")
    with zipfile.ZipFile(jar_path, "r") as jar_in, zipfile.ZipFile(temp_jar, "w") as jar_out:
        for item in jar_in.infolist():
            if item.filename == manifest_path:
                continue
            jar_out.writestr(item, jar_in.read(item.filename))
        jar_out.writestr(manifest_path, new_manifest)

    temp_jar.replace(jar_path)
