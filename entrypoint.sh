#!/bin/sh
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

set -e

echo "Checking required environment variables..."

# Check each required variable
for var in DB_DSN DB_USER DB_PASSWORD DB_HOST; do
    eval value=\$$var
    if [ -z "$value" ]; then
        echo "ERROR: $var is not set"
        echo ""
        echo "Required variables: DB_DSN, DB_USER, DB_PASSWORD, DB_HOST"
        echo "Optional variables: DB_PORT (default: 1360), DB_PROTOCOL (default: tcp)"
        exit 1
    fi
done

echo "All required variables are set"

# Set defaults for optional variables
DB_PORT="${DB_PORT:-1360}"
DB_PROTOCOL="${DB_PROTOCOL:-tcp}"

# Register the remote database
echo "Registering Mimer SQL database: ${DB_DSN} at ${DB_HOST}:${DB_PORT} (protocol: ${DB_PROTOCOL})"
mimsqlhosts -a -t remote "${DB_DSN}" "${DB_HOST}" "${DB_PORT}" "${DB_PROTOCOL}" || {
    echo "WARNING: Database registration failed, but continuing..."
}

echo "Registration complete"
mimsqlhosts -l || true

echo "Checking Mimer SQL connection..."

while ! bsql -u${DB_USER} -p${DB_PASSWORD} --query="select count(*) from system.onerow" ${DB_DSN} >/dev/null 2>&1
do
  echo "Mimer SQL database ${DB_DSN} is not ready yet - waiting 5 seconds"
  sleep 3
done

echo "Mimer SQL example database is ready"
# Execute the main command
exec "$@"
