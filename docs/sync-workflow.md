# 足球网站同步与发布

先进入项目根目录（已提供统一入口；网站子目录下原命令也兼容）：

```bash
cd "/Users/macstudio/Documents/Codex/codex-claude-code-projects/royal-farmers-fc"
```

只更新本地数据、重算并测试，不发布，不发日报、不同步小程序：

```bash
bash scripts/daily_update.sh --local-only
```

完整同步并发布足球网站，不发日报、不同步小程序：

```bash
bash scripts/daily_update.sh --website-only
```

从任意目录直接运行：

```bash
bash "/Users/macstudio/Documents/Codex/codex-claude-code-projects/royal-farmers-fc/scripts/daily_update.sh" --website-only
```

全局同步 Step 10 同样传入 `--website-only`；小程序由 Step 11 单独负责。
失败会保留业务完成检查，并在全局日志输出本次足球更新的末尾错误。

不带参数保留现有自动任务行为（含独立配置的日报与小程序）。构建使用统一 Python 3.11；必要 CSV 表全部导出成功后才替换本地数据；旧辅助评分表可缺失。并发更新由 .sync-lock 阻止，锁目录 pid 可供排查。

构建包括生产里程碑完整性检查及全部回归测试。发布从最新远端创建干净工作树，将同步入口、计算规则及其本地依赖、测试、前端和数据一起复制，避免只发布数据却遗留旧脚本。复制前校验文件哈希，发布后核验线上 sync-status.json 及真实 JS 文件。Git 推送成功不等于网站已经发布成功。

规则修改后必须重新构建。测试失败时定位缺失事件/列位置/球员归属，不得删除完整性检查。sync-status.json 中 milestoneCount、milestones 和 ruleVersion 可用于核验版本。

球员姓名和档案以本次花名册 CSV 为唯一依据。`update_players.py` 和构建末尾的 `reconcile_stats.py` 使用同一套全量重建规则：改名、删除、新增及数据更正都会替换旧快照，不再把失效名字保存为历史档案或重复计入榜单。历史球员只要仍在 CSV 中就会保留。

战报中 `carlo` / `Carlo` 这类大小写差异按当前花名册名称统一后再计算月榜、搭档、连续纪录和里程碑。仍出现在最新战报中的陌生名字会保留原始记录；不依据球衣号或相似文字猜测改名关系。空花名册或大小写重复姓名会停止同步。

网站为静态部署：完整同步先从 Numbers 导出最新 CSV，再重建并发布网页数据，更新资源版本号。浏览器读取本次发布的数据；修改本地 CSV 后需运行同步/构建发布，浏览器无法直接读取电脑上的 CSV。
