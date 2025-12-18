import subprocess
from pathlib import Path
import shutil
import OptifinePatcher
import json

def create_basic_launcher_profiles(minecraft_dir: Path):
    profiles_file = minecraft_dir / "launcher_profiles.json"
    if profiles_file.exists():
        return

    basic_data = {
        "profiles": {},
        "selectedProfile": "",
        "authenticationDatabase": {},
    }

    profiles_file.write_text(json.dumps(basic_data, indent=2), encoding="utf-8")
    print(f"[INFO] launcher_profiles.json creado en {profiles_file}")

def execute_optifine(optifine_jar_path: str, minecraft_dir_path: str, java_cmd: str = "/usr/lib/jvm/java-latest-openjdk/bin/java"):
    base_dir = Path(__file__).parent.resolve()
    optifine_jar = Path(optifine_jar_path).expanduser().resolve()
    minecraft_dir = Path(minecraft_dir_path).expanduser().resolve()
    cfr_jar = (base_dir / "libraries" / "cfr-0.152.jar").resolve()
    if not optifine_jar.exists():
        raise FileNotFoundError(f"OptiFine jar no encontrado: {optifine_jar}")
    if not cfr_jar.exists():
        raise FileNotFoundError(f"cfr.jar no encontrado: {cfr_jar}")
    if not Path(java_cmd).exists():
        raise FileNotFoundError(f"Java no encontrado: {java_cmd}")

    minecraft_dir.mkdir(parents=True, exist_ok=True)
    create_basic_launcher_profiles(minecraft_dir)

    patched_jar = optifine_jar.parent / f"{optifine_jar.stem}_PATCHED.jar"
    work_dir = Path(".optifine_patch_work")

    if patched_jar.exists():
        patched_jar.unlink()
    if work_dir.exists():
        shutil.rmtree(work_dir)

    OptifinePatcher.patch_optifine_installer(
        optifine_jar=optifine_jar,
        output_jar=patched_jar,
        cfr_jar=cfr_jar,
        workdir=work_dir
    )

    OptifinePatcher.patch_manifest(
        jar_path=patched_jar,
        new_main_class="optifine.Installer"
    )

    if not patched_jar.exists():
        raise RuntimeError("No se generó el OptiFine parcheado")
    cmd = [java_cmd, "-jar", str(patched_jar), "--mcdir", str(minecraft_dir)]
    subprocess.run(cmd, check=True)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    if patched_jar.exists():
        patched_jar.unlink()
