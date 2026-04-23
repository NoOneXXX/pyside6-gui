## 1, 初始化文档到GitHub上去，创建私有库
1. 点击右上角 + → New repository
2. Repository name：填入仓库名（建议和本地项目同名）
3. Description：可选，写点描述
4. Visibility：选择 Private（私有）
5. Initialize this repository with：全部不要勾选！（不要勾选 README、.gitignore、license）
6. 点击绿色按钮 Create repository
## 2,实例化项目
```shell
git init # 初始化项目
git add . #将文件加到缓存区
git commit -m "Initial commit"
git branch -M master
git remote add origin https://github.com/NoOneXXX/fetureNotes.git
git push -u origin master # 推送上去
```
```shell
# 1. 最基础查看日志
git log

# 2. 推荐：简洁 + 分支图形（最常用）
git log --oneline --graph --decorate --all

# 3. 简洁一行显示（最常用）
git log --oneline
```


