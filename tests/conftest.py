from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Settings
from src.ingest import ingest_directory

HANDBOOK = """# Acme Employee Handbook

> Last reviewed: 1 January 2026

## 1. Paid time off

Eligible employees receive **20 days of paid time off (PTO)** per calendar year.
PTO accrues at 1.67 days per month. Employees may carry over at most 5 days.

## 2. Parental leave

The primary caregiver receives **16 weeks of fully paid parental leave**. The
secondary caregiver receives 6 weeks.

## 3. Remote work

Employees may work remotely up to three days per week. Core hours are 10:00 to
15:00 India Standard Time.
"""

SECURITY = """# Acme Security Policy

## 1. Lost devices

Report a lost or stolen laptop to the Security Office within **one hour**. Do not
attempt to recover the device yourself.

## 2. Artificial intelligence

Do not paste customer data, credentials, or source code into public AI tools.
Only approved AI assistants may be used for company work.

## 3. Passwords

Use a password manager. Multi-factor authentication is mandatory for production
systems.
"""


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / "docs"
    data_dir.mkdir()
    (data_dir / "handbook.md").write_text(HANDBOOK, encoding="utf-8")
    (data_dir / "security.md").write_text(SECURITY, encoding="utf-8")
    return Settings(
        data_dir=data_dir,
        vector_dir=tmp_path / "vector_store",
        embedding_backend="hash",
        vector_backend="sqlite",
        chunk_size=420,
        chunk_overlap=90,
        top_k=3,
        retrieval_candidates=8,
        llm_provider="offline",
    )


@pytest.fixture()
def indexed_settings(settings: Settings) -> Settings:
    ingest_directory(settings)
    return settings
