# Claude Code Viewer 快速启动

## 🚀 一键启动

我为您创建了3个简单可靠的bat启动脚本：

### 1. `start-viewer-simple.bat` ⭐ 推荐
- **最简单直接的启动方式**
- 双击即可启动
- 访问：http://127.0.0.1:6300

### 2. `start-with-default-path.bat`
- 使用Claude Code默认路径
- 适合有真实Claude对话数据的用户
- 路径：`%USERPROFILE%\.claude\projects`

### 3. `start-with-test-data.bat`
- 使用测试数据启动
- 适合演示和测试
- 路径：`D:\Project\AI\test-claude-data`

## 📋 使用步骤

1. **双击任意bat文件** 启动程序
2. **等待提示** 看到 "Uvicorn running" 
3. **打开浏览器** 访问 http://127.0.0.1:6300
4. **停止程序** 在命令行窗口按 `Ctrl+C`

## ❗ 第一次使用

如果提示"uvicorn不是内部命令"，请先安装依赖：
```bash
pip install -e .
```

## 🎯 快速测试

推荐先用 `start-with-test-data.bat` 测试，因为我已经准备了测试数据。

---
*现在您可以方便地一键启动Claude Code Viewer了！*