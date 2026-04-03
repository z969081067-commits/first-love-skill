#!/usr/bin/env python3
"""Shared chat parsing and analysis helpers."""

from __future__ import annotations

import json
import os
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional


PARTICLE_PATTERN = re.compile(r"[哈嗯哦噢嘿唉呜啊呀吧嘛呢吗么哇啦欸诶]+")
EMOJI_PATTERN = re.compile(
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
    r"\U00002702-\U000027B0\U0000FE00-\U0000FE0F"
    r"\U0001F900-\U0001F9FF]+",
    re.UNICODE,
)
CLAUSE_SPLIT_PATTERN = re.compile(r"[，。！？!?~～…\n\r]+")
CONFLICT_KEYWORDS = ("烦", "别", "算了", "不想", "生气", "吵", "烦死", "别烦", "拉倒")
AFFECTION_KEYWORDS = ("想你", "抱抱", "爱", "亲", "宝", "晚安", "早安", "贴贴")
PLANNING_KEYWORDS = ("几点", "明天", "周末", "吃饭", "见面", "去哪", "一起", "安排")
SYSTEM_MESSAGE_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"撤回了一条消息",
        r"拍了拍",
        r"以下为新消息",
        r"以上是打招呼的内容",
        r"开启了朋友验证",
        r"消息已发出，但被对方拒收了",
        r"你们已添加了.*现在可以开始聊天了",
        r"加入了群聊",
        r"移出了群聊",
        r"修改群名",
        r"QQ离线文件",
        r"系统消息",
    )
]
PLACEHOLDER_PATTERNS = [
    (re.compile(r"^\[?(图片|image)\]?$", re.I), "[图片]"),
    (re.compile(r"^\[?(表情|动画表情|sticker)\]?$", re.I), "[表情]"),
    (re.compile(r"^\[?(语音|voice)\]?$", re.I), "[语音]"),
    (re.compile(r"^\[?(视频|video)\]?$", re.I), "[视频]"),
    (re.compile(r"^\[?(文件|file)\]?$", re.I), "[文件]"),
    (re.compile(r"^\[?(位置|location)\]?$", re.I), "[位置]"),
    (re.compile(r"^\[?(链接|link)\]?$", re.I), "[链接]"),
    (re.compile(r"^\[?(通话|voice call|video call)\]?$", re.I), "[通话]"),
]
GENERIC_SELF_TOKENS = {"我", "自己", "本人", "me", "self", "myself"}
ADDRESSING_STOPWORDS = {
    "今天", "现在", "真的", "就是", "怎么", "那个", "这个", "你说", "哈哈", "哈哈哈",
    "晚安", "早安", "在吗", "好的", "可以", "不是", "如果", "然后", "因为", "所以",
}


@dataclass
class MessageEvent:
    timestamp: Optional[str]
    sender: str
    content: str
    sender_role: str
    hour: Optional[int]
    minute_of_day: Optional[int]
    source_format: str
    evidence_type: str
    evidence_strength: str
    sender_confidence: str
    is_placeholder: bool


def read_text_file(file_path: str) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_timestamp(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts)
        except (OSError, OverflowError, ValueError):
            return None

    text = str(value).strip()
    if not text:
        return None
    text = text.replace("/", "-").replace("T", " ")
    text = re.sub(r"\.\d+$", "", text)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S %z"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def isoformat_or_none(ts: Optional[datetime]) -> Optional[str]:
    return ts.strftime("%Y-%m-%d %H:%M:%S") if ts else None


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_message_text(text: str) -> str:
    text = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u200b", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_aliases(primary_name: str, aliases: Optional[str | list[str]]) -> list[str]:
    values: list[str] = []
    for raw in [primary_name, aliases]:
        if not raw:
            continue
        if isinstance(raw, list):
            parts = raw
        else:
            parts = re.split(r"[,/|;，、]+", str(raw))
        for part in parts:
            cleaned = normalize_space(str(part))
            if cleaned and cleaned not in values:
                values.append(cleaned)
    return values


