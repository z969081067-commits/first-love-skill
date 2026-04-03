# 安装说明

建议将仓库发布为 `first-love-skill`，并把 skill 安装为 `create-first-love`。

## Claude Code

```bash
mkdir -p .claude/skills
git clone https://github.com/<your-username>/first-love-skill .claude/skills/create-first-love
```

## 全局安装

```bash
git clone https://github.com/<your-username>/first-love-skill ~/.claude/skills/create-first-love
```

## OpenClaw

```bash
git clone https://github.com/<your-username>/first-love-skill ~/.openclaw/workspace/skills/create-first-love
```

## 可选依赖

```bash
cd .claude/skills/create-first-love
pip3 install -r requirements.txt
```

`Pillow` 主要用于照片 EXIF 读取，不做照片分析可以不装。

## 安装后包含的能力

当前版本除了基础的 `memory.md` 和 `persona.md` 生成外，还包含：

1. `response_router.md`
   用于在回复前判断当前输入属于哪种情境。
2. `response_modules.md`
   用于定义可复用但不僵硬的表达模块。
3. `response_profile_builder.md`
   用于生成每个初恋专属的 `response_profile.json`。
4. `tools/variability_engine.py`
   用于按权重、冷却和情境偏好选择本轮表达模块。

## 兼容性说明

这套“回复变化系统”是附加层，不会替代原有主流程：

- 没有 `response_profile.json` 时，skill 仍可按 `memory.md` + `persona.md` 正常工作
- 有 `response_profile.json` 时，会优先用它做表达路径调味
- 追加记忆和对话纠正后，建议同步更新 `response_profile.json`

## 原材料建议

优先级建议：

1. 聊天记录
2. 照片和时间线
3. 社交媒体截图
4. 你自己的口述

如果没有导出工具，也可以手动复制关键对话到文本文件，再在 `/create-first-love` 流程中上传。

## 安装后快速自检

安装完成后，建议确认以下几点：

1. `SKILL.md`、`prompts/`、`tools/` 都在 `create-first-love` 目录内
2. `python3` 可用，至少能运行：

```bash
python3 tools/skill_writer.py --help
```

3. 如果你需要回复变化引擎，也可以测试：

```bash
python3 tools/variability_engine.py --help
```

4. 新开一个会话后再触发 `/create-first-love`，避免旧会话缓存旧版 skill
