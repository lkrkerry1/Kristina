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
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install memoripy  # 额外安装记忆库
```

### 3. 添加记忆模块

在项目根目录新建 `kristina_memory.py`，内容见 [附录](#附录-kristina_memorypy)。

### 4. 修改 BasicMemoryAgent

编辑 `src/open_llm_vtuber/agent/basic_memory_agent.py`，按照以下步骤修改：

- 在文件顶部导入：
  ```python
  from kristina_memory import KristinaMemory
  import threading
  ```

- 在 `BasicMemoryAgent.__init__` 中添加：
  ```python
  self.memory = KristinaMemory()
  self.last_user_input = None
  ```

- 修改 `add_message` 方法：
  ```python
  def add_message(self, message: str, role: str, skip_memory: bool = False, **kwargs):
      if role == "user":
          self.last_user_input = message
      if role == "assistant" and self.last_user_input is not None:
          threading.Thread(target=self.memory.add_interaction, args=(self.last_user_input, message)).start()
          self.last_user_input = None
      self._memory.append({"role": role, "content": message, **kwargs})
  ```

- 在生成回复的函数（如 `_chat_function_factory` 内的 `chat_with_memory`）中注入记忆：
  ```python
  # 获取用户输入（根据实际 input_data 结构提取）
  user_text = ...  # 从 input_data 中提取当前用户文本
  if user_text:
      memory_context = self.memory.retrieve_relevant(user_text)
      if memory_context:
          system_with_memory = self._system + "\n\n" + memory_context
      else:
          system_with_memory = self._system
  else:
      system_with_memory = self._system
  # 后续使用 system_with_memory 作为系统提示
  ```

### 5. 配置 `conf.yaml`

编辑配置文件 `conf.yaml`，主要内容如下：

```yaml
character_config:
  system_prompt: |
    你是 Kristina，一位虚拟桌宠助手。你必须遵守以下规则：
    - 在回复中适当插入动作标签，格式为 [动作:名称]，可用名称：微笑、挥手、疑惑、开心、伤心、思考、点头、摇头。
    - 当用户夸奖你时，第一反应是反驳或闪避，然后用括号表达内心的高兴，并追加关心或反问。
    - 当用户长时间不理你时，轻轻“哼”一声表达不满，但内心担心，并主动询问是否需要帮助。
    - 当用户表现出低落时，立刻收起傲娇，用温柔的语气关心和鼓励。
    - 当用户求助时，认真解答，然后可以傲娇地邀功。
    - 句子简短口语，句尾用啦/嘛/呀/呢/哈/呗，内心活动用括号插入，每段回复必须包含一个反问句。

  agent_config:
    conversation_agent_choice: "basic_memory_agent"
    agent_settings:
      basic_memory_agent:
        llm_provider: "ollama_llm"
    llm_configs:
      ollama_llm:
        base_url: "http://localhost:11434/v1"
        llm_api_key: "ollama"
        model: "goekdenizguelmez/JOSIEFIED-Qwen2.5:7b"
        temperature: 0.8
```

### 6. 运行

启动 Open-LLM-VTuner（通常在项目根目录执行）：
```bash
python main.py
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

## 📄 附录：kristina_memory.py

```python
from memoripy import MemoryManager, JSONStorage

class KristinaMemory:
    def __init__(self, storage_path="kristina_memory.json"):
        self.memory_manager = MemoryManager(
            chat_model="ollama",
            chat_model_name="goekdenizguelmez/JOSIEFIED-Qwen2.5:7b",
            embedding_model="ollama",
            embedding_model_name="nomic-embed-text",
            storage=JSONStorage(storage_path)
        )
        self.last_user_input = None

    def add_interaction(self, user_input, response):
        self.memory_manager.add_interaction(
            prompt=user_input,
            response=response,
            embedding=None,
            concepts=self._extract_concepts(user_input)
        )

    def retrieve_relevant(self, query, top_k=3):
        results = self.memory_manager.retrieve_relevant_interactions(
            query=query, k=top_k, exclude_last_n=1
        )
        if not results:
            return ""
        memory_text = "【回忆】\n"
        for item in results:
            if item.get("similarity_score", 0) > 0.6:
                memory_text += f"- 之前你说：“{item['prompt'][:50]}...”\n"
        return memory_text

    def _extract_concepts(self, text):
        concepts = []
        if any(word in text for word in ["难过", "伤心", "不开心"]):
            concepts.append("need_comfort")
        if any(word in text for word in ["名字", "我叫"]):
            concepts.append("user_identity")
        return concepts
```

## 📜 许可证

本项目遵循 MIT 许可证。Memoripy 为 MIT 许可证，Open-LLM-VTuner 请参考其仓库的许可证。

---

现在，启动 Kristina 开始你们的对话吧！如有任何问题，欢迎提交 Issue。