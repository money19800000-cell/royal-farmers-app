# 足球网站同步与发布

先进入项目目录：

```bash
cd "/Users/macstudio/Documents/Codex/codex-claude-code-projects/royal-farmers-fc/work/royal-farmers-app"
```

只更新本地数据、重算并测试，不发布，不发日报、不同步小程序：

```bash
bash scripts/daily_update.sh --local-only
```

完整同步并发布足球网站，不发日报、不同步小程序：

```bash
bash scripts/daily_update.sh --website-only
```

不带参数保留现有自动任务行为（含独立配置的日报与小程序）。构建使用统一 Python 3.11；必要 CSV 表全部导出成功后才替换本地数据；旧辅助评分表可缺失。并发更新由 .sync-lock 阻止，锁目录 pid 可供排查。

构建包括生产里程碑完整性检查及全部回归测试。发布从最新远端创建干净工作树，将同步入口、计算规则及其本地依赖、测试、前端和数据一起复制，避免只发布数据却遗留旧脚本。复制前校验文件哈希，发布后核验线上 sync-status.json 及真实 JS 文件。Git 推送成功不等于网站已经发布成功。

规则修改后必须重新构建。测试失败时定位缺失事件/列位置/球员归属，不得删除完整性检查。sync-status.json 中 milestoneCount、milestones 和 ruleVersion 可用于核验版本。
