#!/usr/bin/env bash
# ============================================
# 停止全部 OCR 系统容器
# ============================================
echo "停止全部容器..."
docker stop ocr-frontend ocr-backend ocr-redis ocr-postgres 2>/dev/null
docker rm ocr-frontend ocr-backend ocr-redis ocr-postgres 2>/dev/null
echo "全部已停止"
echo ""
echo "如需清除数据卷（删除数据库和上传文件），运行："
echo "  docker volume rm ocr_postgres_data ocr_redis_data ocr_uploads ocr_cache"
