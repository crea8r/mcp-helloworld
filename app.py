from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

import service

app = FastAPI(title="Notes MCP Server", version="0.1.0")


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    content: Optional[str] = Field(None, min_length=1)


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1)


class TagAttach(BaseModel):
    tag_ids: List[int] = Field(default_factory=list)


class TagAttachByName(BaseModel):
    names: List[str] = Field(default_factory=list)


def _handle_service_error(exc: service.ServiceError) -> None:
    status = 400
    if exc.code == "not_found":
        status = 404
    elif exc.code == "conflict":
        status = 409
    raise HTTPException(status_code=status, detail=str(exc))


@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/notes")
def create_note(payload: NoteCreate) -> Dict[str, Any]:
    try:
        return service.create_note(payload.title, payload.content)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.get("/notes")
def list_notes() -> List[Dict[str, Any]]:
    return service.list_notes()


@app.get("/notes/{note_id}")
def get_note(note_id: int) -> Dict[str, Any]:
    try:
        return service.get_note(note_id)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.put("/notes/{note_id}")
def update_note(note_id: int, payload: NoteUpdate) -> Dict[str, Any]:
    try:
        return service.update_note(note_id, title=payload.title, content=payload.content)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.delete("/notes/{note_id}")
def delete_note(note_id: int) -> Dict[str, Any]:
    try:
        return service.delete_note(note_id)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.post("/tags")
def create_tag(payload: TagCreate) -> Dict[str, Any]:
    try:
        return service.create_tag(payload.name)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.get("/tags")
def list_tags() -> List[Dict[str, Any]]:
    return service.list_tags()


@app.post("/notes/{note_id}/tags")
def attach_tags(note_id: int, payload: TagAttach) -> Dict[str, Any]:
    try:
        return service.attach_tags(note_id, payload.tag_ids)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.post("/notes/{note_id}/tags/by-name")
def attach_tags_by_name(note_id: int, payload: TagAttachByName) -> Dict[str, Any]:
    try:
        return service.attach_tags_by_name(note_id, payload.names)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.delete("/notes/{note_id}/tags/{tag_id}")
def detach_tag(note_id: int, tag_id: int) -> Dict[str, Any]:
    try:
        return service.detach_tag(note_id, tag_id)
    except service.ServiceError as exc:
        _handle_service_error(exc)


@app.get("/search")
def search(q: str = Query(..., min_length=1)) -> Dict[str, Any]:
    try:
        return service.search_notes(q)
    except service.ServiceError as exc:
        _handle_service_error(exc)
