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

# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS uv

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*


# Install the project into `/app`
WORKDIR /app


# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# setuptools-scm needs an explicit version when the git metadata is unavailable in the build context
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_MIMER_MCP_SERVER=0.0.0

# Install the project's dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Add source code and install the project itself
ADD . /app
RUN if [ -d .git ]; then cp -r .git /app/.git; fi

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim-bookworm

WORKDIR /app

# update and install necessary utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget git procps file sudo libdw1 && \
    rm -rf /var/lib/apt/lists/*

# fetch the package and install it
RUN case "$(uname -m)" in \
        aarch64) export MIMER_DEB="linux_arm_64/mimersqlsrv1109_11.0.9E-49534_arm64-openssl3.deb" ;; \
        x86_64)  export MIMER_DEB="linux_x86_64/mimersqlsrv1109_11.0.9E-49534_amd64-openssl3.deb" ;; \
    esac; \
    wget -nv -O mimersql.deb https://download.mimer.com/pub/dist/${MIMER_DEB} && \
    dpkg -i mimersql.deb && \
    rm mimersql.deb

COPY --from=uv /root/.local /root/.local
COPY --from=uv /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Copy and use the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run the MCP server
ENTRYPOINT ["/entrypoint.sh", "mimer_mcp_server"]