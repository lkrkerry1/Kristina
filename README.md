# Kristina - 傲娇AI桌宠

Kristina 是一个运行在 Windows 本地、具有拟人化傲娇性格、长期记忆、支持语音交互和 Live2D 形象驱动的桌面宠物 AI 助手。她住在你的电脑桌面角落，会用傲娇但温柔的语气陪伴你、帮你解决问题，并逐渐记住你的喜好。

![Kristina 示例](docs/preview.png) <!-- 可替换为实际截图 -->

## ✨ 功能特点

- **拟人性格**：傲娇、幽默、内心温柔，会根据对话情境自然切换语气（系统提示词精心设计）。
- **长期记忆**：通过 PowerMem 记住你的生日、喜好、过往对话，随着交流越来越懂你。
- **本地运行**：所有处理均在本地完成，保护隐私，无需联网（除可选的 TTS 外）。
- **语音交互**：支持语音输入（Sherpa-Onnx ASR）和语音输出（Piper TTS 离线合成），告别机械感。
- **Live2D 驱动**：计划支持通过表情标签控制 Live2D 模型，让形象更加生动。
- **高度可定制**：基于 Open-LLM-VTuber 框架，可自由更换 LLM、TTS、记忆引擎等组件。

## 🧠 技术架构

- **核心框架**：[Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)（定制修改版）
- **LLM 引擎**：Ollama + `goekdenizguelmez/JOSIEFIED-Qwen2.5:7b`（中文优化、角色扮演强）
- **嵌入模型**：Ollama + `nomic-embed-text`（用于记忆向量化）
- **长期记忆**：PowerMem（SQLite 存储，轻量无依赖）
- **语音合成**：Piper TTS（离线，中文自然）
- **语音识别**：Sherpa-Onnx ASR（离线）
- **形象驱动**：VTube Studio（通过 WebSocket 集成，计划中）

## 🚀 快速开始

### 环境要求

- Windows 10/11 或 Linux（主推 Windows）
- Python 3.10
- Ollama（已安装并运行，拉取了所需模型）
- 至少 8GB 内存，推荐 16GB
- 麦克风（可选，用于语音输入）

### 安装步骤

1. **克隆项目**（注意包含子模块）
   ```bash
   git clone --recursive https://github.com/yourname/Kristina.git
   cd Kristina
   ```

2. **创建虚拟环境**
   ```bash
   uv sync
   ```


