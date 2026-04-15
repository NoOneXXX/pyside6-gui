## 使用这个命令将ui文件转换成py文件 只有转换了这个文件 pyside6才能识别 否则就无法识别不能加载

```shell
-- window的命令
pyside6-uic .\pyside6-mainwindow.ui -o ui_main_window.py
-- mac/linux 
pyside6-uic pyside6-mainwindow.ui -o ui_main_window.py
```
### 如果要更换图标就执行gui/func/utils/branch_image_gen/create_plus_add2.py和create_minus_add2.py这两个文件生成图标
### 然后执行下面得命令生成对应得图标qrc文件
```shell
pyside6-rcc gui/ui/resource.qrc -o gui/ui/resource_rc.py
```

## 将qrc文件打包成py文件
### 这个py文件生成后就可以直接的在main中引用 使用qrc文件的优势是会将image的二进制文件直接转成py文件可以引用 
### 这样打包的时候就不用再打包images文件夹了 直接的就可以引用 性能更好 更好维护 防止路径问题
```shell
pyside6-rcc gui/ui/resource.qrc -o gui/ui/resource_rc.py
```



## 上面两步执行完成后就直接的执行下面命令打包，mac和window都可以用下面的命令打包，只是mac版本的要在mac电脑上操作，windows版本的要在window系统上操作
```shell
python build.py
```

### git的代理推送，git默认是不走系统代理的，哪怕你用了clash开启了系统代理模式
```shell
git -c http.proxy="http://127.0.0.1:7890" push
```
pip freeze > requirements.txt