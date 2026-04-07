from __future__ import annotations

import json
import os
from urllib import error, request
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from pantryapp.pantry_model import get_all_items, get_item_lookup_by_id
from database import engine


def _load_dotenv_from_home_app() -> None:
    """
    Load KEY=VALUE pairs from home_app/.env into process env if not already set.
    Keeps behavior dependency-free (no python-dotenv required).
    """
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        # Keep assistant usable even if .env parsing fails.
        return


def _pantry_snapshot(max_items: int = 120) -> list[dict[str, object]]:
    items = get_all_items() or []
    snapshot: list[dict[str, object]] = []

    for item in items[:max_items]:
        lookup = get_item_lookup_by_id(item.item_lookup_id)
        name = "Unknown item"
        barcode = None
        if lookup is not None:
            name = str(getattr(lookup, "item_name", "") or "Unknown item")
            barcode = str(getattr(lookup, "barcode", "") or "").strip() or None

        snapshot.append(
            {
                "name": name,
                "quantity": int(getattr(item, "quantity", 0) or 0),
                "barcode": barcode,
            }
        )

    return snapshot


def _normalize_cell(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        try:
            return float(value)
        except Exception:
            return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<binary:{len(value)} bytes>"
    if isinstance(value, str):
        text_val = value.strip()
        if len(text_val) > 240:
            return text_val[:240] + "..."
        return text_val
    return value


def _database_snapshot(max_rows_per_table: int = 20, max_tables: int = 50) -> dict[str, object]:
    """
    Return a lightweight snapshot of all public tables so the assistant can reason
    over data across modules (pantry, chores, cooking, people, etc.).
    """
    result: dict[str, object] = {"tables": {}, "errors": []}

    try:
        with engine.begin() as conn:
            table_rows = conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
            ).all()
            table_names = [row[0] for row in table_rows][:max_tables]

            col_rows = conn.execute(
                text(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                    """
                )
            ).all()
            columns_by_table: dict[str, list[str]] = {}
            for table_name, column_name in col_rows:
                columns_by_table.setdefault(table_name, []).append(column_name)

            for table_name in table_names:
                safe_table = str(table_name).replace('"', '""')
                rows = (
                    conn.execute(
                        text(f'SELECT * FROM "{safe_table}" LIMIT :row_limit'),
                        {"row_limit": max_rows_per_table},
                    )
                    .mappings()
                    .all()
                )

                normalized_rows = []
                for row in rows:
                    normalized_rows.append({k: _normalize_cell(v) for k, v in dict(row).items()})

                result["tables"][table_name] = {
                    "columns": columns_by_table.get(table_name, []),
                    "sample_rows": normalized_rows,
                }
    except SQLAlchemyError as e:
        result["errors"].append(f"Database snapshot error: {e}")
    except Exception as e:
        result["errors"].append(f"Unexpected snapshot error: {e}")

    return result


def ask_pantry_assistant(question: str) -> str:
    _load_dotenv_from_home_app()

    user_question = str(question or "").strip()
    if not user_question:
        return "Please enter a question."

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return "OPENROUTER_API_KEY is not set. Add it to your environment, then try again."

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    pantry_data = _pantry_snapshot()
    app_data = _database_snapshot()

    system_prompt = (
        "You are HomeCopilot, a conversational but strict home-app assistant.\n"
        "You can answer questions about pantry, chores, recipes, people, and related app data.\n"
        "Examples of supported questions: 'What chores are there?', 'What can I cook?', 'What items are low?'.\n"
        "Rules:\n"
        "1) Use only the app data JSON provided in the user message. Do not invent records.\n"
        "2) If information is missing, say that clearly and ask one short follow-up question.\n"
        "3) Be friendly and concise. Prefer short bullets for lists.\n"
        "4) Stay task-focused on home app data; avoid unrelated advice or long tangents.\n"
        "5) If a request cannot be completed from available data, say what is possible right now.\n"
        "Response style:\n"
        "- For list-style questions (like chores), return a clear bullet list.\n"
        "- For pantry/cooking questions, include: options, missing items, and a practical next step."
    )
    user_content = (
        f"Pantry inventory JSON:\n{json.dumps(pantry_data, ensure_ascii=True)}\n\n"
        f"All app tables JSON:\n{json.dumps(app_data, ensure_ascii=True)}\n\n"
        f"User question:\n{user_question}"
    )

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }

    req = request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Home App Pantry Assistant",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        try:
            details = e.read().decode("utf-8", errors="replace")
        except Exception:
            details = str(e)
        return f"OpenRouter request failed ({e.code}): {details}"
    except error.URLError as e:
        return f"Network error calling OpenRouter: {e.reason}"
    except Exception as e:
        return f"Unexpected error calling OpenRouter: {e}"

    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        return f"Unexpected OpenRouter response: {json.dumps(data)[:500]}"

    if isinstance(content, list):
        joined = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                joined.append(str(block.get("text", "")))
        content = "\n".join(joined).strip()

    return str(content or "").strip() or "No response from model."
