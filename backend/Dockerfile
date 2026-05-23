FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy app code
COPY . .

# Run
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT