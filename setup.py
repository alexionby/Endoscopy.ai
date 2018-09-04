import os
from cx_Freeze import setup, Executable

include_files = ["static/" , "templates/", "models/", "model_cnn/", "parameters/"]

build_exe_options = {"packages": ["keras","numpy","tensorflow","scipy","skimage","google","flask","asyncio","jinja2"], 
                     "excludes": ["tkinter","PyQt5"], 
                     "include_files": include_files,
                     "optimize": 0
                    }

setup(
    name = "Endoscopy.ai",
    version = "0.2.1",
    description = "Endoscopy.ai",
    executables = [Executable("app.py")],
    options = {"build_exe": build_exe_options},
)
