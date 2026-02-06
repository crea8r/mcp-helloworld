# Notes Webserver (SQLite)

A minimal FastAPI webserver that supports notes, tags, and a simple search endpoint. Uses SQLite for storage and keeps everything in a single file: `notes.db`.

This repo is designed as a small, inspectable example for building agent-friendly services. For a high-level explanation of how an agent loop works, see the interactive: [Agent Loop Interactive](https://techexplain.netlify.app/interactives/agent-loop/).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app:app --reload
```

Server will run at `http://127.0.0.1:8000`.

## Purpose

- Provide a tiny notes API with tags and search.
- Expose an MCP server so agents can call typed tools.
- Offer a simple example of intent-to-tool mapping for agent workflows.

## Data Model

- `notes`: id, title, content, created_at, updated_at
- `tags`: id, name (unique)
- `note_tags`: note_id, tag_id (unique per pair)

## API

### Notes

Create a note:

```bash
curl -X POST http://127.0.0.1:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"First note","content":"Hello world. This is a test note."}'
```

List notes:

```bash
curl http://127.0.0.1:8000/notes
```

Get one note:

```bash
curl http://127.0.0.1:8000/notes/1
```

Update a note:

```bash
curl -X PUT http://127.0.0.1:8000/notes/1 \
  -H "Content-Type: application/json" \
  -d '{"content":"Updated content. Now with more details."}'
```

Delete a note:

```bash
curl -X DELETE http://127.0.0.1:8000/notes/1
```

### Tags

Create a tag:

```bash
curl -X POST http://127.0.0.1:8000/tags \
  -H "Content-Type: application/json" \
  -d '{"name":"ideas"}'
```

List tags:

```bash
curl http://127.0.0.1:8000/tags
```

Attach tags (by tag IDs):

```bash
curl -X POST http://127.0.0.1:8000/notes/1/tags \
  -H "Content-Type: application/json" \
  -d '{"tag_ids":[1,2]}'
```

Attach tags by name (creates missing tags):

```bash
curl -X POST http://127.0.0.1:8000/notes/1/tags/by-name \
  -H "Content-Type: application/json" \
  -d '{"names":["ideas","mcp"]}'
```

Detach a tag from a note:

```bash
curl -X DELETE http://127.0.0.1:8000/notes/1/tags/1
```

### Search

Simple token search with sentence scoring. Query is split into tokens, then each note is scored by matching tokens in sentences. Top sentences are returned per note.

```bash
curl "http://127.0.0.1:8000/search?q=hello+test"
```

Response shape:

```json
{
  "query": "hello test",
  "tokens": ["hello", "test"],
  "results": [
    {
      "note": { "id": 1, "title": "First note", "content": "...", "created_at": "...", "updated_at": "...", "tags": [] },
      "score": 2,
      "top_sentences": [
        { "sentence": "Hello world.", "score": 1 },
        { "sentence": "This is a test note.", "score": 1 }
      ]
    }
  ]
}
```

## MCP Server

This project includes an MCP server that exposes tools and resources for the notes database.

### Run (stdio)

```bash
python mcp_server.py --transport stdio
```

### Run (HTTP streamable)

```bash
python mcp_server.py --transport streamable-http --host 127.0.0.1 --port 8001 --path /mcp
```

### Run (SSE)

```bash
python mcp_server.py --transport sse --host 127.0.0.1 --port 8001
```

### Tools

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

### Resources

- `note://{note_id}`
- `tags://list`

## MCP Client Setup (Codex, Claude, etc.)

Most MCP-capable clients let you add a server in one of two ways:

1. **stdio (local command)**: the client launches the server process directly.
2. **HTTP/SSE (remote URL)**: the client connects to a running MCP server.

Use one of the transports below depending on what your client supports. Refer to your client’s MCP settings UI or docs for the exact config format.

**stdio (local process)**

```bash
python mcp_server.py --transport stdio
```

**streamable HTTP (URL)**

```bash
python mcp_server.py --transport streamable-http --host 127.0.0.1 --port 8001 --path /mcp
```

Connect your client to:

```text
http://127.0.0.1:8001/mcp
```

**SSE (URL)**

```bash
python mcp_server.py --transport sse --host 127.0.0.1 --port 8001
```

Connect your client to:

```text
http://127.0.0.1:8001
```

## Example Skill File

This repo includes an example `SKILL.md` that documents how an agent should use the Notes MCP tools. It is not installed into any global skill list.

- Example skill: `SKILL.md`
- Served at runtime: `GET /skill.md`

## Intent-to-Tool Mapping (How the Agent Chooses MCP Calls)

When using the MCP tools via an agent, the agent first derives a structured intent from a natural language request, then maps that intent to the most specific MCP tool available.

Example user request:

```text
I want to show notes that has the word "fox".
```

Structured intent (example):

```json
{
  "actions": [
    {
      "type": "search_notes",
      "query": "fox",
      "purpose": "show notes containing word 'fox'"
    }
  ]
}
```

Tool mapping:

- Intent: `search_notes` -> MCP tool: `search_notes(query)`
- Payload: `{ "query": "fox" }`

Why `search_notes` is chosen:

- The request asks for notes containing a word.
- `list_notes()` has no filter.
- `search_notes(query)` is the only tool that can filter by content.

This same pattern applies to other requests (e.g., "create a note", "update note 1", "attach tags", "list tags").

## Notes

- The database file `notes.db` will be created in the project root.
- This is a minimal server with direct SQLite access for clarity and ease of hacking.
