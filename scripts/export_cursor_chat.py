# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer",
# ]
# ///
"""
Export Cursor agent chat transcripts from local JSONL files to Markdown or plain text.

Transcripts are read line-by-line (streaming) for large histories.
"""

from __future__ import annotations

import json
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Iterator, TextIO

import typer

app = typer.Typer(add_completion=False, help=__doc__ or "Export Cursor JSONL transcripts.")


class OutputFormat(str, Enum):
    """Supported output formats."""

    markdown = "markdown"
    text = "text"


def cursor_transcripts_root_for_project(project_dir: Path) -> Path:
    """
    Map a workspace directory to Cursor's ``agent-transcripts`` folder.

    Cursor stores per-project data under ``~/.cursor/projects/<slug>/`` where
    ``slug`` is the absolute project path with path separators replaced by hyphens
    and without a leading slash (observed on macOS/Linux).

    :param project_dir: Workspace root (repository or folder opened in Cursor).
    :returns: Path to the ``agent-transcripts`` directory for that workspace.
    """
    resolved = project_dir.resolve()
    slug = resolved.as_posix().lstrip("/").replace("/", "-")
    return Path.home() / ".cursor" / "projects" / slug / "agent-transcripts"


def iter_main_transcript_files(transcripts_root: Path) -> Iterator[Path]:
    """
    Yield ``<uuid>/<uuid>.jsonl`` files under a transcripts root (excludes subagent logs).

    :param transcripts_root: Directory containing one folder per conversation UUID.
    :yields: Paths to each main transcript JSONL file.
    """
    if not transcripts_root.is_dir():
        return
    for child in transcripts_root.iterdir():
        if not child.is_dir():
            continue
        candidate = child / f"{child.name}.jsonl"
        if candidate.is_file():
            yield candidate


def latest_main_transcript(transcripts_root: Path) -> Path | None:
    """
    Return the most recently modified main transcript under ``transcripts_root``.

    :param transcripts_root: Directory containing conversation folders.
    :returns: Path to newest ``<uuid>/<uuid>.jsonl``, or ``None`` if none exist.
    """
    paths = list(iter_main_transcript_files(transcripts_root))
    if not paths:
        return None
    return max(paths, key=lambda p: p.stat().st_mtime)


def resolve_input_path(
    transcript: Path | None,
    uuid: str | None,
    transcripts_root: Path,
) -> Path:
    """
    Resolve which JSONL file to read.

    :param transcript: Explicit path to a ``.jsonl`` file.
    :param uuid: Conversation UUID; reads ``<root>/<uuid>/<uuid>.jsonl``.
    :param transcripts_root: Default root when resolving ``uuid``.
    :returns: Path to an existing JSONL file.
    :raises typer.BadParameter: If arguments are inconsistent or file missing.
    """
    if transcript is not None and uuid is not None:
        raise typer.BadParameter("Pass either --transcript or --uuid, not both.")
    if transcript is not None:
        p = transcript.expanduser().resolve()
        if not p.is_file():
            raise typer.BadParameter(f"Transcript not found: {p}")
        return p
    if uuid is not None:
        p = transcripts_root / uuid / f"{uuid}.jsonl"
        if not p.is_file():
            raise typer.BadParameter(f"No transcript at {p}")
        return p
    latest = latest_main_transcript(transcripts_root)
    if latest is None:
        raise typer.BadParameter(
            f"No transcripts under {transcripts_root}. "
            "Use --transcript, --uuid, or --transcripts-root."
        )
    return latest


_USER_TEXT_RE = re.compile(
    r"(?:<timestamp>(?P<ts>.*?)</timestamp>\s*)?"
    r"<user_query>\s*(?P<body>.*?)\s*</user_query>\s*$",
    re.DOTALL,
)


def normalize_user_display(text: str) -> tuple[str | None, str]:
    """
    Pull optional timestamp and user body from Cursor's wrapped user text.

    :param text: Raw ``text`` field from a user message block.
    :returns: Tuple of optional timestamp string and display body.
    """
    m = _USER_TEXT_RE.match(text.strip())
    if not m:
        return None, text
    ts = m.group("ts")
    body = m.group("body").strip()
    return (ts if ts else None), body


