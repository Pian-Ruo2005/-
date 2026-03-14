# 小韩的空间

小韩在偷偷学 🚀

## 🖥️ 如何打开前端页面

### 方法一：直接双击（最简单）

找到项目文件夹，**双击 `index.html`**，浏览器会自动打开页面。

> ✅ 无需安装任何工具，零依赖，开箱即用。

---

### 方法二：使用 VS Code + Live Server（推荐开发时使用）

1. 安装 [Visual Studio Code](https://code.visualstudio.com/)
2. 在 VS Code 扩展商店搜索并安装 **Live Server**
3. 右键点击 `index.html` → 选择 **"Open with Live Server"**
4. 浏览器自动打开，修改文件时页面实时刷新

---

### 方法三：使用 Python 本地服务器

如果你安装了 Python，在项目目录下打开终端，运行：

```bash
# Python 3
python -m http.server 8080

# Python 2
python -m SimpleHTTPServer 8080
```

然后在浏览器中访问：**http://localhost:8080**

---

### 方法四：一键启动脚本

**macOS / Linux：**

```bash
# 赋予执行权限（只需一次）
chmod +x serve.sh

# 启动
./serve.sh
```

**Windows：**

双击运行 `serve.bat`

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `index.html` | 前端页面（全部内容，零依赖） |
| `serve.sh` | macOS/Linux 一键启动脚本 |
| `serve.bat` | Windows 一键启动脚本 |
