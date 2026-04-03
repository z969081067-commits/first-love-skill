# 初恋.skill

> "如果记忆有形状，它大概是你第一次看向 ta 的那一秒。"

**把记忆里的初恋，蒸馏成一个可以对话的 AI Skill。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)](https://agentskills.io)

提供初恋相关原材料（聊天记录、照片、社交媒体内容）+ 你的主观描述，
生成一个**真正像 ta 的 AI Skill**：
用 ta 的说话节奏回复你，记得你们最亮的片段，也保留青涩和留白。

⚠️ **本项目仅用于个人回忆与情感整理，不用于骚扰、跟踪、冒充或侵犯隐私。**

[安装](#安装) · [使用](#使用) · [效果示例](#效果示例) · [功能特性](#功能特性) · [项目结构](#项目结构) · [English](README_EN.md)

---

## 安装

### Claude Code

> **重要**：Claude Code 从 git 仓库根目录的 `.claude/skills/` 查找 skill，请在正确目录执行。

```bash
# 安装到当前项目（推荐）
mkdir -p .claude/skills
git clone https://github.com/<your-username>/first-love-skill .claude/skills/create-first-love

# 或安装到全局（所有项目可用）
git clone https://github.com/<your-username>/first-love-skill ~/.claude/skills/create-first-love
```

### 依赖（可选）

```bash
pip3 install -r requirements.txt
```

---

## 使用

在 Claude Code 中输入：

```text
/create-first-love
```

按流程填写：

1. 关系锚点（怎么认识、停在哪个阶段、主要城市/地点）
2. 心动记忆（第一次见面、第一次认真说话、第一次明确心动）
3. 相处画像（说话方式、情绪反应、边界与雷区）
4. 原材料导入（微信 / QQ / 社交媒体 / 照片 / 口述）

完成后使用 `/first-love-{slug}` 开始对话。

### 管理命令

| 命令 | 说明 |
|------|------|
| `/list-first-loves` | 列出所有初恋 Skill |
| `/first-love-{slug}` | 完整模式 |
| `/first-love-{slug}-memory` | 回忆模式 |
| `/first-love-{slug}-persona` | 性格模式 |
| `/first-love-rollback {slug} {version}` | 回滚版本 |
| `/delete-first-love {slug}` | 删除 |
| `/seal-summer {slug}` | 温柔删除别名 |

---

## 效果示例

> 输入：`大学同班，ENFP，双子座，说话很快，半夜会突然发语音，吵完架又会别扭地关心我`

**场景一：日常聊天**

```text
用户      ❯ 在干嘛
初恋.skill ❯ 刚到家 在楼下买了点水果
             你呢 怎么突然找我
```

**场景二：回忆闪回**

```text
用户      ❯ 你还记得我们第一次一起吃饭吗
初恋.skill ❯ 记得啊 你当时紧张到筷子都拿反了
             还嘴硬说是新拿法
```

**场景三：深夜情绪**

```text
用户      ❯ 我有点想回到以前
初恋.skill ❯ 嗯
             先别急着难过
             你今天是不是又没好好睡觉
```

---

## 功能特性

### 数据来源

| 来源 | 格式 | 备注 |
|------|------|------|
| 微信聊天记录 | txt / html / csv / json / sqlite | 优先推荐，细节密度高 |
| QQ 聊天记录 | txt / mht / mhtml | 适合校园时期关系 |
| 社交媒体内容 | 截图 / 文本导出 | 用于补足公开表达风格 |
| 照片 | JPEG / PNG（含 EXIF） | 提取时间线与地点线索 |
| 口述回忆 | 纯文本 | 无附件时也可完整生成 |

### 输出结构（每个 `{slug}`）

- `first_loves/{slug}/memory.md`
- `first_loves/{slug}/persona.md`
- `first_loves/{slug}/meta.json`
- `first_loves/{slug}/response_profile.json`
- `first_loves/{slug}/SKILL.md`

### 回复变化系统（非随机胡说）

- `response_router.md`：判断输入类型、关系相位、表达强度
- `response_modules.md`：定义主/副表达模块
- `response_profile.json`：记录模块权重 + 冷却窗口，减少腔调重复

目标是在**人格稳定**前提下，让回复有自然波动。

---

## 安全边界

1. 仅用于个人回忆与情感整理
2. 不主动联系真人，不替代现实关系
3. 不鼓励沉迷理想化执念
4. 数据默认本地处理与存储
5. 关键表达尽量基于证据，不把 ta 写成完美角色

---

## 项目结构

```text
first-love-skill/
├── SKILL.md
├── README.md
├── README_EN.md
├── INSTALL.md
├── prompts/
│   ├── intake.md
│   ├── intake_structurer.md
│   ├── memory_analyzer.md
│   ├── memory_builder.md
│   ├── persona_analyzer.md
│   ├── persona_builder.md
│   ├── response_router.md
│   ├── response_modules.md
│   ├── response_profile_builder.md
│   ├── merger.md
│   └── correction_handler.md
├── tools/
│   ├── wechat_parser.py
│   ├── qq_parser.py
│   ├── social_parser.py
│   ├── photo_analyzer.py
│   ├── chat_analysis.py
│   ├── variability_engine.py
│   ├── skill_writer.py
│   └── version_manager.py
├── docs/
└── first_loves/
```

---

## 致谢与来源说明

- 本项目基于 **[therealXiaomanChu/ex-skill](https://github.com/therealXiaomanChu/ex-skill)** 的思路与工程结构进行修改扩展。
- 遵循 GitHub 开源社区常见做法：当项目明显来源于上游实现时，在 README 中公开标注来源与灵感，并保留原项目许可协议（本仓库为 MIT）。
- 同时感谢 ex-skill 所致敬的上游启发项目 **[titanwings/colleague-skill](https://github.com/titanwings/colleague-skill)**。

如果你继续二次开发，也建议在 README 保留这一来源链路，方便社区追溯与致谢。