def format_content_blocks(blocks: list[dict[str, Any]], role: str, fmt: OutputFormat) -> str:
    """
    Turn ``message.content`` items into readable text.

    :param blocks: List of content dicts (``type`` ``text`` or ``tool_use``).
    :param role: ``user`` or ``assistant`` (affects user text normalization).
    :param fmt: Markdown or plain text.
    :returns: Formatted chunk (may be empty).
    """
    parts: list[str] = []
    for item in blocks:
        kind = item.get("type")
        if kind == "text":
            raw = item.get("text", "")
            if not isinstance(raw, str):
                raw = str(raw)
            if role == "user":
                ts, body = normalize_user_display(raw)
                if fmt == OutputFormat.markdown:
                    if ts:
                        parts.append(f"*{ts}*\n")
                    parts.append(body)
                else:
                    if ts:
                        parts.append(f"[{ts}]")
                    parts.append(body)
            else:
                parts.append(raw)
        elif kind == "tool_use":
            name = item.get("name", "")
            inp = item.get("input")
            if fmt == OutputFormat.markdown:
                parts.append(f"\n**Tool:** `{name}`\n")
                if isinstance(inp, (dict, list)):
                    parts.append("```json\n" + json.dumps(inp, indent=2, ensure_ascii=False) + "\n```")
                else:
                    parts.append(f"```\n{inp}\n```")
            else:
                parts.append(f"\n[TOOL {name}]\n")
                if isinstance(inp, (dict, list)):
                    parts.append(json.dumps(inp, indent=2, ensure_ascii=False))
                else:
                    parts.append(str(inp))
    return "\n\n".join(p for p in parts if p)


def stream_transcript_to_writer(
    path: Path,
    writer: TextIO,
    fmt: OutputFormat,
) -> None:
    """
    Read JSONL from ``path`` and write formatted turns to ``writer``.

    :param path: Transcript file.
    :param writer: Open text stream (e.g. ``sys.stdout``).
    :param fmt: Output format.
    """
    turn = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            role = row.get("role", "unknown")
            message = row.get("message") or {}
            content = message.get("content")
            if not isinstance(content, list):
                content = []
            body = format_content_blocks(content, str(role), fmt)
            turn += 1
            if fmt == OutputFormat.markdown:
                writer.write(f"\n## Turn {turn} — **{role}**\n\n")
                writer.write(body)
                writer.write("\n\n---\n")
            else:
                writer.write(f"\n{'=' * 72}\nTurn {turn} | {role}\n{'=' * 72}\n\n")
                writer.write(body)
                writer.write("\n")


@app.command()
def main(
    transcript: Path | None = typer.Option(
        None,
        "--transcript",
        "-t",
        help="Path to a .jsonl transcript file.",
        exists=False,
        file_okay=True,
        dir_okay=False,
    ),
    uuid: str | None = typer.Option(
        None,
        "--uuid",
        "-u",
        help="Conversation UUID; uses <transcripts-root>/<uuid>/<uuid>.jsonl.",
    ),
    transcripts_root: Path | None = typer.Option(
        None,
        "--transcripts-root",
        help="Explicit agent-transcripts directory (overrides --project-dir mapping).",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-p",
        help="Workspace path; used to locate ~/.cursor/projects/<slug>/agent-transcripts.",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    out: Path | None = typer.Option(
        None,
        "--out",
        "-o",
        help="Output file (default: stdout).",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.markdown,
        "--format",
        "-f",
        help="markdown or text.",
        case_sensitive=False,
    ),
) -> None:
    """Export a Cursor JSONL transcript to readable Markdown or text."""
    root = transcripts_root.expanduser().resolve() if transcripts_root else cursor_transcripts_root_for_project(project_dir)
    in_path = resolve_input_path(transcript, uuid, root)
    if out is None:
        stream_transcript_to_writer(in_path, sys.stdout, output_format)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            stream_transcript_to_writer(in_path, fh, output_format)


if __name__ == "__main__":
    app()
