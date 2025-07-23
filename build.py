import os
import subprocess

exe_name = "Riwing"
main_script = "main.py"
icon_path = "icon.ico"
hidden_imports = [
    "controller",
    "model",
    "view",
    "worker",
    "apps"
]

cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onefile",
    f"--name={exe_name}",
    "--distpath=dist",   
    "--workpath=build",     
    f"--icon={icon_path}"
]

for module in hidden_imports:
    cmd.append(f"--hidden-import={module}")

cmd.append(main_script)

subprocess.run(cmd)

for item in ["__pycache__", "build", "main.spec"]:
    if os.path.isdir(item):
        os.system(f"rmdir /s /q {item}")
    elif os.path.isfile(item):
        os.remove(item)

print(f"[✔] Executável gerado com sucesso em /dist/{exe_name}.exe")
