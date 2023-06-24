from PyInstaller.utils.hooks import get_package_paths

datas = [(get_package_paths('uvicorn')[1], 'uvicorn')]