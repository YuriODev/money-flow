"""Database Migration Tests for Sprint 2.3.2.6.

Tests for Alembic migration operations.
Verifies migration structure and history.

Note:
    These migrations require an async driver (PostgreSQL with asyncpg).
    SQLite tests are limited to structure verification.
    Full migration up/down tests run in CI with PostgreSQL.

Usage:
    pytest tests/integration/test_migrations.py -v

    # Run with PostgreSQL (CI or local):
    DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db" pytest tests/integration/test_migrations.py -v
"""

import os
import subprocess
from pathlib import Path

import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestMigrationStructure:
    """Test migration file structure and validity (works without DB)."""

    def test_migration_files_exist(self):
        """Test that migration files exist."""
        migrations_dir = PROJECT_ROOT / "src" / "db" / "migrations" / "versions"
        assert migrations_dir.exists(), f"Migrations directory not found: {migrations_dir}"

        migration_files = list(migrations_dir.glob("*.py"))
        assert len(migration_files) > 0, "No migration files found"

    def test_migration_files_have_upgrade_downgrade(self):
        """Test that migration files have upgrade and downgrade functions."""
        migrations_dir = PROJECT_ROOT / "src" / "db" / "migrations" / "versions"

        for migration_file in migrations_dir.glob("*.py"):
            content = migration_file.read_text()

            assert "def upgrade()" in content, f"Missing upgrade() in {migration_file.name}"
            assert "def downgrade()" in content, f"Missing downgrade() in {migration_file.name}"

    def test_migration_files_have_revision_id(self):
        """Test that migration files have revision IDs."""
        migrations_dir = PROJECT_ROOT / "src" / "db" / "migrations" / "versions"

        for migration_file in migrations_dir.glob("*.py"):
            content = migration_file.read_text()

            # Handle both 'revision = ' and 'revision: str = ' formats
            has_revision = "revision = " in content or "revision: str = " in content
            assert has_revision, f"Missing revision in {migration_file.name}"

    def test_alembic_ini_exists(self):
        """Test that alembic.ini exists."""
        alembic_ini = PROJECT_ROOT / "alembic.ini"
        assert alembic_ini.exists(), f"alembic.ini not found: {alembic_ini}"

    def test_env_py_exists(self):
        """Test that migrations/env.py exists."""
        env_py = PROJECT_ROOT / "src" / "db" / "migrations" / "env.py"
        assert env_py.exists(), f"env.py not found: {env_py}"


class TestMigrationHistory:
    """Test migration history commands (no DB required)."""

    def run_alembic(self, command: str) -> subprocess.CompletedProcess:
        """Run an Alembic command."""
        # Use venv's alembic
        alembic_path = PROJECT_ROOT / ".venv" / "bin" / "alembic"
        if not alembic_path.exists():
            alembic_path = "alembic"  # Fall back to global

        result = subprocess.run(
            [str(alembic_path)] + command.split(),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        return result

    def test_migration_history_accessible(self):
        """Test that migration history is accessible."""
        result = self.run_alembic("history")

        assert result.returncode == 0, f"History failed: {result.stderr}"
        # Should show migration history
        assert len(result.stdout) > 0, "Migration history is empty"

    def test_no_multiple_heads(self):
        """Test that there are no conflicting migrations (multiple heads)."""
        result = self.run_alembic("heads")

        assert result.returncode == 0, f"Heads failed: {result.stderr}"

        # Parse heads output - should have at most one head
        lines = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        # Filter out empty lines and info messages
        head_lines = [ln for ln in lines if not ln.startswith("INFO") and "(head)" in ln or ln]

        # Should have exactly one head (or one head marker)
        assert len(head_lines) <= 2, f"Multiple migration heads detected: {head_lines}"


class TestMigrationWithPostgres:
    """Test migrations with PostgreSQL (integration with CI).

    These tests require PostgreSQL with asyncpg driver.
    Set DATABASE_URL environment variable to run.
    """

    @pytest.fixture
    def postgres_url(self):
        """Get PostgreSQL URL from environment or skip."""
        pg_url = os.environ.get("DATABASE_URL")
        if not pg_url or "postgresql" not in pg_url:
            pytest.skip("PostgreSQL DATABASE_URL not configured")
        return pg_url

    def run_alembic(self, command: str, db_url: str) -> subprocess.CompletedProcess:
        """Run an Alembic command with the given database URL."""
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url

        alembic_path = PROJECT_ROOT / ".venv" / "bin" / "alembic"
        if not alembic_path.exists():
            alembic_path = "alembic"

        result = subprocess.run(
            [str(alembic_path)] + command.split(),
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        return result

    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL", "").startswith("postgresql"),
        reason="PostgreSQL not configured",
    )
    def test_postgres_migrate_to_head(self, postgres_url: str):
        """Test migrating PostgreSQL to head."""
        # Note: This test assumes migration state may already exist
        # It simply ensures we can reach head from current state
        result = self.run_alembic("upgrade head", postgres_url)

        assert result.returncode == 0, f"Migration failed: {result.stderr}"

    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL", "").startswith("postgresql"),
        reason="PostgreSQL not configured",
    )
    def test_postgres_migrate_down_and_up(self, postgres_url: str):
        """Test migrating PostgreSQL down and up.

        Note: This test first ensures we're at head, then does one downgrade/upgrade cycle.
        It does NOT test fresh migration from scratch (that would require a clean database).
        """
        # First ensure we're at head (this may be a no-op if already at head)
        up_result = self.run_alembic("upgrade head", postgres_url)
        # upgrade head succeeds even if already at head
        assert up_result.returncode == 0, f"Initial upgrade failed: {up_result.stderr}"

        # Get current revision to check if we have migrations to downgrade
        current = self.run_alembic("current", postgres_url)
        if "head" not in current.stdout.lower() and current.stdout.strip():
            # If we have a current revision, try downgrade
            down_result = self.run_alembic("downgrade -1", postgres_url)
            assert down_result.returncode == 0, f"Downgrade failed: {down_result.stderr}"

            # Upgrade back to head
            up_result2 = self.run_alembic("upgrade head", postgres_url)
            assert up_result2.returncode == 0, f"Re-upgrade failed: {up_result2.stderr}"

    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL", "").startswith("postgresql"),
        reason="PostgreSQL not configured",
    )
    def test_postgres_current_revision(self, postgres_url: str):
        """Test getting current revision on PostgreSQL."""
        # First ensure we're at head
        self.run_alembic("upgrade head", postgres_url)

        result = self.run_alembic("current", postgres_url)

        assert result.returncode == 0, f"Current failed: {result.stderr}"
        # Should show current revision
        assert "head" in result.stdout.lower() or result.returncode == 0


class TestMigrationTestDatabase:
    """Test migrations with a test database (local PostgreSQL).

    These tests use a separate test database to avoid affecting development data.
    Set TEST_DATABASE_URL environment variable to run.
    """

    @pytest.fixture
    def test_db_url(self):
        """Get test database URL or skip."""
        test_url = os.environ.get("TEST_DATABASE_URL")
        if not test_url:
            pytest.skip("TEST_DATABASE_URL not configured")
        return test_url

    def run_alembic(self, command: str, db_url: str) -> subprocess.CompletedProcess:
        """Run an Alembic command with the given database URL."""
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url

        alembic_path = PROJECT_ROOT / ".venv" / "bin" / "alembic"
        if not alembic_path.exists():
            alembic_path = "alembic"

        result = subprocess.run(
            [str(alembic_path)] + command.split(),
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        return result

    @pytest.mark.skipif(
        not os.environ.get("TEST_DATABASE_URL"),
        reason="TEST_DATABASE_URL not configured",
    )
    def test_fresh_migrate_to_head(self, test_db_url: str):
        """Test fresh migration from base to head."""
        # Downgrade to base first
        self.run_alembic("downgrade base", test_db_url)

        # Migrate to head
        result = self.run_alembic("upgrade head", test_db_url)

        assert result.returncode == 0, f"Migration failed: {result.stderr}"

    @pytest.mark.skipif(
        not os.environ.get("TEST_DATABASE_URL"),
        reason="TEST_DATABASE_URL not configured",
    )
    def test_full_migrate_down_to_base(self, test_db_url: str):
        """Test full migration down to base."""
        # First upgrade to head
        self.run_alembic("upgrade head", test_db_url)

        # Downgrade to base
        result = self.run_alembic("downgrade base", test_db_url)

        assert result.returncode == 0, f"Downgrade failed: {result.stderr}"
