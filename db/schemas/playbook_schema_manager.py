"""
SurrealDB Playbook Schema Manager

This module provides comprehensive schema management for the playbook system
in SurrealDB, including schema creation, validation, migration, and maintenance.

Features:
- Schema creation and initialization
- Migration management and versioning
- Data validation and integrity checks
- Performance optimization and indexing
- Cleanup and maintenance operations
- Agent capability registration
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

try:
    import logfire
except ImportError:
    class MockLogfire:
        @staticmethod
        def span(name, **kwargs):
            class MockSpan:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return MockSpan()
        @staticmethod
        def info(*args, **kwargs): pass
        @staticmethod
        def error(*args, **kwargs): pass
    logfire = MockLogfire()

from ..surrealdb_client import SurrealDBClient, SurrealDBConfig

logger = logging.getLogger(__name__)


@dataclass
class SchemaVersion:
    """Schema version information."""
    version: str
    description: str
    applied_at: Optional[datetime] = None
    migration_script: Optional[str] = None


@dataclass
class AgentCapability:
    """Agent capability definition for pool discovery."""
    agent_id: str
    agent_type: str
    available_tools: List[str]
    supported_workflows: List[str]
    max_concurrent: int = 1
    specializations: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)


class PlaybookSchemaManager:
    """Manages SurrealDB schema for the playbook system."""

    def __init__(self, client: SurrealDBClient):
        """Initialize schema manager with SurrealDB client."""
        self.client = client
        self.schema_path = Path(__file__).parent / "playbook_schema.surql"
        self.current_version = "1.0.0"
        self.logger = logger

    async def initialize_schema(self, force: bool = False) -> bool:
        """
        Initialize the complete playbook schema.

        Args:
            force: If True, drop existing schema before creating

        Returns:
            bool: Success status
        """
        with logfire.span("Initialize playbook schema", force=force):
            try:
                if force:
                    await self._drop_schema()

                # Check if schema already exists
                if not force and await self._schema_exists():
                    self.logger.info("Playbook schema already exists")
                    return True

                # Read and execute schema file
                schema_content = await self._read_schema_file()
                await self._execute_schema(schema_content)

                # Register schema version
                await self._register_schema_version()

                # Initialize with default agent capabilities
                await self._initialize_agent_capabilities()

                logfire.info("Playbook schema initialized successfully")
                return True

            except Exception as e:
                logfire.error("Failed to initialize schema", error=str(e))
                self.logger.error(f"Schema initialization failed: {e}")
                return False

    async def validate_schema(self) -> Dict[str, Any]:
        """
        Validate the current schema structure and integrity.

        Returns:
            Dict containing validation results
        """
        with logfire.span("Validate playbook schema"):
            results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "table_counts": {},
                "index_status": {},
                "functions_status": {}
            }

            try:
                # Check table existence
                tables = await self._get_table_list()
                expected_tables = [
                    "playbooks", "playbook_steps", "playbook_variables",
                    "playbook_executions", "step_executions", "playbook_aars",
                    "playbook_templates", "agent_capabilities"
                ]

                for table in expected_tables:
                    if table not in tables:
                        results["errors"].append(f"Missing table: {table}")
                        results["valid"] = False
                    else:
                        count = await self._get_table_count(table)
                        results["table_counts"][table] = count

                # Check indexes
                for table in expected_tables:
                    if table in tables:
                        indexes = await self._get_table_indexes(table)
                        results["index_status"][table] = len(indexes)

                # Check functions
                functions = await self._get_functions()
                expected_functions = [
                    "fn::playbook_success_rate",
                    "fn::step_success_rate",
                    "fn::execution_duration",
                    "fn::cleanup_old_executions",
                    "fn::update_agent_heartbeat",
                    "fn::update_performance_metrics"
                ]

                for func in expected_functions:
                    if func not in functions:
                        results["warnings"].append(f"Missing function: {func}")
                    else:
                        results["functions_status"][func] = "exists"

                logfire.info("Schema validation completed",
                           valid=results["valid"],
                           errors_count=len(results["errors"]))

            except Exception as e:
                results["valid"] = False
                results["errors"].append(f"Validation error: {str(e)}")
                logfire.error("Schema validation failed", error=str(e))

            return results

    async def register_agent_capability(self, capability: AgentCapability) -> bool:
        """
        Register or update an agent's capabilities in the pool.

        Args:
            capability: Agent capability definition

        Returns:
            bool: Success status
        """
        with logfire.span("Register agent capability", agent_id=capability.agent_id):
            try:
                query = """
                    UPSERT agent_capabilities SET
                        agent_id = $agent_id,
                        agent_type = $agent_type,
                        available_tools = $available_tools,
                        supported_workflows = $supported_workflows,
                        max_concurrent = $max_concurrent,
                        specializations = $specializations,
                        resource_limits = $resource_limits,
                        health_status = "healthy",
                        last_heartbeat = time::now(),
                        updated_at = time::now()
                    WHERE agent_id = $agent_id
                """

                params = {
                    "agent_id": capability.agent_id,
                    "agent_type": capability.agent_type,
                    "available_tools": capability.available_tools,
                    "supported_workflows": capability.supported_workflows,
                    "max_concurrent": capability.max_concurrent,
                    "specializations": capability.specializations,
                    "resource_limits": capability.resource_limits
                }

                await self.client.query(query, params)

                logfire.info("Agent capability registered",
                           agent_id=capability.agent_id,
                           agent_type=capability.agent_type)
                return True

            except Exception as e:
                logfire.error("Failed to register agent capability",
                            agent_id=capability.agent_id,
                            error=str(e))
                return False

    async def get_agent_pool(self, filter_healthy: bool = True) -> List[Dict[str, Any]]:
        """
        Get current agent pool with capabilities.

        Args:
            filter_healthy: Only return healthy agents

        Returns:
            List of agent capability dictionaries
        """
        with logfire.span("Get agent pool", filter_healthy=filter_healthy):
            try:
                base_query = "SELECT * FROM agent_capabilities"

                if filter_healthy:
                    query = f"{base_query} WHERE health_status = 'healthy'"
                    # Also filter agents with recent heartbeat (within last 5 minutes)
                    query += " AND last_heartbeat > time::now() - 5m"
                else:
                    query = base_query

                query += " ORDER BY agent_type, agent_id"

                result = await self.client.query(query)
                agents = result[0] if result else []

                logfire.info("Retrieved agent pool",
                           total_agents=len(agents),
                           filter_healthy=filter_healthy)

                return agents

            except Exception as e:
                logfire.error("Failed to get agent pool", error=str(e))
                return []

    async def update_agent_heartbeat(self, agent_id: str) -> bool:
        """
        Update agent heartbeat timestamp.

        Args:
            agent_id: Agent identifier

        Returns:
            bool: Success status
        """
        try:
            query = "SELECT fn::update_agent_heartbeat($agent_id)"
            await self.client.query(query, {"agent_id": agent_id})
            return True
        except Exception as e:
            self.logger.error(f"Failed to update heartbeat for {agent_id}: {e}")
            return False

    async def cleanup_old_data(self, days_old: int = 90) -> Dict[str, int]:
        """
        Clean up old execution data.

        Args:
            days_old: Number of days to keep

        Returns:
            Dict with cleanup counts
        """
        with logfire.span("Cleanup old data", days_old=days_old):
            results = {"executions_deleted": 0, "step_executions_deleted": 0}

            try:
                cutoff_date = datetime.now() - timedelta(days=days_old)

                # Delete old playbook executions
                query = """
                    LET $deleted = DELETE playbook_executions
                    WHERE created_at < $cutoff
                    RETURN count();
                """
                result = await self.client.query(query, {"cutoff": cutoff_date})
                results["executions_deleted"] = result[0] if result else 0

                # Delete old step executions
                query = """
                    LET $deleted = DELETE step_executions
                    WHERE created_at < $cutoff
                    RETURN count();
                """
                result = await self.client.query(query, {"cutoff": cutoff_date})
                results["step_executions_deleted"] = result[0] if result else 0

                logfire.info("Data cleanup completed", **results)

            except Exception as e:
                logfire.error("Data cleanup failed", error=str(e))

            return results

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for the playbook system.

        Returns:
            Dict containing various performance metrics
        """
        with logfire.span("Get performance metrics"):
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "playbooks": {},
                "executions": {},
                "agents": {},
                "system": {}
            }

            try:
                # Playbook metrics
                playbook_query = """
                    SELECT
                        count() as total_playbooks,
                        count(status = 'active') as active_playbooks,
                        count(is_template = true) as templates,
                        math::mean(total_executions) as avg_executions,
                        math::mean(average_execution_time) as avg_execution_time
                    FROM playbooks
                """
                result = await self.client.query(playbook_query)
                if result:
                    metrics["playbooks"] = result[0]

                # Execution metrics (last 30 days)
                execution_query = """
                    SELECT
                        count() as total_executions,
                        count(overall_success = true) as successful_executions,
                        count(overall_success = false) as failed_executions,
                        math::mean(execution_time_seconds) as avg_execution_time,
                        math::max(execution_time_seconds) as max_execution_time
                    FROM playbook_executions
                    WHERE created_at > time::now() - 30d
                """
                result = await self.client.query(execution_query)
                if result:
                    metrics["executions"] = result[0]

                # Agent metrics
                agent_query = """
                    SELECT
                        count() as total_agents,
                        count(health_status = 'healthy') as healthy_agents,
                        math::sum(max_concurrent) as total_capacity,
                        math::sum(current_load) as current_load
                    FROM agent_capabilities
                """
                result = await self.client.query(agent_query)
                if result:
                    metrics["agents"] = result[0]

                # System metrics
                table_counts = {}
                for table in ["playbooks", "playbook_executions", "step_executions", "playbook_aars"]:
                    count = await self._get_table_count(table)
                    table_counts[table] = count

                metrics["system"] = {
                    "table_counts": table_counts,
                    "schema_version": self.current_version
                }

                logfire.info("Performance metrics collected")

            except Exception as e:
                logfire.error("Failed to collect performance metrics", error=str(e))

            return metrics

    # Private helper methods

    async def _read_schema_file(self) -> str:
        """Read the schema file content."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        return self.schema_path.read_text(encoding='utf-8')

    async def _execute_schema(self, schema_content: str) -> None:
        """Execute schema statements."""
        # Split schema into individual statements
        statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]

        for statement in statements:
            if statement and not statement.startswith('--'):
                try:
                    await self.client.query(statement)
                except Exception as e:
                    self.logger.warning(f"Schema statement failed: {statement[:100]}... Error: {e}")

    async def _schema_exists(self) -> bool:
        """Check if playbook schema already exists."""
        try:
            result = await self.client.query("SELECT * FROM playbooks LIMIT 1")
            return True
        except:
            return False

    async def _drop_schema(self) -> None:
        """Drop existing schema (use with caution)."""
        tables = [
            "playbook_aars", "step_executions", "playbook_executions",
            "playbook_variables", "playbook_steps", "playbooks",
            "playbook_templates", "agent_capabilities"
        ]

        for table in tables:
            try:
                await self.client.query(f"REMOVE TABLE {table}")
            except:
                pass  # Table might not exist

    async def _register_schema_version(self) -> None:
        """Register the current schema version."""
        try:
            # Create schema_versions table if it doesn't exist
            await self.client.query("""
                DEFINE TABLE schema_versions SCHEMAFULL;
                DEFINE FIELD version ON TABLE schema_versions TYPE string;
                DEFINE FIELD description ON TABLE schema_versions TYPE string;
                DEFINE FIELD applied_at ON TABLE schema_versions TYPE datetime DEFAULT time::now();
            """)

            # Insert current version
            await self.client.query("""
                INSERT INTO schema_versions {
                    version: $version,
                    description: "Initial playbook system schema",
                    applied_at: time::now()
                }
            """, {"version": self.current_version})

        except Exception as e:
            self.logger.warning(f"Failed to register schema version: {e}")

    async def _initialize_agent_capabilities(self) -> None:
        """Initialize default agent capabilities."""
        default_agents = [
            AgentCapability(
                agent_id="super_agent",
                agent_type="super",
                available_tools=["all_mcp_servers", "ptolemies-mcp", "taskmaster-ai"],
                supported_workflows=["all_types"],
                max_concurrent=10,
                specializations=["meta_coordination", "user_communication", "supervision"]
            ),
            AgentCapability(
                agent_id="codifier_agent",
                agent_type="codifier",
                available_tools=["filesystem", "git", "ptolemies-mcp", "magic-mcp"],
                supported_workflows=["sequential", "pipeline", "self_feedback"],
                max_concurrent=5,
                specializations=["documentation", "knowledge_codification", "aar_generation"]
            ),
            AgentCapability(
                agent_id="io_agent",
                agent_type="io",
                available_tools=["logfire-mcp", "memory", "fetch", "surrealdb-mcp"],
                supported_workflows=["loop", "conditional", "parallel"],
                max_concurrent=8,
                specializations=["monitoring", "observation", "validation", "progress_tracking"]
            ),
            AgentCapability(
                agent_id="playbook_agent",
                agent_type="playbook",
                available_tools=["taskmaster-ai", "context7-mcp", "sequentialthinking"],
                supported_workflows=["all_types"],
                max_concurrent=6,
                specializations=["strategic_execution", "playbook_management", "orchestration"]
            )
        ]

        for agent in default_agents:
            await self.register_agent_capability(agent)

    async def _get_table_list(self) -> List[str]:
        """Get list of existing tables."""
        try:
            result = await self.client.query("INFO FOR DB")
            if result and isinstance(result[0], dict):
                tables = result[0].get('tb', {})
                return list(tables.keys())
            return []
        except:
            return []

    async def _get_table_count(self, table: str) -> int:
        """Get record count for a table."""
        try:
            result = await self.client.query(f"SELECT count() FROM {table} GROUP ALL")
            return result[0].get('count', 0) if result else 0
        except:
            return 0

    async def _get_table_indexes(self, table: str) -> List[str]:
        """Get indexes for a table."""
        try:
            result = await self.client.query(f"INFO FOR TABLE {table}")
            if result and isinstance(result[0], dict):
                indexes = result[0].get('ix', {})
                return list(indexes.keys())
            return []
        except:
            return []

    async def _get_functions(self) -> List[str]:
        """Get list of defined functions."""
        try:
            result = await self.client.query("INFO FOR DB")
            if result and isinstance(result[0], dict):
                functions = result[0].get('fc', {})
                return list(functions.keys())
            return []
        except:
            return []


class PlaybookSchemaFactory:
    """Factory for creating and managing playbook schema instances."""

    _instance = None
    _managers = {}

    @classmethod
    async def get_manager(cls, config: Optional[SurrealDBConfig] = None) -> PlaybookSchemaManager:
        """
        Get or create a schema manager instance.

        Args:
            config: SurrealDB configuration

        Returns:
            PlaybookSchemaManager instance
        """
        if config is None:
            config = SurrealDBConfig()

        config_key = f"{config.url}:{config.namespace}:{config.database}"

        if config_key not in cls._managers:
            client = SurrealDBClient(config)
            await client.connect()
            cls._managers[config_key] = PlaybookSchemaManager(client)

        return cls._managers[config_key]

    @classmethod
    async def cleanup_all(cls):
        """Clean up all manager instances."""
        for manager in cls._managers.values():
            try:
                await manager.client.close()
            except:
                pass
        cls._managers.clear()


# Convenience functions

async def initialize_playbook_schema(config: Optional[SurrealDBConfig] = None, force: bool = False) -> bool:
    """
    Initialize playbook schema with default configuration.

    Args:
        config: SurrealDB configuration
        force: Force schema recreation

    Returns:
        bool: Success status
    """
    manager = await PlaybookSchemaFactory.get_manager(config)
    return await manager.initialize_schema(force=force)


async def validate_playbook_schema(config: Optional[SurrealDBConfig] = None) -> Dict[str, Any]:
    """
    Validate playbook schema.

    Args:
        config: SurrealDB configuration

    Returns:
        Dict containing validation results
    """
    manager = await PlaybookSchemaFactory.get_manager(config)
    return await manager.validate_schema()


async def register_default_agents(config: Optional[SurrealDBConfig] = None) -> bool:
    """
    Register default agent capabilities.

    Args:
        config: SurrealDB configuration

    Returns:
        bool: Success status
    """
    manager = await PlaybookSchemaFactory.get_manager(config)
    await manager._initialize_agent_capabilities()
    return True
