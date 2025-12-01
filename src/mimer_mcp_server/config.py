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

import os
from dotenv import load_dotenv

# first check DOTENV_PATH env var to load .env from explicit path
dotenv_path = os.getenv("DOTENV_PATH")
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()

DB_DSN = os.getenv("DB_DSN")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Optional pool configuration
DB_POOL_INITIAL_CON = os.getenv("DB_POOL_INITIAL_CON")
DB_POOL_MAX_UNUSED = os.getenv("DB_POOL_MAX_UNUSED")
DB_POOL_MAX_CON = os.getenv("DB_POOL_MAX_CON")
DB_POOL_BLOCK = os.getenv("DB_POOL_BLOCK")
DB_POOL_DEEP_HEALTH_CHECK = os.getenv("DB_POOL_DEEP_HEALTH_CHECK")

# Logging configuration
LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO") or "INFO"
