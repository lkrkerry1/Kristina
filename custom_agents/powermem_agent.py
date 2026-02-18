# custom_agents/powermem_agent.py
import asyncio
from datetime import datetime
from typing import AsyncIterator, Union, Dict, Any

from loguru import logger  # 导入 loguru

from powermem import Memory, auto_config

# 导入父类（需要确保 Python 路径正确）
from open_llm_vtuber.agent.agents.basic_memory_agent import (
    BasicMemoryAgent,
)
from open_llm_vtuber.agent.input_types import (
    BatchInput,
    TextSource,
)
from open_llm_vtuber.agent.output_types import (
    SentenceOutput,
    DisplayText,
)


class PowerMemAgent(BasicMemoryAgent):
    """继承 BasicMemoryAgent，增加 PowerMem 长期记忆功能"""

    def __init__(
        self,
        llm,
        system: str,
        live2d_model,
        tts_preprocessor_config=None,
        faster_first_response: bool = True,
        segment_method: str = "pysbd",
        use_mcpp: bool = False,
        interrupt_method: str = "user",
        tool_prompts: Dict[str, str] = None,
        tool_manager=None,
        tool_executor=None,
        mcp_prompt_string: str = "",
        # PowerMem 参数
        powermem_user_id: str = "kristina_default",
        powermem_data_dir: str = "./powermem_data",
        memory_top_k: int = 3,
        memory_threshold: float = 0.6,
        powermem_embed_config: dict = None,
    ):
        super().__init__(
            llm=llm,
            system=system,
            live2d_model=live2d_model,
            tts_preprocessor_config=tts_preprocessor_config,
            faster_first_response=faster_first_response,
            segment_method=segment_method,
            use_mcpp=use_mcpp,
            interrupt_method=interrupt_method,
            tool_prompts=tool_prompts,
            tool_manager=tool_manager,
            tool_executor=tool_executor,
            mcp_prompt_string=mcp_prompt_string,
        )

        logger.info(
            f"Initializing PowerMemAgent for user '{powermem_user_id}'"
        )
        logger.debug(
            f"Memory data directory: {powermem_data_dir}"
        )
        logger.debug(
            f"Memory top_k: {memory_top_k}, threshold: {memory_threshold}"
        )
        if powermem_embed_config:
            logger.debug(
                f"Embedding config: {powermem_embed_config}"
            )

        # 初始化 PowerMem
        self._init_powermem(
            powermem_user_id,
            powermem_data_dir,
            embed_config=powermem_embed_config,
        )

        self.memory_top_k = memory_top_k
        self.memory_threshold = memory_threshold
        self._last_user_input = None
        # 删除实例属性 chat，确保后续调用使用子类的方法
        if hasattr(self, "chat"):
            delattr(self, "chat")
            logger.debug(
                "Deleted instance attribute 'chat', now using subclass method"
            )
        logger.info("PowerMemAgent initialization complete")

    def _init_powermem(
        self,
        user_id: str,
        data_dir: str,
        embed_config: dict = None,
    ):
        """配置并初始化 PowerMem 实例（遵循官方文档，使用 ollama provider）"""
        import os

        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(
            data_dir, f"{user_id}_memory.db"
        )
        logger.info(f"PowerMem database path: {db_path}")

        # 1. Vector Store 配置（SQLite）
        vector_store_config = {
            "provider": "sqlite",
            "config": {
                "database_path": db_path,
            },
        }

        # 2. Embedder 配置 - 使用 ollama provider
        if embed_config is None:
            embed_config = {}
        embedder_provider = embed_config.get(
            "provider", "ollama"
        )
        embedder_model = embed_config.get(
            "model", "nomic-embed-text"
        )
        embedder_base_url = embed_config.get(
            "base_url", "http://localhost:11434"
        )

        embedder_config = {
            "provider": embedder_provider,
            "config": {
                "model": embedder_model,
                "OLLAMA_EMBEDDING_BASE_URL": embedder_base_url,  # byd的别名写炸了
            },
        }

        # 3. LLM 配置 - 保持使用 openai 兼容模式（已验证可行）
        llm_config = {
            "provider": "openai",
            "config": {
                "api_key": "ollama",
                "openai_base_url": "http://localhost:11434/v1",
                "model": "goekdenizguelmez/JOSIEFIED-Qwen2.5:7b",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        }

        full_config = {
            "vector_store": vector_store_config,
            "embedder": embedder_config,
            "llm": llm_config,
        }

        try:
            self.memory = Memory(config=full_config)
            self.user_id = user_id
            logger.info(
                "PowerMem client successfully created with SQLite backend"
            )
            logger.debug(f"Full config: {full_config}")
        except Exception as e:
            logger.error(
                f"Failed to initialize PowerMem client: {e}"
            )
            raise

    def _add_message(
        self,
        message: Union[str, list[dict[str, Any]]],
        role: str,
        display_text: DisplayText | None = None,
        skip_memory: bool = False,
    ):
        """重写 _add_message，在原有逻辑基础上增加记忆存储"""
        # 先调用父类方法
        super()._add_message(
            message, role, display_text, skip_memory
        )

        if skip_memory:
            logger.debug(
                f"Skipping memory storage for {role} message (skip_memory=True)"
            )
            return

        # 提取消息文本
        text_content = ""
        if isinstance(message, list):
            for item in message:
                if item.get("type") == "text":
                    text_content += item["text"] + " "
            text_content = text_content.strip()
        else:
            text_content = str(message)

        if not text_content:
            logger.debug(
                f"Empty content for {role} message, skipping memory storage"
            )
            return

        # 存储逻辑
        if role == "user":
            self._last_user_input = text_content
            logger.debug(
                f"Stored user input for later pairing: {text_content[:50]}..."
            )
        elif (
            role == "assistant"
            and self._last_user_input is not None
        ):
            logger.debug(
                f"Pairing assistant response with last user input: {text_content[:50]}..."
            )
            asyncio.create_task(
                self._store_interaction_async(
                    self._last_user_input, text_content
                )
            )
            self._last_user_input = None

    async def _store_interaction_async(
        self, user_input: str, response: str
    ):
        """异步存储一次对话到 PowerMem（使用线程池避免阻塞）"""

        def sync_store():
            try:
                memory_content = f"用户说：{user_input}\n你回答：{response}"
                tags = self._extract_tags(
                    user_input, response
                )
                self.memory.add(
                    memory_content,
                    user_id=self.user_id,
                    metadata={
                        "type": "conversation",
                        "tags": tags,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                logger.debug(
                    f"Stored interaction with tags: {tags}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to store interaction to PowerMem: {e}"
                )

        await asyncio.to_thread(sync_store)

    def _extract_tags(
        self, user_input: str, response: str
    ) -> list:
        """简单关键词标签提取"""
        tags = []
        combined = (user_input + " " + response).lower()
        if any(
            word in combined
            for word in ["难过", "伤心", "不开心", "郁闷"]
        ):
            tags.append("need_comfort")
        if any(
            word in combined
            for word in ["名字", "我叫", "我是"]
        ):
            tags.append("user_identity")
        if any(
            word in combined
            for word in ["喜欢", "爱", "讨厌"]
        ):
            tags.append("preference")
        if tags:
            logger.debug(f"Extracted tags: {tags}")
        return tags

    def _retrieve_relevant(self, query: str) -> str:
        """从 PowerMem 检索相关记忆，返回格式化文本（同步方法，应在线程池中调用）"""
        import time

        start_time = time.time()
        try:
            logger.debug(
                f"Retrieving memories for query: {query[:50]}..."
            )
            results = self.memory.search(
                query,
                user_id=self.user_id,
                limit=self.memory_top_k,
            )
            if not results or not results.get("results"):
                logger.debug("No relevant memories found")
                return ""

            memory_text = "【回忆】\n"
            count = 0
            for item in results["results"]:
                score = item.get("score", 0)
                if score > self.memory_threshold:
                    content = item.get("memory", "")[:100]
                    memory_text += (
                        f"- 我记得：{content}...\n"
                    )
                    count += 1
            elapsed = time.time() - start_time
            logger.info(
                f"Retrieved {count} relevant memories in {elapsed:.3f}s"
            )
            return memory_text
        except Exception as e:
            logger.error(f"Memory retrieval error: {e}")
            return ""

    def _to_messages(
        self, input_data: BatchInput
    ) -> list[dict[str, Any]]:
        messages = self._memory.copy()
        user_content = []
        text_prompt = ""
        if input_data.texts:
            text_prompt = input_data.texts[0].content
            user_content.append(
                {"type": "text", "text": text_prompt}
            )

        if input_data.images:
            image_added = False
            for img_data in input_data.images:
                if isinstance(
                    img_data.data, str
                ) and img_data.data.startswith(
                    "data:image"
                ):
                    user_content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_data.data,
                                "detail": "auto",
                            },
                        }
                    )
                    image_added = True
                else:
                    logger.error(
                        f"Invalid image data format: {type(img_data.data)}. Skipping image."
                    )
            if not image_added and not text_prompt:
                logger.warning(
                    "User input contains images but none could be processed."
                )

        if user_content:
            user_message = {
                "role": "user",
                "content": user_content,
            }
            messages.append(user_message)

            skip_memory = False
            if (
                input_data.metadata
                and input_data.metadata.get(
                    "skip_memory", False
                )
            ):
                skip_memory = True

            if not skip_memory:
                self._add_message(
                    (
                        text_prompt
                        if text_prompt
                        else "[User provided image(s)]"
                    ),
                    "user",
                )
        else:
            logger.warning(
                "No content generated for user message."
            )

        return messages

    async def chat(
        self, input_data: BatchInput
    ) -> AsyncIterator[
        Union[SentenceOutput, Dict[str, Any]]
    ]:
        logger.debug(
            "Starting chat method with memory retrieval"
        )
        logger.debug(
            f"input_data.texts: {[(t.source, t.content) for t in input_data.texts]}"
        )

        user_text = ""
        if input_data.texts:
            user_text = input_data.texts[0].content
            logger.debug(
                f"Using first text as user input: {user_text}"
            )
        else:
            logger.debug("No texts in input_data")

        memory_context = ""
        if user_text:
            logger.debug(
                f"Retrieving memories for user input: {user_text[:50]}..."
            )
            memory_context = await asyncio.to_thread(
                self._retrieve_relevant, user_text
            )
        else:
            logger.info(
                "No user input found in BatchInput, skipping memory retrieval"
            )

        original_system = self._system
        if memory_context:
            logger.info(
                "Injecting retrieved memories into system prompt"
            )
            self._system = (
                original_system + "\n\n" + memory_context
            )
        else:
            logger.debug("No memory context to inject")

        try:
            async for output in super().chat(input_data):
                yield output
        finally:
            if memory_context:
                logger.debug(
                    "Restoring original system prompt"
                )
                self._system = original_system
