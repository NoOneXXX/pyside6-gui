import os

AUTHOR = 'Echo'
VERSION = '1.0.0'
app_name = 'KeepnotePlus'

build_command = "nuitka --standalone --mingw64 --enable-plugin=pyside6 "
build_command += "--windows-disable-console "
build_command += "--windows-icon-from-ico=gui/images/icon/keepnotesPlus.ico --output-dir=out "
build_command += f"--windows-company-name={AUTHOR}  --windows-product-name={app_name} "
build_command += f"--windows-product-version={VERSION} "
# 打包成功后要手动的加上gui/ui/qss/light.qss这个文件和这个文件夹下的其他文件
build_command += "--follow-import-to=gui "
build_command += "main.py  --lto=no "
# ========
# 运行pack_resources.py 如果这两个文件已经生成了就不要运行这个代码
# 没有必要重复的生成，因为这样也会让已经修改的文件出现问题
# ========
# os.system("python pack_resources.py")
print(build_command)
os.system(build_command)  # 打包