3. **下载模型文件**
   - **Ollama 模型**（确保 Ollama 已运行）：
     ```bash
     ollama pull goekdenizguelmez/JOSIEFIED-Qwen2.5:7b
     ollama pull nomic-embed-text
     ```
   - **Piper TTS 模型**：
     从 [HuggingFace](https://huggingface.co/csukuangfj/vits-piper-zh_CN-huayan-medium) 下载以下文件，放入 `models/piper/` 目录：
     - `zh_CN-huayan-medium.onnx`
     - `tokens.txt`
     - `MODEL_CARD`（可选）

4. **配置**
   复制 `conf.yaml.example` 为 `conf.yaml`，根据需要修改（模型路径、API 地址等）。默认配置已适配本地 Ollama 和 Piper TTS。

5. **启动**
   ```bash
   uv run main.py
   ```
   访问 `http://localhost:12393` 即可与 Kristina 对话（支持语音输入需配置麦克风）。

## ⚙️ 配置详解

主配置文件 `conf.yaml` 包含所有模块设置。关键部分：

### LLM 配置
```yaml
agent_settings:
  basic_memory_agent:
    llm_provider: ollama_llm   # 使用原生 ollama LLM
    faster_first_response: true
    segment_method: pysbd
    use_mcpp: false             # 暂时禁用 MCP 工具
    mcp_enabled_servers:
      - time
      - ddg-search

llm_configs:
  ollama_llm:
    interrupt_method: system
    base_url: http://localhost:11434
    model: goekdenizguelmez/JOSIEFIED-Qwen2.5:7b
    temperature: 0.8
    keep_alive: -1.0
    unload_at_exit: true
    stream: true                 # 启用流式输出
```

### 记忆配置（PowerMem）
```yaml
agent_settings:
  custom_agents.powermem_agent.PowerMemAgent:
    llm_provider: ollama_llm
    powermem_user_id: kristina
    powermem_data_dir: ./powermem_data
    memory_top_k: 3
    memory_threshold: 0.6
    powermem_embed_config:
      provider: ollama
      model: nomic-embed-text
      base_url: http://localhost:11434
```

### TTS 配置
```yaml
tts_model: piper_tts
piper_tts:
  model_path: models/piper/zh_CN-huayan-medium.onnx
  speaker_id: 0
  length_scale: 1.0          # 语速
  noise_scale: 0.667          # 声音变化
  noise_w: 0.8                # 风格变化
  use_cuda: false             # CPU 运行
```

### ASR 配置（语音输入）
```yaml
asr_model: sherpa_onnx_asr
sherpa_onnx_asr:
  model_type: sense_voice
  sense_voice: ./models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.int8.onnx
  tokens: ./models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tokens.txt
  num_threads: 4
  provider: cpu
  use_itn: true
```

## 🎭 自定义你的 Kristina

### 修改性格
编辑 `service_context.py` 中的 `construct_system_prompt` 方法，调整人格描述、语言风格、示例等。当前 prompt 已包含：
- 傲娇表现模式
- 温柔陪伴指令
- 语言风格强制规则（短句、语气词、内心括号、反问句）
- 表情标签示例

### 更换 LLM
支持多种 LLM 后端（Ollama、OpenAI、Gemini 等），只需修改 `llm_provider` 和相应配置。例如改用 OpenAI：
```yaml
llm_provider: openai_llm
openai_llm:
  base_url: https://api.openai.com/v1
  llm_api_key: sk-xxxx
  model: gpt-4
```

### 更换 TTS
在 `conf.yaml` 中更改 `tts_model` 为 `edge_tts`、`coqui_tts`、`gpt_sovits` 等，并配置对应参数。例如改用 Edge-TTS：
```yaml
tts_model: edge_tts
edge_tts:
  voice: zh-CN-XiaoxiaoNeural
```

### 添加自定义工具（未来）
计划支持通过 MCP 协议添加工具，如计算器、天气查询等，让 Kristina 具备实时计算能力。

## 📁 项目结构
```
Kristina/
├── Open-LLM-VTuber/          # 子仓库（定制修改版）
│   └── src/open_llm_vtuber/
│       ├── agent/
│       ├── config_manager/
│       └── ...
├── custom_agents/            # 自定义 Agent
│   └── powermem_agent.py      # PowerMem 集成
├── powermem_data/             # 记忆数据库（自动生成）
├── models/                    # 存放 TTS、ASR 等模型文件
│   └── piper/
│       ├── zh_CN-huayan-medium.onnx
│       └── tokens.txt
├── conf.yaml                  # 主配置文件
├── run.py                     # 启动脚本（管理路径、调用子仓库）
├── requirements.txt           # Python 依赖
└── README.md                  # 本文档
```

## 🔧 常见问题

### Q: 语音合成失败怎么办？
A: 
- 确认 Piper 模型路径正确，且文件完整。
- 检查 `piper_tts` 配置中的 `model_path` 是否指向 `.onnx` 文件。
- 若仍失败，可临时切换到 Edge-TTS 测试网络连通性。

### Q: 记忆不生效？
A: 
- 检查 PowerMem 配置是否正确，确保 `powermem_data_dir` 有写入权限。
- 首次使用需对话几条才会积累记忆，可查看 `powermem_data/kristina_memory.db` 是否存在。
- 日志中应有 `Retrieved X relevant memories` 字样，表示检索成功。

### Q: 如何启用 Live2D？
A: Live2D 驱动正在开发中，请关注后续更新。目前可使用静态头像（配置 `avatar` 字段）。

### Q: 头像不显示？
A: 检查 `conf.yaml` 中 `avatar` 字段是否指向 `avatars/` 目录下的图片，且文件名正确。若仍为 `null`，可在 `conversation_utils.py` 的 `handle_sentence_output` 中添加默认头像逻辑（参见常见修改记录）。

### Q: 流式输出不起作用？
A: 
- 确认 `ollama_llm` 配置中 `stream: true`。
- 检查 `ollama_llm.py` 是否已修改为支持流式（参考之前讨论的代码）。
- 目前前端支持 `sentence` 类型逐句显示，若需逐字显示需额外开发。

## 🗺️ 未来计划

- [x] 基础对话与记忆
- [x] 离线 TTS 支持（Piper）
- [ ] 流式输出恢复
- [ ] 工具调用（日期计算、搜索等）
- [ ] Live2D 动作驱动
- [ ] 一键安装脚本
- [ ] 更多语言支持
- [ ] 表情标签与 VTube Studio 集成

## 🤝 贡献

欢迎提交 Issue 和 PR！如果你想参与开发，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。特别感谢 [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) 项目提供的强大框架。

## 📄 许可证

本项目基于 MIT 许可证开源。