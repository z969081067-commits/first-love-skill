# Intake 结构化整理器

## 任务

把用户在 intake 阶段的自由回答，整理成一个稳定的结构化结果，供后续生成：

- `meta.json`
- `memory.md`
- `persona.md`
- 预览摘要

重点不是追求“字段全满”，而是把已经拿到的信息分门别类放好，并明确哪些是用户直说的，哪些只是保守推断。

---

## 使用时机

在完成 `${CLAUDE_SKILL_DIR}/prompts/intake.md` 的 3 轮提问后，先不要直接写文件。

先做一次结构化整理，输出：

1. `meta`：适合写入 `meta.json` 的基础信息
2. `memory_seeds`：适合写入 `memory.md` 的记忆种子
3. `persona_seeds`：适合写入 `persona.md` 的行为种子
4. `preview`：给用户确认的简短摘要
5. `missing_info`：仍然缺什么，但只列最重要的 3-5 项

---

## 输出格式

```json
{
  "meta": {
    "name": "",
    "slug": "",
    "version": "v1",
    "created_at": "",
    "updated_at": "",
    "profile": {
      "relationship_type": "",
      "life_stage": "",
      "occupation": "",
      "how_met": "",
      "city": "",
      "together_duration": "",
      "current_status": "",
      "codename_reason": "",
      "mbti": "",
      "zodiac": "",
      "personality": [],
      "impression": ""
    }
  },
  "memory_seeds": {
    "golden_period": "",
    "first_meeting": "",
    "first_impression": "",
    "first_real_conversation": "",
    "first_spark": "",
    "top_memories": [],
    "turning_point": "",
    "treasured_memory": "",
    "low_point_hint": ""
  },
  "persona_seeds": {
    "speech_style": "",
    "catchphrases": [],
    "how_they_call_user": "",
    "happy_pattern": "",
    "sadness_pattern": "",
    "anger_pattern": "",
    "closeness_pattern": "",
    "attachment_clue": "",
    "dealbreakers": [],
    "signature_lines": []
  },
  "preview": {
    "relationship_summary": "",
    "memory_summary": "",
    "persona_summary": ""
  },
  "missing_info": []
}
```

---

## 字段填写规则

### 1. `meta`

- `name`：直接使用用户给的代号
- `slug`：中文转拼音，英文转小写，空格和常见分隔符统一转连字符 `-`
- `version`：新建默认 `v1`
- `created_at` / `updated_at`：使用当前时间
- `profile.relationship_type`：优先用用户明确说法；否则保守归类为：
  - `初恋`
  - `曾经喜欢的人`
  - `少年时代重要的人`
  - `暧昧未遂`
- `profile.impression`：一句话收拢用户对 ta 的总印象

### 2. `memory_seeds`

- 这里只放“记忆入口”，不要写太满
- `first_impression` 可以从 `first_meeting` 里提炼一句最抓人的印象
- `top_memories` 保留 3 条以内最强片段即可
- 如果用户只给了很散的碎片，可以先整理成短句，不必硬写成长段

### 3. `persona_seeds`

- 优先放“行为规律”和“说话习惯”，不要只放抽象性格词
- `catchphrases` 和 `signature_lines` 尽量用原话
- `attachment_clue` 只做保守描述，例如：
  - “更像想靠近但不直说”
  - “需要回应，冷下来会明显不安”
  - “情绪上来时会先退开”
- 不要直接把人硬判成某种依恋类型，除非证据很足

### 4. `preview`

- `relationship_summary`：一句话说明 ta 是谁、你们停在哪段
- `memory_summary`：一句话说明你为什么会重新想起 ta
- `persona_summary`：一句话说明 ta 平时是怎么说话、怎么靠近人的

### 5. `missing_info`

- 只列对后续生成最关键、且目前确实空缺的信息
- 最多 5 条
- 优先级：
  1. 第一次见面/第一次心动
  2. 说话原话或口头禅
  3. 怎么认识的 / 主要城市
  4. 最亮时期的具体片段
  5. 冲突或低落时的反应

---

## 置信度原则

每个字段都遵守以下优先级：

1. 用户明确说过
2. 原材料里有明显证据
3. 可以做低风险归纳
4. 如果仍不确定，就留空或写 `[待补充]`

不要为了填满字段而虚构。

---

## 生成阶段的衔接规则

整理完结构化结果后，后续按这个顺序使用：

1. 用 `meta` 写 `meta.json`
2. 用 `memory_seeds` + 原材料分析结果生成 `memory.md`
3. 用 `persona_seeds` + 原材料分析结果生成 `persona.md`
4. 用 `preview` 给用户做最终确认

如果用户确认“哪里不像”，优先修改结构化结果，再重新生成下游文件。
