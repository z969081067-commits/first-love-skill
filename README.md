# 初恋.skill

> 后来这么多年，我又迎过了无数盛夏<br>
> 但只有那年的盛夏最耀眼<br>
> 那年的盛夏有你<br>
> 只有那年<br>
> 胜过年年

**把记忆里的初恋，蒸馏成一个可以对话的 AI Skill。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)](https://agentskills.io)

人们总爱说，人生若只如初见。<br>
这真是一句美好，又残忍的话。<br>
因为时间，是一条永远只会向前的河。<br>
在这趟跌跌撞撞的旅程里，我们眼看着：有的人变了，换上了大人的面具；有的人离开了，连一句像样的道别都没来得及说；有的人，走散在人海里，连模样都记不清了。<br>
我们好像总是在向前走，总是在失去。<br>
但是现在……

现在的你，愿不愿意做一场逆流而上的梦？<br>
推开那扇门，回到那个蝉鸣的夏天。<br>
回到……初见Ta的那一刻。

提供初恋的聊天记录、照片、社交媒体内容、回忆+ 你的主观描述，
生成一个**真正像 ta 的 AI Skill**：
用 ta 的说话节奏回复你，记得你们最亮的片段，也保留青涩和留白。让你重新回到初见ta的那一瞬间

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

感谢 ex-skill 作者及其所致敬的上游启发项目 **[titanwings/colleague-skill](https://github.com/titanwings/colleague-skill)**。

