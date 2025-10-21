"""
统一的内容与风格数据模型（避免在页面/Agent中硬编码平台与风格规则）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from config.workflow_config import (
    get_workflow_config,
    load_style_presets,
    load_platform_guidelines,
)


@dataclass
class StyleSpec:
    """风格预设的语义结构，来源于 style_presets.json 中的某个 preset。"""
    key: str
    tone: Optional[str] = None
    structure: List[str] = field(default_factory=list)
    length: Dict[str, Any] = field(default_factory=dict)
    emoji: bool = False
    hashtags: Dict[str, Any] = field(default_factory=dict)
    forbidden: List[str] = field(default_factory=list)

    @staticmethod
    def from_presets(presets: Dict[str, Any], key: str) -> "StyleSpec":
        if not presets or "presets" not in presets:
            raise ValueError("style_presets.json 加载失败或结构不正确")
        data = presets["presets"].get(key)
        if not data:
            raise KeyError(f"未找到风格预设: {key}")
        return StyleSpec(
            key=key,
            tone=data.get("tone"),
            structure=list(data.get("structure", [])),
            length=dict(data.get("length", {})),
            emoji=bool(data.get("emoji", False)),
            hashtags=dict(data.get("hashtags", {})),
            forbidden=list(data.get("forbidden", [])),
        )


@dataclass
class PlatformGuidelines:
    """平台规范集合，来源于 platform_guidelines.json。"""
    wechat: Dict[str, Any] = field(default_factory=dict)
    weibo: Dict[str, Any] = field(default_factory=dict)
    bilibili: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PlatformGuidelines":
        if not data:
            return PlatformGuidelines()
        return PlatformGuidelines(
            wechat=dict(data.get("wechat", {})),
            weibo=dict(data.get("weibo", {})),
            bilibili=dict(data.get("bilibili", {})),
        )

    def get(self, platform: str) -> Dict[str, Any]:
        if platform == "wechat":
            return self.wechat
        if platform == "weibo":
            return self.weibo
        if platform == "bilibili":
            return self.bilibili
        return {}


@dataclass
class PlatformContent:
    """统一的多平台内容承载结构。"""
    contents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    style_key: Optional[str] = None
    cluster_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get(self, platform: str) -> Optional[Dict[str, Any]]:
        return self.contents.get(platform)

    def set(self, platform: str, content: Dict[str, Any]) -> None:
        self.contents[platform] = content

    def platforms(self) -> List[str]:
        return list(self.contents.keys())


# 加载器

def load_default_style() -> StyleSpec:
    cfg = get_workflow_config()
    presets = load_style_presets(cfg.style_presets_path)
    key = cfg.style_default
    return StyleSpec.from_presets(presets, key)


def load_guidelines() -> PlatformGuidelines:
    data = load_platform_guidelines()
    return PlatformGuidelines.from_dict(data or {})


# 校验规则（基于平台规范进行快速静态检查）

def validate_by_guideline(platform: str, content: Dict[str, Any], guidelines: PlatformGuidelines) -> Tuple[bool, Optional[str]]:
    rules = guidelines.get(platform) or {}
    text = (content or {}).get("content", "") or ""
    title = (content or {}).get("title")

    if platform == "wechat":
        min_len = int(rules.get("content_min", 0))
        max_len = int(rules.get("content_max", 10_000))
        if not title or not str(title).strip():
            return False, "微信公众号内容需要标题"
        if not (min_len <= len(text) <= max_len):
            return False, f"微信公众号内容长度需在{min_len}-{max_len}字"

    elif platform == "weibo":
        max_len = int(rules.get("content_max", 2000))
        if len(text) > max_len:
            return False, f"微博内容不能超过{max_len}字"

    elif platform == "bilibili":
        meta = (content or {}).get("metadata", {})
        scenes = (meta or {}).get("scenes")
        if not scenes or not isinstance(scenes, list):
            return False, "B站脚本需要包含 metadata.scenes 分镜信息"

    return True, None


def validate_platform_contents(contents: PlatformContent, guidelines: Optional[PlatformGuidelines] = None) -> Dict[str, Tuple[bool, Optional[str]]]:
    if guidelines is None:
        guidelines = load_guidelines()
    results: Dict[str, Tuple[bool, Optional[str]]] = {}
    for platform, content in contents.contents.items():
        results[platform] = validate_by_guideline(platform, content, guidelines)
    return results
