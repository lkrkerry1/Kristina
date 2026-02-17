# Kristina 桌宠助手

Kristina 是一个运行在 Windows 本地、具有傲娇温柔性格的 Live2D 桌宠助手。她通过 Ollama 运行大语言模型，使用 Memoripy 实现长期记忆，并通过 Open-LLM-VTuner 提供交互界面和 Live2D 驱动。

## ✨ 特性

- **傲娇温柔性格**：根据预设的人格指令，在对话中表现出傲娇与温柔的一面。
- **长期记忆**：借助 Memoripy 自动存储对话历史，支持跨会话回忆。
- **动作标签**：回复中可插入 `[动作:名称]` 标签，用于驱动 Live2D 模型（需自行集成 VTube Studio）。
- **本地运行**：所有组件均在本地运行，无需依赖云端服务。

## 🛠️ 技术栈

- **前端交互**：Open-LLM-VTuner（透明窗口、TTS、Live2D 驱动接口）
- **大语言模型**：Ollama + `goekdenizguelmez/JOSIEFIED-Qwen2.5:7b`（中文优化，无审查）
- **嵌入模型**：Ollama + `nomic-embed-text`（用于记忆向量化）
- **长期记忆**：Memoripy（纯 Python，JSON 持久化）
- **语音合成**：Edge-TTS / VITS（可选）
- **Live2D 驱动**：VTube Studio（通过 WebSocket 接收动作指令）

## 📋 前提条件

- Windows 10/11 系统
- 已安装 [Ollama](https://ollama.com/) 并拉取所需模型：
  ```bash
  ollama pull goekdenizguelmez/JOSIEFIED-Qwen2.5:7b
  ollama pull nomic-embed-text
  ```
- Python 3.10+ 环境
- （可选）[VTube Studio](https://denchisoft.com/) 及一个 Live2D 模型
- （可选）[Docker Desktop](https://www.docker.com/products/docker-desktop/)（如需运行 Letta，但本方案不依赖）

## 🚀 快速开始

### 1. 克隆或准备 Open-LLM-VTuner

如果你还没有 Open-LLM-VTuner，请从官方仓库获取：
```bash
git clone https://github.com/Ikaros-521/open-llm-vtuber.git
cd open-llm-vtuber
```

### 2. 安装 Python 依赖

在项目根目录下创建虚拟环境（推荐）并安装依赖：
```bash
uv sync
```


### 3. 运行

启动 Open-LLM-VTuner（通常在项目根目录执行）：
```bash
uv run main.py
```

之后即可与 Kristina 对话。记忆文件将保存在项目根目录的 `kristina_memory.json` 中。

## 🎨 自定义与扩展

### 修改人格指令
编辑 `conf.yaml` 中的 `system_prompt` 即可调整 Kristina 的性格和语言风格。

### 调整记忆参数
- 在 `kristina_memory.py` 中可修改 `top_k`（检索条数）、相似度阈值等。
- Memoripy 支持记忆衰减、时间权重等高级特性，可参考其文档。

### 集成 Live2D 动作
1. 在 VTube Studio 中为模型配置好动作热键。
2. 在 Open-LLM-VTuner 的输出处理中添加解析逻辑，提取 `[动作:名称]` 标签。
3. 通过 WebSocket 向 VTube Studio 发送指令（具体格式参考 VTube Studio API）。

### 更换 TTS
在 `conf.yaml` 中配置 `tts_config` 选择 Edge-TTS 或 VITS。

## ❓ 故障排除

### 记忆不生效
- 检查 `kristina_memory.json` 是否生成，文件内容是否包含对话记录。
- 确认在 `add_message` 中存储逻辑被调用（可添加 print 调试）。
- 检查 `retrieve_relevant` 的返回值是否为空，尝试降低相似度阈值。

### 对话卡顿或错误
- 确保 Ollama 服务正常运行，且模型已拉取。
- 检查 Ollama API 地址是否与 `conf.yaml` 中的 `base_url` 一致。
- 查看 Open-LLM-VTuner 的控制台输出，定位具体错误。

### 动作标签未解析
- 确认系统提示中包含生成标签的指令。
- 检查模型是否真的输出了标签（可在控制台查看原始回复）。
- 实现解析函数并在输出前调用。


## 📜 许可证

本项目遵循 MIT 许可证。

---

现在，启动 Kristina 开始你们的对话吧！如有任何问题，欢迎提交 Issue。