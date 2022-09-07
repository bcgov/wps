""" Create/Read/Update/Delete """
from datetime import date
import logging
from time import perf_counter
from typing import List
from sqlalchemy import select
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from advisory.db.models.tileserver import (Hfi, FireZone)

logger = logging.getLogger(__name__)
