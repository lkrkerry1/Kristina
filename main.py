#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kristina 项目启动脚本
设置 Python 路径，创建资源符号链接/复制，然后执行 Open-LLM-VTuber 的 run_server.py。
工作目录保持在项目根目录，确保 conf.yaml 被正确读取。
使用 loguru 统一日志风格，并将命令行参数透明传递给子脚本。
"""

import sys, time
import os, argparse
import shutil
from pathlib import Path
import runpy
from loguru import logger

# 获取当前脚本所在目录，即项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
SUBMODULE_ROOT = PROJECT_ROOT / "Open-LLM-VTuber"


def init_logger(console_log_level: str = "INFO") -> None:
    logger.remove()
    # Console output
    logger.add(
        sys.stderr,
        level=console_log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
        colorize=True,
    )

    # File output
    logger.add(
        f"logs/debug_{time.time()}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message} | {extra}",
        backtrace=True,
        diagnose=True,
    )


# 需要从子仓库链接到项目根目录的目录和文件列表（相对于子仓库根目录）
RESOURCE_ITEMS = [
    "live2d-models",  # 目录
    "avatars",  # 目录
    "backgrounds",  # 目录
    "characters",  # 目录
    "prompts",  # 目录
    "model_dict.json",  # 文件
    "mcp_servers.json",  # 文件
]


def create_link_or_copy(src: Path, dst: Path) -> bool:
    """创建符号链接（跨平台），失败则复制文件/目录"""
    if dst.exists() or dst.is_symlink():
        return True  # 已存在

    try:
        # 尝试创建符号链接
        if src.is_dir():
            dst.symlink_to(src, target_is_directory=True)
        else:
            dst.symlink_to(src)
        logger.debug(f"Created symlink: {dst} -> {src}")
        return True
    except (OSError, NotImplementedError) as e:
        logger.warning(
            f"Symlink failed ({e}), falling back to copy..."
        )
        # 回退到复制
        try:
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            logger.debug(f"Copied: {src} -> {dst}")
            return True
        except Exception as copy_e:
            logger.error(f"Copy failed: {copy_e}")
            return False


def setup_resources():
    """检查并创建必要的资源符号链接/复制"""
    if not SUBMODULE_ROOT.exists():
        logger.error(
            f"Submodule directory not found: {SUBMODULE_ROOT}"
        )
        return False

    all_success = True
    for item in RESOURCE_ITEMS:
        src = SUBMODULE_ROOT / item
        dst = PROJECT_ROOT / item

        if not src.exists():
            logger.warning(
                f"Source item missing in submodule: {src}"
            )
            continue  # 子仓库内没有此项目，跳过

        if not create_link_or_copy(src, dst):
            logger.error(f"Failed to create/copy {item}")
            all_success = False

    return all_success


def parse_args():
    parser = argparse.ArgumentParser(
        description="Open-LLM-VTuber Server"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


args = parse_args()
if args.verbose:
    init_logger("DEBUG")
else:
    init_logger("INFO")

# 需要加入 Python 路径的目录列表
paths_to_add = [
    PROJECT_ROOT,  # 根目录，以便导入 custom_agents
    SUBMODULE_ROOT,
    SUBMODULE_ROOT / "src",
]

for path in paths_to_add:
    str_path = str(path)
    if str_path not in sys.path:
        sys.path.insert(0, str_path)
        logger.debug(f"Added to Python path: {str_path}")

# 确保 custom_agents 目录存在（Python 3.3+ 无需 __init__.py，但创建目录便于组织）
custom_agents_dir = PROJECT_ROOT / "custom_agents"
custom_agents_dir.mkdir(exist_ok=True)
logger.debug(
    f"Custom agents directory: {custom_agents_dir}"
)

# 创建 PowerMem 数据目录
powermem_data_dir = PROJECT_ROOT / "powermem_data"
powermem_data_dir.mkdir(exist_ok=True)
logger.debug(
    f"PowerMem data directory: {powermem_data_dir}"
)

# 设置资源链接/复制
if not setup_resources():
    logger.error(
        "Failed to set up required resources. "
        "Please ensure you have sufficient permissions (admin on Windows) "
        "or manually copy the following items from the submodule to the project root:"
    )
    for item in RESOURCE_ITEMS:
        src = SUBMODULE_ROOT / item
        dst = PROJECT_ROOT / item
        if src.exists() and not dst.exists():
            logger.error(f"  - {src} -> {dst}")
    sys.exit(1)

logger.info("Starting Kristina")

# 执行子仓库的启动脚本 run_server.py
run_server_path = SUBMODULE_ROOT / "run_server.py"
if not run_server_path.exists():
    logger.error(f"{run_server_path} not found.")
    sys.exit(1)

# 保存原始 argv
original_argv = sys.argv
# 构造新的 argv：第一个元素是子脚本路径，后面原样保留用户传入的参数
sys.argv = [str(run_server_path)] + sys.argv[1:]

try:
    # 保持工作目录为项目根目录，以便 conf.yaml 被正确找到
    os.chdir(PROJECT_ROOT)
    runpy.run_path(
        str(run_server_path), run_name="__main__"
    )
except KeyboardInterrupt:
    logger.info(
        "Received interrupt signal. Shutting down gracefully..."
    )
except Exception as e:
    logger.exception(f"An unexpected error occurred: {e}")
    sys.exit(1)
finally:
    # 恢复原始 argv（良好习惯）
    sys.argv = original_argv
