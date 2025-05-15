## 使用这个命令将ui文件转换成py文件 只有转换了这个文件 pyside6才能识别 否则就无法识别不能加载

```shell
-- window的命令
pyside6-uic .\pyside6-mainwindow.ui -o ui_main_window.py
-- mac/linux 
pyside6-uic pyside6-mainwindow.ui -o ui_main_window.py
```

## 将qrc文件打包成py文件
### 这个py文件生成后就可以直接的在main中引用 使用qrc文件的优势是会将image的二进制文件直接转成py文件可以引用 
### 这样打包的时候就不用再打包images文件夹了 直接的就可以引用 性能更好 更好维护 防止路径问题
```shell
pyside6-rcc gui/ui/resource.qrc -o gui/ui/resource_rc.py
```