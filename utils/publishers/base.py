from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import json
import os

from agents.content_agent import Content


@dataclass
class PublishResult:
    platform: str
    mode: str
    ok: bool
    output_dir: Optional[str] = None
    error: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class BasePublisher:
    def __init__(self, platform: str, dry_run: bool = True, output_root: Optional[str] = None):
        self.platform = platform
        self.dry_run = dry_run
        self.output_root = Path(output_root or os.path.join("output", "content"))

    def ensure_dir(self, hotspot_id: str) -> Path:
        date_part = (hotspot_id.split("-")[1] if "-" in hotspot_id else None) or "latest"
        out_dir = self.output_root / date_part / hotspot_id / self.platform
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def render(self, content: Content) -> str:
        """子类实现：基于模板渲染文本。"""
        raise NotImplementedError

    def publish(self, hotspot_id: str, content: Content) -> PublishResult:
        try:
            if not self.dry_run:
                # 实发模式留空（后续接入 API）
                return PublishResult(platform=self.platform, mode="api", ok=False, error="API 未实现")

            # dry-run: 渲染并落盘
            out_dir = self.ensure_dir(hotspot_id)
            rendered = self.render(content)
            # 统一文件名
            text_name = {
                "wechat": "article.md",
                "weibo": "post.md",
                "bilibili": "script.md",
            }.get(self.platform, "content.md")

            (out_dir / text_name).write_text(rendered, encoding="utf-8")
            meta = {
                "platform": self.platform,
                "hotspot_id": hotspot_id,
                "title": content.title,
                "hashtags": content.hashtags,
                "images": content.images,
                "timestamp": content.timestamp,
                "metadata": content.metadata,
            }
            with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            return PublishResult(platform=self.platform, mode="dry", ok=True, output_dir=str(out_dir))
        except Exception as e:
            return PublishResult(platform=self.platform, mode="dry" if self.dry_run else "api", ok=False, error=str(e))
