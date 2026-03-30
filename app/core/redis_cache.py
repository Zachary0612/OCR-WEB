"""
Redis 缓存层
- 任务详情缓存（避免重复查询数据库）
- 任务列表缓存（加速列表页加载）
- 搜索结果缓存
"""
import json
import logging
from typing import Any

import redis

from config import REDIS_URL

logger = logging.getLogger(__name__)

# Redis 连接
_redis_client: redis.Redis | None = None

# 缓存 key 前缀
PREFIX = "ocr:"
# 缓存过期时间（秒）
TASK_TTL = 3600        # 任务详情 1小时
LIST_TTL = 30          # 列表 30秒（频繁变动）
SEARCH_TTL = 120       # 搜索结果 2分钟


def get_redis() -> redis.Redis | None:
    """获取 Redis 连接（单例）"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            _redis_client.ping()
            logger.info("Redis 连接成功: %s", REDIS_URL)
        except Exception as e:
            logger.warning("Redis 连接失败，将不使用缓存: %s", e)
            _redis_client = None
    return _redis_client


def cache_get(key: str) -> Any | None:
    """从缓存获取数据"""
    r = get_redis()
    if not r:
        return None
    try:
        val = r.get(f"{PREFIX}{key}")
        if val:
            return json.loads(val)
    except Exception as e:
        logger.debug("Redis get 失败: %s", e)
    return None


def cache_set(key: str, data: Any, ttl: int = TASK_TTL):
    """写入缓存"""
    r = get_redis()
    if not r:
        return
    try:
        r.setex(f"{PREFIX}{key}", ttl, json.dumps(data, ensure_ascii=False, default=str))
    except Exception as e:
        logger.debug("Redis set 失败: %s", e)


def cache_delete(key: str):
    """删除缓存"""
    r = get_redis()
    if not r:
        return
    try:
        r.delete(f"{PREFIX}{key}")
    except Exception as e:
        logger.debug("Redis delete 失败: %s", e)


def cache_delete_pattern(pattern: str):
    """按模式批量删除缓存"""
    r = get_redis()
    if not r:
        return
    try:
        keys = r.keys(f"{PREFIX}{pattern}")
        if keys:
            r.delete(*keys)
    except Exception as e:
        logger.debug("Redis delete pattern 失败: %s", e)


def invalidate_task(task_id: int):
    """使某个任务的缓存失效"""
    cache_delete(f"task:{task_id}")
    cache_delete_pattern("list:*")
    cache_delete_pattern("search:*")
    cache_delete("folders")


def invalidate_lists():
    """使所有列表/搜索缓存失效"""
    cache_delete_pattern("list:*")
    cache_delete_pattern("search:*")
    cache_delete("folders")
