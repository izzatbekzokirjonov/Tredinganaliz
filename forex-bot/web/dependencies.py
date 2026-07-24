"""
FastAPI uchun umumiy dependency lar.
"""
from fastapi import Request
import asyncpg


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool
