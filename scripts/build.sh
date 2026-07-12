#!/bin/bash
# Royal Farmers FC — 前端预编译（esbuild）
# 将 data.jsx / components.jsx / app.jsx 编译为压缩 IIFE，浏览器无需 Babel Standalone。
# 每次 data.jsx 变更后运行（daily_update.sh 已集成）。
set -e
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SRC_DIR"

ESBUILD="${ESBUILD:-esbuild}"
command -v "$ESBUILD" >/dev/null || ESBUILD=/opt/homebrew/bin/esbuild

# IIFE 包裹避免顶层 const 跨文件冲突；target=es2017 兼容旧手机
"$ESBUILD" data.jsx       --bundle --format=iife --minify --target=es2017 --charset=utf8 --outfile=data.min.js       --log-level=error
"$ESBUILD" components.jsx --bundle --format=iife --minify --target=es2017 --charset=utf8 --outfile=components.min.js --log-level=error
"$ESBUILD" app.jsx        --bundle --format=iife --minify --target=es2017 --charset=utf8 --outfile=app.min.js        --log-level=error

# 版本号打到 index.html（缓存失效）
V=$(date +%Y%m%d%H%M)
/usr/bin/sed -i '' -E "s/(data|components|app)\.min\.js\?v=[0-9]+/\1.min.js?v=${V}/g" index.html

echo "✅ build 完成 v=${V}: $(du -h data.min.js components.min.js app.min.js | tr '\n' ' ')"
