#!/usr/bin/env bash
# Apply all pending migrations to the running PostgreSQL container.
#
# Usage:  bash scripts/migrate.sh
#
# Migrations are applied in numeric order (001..NNN). Each file is idempotent:
# use IF NOT EXISTS / ON CONFLICT DO NOTHING in migration SQL.
set -euo pipefail

MIGRATIONS_DIR="$(cd "$(dirname "$0")/../db/migrations" && pwd)"

# ---------------------------------------------------------------------------
# Resolve connection — prefer PGHOST from .env, fall back to docker exec.
# ---------------------------------------------------------------------------
if [ -f "$(dirname "$0")/../.env" ]; then
  # shellcheck disable=SC1090
  source "$(dirname "$0")/../.env" 2>/dev/null || true
fi

PGHOST="${PGHOST:-}"
PGPORT="${PGPORT:-5432}"
PGUSER="${POSTGRES_USER:-moufida}"
PGPASSWORD="${POSTGRES_PASSWORD:-moufida}"
PGDATABASE="${POSTGRES_DB:-moufida}"

green()  { printf '\033[32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[33m%s\033[0m\n' "$1"; }
red()    { printf '\033[31m%s\033[0m\n' "$1"; }

run_sql() {
  local file="$1"
  if [ -n "$PGHOST" ]; then
    PGPASSWORD="$PGPASSWORD" psql \
      -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
      -f "$file" -q
  else
    # Fall back to docker exec (works when the DB is a container named 'postgres')
    local container
    container=$(docker compose ps -q postgres 2>/dev/null || docker ps -qf name=postgres | head -1)
    if [ -z "$container" ]; then
      red "Cannot reach PostgreSQL: PGHOST not set and no postgres container found."
      exit 1
    fi
    docker exec -i "$container" \
      env PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" \
      < "$file"
  fi
}

# ---------------------------------------------------------------------------
# Ensure the migration tracker table exists.
# ---------------------------------------------------------------------------
TRACKER_SQL="
CREATE TABLE IF NOT EXISTS _schema_migrations (
  filename   TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ DEFAULT now()
);
"

if [ -n "$PGHOST" ]; then
  PGPASSWORD="$PGPASSWORD" psql \
    -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
    -c "$TRACKER_SQL" -q
else
  container=$(docker compose ps -q postgres 2>/dev/null || docker ps -qf name=postgres | head -1)
  docker exec -i "$container" \
    env PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" \
    -c "$TRACKER_SQL"
fi

# ---------------------------------------------------------------------------
# Apply migrations in order, skipping already-applied ones.
# ---------------------------------------------------------------------------
echo ">> Applying migrations from $MIGRATIONS_DIR"

for f in "$MIGRATIONS_DIR"/[0-9][0-9][0-9]_*.sql; do
  fname="$(basename "$f")"

  # Check if already applied
  if [ -n "$PGHOST" ]; then
    already=$(PGPASSWORD="$PGPASSWORD" psql \
      -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
      -tAc "SELECT COUNT(1) FROM _schema_migrations WHERE filename = '$fname';" 2>/dev/null || echo "0")
  else
    container=$(docker compose ps -q postgres 2>/dev/null || docker ps -qf name=postgres | head -1)
    already=$(docker exec -i "$container" \
      env PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" \
      -tAc "SELECT COUNT(1) FROM _schema_migrations WHERE filename = '$fname';" 2>/dev/null || echo "0")
  fi

  already="${already//[[:space:]]/}"
  if [ "$already" = "1" ]; then
    yellow "   skip   $fname (already applied)"
    continue
  fi

  echo "   apply  $fname"
  if run_sql "$f"; then
    # Record as applied
    MARK_SQL="INSERT INTO _schema_migrations (filename) VALUES ('$fname') ON CONFLICT DO NOTHING;"
    if [ -n "$PGHOST" ]; then
      PGPASSWORD="$PGPASSWORD" psql \
        -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        -c "$MARK_SQL" -q
    else
      container=$(docker compose ps -q postgres 2>/dev/null || docker ps -qf name=postgres | head -1)
      docker exec -i "$container" \
        env PGPASSWORD="$PGPASSWORD" psql -U "$PGUSER" -d "$PGDATABASE" \
        -c "$MARK_SQL"
    fi
    green "   done   $fname"
  else
    red "   FAILED $fname — aborting"
    exit 1
  fi
done

green ">> All migrations applied."
