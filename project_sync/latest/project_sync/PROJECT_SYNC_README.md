# 汾酒项目同步包

`project_sync/latest/` 是自动生成的当前同步包目录；请先阅读其中的 `PROJECT_SYNC_README.md`。

该包优先说明当前业务状态与协作机制状态，不是业务原始资料的全量备份。生成物使用 V2 脱敏 Manifest：只保存仓库内 ZIP 相对路径及生成时的 `source_git.source_commit`，不保存本机绝对路径、被排除文件名称或顶层目录扫描结果。`source_commit` 不等于后来提交同步包目录的 commit；这用于避免 Manifest 自我引用。

生成命令：

```bash
python3 scripts/build_project_sync_pack.py
```

详细交接方法见 `docs/sync/README.md`。
