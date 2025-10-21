from __future__ import annotations
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Dict, Any

from .base import BasePublisher


class WechatPublisher(BasePublisher):
    def __init__(self, dry_run: bool = True, output_root: str | None = None):
        super().__init__(platform="wechat", dry_run=dry_run, output_root=output_root)
        self.env = Environment(
            loader=FileSystemLoader(str(Path("templates/platform"))),
            autoescape=select_autoescape()
        )
        self.template = self.env.get_template("wechat.md.j2")

    def render(self, content):
        data: Dict[str, Any] = {
            "title": content.title or "",
            "lead": content.metadata.get("lead", "") if isinstance(content.metadata, dict) else "",
            "sections": content.metadata.get("sections", []) if isinstance(content.metadata, dict) else [],
            "outro": content.metadata.get("outro", "") if isinstance(content.metadata, dict) else "",
            "images": content.images or [],
        }
        if not data["sections"]:
            # 回退：将正文放入单节
            data["sections"] = [{"title": "正文", "content": content.content}]
        return self.template.render(**data)
