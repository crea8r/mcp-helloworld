# Notes Webserver (SQLite)

A minimal FastAPI webserver that supports notes, tags, and a simple search endpoint. Uses SQLite for storage and keeps everything in a single file: `notes.db`.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app:app --reload
```

Server will run at `http://127.0.0.1:8000`.

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

## Notes

- The database file `notes.db` will be created in the project root.
- This is a minimal server with direct SQLite access for clarity and ease of hacking.
