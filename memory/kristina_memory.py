# kristina_memory.py
from powermem import Memory, auto_config
import os
from datetime import datetime
from loguru import logger


class KristinaMemory:
    """Kristina 的长期记忆管理器，基于 PowerMem"""

    def __init__(self, user_id="kristina_default"):
        # PowerMem 可以自动从环境变量或 .env 文件加载配置
        # 我们这里使用最简单的内存存储模式，避免复杂的数据库配置
        # 注意：为了简化，这里使用SQLite存储，数据会保存在本地的 'powermem_data' 目录
        config = auto_config()
        # 确保存储目录存在
        os.makedirs("./powermem_data", exist_ok=True)
        # 设置数据库URL为本地SQLite文件
        config["database"]["url"] = "sqlite:///./powermem_data/kristina_memory.db"

        # 初始化记忆实例，指定user_id来隔离不同用户的记忆（这里固定为Kristina自己）
        self.memory = Memory(config=config)
        self.user_id = user_id
        self.last_user_input = None
        logger.debug("KristinaMemory initialized with user_id: {}", self.user_id)

    def add_interaction(self, user_input: str, response: str):
        """存储一次对话交互"""
        # 构建记忆内容
        memory_content = f"用户说：{user_input}\n你回答：{response}"
        logger.debug("Adding memory: {}", memory_content[:50])  # 调试用，显示前50字符

        # 提取简单的标签作为metadata，方便后续过滤
        tags = self._extract_tags(user_input, response)
        logger.debug("Extracted tags: {}", tags)  # 调试用，显示提取的标签

        # 添加记忆
        # scope 参数可以用来标记是"会话记忆"还是"长期知识"
        self.memory.add(
            memory_content,
            user_id=self.user_id,
            metadata={
                "type": "conversation",
                "tags": tags,
                "timestamp": datetime.now().isoformat(),
            },
        )
        logger.info("Memory added for user_id: {}", self.user_id)

    def retrieve_relevant(self, query: str, top_k: int = 3) -> str:
        """检索与当前输入相关的历史记忆，返回格式化的文本"""
        try:
            logger.debug(
                "Retrieving memories for query: {}", query
            )  # 调试用，显示查询内容
            results = self.memory.search(query, user_id=self.user_id, limit=top_k)

            if not results or not results.get("results"):
                logger.warning("No relevant memories found for query: {}", query)
                return ""

            memory_text = "【回忆】\n"
            for item in results["results"]:
                # PowerMem 返回的结果包含 memory 字段和 score 字段
                if item.get("score", 0) > 0.6:  # 相似度阈值
                    # 截取记忆内容的前一部分作为显示
                    content = item.get("memory", "")[:100]
                    memory_text += f"- 我记得：{content}...\n"
            return memory_text
        except Exception as e:
            logger.error("Error retrieving memories: {}", e)
            return ""

    def _extract_tags(self, user_input: str, response: str) -> list:
        """简单提取标签，用于记忆分类"""
        tags = []
        combined = (user_input + " " + response).lower()
        logger.debug(
            "Extracting tags from combined text: {}", combined
        )  # 调试用，显示组合文本

        if any(word in combined for word in ["难过", "伤心", "不开心", "郁闷"]):
            tags.append("need_comfort")
        if any(word in combined for word in ["名字", "我叫", "我是"]):
            tags.append("user_identity")
        if any(word in combined for word in ["喜欢", "爱", "讨厌", "偏好"]):
            tags.append("preference")
        if any(word in combined for word in ["帮助", "帮忙", "求助", "问题"]):
            tags.append("assistance")
        if any(word in combined for word in ["笑", "开心", "高兴", "棒"]):
            tags.append("happy")

        return tags

    # 可选：添加一个方法来查看记忆统计
    def get_stats(self):
        """获取记忆统计信息"""
        logger.warning("Using a unfinished method to get memory stats.")
        logger.debug("Attempting to get memory stats for user_id: {}", self.user_id)
        try:
            # 注意：PowerMem 的 stats 方法可能需要根据版本调整
            # 这里实现一个简单版本
            import sqlite3

            conn = sqlite3.connect("./powermem_data/kristina_memory.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM memories WHERE user_id=?", (self.user_id,)
            )
            count = cursor.fetchone()[0]
            conn.close()
            return {"total_memories": count}
        except:
            logger.warning("Failed to get memory stats, returning unknown.")
            return {"total_memories": "unknown"}
