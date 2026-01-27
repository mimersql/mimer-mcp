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

import logging
from mimer_mcp_server import config
import subprocess

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dsn": config.DB_DSN,
    "user": config.DB_USER,
    "password": config.DB_PASSWORD,
}

# MIMINFO (Mimer SQL runtime statistics)
def get_miminfo_stats() -> str:
    """Retrieve Mimer SQL runtime statistics using the miminfo CLI tool

    Returns:
        str: The output of the miminfo command containing runtime statistics.

    Raises:
        RuntimeError: If the miminfo command fails.
    """
    try:
        result = subprocess.run(
            ['miminfo', 
             '-p',
             DB_CONFIG["dsn"],
             ],
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to retrieve Mimer SQL stats: {e.stderr}")
        raise RuntimeError("Failed to retrieve Mimer SQL stats") from e

# SQLMONITOR
def get_sqlmonitor_stats() -> str:
    """Retrieve SQL monitoring statistics using the sqlmonitor CLI tool.

    Returns:
        str: The output of the sqlmonitor command.

    Raises:
        RuntimeError: If the SQL monitoring command fails.
    """
    try:
        result = subprocess.run(
            ['sqlmonitor', 
             DB_CONFIG["dsn"],
             '-u',
             DB_CONFIG["user"],
             '-p',
             DB_CONFIG["password"],
             ],
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to retrieve sqlmonitor stats: {e.stderr}")
        raise RuntimeError("Failed to retrieve sqlmonitor stats") from e
    
    
