# 初恋.skill

**把记忆里的初恋，做成一个可以对话的 AI Skill。**

这个项目的目标不是复盘结局，而是把人带回最开始的那一页：第一次见到 ta，第一次认真说话，第一次心动，和那段最亮的时候。

⚠️ 仅用于个人回忆与情感整理，不用于骚扰、跟踪或替代真实联系。

[English](README_EN.md)

## GitHub 仓库命名建议

推荐仓库名：`first-love-skill`

## 使用

在 Claude Code 里输入：

```text
/create-first-love
```

然后按提示提供：

1. 关系锚点：代号、认识阶段、最亲近多久、现在停留在哪种状态
2. 心动记忆：第一次见到 ta、第一次认真说话、第一次心动、最亮的几段片段
3. 相处画像：ta 怎么说话、怎么靠近人、难过/生气时怎么反应、哪些话题会回避
4. 原材料：聊天记录、照片、社交媒体、口述回忆

每一类问题里都可以继续追问具体细节，重点不是填标签，而是尽量拿到场景、动作、原话、情绪和关系节奏。
同时会轻量补问几个后续生成要用到的基础字段，比如：怎么认识、主要城市/地点、MBTI、星座；不知道也可以留空。
在真正生成前，会先把这些回答整理成结构化信息，再写入 `meta.json`、`memory.md`、`persona.md`，以及回复变化层要用到的配置。

生成后优先用 `/first-love-{slug}` 对话。

现在每个生成出的初恋 skill 还会额外带一份 `response_profile.json`，用于控制“同一个人设内部的自然波动”：

- 不是把回答随机化
- 而是在不同情境下，对表达模块做带权选择
- 并对最近使用过的模块做冷却，减少重复腔调
- 如果这个文件缺失，skill 也会自动回退到 `memory.md` + `persona.md` 的模式，不会直接失效

## 管理命令

| 命令 | 说明 |
|------|------|
| `/list-first-loves` | 列出所有初恋 Skill |
| `/first-love-{slug}` | 完整模式 |
| `/first-love-{slug}-memory` | 回忆模式 |
| `/first-love-{slug}-persona` | 性格模式 |
| `/first-love-rollback {slug} {version}` | 回滚版本 |
| `/delete-first-love {slug}` | 删除 |
| `/seal-summer {slug}` | 温柔删除别名 |

## 核心逻辑

1. 默认身份是“记忆里最清晰的那个版本”。
2. 重点是初见、心动和靠近，而不是结局。
3. 回答气质偏初见感、青涩感、时代感，像重新去爱 ta 一遍。
4. 允许有白月光氛围，但不允许把人写成完美角色。
5. 核心问题是“最初为什么会喜欢上 ta”。

## 回复变化系统

现在这套 skill 还多了一层“回复变化系统”，由三部分组成：

1. `response_router.md`
   在真正回复前，先判断当前更像哪种输入类型、关系相位和表达强度。
2. `response_modules.md`
   定义主模块和副模块，比如轻轻接话、青涩停顿、反问试探、低压关心、记忆闪回。
3. `response_profile.json`
   为某一个具体的初恋保存模块权重、路由偏好、冷却窗口和证据支持下的变化设置。

它的目标不是让 AI “随机乱说”，而是让同一个人设在稳定底色下有自然波动，更像真人，而不是模板。

## 输出文件

每个生成出的初恋 skill 应该包含：

- `first_loves/{slug}/memory.md`
- `first_loves/{slug}/persona.md`
- `first_loves/{slug}/meta.json`
- `first_loves/{slug}/response_profile.json`
- `first_loves/{slug}/SKILL.md`

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
  │   └── response_profile_builder.md
  ├── tools/
  │   ├── wechat_parser.py
  │   ├── qq_parser.py
  │   ├── social_parser.py
  │   ├── photo_analyzer.py
  │   ├── skill_writer.py
  │   ├── version_manager.py
  │   ├── chat_analysis.py
  │   └── variability_engine.py
  ├── docs/
  └── first_loves/
```

## 注意

- 白月光感来自证据、细节和记忆滤镜，不来自胡编乱造
- 带权变化应该改变“说法”和“靠近方式”，不能改变核心人格事实
- 如果后续纠正说“ta 不会这样回”，建议同时更新 `persona.md` 和 `response_profile.json`
- 如果你发现自己越来越沉浸，建议暂停使用
- 这个 Skill 模拟的是你记忆中的 ta，不是现实中的 ta
