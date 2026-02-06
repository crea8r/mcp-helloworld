from __future__ import annotations

import argparse
import inspect
import os
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

import service

MCP_HOST = os.environ.get("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("MCP_PORT", "8001"))
MCP_PATH = os.environ.get("MCP_PATH", "/mcp")

mcp = FastMCP(
    "Notes MCP",
    json_response=True,
    host=MCP_HOST,
    port=MCP_PORT,
    streamable_http_path=MCP_PATH,
)


def _handle_service_error(exc: service.ServiceError) -> None:
    raise ValueError(str(exc))


@mcp.tool()
def create_note(title: str, content: str) -> Dict[str, Any]:
    """Create a note."""
    try:
        return service.create_note(title, content)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def list_notes() -> List[Dict[str, Any]]:
    """List notes."""
    return service.list_notes()


@mcp.tool()
def get_note(note_id: int) -> Dict[str, Any]:
    """Get a note by id."""
    try:
        return service.get_note(note_id)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def update_note(note_id: int, title: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
    """Update a note by id."""
    try:
        return service.update_note(note_id, title=title, content=content)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def delete_note(note_id: int) -> Dict[str, Any]:
    """Delete a note by id."""
    try:
        return service.delete_note(note_id)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def create_tag(name: str) -> Dict[str, Any]:
    """Create a tag."""
    try:
        return service.create_tag(name)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def list_tags() -> List[Dict[str, Any]]:
    """List tags."""
    return service.list_tags()


@mcp.tool()
def attach_tags(note_id: int, tag_ids: List[int]) -> Dict[str, Any]:
    """Attach tags to a note (by tag IDs)."""
    try:
        return service.attach_tags(note_id, tag_ids)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def attach_tags_by_name(note_id: int, names: List[str]) -> Dict[str, Any]:
    """Attach tags to a note (by tag names, creates missing tags)."""
    try:
        return service.attach_tags_by_name(note_id, names)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def detach_tag(note_id: int, tag_id: int) -> Dict[str, Any]:
    """Detach a tag from a note."""
    try:
        return service.detach_tag(note_id, tag_id)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.tool()
def search_notes(query: str) -> Dict[str, Any]:
    """Search notes by query and return scored sentences."""
    try:
        return service.search_notes(query)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@mcp.resource("note://{note_id}")
def note_resource(note_id: int) -> Dict[str, Any]:
    """Read a note by id as a resource."""
    return get_note(note_id)


@mcp.resource("tags://list")
def tags_resource() -> List[Dict[str, Any]]:
    """List tags as a resource."""
    return list_tags()


def main() -> None:
    parser = argparse.ArgumentParser(description="Notes MCP server")
    parser.add_argument(
        "--transport",
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        choices=["stdio", "streamable-http", "sse"],
        help="MCP transport to use",
    )
    parser.add_argument("--host", default=MCP_HOST)
    parser.add_argument("--port", type=int, default=MCP_PORT)
    parser.add_argument("--path", default=MCP_PATH)
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return

    run_sig = inspect.signature(mcp.run)
    supports_host = "host" in run_sig.parameters
    supports_port = "port" in run_sig.parameters
    supports_path = "path" in run_sig.parameters
    supports_mount = "mount_path" in run_sig.parameters

    if args.transport == "streamable-http":
        if supports_host and supports_port and supports_path:
            mcp.run(transport="streamable-http", host=args.host, port=args.port, path=args.path)
            return
        if supports_mount:
            mcp.run(transport="streamable-http", mount_path=args.path)
            return
        mcp.run(transport="streamable-http")
        return

    if supports_host and supports_port:
        mcp.run(transport="sse", host=args.host, port=args.port)
        return
    if supports_mount:
        mcp.run(transport="sse", mount_path=args.path)
        return
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