def canonicalize_identifier(text: str) -> str:
    return re.sub(r"[\W_]+", "", normalize_space(text).lower())


def normalize_placeholder(text: str) -> tuple[str, bool]:
    text = normalize_message_text(text)
    compact = normalize_space(text.replace("\n", " "))
    for pattern, replacement in PLACEHOLDER_PATTERNS:
        if pattern.fullmatch(compact):
            return replacement, True
    return text, False


def is_system_message(text: str) -> bool:
    compact = normalize_space(text.replace("\n", " "))
    if not compact:
        return True
    return any(pattern.search(compact) for pattern in SYSTEM_MESSAGE_PATTERNS)


def classify_sender(
    sender: str,
    target_name: str,
    target_aliases: Optional[str | list[str]] = None,
    self_name: Optional[str] = None,
    explicit_sender_role: Optional[str] = None,
) -> tuple[str, str]:
    if explicit_sender_role in {"target", "user"}:
        return explicit_sender_role, "high"

    sender_clean = normalize_space(sender)
    if not sender_clean:
        return "unknown", "low"

    sender_key = canonicalize_identifier(sender_clean)
    aliases = [canonicalize_identifier(alias) for alias in parse_aliases(target_name, target_aliases)]
    self_aliases = [canonicalize_identifier(self_name)] if self_name else []
    self_aliases.extend(canonicalize_identifier(token) for token in GENERIC_SELF_TOKENS)

    if any(alias and sender_key == alias for alias in aliases):
        return "target", "high"
    if any(alias and alias in sender_key for alias in aliases):
        return "target", "medium"
    if any(alias and sender_key == alias for alias in self_aliases):
        return "user", "high"
    if any(alias and alias in sender_key for alias in self_aliases):
        return "user", "medium"
    return "user", "low"


def build_event(
    timestamp: Optional[datetime],
    sender: str,
    content: str,
    target_name: str,
    source_format: str,
    *,
    target_aliases: Optional[str | list[str]] = None,
    self_name: Optional[str] = None,
    explicit_sender_role: Optional[str] = None,
    evidence_type: str = "direct_chat_evidence",
    evidence_strength: str = "high",
) -> Optional[MessageEvent]:
    normalized_content, is_placeholder = normalize_placeholder(content)
    sender = normalize_space(sender)
    sender_role, sender_confidence = classify_sender(
        sender,
        target_name,
        target_aliases=target_aliases,
        self_name=self_name,
        explicit_sender_role=explicit_sender_role,
    )

    aliases = parse_aliases(target_name, target_aliases)
    if not sender:
        if sender_role == "user":
            sender = self_name or "我"
        elif sender_role == "target":
            sender = aliases[0] if aliases else target_name

    if not normalized_content or not sender:
        return None

    return MessageEvent(
        timestamp=isoformat_or_none(timestamp),
        sender=sender,
        content=normalized_content,
        sender_role=sender_role,
        hour=timestamp.hour if timestamp else None,
        minute_of_day=(timestamp.hour * 60 + timestamp.minute) if timestamp else None,
        source_format=source_format,
        evidence_type=evidence_type,
        evidence_strength=evidence_strength,
        sender_confidence=sender_confidence,
        is_placeholder=is_placeholder,
    )


def minutes_between(ts1: Optional[str], ts2: Optional[str]) -> Optional[float]:
    if not ts1 or not ts2:
        return None
    dt1 = parse_timestamp(ts1)
    dt2 = parse_timestamp(ts2)
    if not dt1 or not dt2:
        return None
    return (dt2 - dt1).total_seconds() / 60.0


