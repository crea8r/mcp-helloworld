# notes-mcp (example skill)

This is an example skill file for the Notes MCP server in this repo. It is
not installed into any global skill list.

## Purpose
Help an agent interact with the Notes MCP tools to create, read, update,
delete, tag, and search notes.

## When to use
- Any request about notes, tags, or search in this project.
- When the user asks to perform actions via MCP tools.

## Core tools
- `create_note(title, content)`
- `list_notes()`
- `get_note(note_id)`
- `update_note(note_id, title?, content?)`
- `delete_note(note_id)`
- `create_tag(name)`
- `list_tags()`
- `attach_tags(note_id, tag_ids)`
- `attach_tags_by_name(note_id, names)`
- `detach_tag(note_id, tag_id)`
- `search_notes(query)`

## Workflow
1. Parse the request into structured actions.
2. Map each action to the most specific MCP tool.
3. Execute tool calls with typed payloads.
4. Report results with returned IDs and timestamps.

## Examples
- "Show notes containing 'fox'" -> `search_notes(query="fox")`
- "Create a note about X" -> `create_note(title="Note", content="...")`
- "Tag note 12 with ideas" -> `attach_tags_by_name(note_id=12, names=["ideas"])`
