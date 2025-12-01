# Copyright (c) 2025 Mimer Information Technology

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# See license for more details.

from mimerpy.pool import MimerPool, MimerPoolError
import logging
from typing import Optional

from mimer_mcp_server import config

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dsn": config.DB_DSN,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
}

# Global pool variable
pool: Optional[MimerPool] = None


def init_db_pool() -> MimerPool:
    """Initialize the database connection pool.

    This function should be called once at application startup to create
    a connection pool that will be used throughout the application lifetime.

    Returns:
        MimerPool: The initialized connection pool

    Raises:
        MimerPoolError: If pool creation fails
    """
    global pool
    if pool is not None:
        logger.debug("Database connection pool is already initialized.")
        return pool
    # Validate mandatory config
    if not config.DB_DSN:
        raise ValueError("Missing DB_DSN. Check enviroment variables.")
    if not config.DB_USER:
        raise ValueError("Missing DB_USER. Check environment variables.")
    if not config.DB_PASSWORD:
        raise ValueError("Missing DB_PASSWORD. Check environment variables.")

    try:
        # Build pool kwargs - only include params that are explicitly set
        pool_kwargs = {**DB_CONFIG}

        if config.DB_POOL_INITIAL_CON is not None:
            pool_kwargs["initialconnections"] = int(config.DB_POOL_INITIAL_CON)
        if config.DB_POOL_MAX_UNUSED is not None:
            pool_kwargs["maxunused"] = int(config.DB_POOL_MAX_UNUSED)
        if config.DB_POOL_MAX_CON is not None:
            pool_kwargs["maxconnections"] = int(config.DB_POOL_MAX_CON)
        if config.DB_POOL_BLOCK is not None:
            pool_kwargs["block"] = config.DB_POOL_BLOCK.lower() in {"1", "true", "yes"}
        if config.DB_POOL_DEEP_HEALTH_CHECK is not None:
            pool_kwargs["deep_health_check"] = (
                config.DB_POOL_DEEP_HEALTH_CHECK.lower() in {"1", "true", "yes"}
            )

        logger.info("Creating database connection pool...")
        pool = MimerPool(**pool_kwargs)

        # Test a connection from the pool
        with pool.get_connection() as con:
            cursor = con.cursor()
            cursor.execute("VALUES (CURRENT_USER);")
            user = cursor.fetchone()
            cursor.close()
            logger.debug(f"Connected to Mimer SQL as user: {user[0]}")
        return pool

    except MimerPoolError as e:
        logger.error(f"Failed to create database connection pool: {e}")
        raise


def get_connection():
    """Get a pooled MimerPy connection.

    Returns:
        A PooledConnection that can be used as a standard MimerPy connection.

    Raises:
        RuntimeError: if called before init_db_pool
    """

    if pool is None:
        raise RuntimeError(
            "Database connection pool is not initialized. Call init_db_pool() at startup."
        )
    return pool.get_connection()


def close_db_pool():
    """Close all connections in the pool.

    This is called during application shutdown to clean up all database connections.

    """
    global pool
    if pool is not None:
        try:
            pool.close()
            logger.debug("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database connection pool: {e}")
        finally:
            pool = None