def percentile(values: list[float], ratio: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    idx = ratio * (len(ordered) - 1)
    low = int(idx)
    high = min(low + 1, len(ordered) - 1)
    if low == high:
        return ordered[low]
    weight = idx - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def summarize_numeric(values: list[float]) -> dict[str, Optional[float]]:
    if not values:
        return {"count": 0, "avg": None, "median": None, "p75": None, "min": None, "max": None}
    return {
        "count": len(values),
        "avg": round(sum(values) / len(values), 1),
        "median": round(statistics.median(values), 1),
        "p75": round(percentile(values, 0.75) or 0, 1),
        "min": round(min(values), 1),
        "max": round(max(values), 1),
    }


def format_minutes(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    if value < 1:
        return f"{int(round(value * 60))} 秒"
    if value < 60:
        return f"{value:.1f} 分钟"
    if value < 24 * 60:
        return f"{value / 60:.1f} 小时"
    return f"{value / 1440:.1f} 天"


def extract_repeated_clauses(messages: list[str], limit: int = 10) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    for text in messages:
        clauses = [normalize_space(part) for part in CLAUSE_SPLIT_PATTERN.split(text)]
        for clause in clauses:
            clause = clause.strip("~～ ")
            if 2 <= len(clause) <= 12 and not clause.startswith("["):
                counter[clause] += 1
                if len(examples[clause]) < 3:
                    examples[clause].append(text[:80])

    items = []
    for phrase, count in counter.most_common():
        if count < 2:
            continue
        items.append({"phrase": phrase, "count": count, "examples": examples[phrase]})
        if len(items) >= limit:
            break
    return items


def extract_openers_closers(messages: list[str], limit: int = 8) -> dict[str, list[dict[str, Any]]]:
    openers: Counter[str] = Counter()
    closers: Counter[str] = Counter()
    opener_examples: dict[str, list[str]] = defaultdict(list)
    closer_examples: dict[str, list[str]] = defaultdict(list)

    for text in messages:
        parts = [normalize_space(part) for part in CLAUSE_SPLIT_PATTERN.split(text) if normalize_space(part)]
        if not parts:
            continue
        opener = parts[0][:10]
        closer = parts[-1][:10]
        if 1 <= len(opener) <= 10 and not opener.startswith("["):
            openers[opener] += 1
            if len(opener_examples[opener]) < 2:
                opener_examples[opener].append(text[:80])
        if 1 <= len(closer) <= 10 and not closer.startswith("["):
            closers[closer] += 1
            if len(closer_examples[closer]) < 2:
                closer_examples[closer].append(text[:80])

    return {
        "openers": [
            {"phrase": phrase, "count": count, "examples": opener_examples[phrase]}
            for phrase, count in openers.most_common(limit)
            if count >= 2
        ],
        "closers": [
            {"phrase": phrase, "count": count, "examples": closer_examples[phrase]}
            for phrase, count in closers.most_common(limit)
            if count >= 2
        ],
    }


def categorize_text_label(text: str, hour: Optional[int] = None) -> str:
    if any(keyword in text for keyword in CONFLICT_KEYWORDS):
        return "conflict"
    if any(keyword in text for keyword in AFFECTION_KEYWORDS):
        return "affection"
    if any(keyword in text for keyword in PLANNING_KEYWORDS):
        return "planning"
    if hour is not None and (hour >= 23 or hour <= 2):
        return "late_night"
    return "daily"


def preprocess_events(events: list[MessageEvent]) -> tuple[list[MessageEvent], dict[str, int]]:
    cleaned: list[MessageEvent] = []
    seen: set[tuple[str, str, str, str]] = set()
    stats = {
        "system_messages_removed": 0,
        "duplicates_removed": 0,
        "empty_messages_removed": 0,
        "placeholder_messages": 0,
    }

    for event in events:
        event.content = normalize_message_text(event.content)
        if not event.content:
            stats["empty_messages_removed"] += 1
            continue
        if is_system_message(event.content):
            stats["system_messages_removed"] += 1
            continue
        signature = (
            event.timestamp or "",
            canonicalize_identifier(event.sender),
            event.content,
            event.source_format,
        )
        if signature in seen:
            stats["duplicates_removed"] += 1
            continue
        seen.add(signature)
        if event.is_placeholder:
            stats["placeholder_messages"] += 1
        cleaned.append(event)

    cleaned.sort(key=lambda e: (parse_timestamp(e.timestamp) or datetime.min, e.sender_role != "target"))
    return cleaned, stats


def build_sessions(events: list[MessageEvent], gap_minutes: int) -> list[dict[str, Any]]:
    if not events:
        return []

    sessions: list[list[MessageEvent]] = []
    current: list[MessageEvent] = []
    for event in events:
        if not current:
            current = [event]
            continue
        gap = minutes_between(current[-1].timestamp, event.timestamp)
        if gap is not None and gap > gap_minutes:
            sessions.append(current)
            current = [event]
        else:
            current.append(event)
    if current:
        sessions.append(current)

    summaries: list[dict[str, Any]] = []
    for idx, session in enumerate(sessions, 1):
        target_messages = [e for e in session if e.sender_role == "target"]
        user_messages = [e for e in session if e.sender_role == "user"]
        session_text = " ".join(e.content for e in session if not e.is_placeholder)
        label = categorize_text_label(session_text, session[0].hour)
        summaries.append(
            {
                "session_id": idx,
                "started_at": session[0].timestamp,
                "ended_at": session[-1].timestamp,
                "message_count": len(session),
                "target_message_count": len(target_messages),
                "user_message_count": len(user_messages),
                "initiated_by": session[0].sender_role,
                "label": label,
                "sample_excerpt": session[0].content[:120],
                "sample_turns": [
                    {
                        "timestamp": event.timestamp,
                        "sender_role": event.sender_role,
                        "content": event.content[:80],
                    }
                    for event in session[:4]
                ],
            }
        )
    return summaries


def select_representative_messages(target_events: list[MessageEvent], limit: int = 12) -> list[dict[str, Any]]:
    candidates = []
    seen: set[str] = set()
    for event in target_events:
        if event.is_placeholder:
            continue
        compact = normalize_space(event.content.replace("\n", " "))
        if len(compact) < 2:
            continue
        signature = compact.lower()
        if signature in seen:
            continue
        seen.add(signature)
        label = categorize_text_label(compact, event.hour)
        score = 0
        if 6 <= len(compact) <= 48:
            score += 3
        elif len(compact) <= 80:
            score += 2
        else:
            score += 1
        if re.search(r"[!！?？~～…]{1,}", compact):
            score += 1
        if EMOJI_PATTERN.search(compact):
            score += 1
        if any(keyword in compact for keyword in AFFECTION_KEYWORDS + CONFLICT_KEYWORDS + PLANNING_KEYWORDS):
            score += 2
        candidates.append(
            {
                "timestamp": event.timestamp,
                "content": compact,
                "label": label,
                "score": score,
            }
        )

    candidates.sort(key=lambda item: (item["score"], item["timestamp"] or ""), reverse=True)
    chosen: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    for item in candidates:
        if label_counts[item["label"]] >= 3:
            continue
        chosen.append(item)
        label_counts[item["label"]] += 1
        if len(chosen) >= limit:
            break
    return chosen


def select_representative_sessions(sessions: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_labels: Counter[str] = Counter()
    for session in sorted(sessions, key=lambda item: (item["message_count"], item["target_message_count"]), reverse=True):
        if seen_labels[session["label"]] >= 2:
            continue
        selected.append(session)
        seen_labels[session["label"]] += 1
        if len(selected) >= limit:
            break
    return selected


def extract_addressing_terms(messages: list[str], limit: int = 6) -> list[str]:
    counter: Counter[str] = Counter()
    for text in messages:
        compact = normalize_space(text.replace("\n", " "))
        match = re.match(r"^([^\s，,。！？!?~～]{1,4})[，,！!？?~～啊呀呢嘛]", compact)
        if not match:
            continue
        token = match.group(1)
        if token in ADDRESSING_STOPWORDS or token.startswith("["):
            continue
        counter[token] += 1
    return [token for token, _count in counter.most_common(limit)]


def build_signal_bundle(
    target_events: list[MessageEvent],
    repeated_clauses: list[dict[str, Any]],
    opening_closing_patterns: dict[str, list[dict[str, Any]]],
    style_tags: list[str],
    active_hours: list[dict[str, Any]],
    target_reply_summary: dict[str, Any],
    representative_messages: list[dict[str, Any]],
    sessions: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    target_texts = [event.content for event in target_events if not event.is_placeholder]
    session_label_counts = Counter(session["label"] for session in sessions)
    persona_signals = {
        "speech_style": style_tags,
        "catchphrases": [item["phrase"] for item in repeated_clauses[:5]],
        "opening_patterns": [item["phrase"] for item in opening_closing_patterns["openers"][:5]],
        "closing_patterns": [item["phrase"] for item in opening_closing_patterns["closers"][:5]],
        "possible_addressing_terms": extract_addressing_terms(target_texts),
        "active_hours": active_hours,
        "reply_speed": target_reply_summary,
        "signature_lines": [item["content"] for item in representative_messages[:5]],
        "evidence_preference": "direct_chat_evidence",
    }
    memory_signals = {
        "dominant_session_labels": dict(session_label_counts),
        "late_night_sessions": [session["sample_excerpt"] for session in sessions if session["label"] == "late_night"][:3],
        "planning_sessions": [session["sample_excerpt"] for session in sessions if session["label"] == "planning"][:3],
        "affection_sessions": [session["sample_excerpt"] for session in sessions if session["label"] == "affection"][:3],
        "conflict_sessions": [session["sample_excerpt"] for session in sessions if session["label"] == "conflict"][:3],
    }
    return persona_signals, memory_signals


def analyze_messages(
    events: list[MessageEvent],
    target_name: str,
    session_gap_minutes: int,
    *,
    platform: str,
) -> dict[str, Any]:
    chronological, cleanup_stats = preprocess_events(events)
    target_events = [e for e in chronological if e.sender_role == "target"]
    user_events = [e for e in chronological if e.sender_role == "user"]
    unknown_events = [e for e in chronological if e.sender_role == "unknown"]
    target_text_events = [e for e in target_events if not e.is_placeholder]
    target_texts = [e.content for e in target_text_events]
    all_target_text = " ".join(target_texts)

    particles = Counter(PARTICLE_PATTERN.findall(all_target_text))
    emojis = Counter(EMOJI_PATTERN.findall(all_target_text))
    msg_lengths = [len(e.content) for e in target_text_events if e.content]
    line_counts = [e.content.count("\n") + 1 for e in target_text_events if e.content]

    punctuation_counts = {
        "句号": all_target_text.count("。"),
        "感叹号": all_target_text.count("！") + all_target_text.count("!"),
        "问号": all_target_text.count("？") + all_target_text.count("?"),
        "省略号": all_target_text.count("...") + all_target_text.count("…"),
        "波浪号": all_target_text.count("～") + all_target_text.count("~"),
    }
    emphasis_counts = {
        "连续哈哈": len(re.findall(r"哈{2,}", all_target_text)),
        "连续问号": len(re.findall(r"[?？]{2,}", all_target_text)),
        "连续感叹号": len(re.findall(r"[!！]{2,}", all_target_text)),
    }

    hourly_counter = Counter(e.hour for e in target_events if e.hour is not None)
    active_hours = [{"hour": hour, "count": count} for hour, count in hourly_counter.most_common(6)]
    time_buckets = {"late_night_23_04": 0, "morning_05_11": 0, "afternoon_12_17": 0, "evening_18_22": 0}
    for event in target_events:
        if event.hour is None:
            continue
        if event.hour >= 23 or event.hour <= 4:
            time_buckets["late_night_23_04"] += 1
        elif event.hour <= 11:
            time_buckets["morning_05_11"] += 1
        elif event.hour <= 17:
            time_buckets["afternoon_12_17"] += 1
        else:
            time_buckets["evening_18_22"] += 1

    target_reply_delays: list[float] = []
    user_reply_delays: list[float] = []
    target_burst_lengths: list[int] = []
    current_target_burst = 0
    for prev, curr in zip(chronological, chronological[1:]):
        if curr.sender_role == "target":
            current_target_burst += 1
        elif current_target_burst:
            target_burst_lengths.append(current_target_burst)
            current_target_burst = 0

        delay = minutes_between(prev.timestamp, curr.timestamp)
        if delay is None:
            continue
        if {prev.sender_role, curr.sender_role} == {"target", "user"}:
            if curr.sender_role == "target":
                target_reply_delays.append(delay)
            else:
                user_reply_delays.append(delay)
    if current_target_burst:
        target_burst_lengths.append(current_target_burst)

    sessions = build_sessions(chronological, session_gap_minutes)
    initiated_by_target = sum(1 for s in sessions if s["initiated_by"] == "target")
    initiated_by_user = sum(1 for s in sessions if s["initiated_by"] == "user")
    repeated_clauses = extract_repeated_clauses(target_texts)
    opening_closing_patterns = extract_openers_closers(target_texts)
    representative_messages = select_representative_messages(target_events)
    representative_sessions = select_representative_sessions(sessions)

    avg_length = round(sum(msg_lengths) / len(msg_lengths), 1) if msg_lengths else 0
    avg_lines = round(sum(line_counts) / len(line_counts), 1) if line_counts else 0
    avg_burst = round(sum(target_burst_lengths) / len(target_burst_lengths), 1) if target_burst_lengths else 0
    target_reply_summary = summarize_numeric(target_reply_delays)
    style_tags: list[str] = []
    if avg_length < 18 and avg_burst >= 1.5:
        style_tags.append("短句连发型")
    elif avg_length >= 35:
        style_tags.append("长段落型")
    else:
        style_tags.append("中短句混合型")
    if time_buckets["late_night_23_04"] >= max(5, len(target_events) * 0.25):
        style_tags.append("夜聊活跃")
    if (target_reply_summary.get("median") or 0) and (target_reply_summary.get("median") or 0) <= 5:
        style_tags.append("回复偏快")
    if punctuation_counts["省略号"] > punctuation_counts["感叹号"]:
        style_tags.append("省略号偏好")
    if emphasis_counts["连续哈哈"] >= 3:
        style_tags.append("笑字强化")

    persona_signals, memory_signals = build_signal_bundle(
        target_events,
        repeated_clauses,
        opening_closing_patterns,
        style_tags,
        active_hours,
        target_reply_summary,
        representative_messages,
        sessions,
    )
    evidence_profile = {
        "by_type": dict(Counter(event.evidence_type for event in chronological)),
        "by_strength": dict(Counter(event.evidence_strength for event in chronological)),
        "sender_confidence": dict(Counter(event.sender_confidence for event in chronological)),
    }

    return {
        "platform": platform,
        "target_name": target_name,
        "total_messages": len(chronological),
        "target_messages": len(target_events),
        "user_messages": len(user_events),
        "unknown_messages": len(unknown_events),
        "analysis": {
            "top_particles": [{"token": token, "count": count} for token, count in particles.most_common(10)],
            "top_emojis": [{"token": token, "count": count} for token, count in emojis.most_common(10)],
            "avg_message_length": avg_length,
            "avg_line_count": avg_lines,
            "punctuation_habits": punctuation_counts,
            "emphasis_habits": emphasis_counts,
            "message_style": style_tags,
            "active_hours": active_hours,
            "time_buckets": time_buckets,
            "target_reply_delay": target_reply_summary,
            "user_reply_delay": summarize_numeric(user_reply_delays),
            "target_burst_length": summarize_numeric(target_burst_lengths),
            "session_count": len(sessions),
            "session_gap_minutes": session_gap_minutes,
            "initiated_sessions": {"target": initiated_by_target, "user": initiated_by_user},
            "repeated_clauses": repeated_clauses,
            "opening_patterns": opening_closing_patterns["openers"],
            "closing_patterns": opening_closing_patterns["closers"],
            "cleanup": cleanup_stats,
        },
        "evidence_profile": evidence_profile,
        "persona_signals": persona_signals,
        "memory_signals": memory_signals,
        "representative_messages": representative_messages,
        "representative_sessions": representative_sessions,
        "sessions": sessions[:20],
        "sample_messages": [{"timestamp": e.timestamp, "content": e.content} for e in target_events[:50]],
        "events": [asdict(event) for event in chronological[:500]],
    }


def write_markdown_report(
    result: dict[str, Any],
    source_file: str,
    detected_format: str,
    output_path: str,
    *,
    title: str,
) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    analysis = result["analysis"]
    cleanup = analysis.get("cleanup", {})
    persona_signals = result.get("persona_signals", {})
    memory_signals = result.get("memory_signals", {})
    evidence = result.get("evidence_profile", {})

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title} — {result['target_name']}\n\n")
        f.write(f"来源文件：{source_file}\n")
        f.write(f"检测格式：{detected_format}\n")
        f.write(f"平台：{result.get('platform', 'chat')}\n")
        f.write(f"总消息数：{result.get('total_messages', 'N/A')}\n")
        f.write(f"ta的消息数：{result.get('target_messages', 'N/A')}\n")
        f.write(f"你的消息数：{result.get('user_messages', 'N/A')}\n")
        f.write(f"未知发送方：{result.get('unknown_messages', 0)}\n\n")

        f.write("## 证据质量\n")
        f.write(f"- 证据类型：{json.dumps(evidence.get('by_type', {}), ensure_ascii=False)}\n")
        f.write(f"- 证据强度：{json.dumps(evidence.get('by_strength', {}), ensure_ascii=False)}\n")
        f.write(f"- 发送方识别置信度：{json.dumps(evidence.get('sender_confidence', {}), ensure_ascii=False)}\n")
        f.write(
            "- 清洗统计：系统消息移除 {system} / 去重 {dedupe} / 空消息 {empty} / 占位消息 {placeholder}\n\n".format(
                system=cleanup.get("system_messages_removed", 0),
                dedupe=cleanup.get("duplicates_removed", 0),
                empty=cleanup.get("empty_messages_removed", 0),
                placeholder=cleanup.get("placeholder_messages", 0),
            )
        )

        f.write("## 风格概览\n")
        f.write(f"- 风格标签：{', '.join(analysis.get('message_style', [])) or 'N/A'}\n")
        f.write(f"- 平均消息长度：{analysis.get('avg_message_length', 'N/A')} 字\n")
        f.write(f"- 平均消息行数：{analysis.get('avg_line_count', 'N/A')} 行\n")
        f.write(f"- 会话片段数：{analysis.get('session_count', 'N/A')}\n")
        initiated = analysis.get("initiated_sessions", {})
        f.write(f"- 会话发起：ta {initiated.get('target', 0)} 次 / 你 {initiated.get('user', 0)} 次\n\n")

        if analysis.get("top_particles"):
            f.write("## 高频语气词\n")
            for item in analysis["top_particles"]:
                f.write(f"- {item['token']}: {item['count']} 次\n")
            f.write("\n")

        if analysis.get("top_emojis"):
            f.write("## 高频 Emoji\n")
            for item in analysis["top_emojis"]:
                f.write(f"- {item['token']}: {item['count']} 次\n")
            f.write("\n")

        repeated = analysis.get("repeated_clauses", [])
        if repeated:
            f.write("## 重复短语 / 口头禅线索\n")
            for item in repeated:
                f.write(f"- {item['phrase']}：{item['count']} 次\n")
                if item["examples"]:
                    f.write(f"  例子：{' | '.join(item['examples'])}\n")
            f.write("\n")

        if analysis.get("opening_patterns"):
            f.write("## 常见开场句\n")
            for item in analysis["opening_patterns"]:
                f.write(f"- {item['phrase']}: {item['count']} 次\n")
            f.write("\n")

        if analysis.get("closing_patterns"):
            f.write("## 常见收尾句\n")
            for item in analysis["closing_patterns"]:
                f.write(f"- {item['phrase']}: {item['count']} 次\n")
            f.write("\n")

        f.write("## 标点与强调习惯\n")
        for punct, count in analysis.get("punctuation_habits", {}).items():
            f.write(f"- {punct}: {count} 次\n")
        for punct, count in analysis.get("emphasis_habits", {}).items():
            f.write(f"- {punct}: {count} 次\n")
        f.write("\n")

        f.write("## 活跃时间分布\n")
        for bucket, count in analysis.get("time_buckets", {}).items():
            f.write(f"- {bucket}: {count} 条\n")
        if analysis.get("active_hours"):
            top_hours = ", ".join(f"{item['hour']}点({item['count']})" for item in analysis["active_hours"])
            f.write(f"- 高频活跃小时：{top_hours}\n")
        f.write("\n")

        target_delay = analysis.get("target_reply_delay", {})
        user_delay = analysis.get("user_reply_delay", {})
        burst = analysis.get("target_burst_length", {})
        f.write("## 回复节奏\n")
        f.write("- ta 回复你：平均 {avg} / 中位 {median} / P75 {p75}\n".format(
            avg=format_minutes(target_delay.get("avg")),
            median=format_minutes(target_delay.get("median")),
            p75=format_minutes(target_delay.get("p75")),
        ))
        f.write("- 你回复 ta：平均 {avg} / 中位 {median} / P75 {p75}\n".format(
            avg=format_minutes(user_delay.get("avg")),
            median=format_minutes(user_delay.get("median")),
            p75=format_minutes(user_delay.get("p75")),
        ))
        f.write("- ta 连发长度：平均 {avg} 条 / 中位 {median} 条 / 最长 {maxv} 条\n\n".format(
            avg=burst.get("avg", "N/A"),
            median=burst.get("median", "N/A"),
            maxv=burst.get("max", "N/A"),
        ))

        if result.get("representative_messages"):
            f.write("## 代表性消息\n")
            for idx, item in enumerate(result["representative_messages"], 1):
                prefix = f"[{item['timestamp']}] " if item.get("timestamp") else ""
                f.write(f"{idx}. ({item['label']}) {prefix}{item['content']}\n")
            f.write("\n")

        if result.get("representative_sessions"):
            f.write("## 代表性会话片段\n")
            for session in result["representative_sessions"]:
                f.write("- Session #{sid} [{label}] {start} -> {end} | ta {target_cnt} / 你 {user_cnt}\n".format(
                    sid=session["session_id"],
                    label=session["label"],
                    start=session["started_at"] or "N/A",
                    end=session["ended_at"] or "N/A",
                    target_cnt=session["target_message_count"],
                    user_cnt=session["user_message_count"],
                ))
                for turn in session.get("sample_turns", []):
                    f.write(f"  - {turn['sender_role']}: {turn['content']}\n")
            f.write("\n")

        f.write("## Persona 线索包\n")
        f.write(f"- 说话风格：{', '.join(persona_signals.get('speech_style', [])) or 'N/A'}\n")
        f.write(f"- 口头禅候选：{', '.join(persona_signals.get('catchphrases', [])) or 'N/A'}\n")
        f.write(f"- 可能的称呼方式：{', '.join(persona_signals.get('possible_addressing_terms', [])) or 'N/A'}\n")
        f.write(f"- 标志性句子：{' | '.join(persona_signals.get('signature_lines', [])) or 'N/A'}\n\n")

        f.write("## Memory 线索包\n")
        f.write(f"- 会话标签分布：{json.dumps(memory_signals.get('dominant_session_labels', {}), ensure_ascii=False)}\n")
        f.write(f"- 深夜片段：{' | '.join(memory_signals.get('late_night_sessions', [])) or 'N/A'}\n")
        f.write(f"- 计划片段：{' | '.join(memory_signals.get('planning_sessions', [])) or 'N/A'}\n")
        f.write(f"- 甜蜜片段：{' | '.join(memory_signals.get('affection_sessions', [])) or 'N/A'}\n")
        f.write(f"- 冲突片段：{' | '.join(memory_signals.get('conflict_sessions', [])) or 'N/A'}\n")
