"""ASGI export. Run: uvicorn app.main:app --reload"""
from app.entrypoints.http.app import create_app

app = create_app()
