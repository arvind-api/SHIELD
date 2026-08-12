"""Shared rate limiter instance. Imported by main.py (to register the
middleware/exception handler) and by individual route modules (to apply
per-endpoint limits) — kept in its own module so both sides can import it
without a circular import through main.py.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
