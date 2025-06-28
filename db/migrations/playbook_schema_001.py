"""
Playbook Schema Migration Script
Migration 001: Initial Playbook System Schema

This migration creates the complete SurrealDB schema for the Agentical playbook system,
including all tables, indexes, relationships, and sample data.

Created: 2025-06-28
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

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
from ..schemas.playbook_schema_manager import PlaybookSchemaManager, AgentCapability

logger = logging.getLogger(__name__)


class PlaybookSchemaMigration:
    """Migration handler for playbook schema creation."""

    def __init__(self, client: SurrealDBClient):
        self.client = client
        self.migration_id = "001_playbook_schema"
        self.version = "1.0.0"
        self.description = "Initial playbook system schema with tables, indexes, and sample data"

    async def up(self) -> bool:
        """Apply the migration - create playbook schema."""
        with logfire.span("Apply playbook schema migration"):
            try:
                logger.info(f"Starting migration {self.migration_id}")

                # Step 1: Create core tables
                await self._create_core_tables()

                # Step 2: Create relationships and edges
                await self._create_relationships()

                # Step 3: Create functions and procedures
                await self._create_functions()

                # Step 4: Create indexes for performance
                await self._create_indexes()

                # Step 5: Insert sample data
                await self._insert_sample_data()

                # Step 6: Register migration
                await self._register_migration()

                logger.info(f"Migration {self.migration_id} completed successfully")
                logfire.info("Playbook schema migration completed", migration_id=self.migration_id)
                return True

            except Exception as e:
                logger.error(f"Migration {self.migration_id} failed: {e}")
                logfire.error("Migration failed", migration_id=self.migration_id, error=str(e))
                return False

    async def down(self) -> bool:
        """Rollback the migration - remove playbook schema."""
        with logfire.span("Rollback playbook schema migration"):
            try:
                logger.info(f"Rolling back migration {self.migration_id}")

                # Remove tables in reverse dependency order
                tables_to_remove = [
                    "playbook_aars", "step_executions", "playbook_executions",
                    "playbook_variables", "playbook_steps", "playbooks",
                    "playbook_templates", "agent_capabilities",
                    "playbook_hierarchy", "step_dependencies", "template_usage"
                ]

                for table in tables_to_remove:
                    try:
                        await self.client.query(f"REMOVE TABLE {table}")
                        logger.info(f"Removed table: {table}")
                    except Exception as e:
                        logger.warning(f"Failed to remove table {table}: {e}")

                # Remove functions
                functions_to_remove = [
                    "fn::playbook_success_rate", "fn::step_success_rate",
                    "fn::execution_duration", "fn::cleanup_old_executions",
                    "fn::update_agent_heartbeat", "fn::update_performance_metrics"
                ]

                for func in functions_to_remove:
                    try:
                        await self.client.query(f"REMOVE FUNCTION {func}")
                        logger.info(f"Removed function: {func}")
                    except Exception as e:
                        logger.warning(f"Failed to remove function {func}: {e}")

                # Remove migration record
                await self.client.query(
                    "DELETE migrations WHERE migration_id = $id",
                    {"id": self.migration_id}
                )

                logger.info(f"Migration {self.migration_id} rolled back successfully")
                logfire.info("Migration rollback completed", migration_id=self.migration_id)
                return True

            except Exception as e:
                logger.error(f"Migration rollback {self.migration_id} failed: {e}")
                logfire.error("Migration rollback failed", migration_id=self.migration_id, error=str(e))
                return False

    async def _create_core_tables(self):
        """Create the core playbook tables."""
        logger.info("Creating core tables...")

        # Create playbooks table
        await self.client.query("""
            DEFINE TABLE playbooks SCHEMAFULL;
            DEFINE FIELD id ON TABLE playbooks TYPE record<playbooks>;
            DEFINE FIELD name ON TABLE playbooks TYPE string ASSERT string::len($value) >= 2 AND string::len($value) <= 100;
            DEFINE FIELD display_name ON TABLE playbooks TYPE string;
            DEFINE FIELD description ON TABLE playbooks TYPE string;
            DEFINE FIELD category ON TABLE playbooks TYPE string ASSERT $value IN [
                "incident_response", "troubleshooting", "deployment", "maintenance", "security",
                "code_review", "testing", "release", "onboarding",
                "monitoring", "backup", "disaster_recovery", "capacity_planning",
                "customer_support", "sales", "marketing", "compliance", "custom", "template"
            ];
            DEFINE FIELD tags ON TABLE playbooks TYPE array<string>;
            DEFINE FIELD purpose ON TABLE playbooks TYPE string ASSERT string::len($value) >= 10;
            DEFINE FIELD strategy ON TABLE playbooks TYPE string ASSERT string::len($value) >= 10;
            DEFINE FIELD success_conditions ON TABLE playbooks TYPE array<string>;
            DEFINE FIELD status ON TABLE playbooks TYPE string DEFAULT "draft" ASSERT $value IN ["draft", "active", "inactive", "deprecated", "archived"];
            DEFINE FIELD is_public ON TABLE playbooks TYPE bool DEFAULT false;
            DEFINE FIELD is_template ON TABLE playbooks TYPE bool DEFAULT false;
            DEFINE FIELD configuration ON TABLE playbooks TYPE object;
            DEFINE FIELD input_schema ON TABLE playbooks TYPE object;
            DEFINE FIELD output_schema ON TABLE playbooks TYPE object;
            DEFINE FIELD max_concurrent_executions ON TABLE playbooks TYPE int DEFAULT 1 ASSERT $value >= 1 AND $value <= 100;
            DEFINE FIELD timeout_minutes ON TABLE playbooks TYPE int ASSERT $value > 0;
            DEFINE FIELD retry_attempts ON TABLE playbooks TYPE int DEFAULT 0 ASSERT $value >= 0 AND $value <= 10;
            DEFINE FIELD total_executions ON TABLE playbooks TYPE int DEFAULT 0;
            DEFINE FIELD successful_executions ON TABLE playbooks TYPE int DEFAULT 0;
            DEFINE FIELD failed_executions ON TABLE playbooks TYPE int DEFAULT 0;
            DEFINE FIELD average_execution_time ON TABLE playbooks TYPE float DEFAULT 0.0;
            DEFINE FIELD version ON TABLE playbooks TYPE string DEFAULT "1.0";
            DEFINE FIELD parent_playbook_id ON TABLE playbooks TYPE option<record<playbooks>>;
            DEFINE FIELD last_execution_at ON TABLE playbooks TYPE option<datetime>;
            DEFINE FIELD published_at ON TABLE playbooks TYPE option<datetime>;
            DEFINE FIELD created_by_user_id ON TABLE playbooks TYPE option<record<users>>;
            DEFINE FIELD created_at ON TABLE playbooks TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE playbooks TYPE datetime DEFAULT time::now();
        """)

        # Create playbook_steps table
        await self.client.query("""
            DEFINE TABLE playbook_steps SCHEMAFULL;
            DEFINE FIELD id ON TABLE playbook_steps TYPE record<playbook_steps>;
            DEFINE FIELD playbook_id ON TABLE playbook_steps TYPE record<playbooks>;
            DEFINE FIELD step_name ON TABLE playbook_steps TYPE string ASSERT string::len($value) >= 1 AND string::len($value) <= 100;
            DEFINE FIELD display_name ON TABLE playbook_steps TYPE string;
            DEFINE FIELD description ON TABLE playbook_steps TYPE string;
            DEFINE FIELD step_type ON TABLE playbook_steps TYPE string ASSERT $value IN [
                "action", "decision", "verification", "notification", "wait", "loop",
                "condition", "parallel", "agent_task", "tool_execution", "human_input", "script"
            ];
            DEFINE FIELD step_order ON TABLE playbook_steps TYPE int ASSERT $value >= 1;
            DEFINE FIELD is_optional ON TABLE playbook_steps TYPE bool DEFAULT false;
            DEFINE FIELD is_manual ON TABLE playbook_steps TYPE bool DEFAULT false;
            DEFINE FIELD configuration ON TABLE playbook_steps TYPE object;
            DEFINE FIELD instructions ON TABLE playbook_steps TYPE string;
            DEFINE FIELD automation_script ON TABLE playbook_steps TYPE string;
            DEFINE FIELD conditions ON TABLE playbook_steps TYPE object;
            DEFINE FIELD depends_on_steps ON TABLE playbook_steps TYPE array<string>;
            DEFINE FIELD agent_type ON TABLE playbook_steps TYPE string;
            DEFINE FIELD tool_name ON TABLE playbook_steps TYPE string;
            DEFINE FIELD parameters ON TABLE playbook_steps TYPE object;
            DEFINE FIELD verification_method ON TABLE playbook_steps TYPE string;
            DEFINE FIELD verification_criteria ON TABLE playbook_steps TYPE array<string>;
            DEFINE FIELD success_indicators ON TABLE playbook_steps TYPE array<string>;
            DEFINE FIELD timeout_minutes ON TABLE playbook_steps TYPE int;
            DEFINE FIELD retry_attempts ON TABLE playbook_steps TYPE int DEFAULT 0 ASSERT $value >= 0 AND $value <= 10;
            DEFINE FIELD retry_delay_seconds ON TABLE playbook_steps TYPE int DEFAULT 30;
            DEFINE FIELD total_executions ON TABLE playbook_steps TYPE int DEFAULT 0;
            DEFINE FIELD successful_executions ON TABLE playbook_steps TYPE int DEFAULT 0;
            DEFINE FIELD failed_executions ON TABLE playbook_steps TYPE int DEFAULT 0;
            DEFINE FIELD average_execution_time ON TABLE playbook_steps TYPE float DEFAULT 0.0;
            DEFINE FIELD created_at ON TABLE playbook_steps TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE playbook_steps TYPE datetime DEFAULT time::now();
        """)

        # Create playbook_variables table
        await self.client.query("""
            DEFINE TABLE playbook_variables SCHEMAFULL;
            DEFINE FIELD id ON TABLE playbook_variables TYPE record<playbook_variables>;
            DEFINE FIELD playbook_id ON TABLE playbook_variables TYPE record<playbooks>;
            DEFINE FIELD variable_name ON TABLE playbook_variables TYPE string ASSERT string::len($value) >= 1 AND string::len($value) <= 100;
            DEFINE FIELD display_name ON TABLE playbook_variables TYPE string;
            DEFINE FIELD description ON TABLE playbook_variables TYPE string;
            DEFINE FIELD variable_type ON TABLE playbook_variables TYPE string ASSERT $value IN ["string", "integer", "float", "boolean", "list", "dict", "secret", "reference"];
            DEFINE FIELD is_required ON TABLE playbook_variables TYPE bool DEFAULT false;
            DEFINE FIELD is_sensitive ON TABLE playbook_variables TYPE bool DEFAULT false;
            DEFINE FIELD default_value ON TABLE playbook_variables TYPE option<any>;
            DEFINE FIELD current_value ON TABLE playbook_variables TYPE option<any>;
            DEFINE FIELD min_value ON TABLE playbook_variables TYPE option<float>;
            DEFINE FIELD max_value ON TABLE playbook_variables TYPE option<float>;
            DEFINE FIELD min_length ON TABLE playbook_variables TYPE option<int>;
            DEFINE FIELD max_length ON TABLE playbook_variables TYPE option<int>;
            DEFINE FIELD pattern ON TABLE playbook_variables TYPE option<string>;
            DEFINE FIELD enum_values ON TABLE playbook_variables TYPE option<array>;
            DEFINE FIELD scope ON TABLE playbook_variables TYPE string DEFAULT "playbook";
            DEFINE FIELD is_output ON TABLE playbook_variables TYPE bool DEFAULT false;
            DEFINE FIELD created_at ON TABLE playbook_variables TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE playbook_variables TYPE datetime DEFAULT time::now();
        """)

        # Create execution tracking tables
        await self.client.query("""
            DEFINE TABLE playbook_executions SCHEMAFULL;
            DEFINE FIELD id ON TABLE playbook_executions TYPE record<playbook_executions>;
            DEFINE FIELD playbook_id ON TABLE playbook_executions TYPE record<playbooks>;
            DEFINE FIELD execution_id ON TABLE playbook_executions TYPE string ASSERT string::len($value) >= 8;
            DEFINE FIELD user_id ON TABLE playbook_executions TYPE option<record<users>>;
            DEFINE FIELD triggered_by ON TABLE playbook_executions TYPE string;
            DEFINE FIELD trigger_context ON TABLE playbook_executions TYPE object;
            DEFINE FIELD status ON TABLE playbook_executions TYPE string DEFAULT "pending" ASSERT $value IN ["pending", "running", "completed", "failed", "cancelled", "paused"];
            DEFINE FIELD input_variables ON TABLE playbook_executions TYPE object;
            DEFINE FIELD output_variables ON TABLE playbook_executions TYPE object;
            DEFINE FIELD error_data ON TABLE playbook_executions TYPE object;
            DEFINE FIELD started_at ON TABLE playbook_executions TYPE option<datetime>;
            DEFINE FIELD completed_at ON TABLE playbook_executions TYPE option<datetime>;
            DEFINE FIELD execution_time_seconds ON TABLE playbook_executions TYPE option<float>;
            DEFINE FIELD current_step_order ON TABLE playbook_executions TYPE option<int>;
            DEFINE FIELD completed_steps ON TABLE playbook_executions TYPE int DEFAULT 0;
            DEFINE FIELD failed_steps ON TABLE playbook_executions TYPE int DEFAULT 0;
            DEFINE FIELD skipped_steps ON TABLE playbook_executions TYPE int DEFAULT 0;
            DEFINE FIELD success_criteria_met ON TABLE playbook_executions TYPE object;
            DEFINE FIELD overall_success ON TABLE playbook_executions TYPE option<bool>;
            DEFINE FIELD lessons_learned ON TABLE playbook_executions TYPE string;
            DEFINE FIELD created_at ON TABLE playbook_executions TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE playbook_executions TYPE datetime DEFAULT time::now();
        """)

        await self.client.query("""
            DEFINE TABLE step_executions SCHEMAFULL;
            DEFINE FIELD id ON TABLE step_executions TYPE record<step_executions>;
            DEFINE FIELD execution_id ON TABLE step_executions TYPE record<playbook_executions>;
            DEFINE FIELD step_id ON TABLE step_executions TYPE record<playbook_steps>;
            DEFINE FIELD agent_id ON TABLE step_executions TYPE string;
            DEFINE FIELD status ON TABLE step_executions TYPE string DEFAULT "pending" ASSERT $value IN ["pending", "running", "completed", "failed", "skipped", "cancelled"];
            DEFINE FIELD start_time ON TABLE step_executions TYPE option<datetime>;
            DEFINE FIELD end_time ON TABLE step_executions TYPE option<datetime>;
            DEFINE FIELD completion_percentage ON TABLE step_executions TYPE float DEFAULT 0.0 ASSERT $value >= 0.0 AND $value <= 100.0;
            DEFINE FIELD output_data ON TABLE step_executions TYPE object;
            DEFINE FIELD error_details ON TABLE step_executions TYPE string;
            DEFINE FIELD retry_count ON TABLE step_executions TYPE int DEFAULT 0;
            DEFINE FIELD validation_results ON TABLE step_executions TYPE object;
            DEFINE FIELD performance_metrics ON TABLE step_executions TYPE object;
            DEFINE FIELD created_at ON TABLE step_executions TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE step_executions TYPE datetime DEFAULT time::now();
        """)

        # Create AAR and template tables
        await self.client.query("""
            DEFINE TABLE playbook_aars SCHEMAFULL;
            DEFINE FIELD id ON TABLE playbook_aars TYPE record<playbook_aars>;
            DEFINE FIELD execution_id ON TABLE playbook_aars TYPE record<playbook_executions>;
            DEFINE FIELD success_rating ON TABLE playbook_aars TYPE float ASSERT $value >= 1.0 AND $value <= 10.0;
            DEFINE FIELD lessons_learned ON TABLE playbook_aars TYPE array<string>;
            DEFINE FIELD recommendations ON TABLE playbook_aars TYPE array<string>;
            DEFINE FIELD performance_metrics ON TABLE playbook_aars TYPE object;
            DEFINE FIELD improvement_areas ON TABLE playbook_aars TYPE array<string>;
            DEFINE FIELD what_went_well ON TABLE playbook_aars TYPE array<string>;
            DEFINE FIELD what_went_wrong ON TABLE playbook_aars TYPE array<string>;
            DEFINE FIELD action_items ON TABLE playbook_aars TYPE array<object>;
            DEFINE FIELD documents ON TABLE playbook_aars TYPE array<string>;
            DEFINE FIELD generated_at ON TABLE playbook_aars TYPE datetime DEFAULT time::now();
            DEFINE FIELD reviewed_by ON TABLE playbook_aars TYPE option<record<users>>;
            DEFINE FIELD review_status ON TABLE playbook_aars TYPE string DEFAULT "draft";
            DEFINE FIELD created_at ON TABLE playbook_aars TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE playbook_aars TYPE datetime DEFAULT time::now();
        """)

        await self.client.query("""
            DEFINE TABLE playbook_templates SCHEMAFULL;
            DEFINE FIELD id ON TABLE playbook_templates TYPE record<playbook_templates>;
            DEFINE FIELD name ON TABLE playbook_templates TYPE string ASSERT string::len($value) >= 2;
            DEFINE FIELD description ON TABLE playbook_templates TYPE string;
            DEFINE FIELD category ON TABLE playbook_templates TYPE string;
            DEFINE FIELD template_data ON TABLE playbook_templates TYPE object;
            DEFINE FIELD parameters ON TABLE playbook_templates TYPE array<object>;
            DEFINE FIELD usage_count ON TABLE playbook_templates TYPE int DEFAULT 0;
            DEFINE FIELD success_rate ON TABLE playbook_templates TYPE float DEFAULT 0.0;
            DEFINE FIELD tags ON TABLE playbook_templates TYPE array<string>;
            DEFINE FIELD is_public ON TABLE playbook_templates TYPE bool DEFAULT false;
            DEFINE FIELD created_by_user_id ON TABLE playbook_templates TYPE option<record<users>>;
            DEFINE FIELD created_at ON TABLE playbook_templates TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE playbook_templates TYPE datetime DEFAULT time::now();
        """)

        # Create agent capabilities table
        await self.client.query("""
            DEFINE TABLE agent_capabilities SCHEMAFULL;
            DEFINE FIELD id ON TABLE agent_capabilities TYPE record<agent_capabilities>;
            DEFINE FIELD agent_id ON TABLE agent_capabilities TYPE string;
            DEFINE FIELD agent_type ON TABLE agent_capabilities TYPE string;
            DEFINE FIELD available_tools ON TABLE agent_capabilities TYPE array<string>;
            DEFINE FIELD supported_workflows ON TABLE agent_capabilities TYPE array<string>;
            DEFINE FIELD max_concurrent ON TABLE agent_capabilities TYPE int DEFAULT 1;
            DEFINE FIELD current_load ON TABLE agent_capabilities TYPE int DEFAULT 0;
            DEFINE FIELD health_status ON TABLE agent_capabilities TYPE string DEFAULT "healthy";
            DEFINE FIELD last_heartbeat ON TABLE agent_capabilities TYPE datetime DEFAULT time::now();
            DEFINE FIELD performance_metrics ON TABLE agent_capabilities TYPE object;
            DEFINE FIELD specializations ON TABLE agent_capabilities TYPE array<string>;
            DEFINE FIELD resource_limits ON TABLE agent_capabilities TYPE object;
            DEFINE FIELD created_at ON TABLE agent_capabilities TYPE datetime DEFAULT time::now();
            DEFINE FIELD updated_at ON TABLE agent_capabilities TYPE datetime DEFAULT time::now();
        """)

        logger.info("Core tables created successfully")

    async def _create_relationships(self):
        """Create relationship tables and edges."""
        logger.info("Creating relationships...")

        await self.client.query("""
            DEFINE TABLE playbook_hierarchy TYPE RELATION IN playbooks OUT playbooks;
            DEFINE FIELD relationship_type ON TABLE playbook_hierarchy TYPE string;
            DEFINE FIELD created_at ON TABLE playbook_hierarchy TYPE datetime DEFAULT time::now();
        """)

        await self.client.query("""
            DEFINE TABLE step_dependencies TYPE RELATION IN playbook_steps OUT playbook_steps;
            DEFINE FIELD dependency_type ON TABLE step_dependencies TYPE string DEFAULT "sequence";
            DEFINE FIELD created_at ON TABLE step_dependencies TYPE datetime DEFAULT time::now();
        """)

        await self.client.query("""
            DEFINE TABLE template_usage TYPE RELATION IN playbook_templates OUT playbooks;
            DEFINE FIELD instantiated_at ON TABLE template_usage TYPE datetime DEFAULT time::now();
            DEFINE FIELD parameters_used ON TABLE template_usage TYPE object;
        """)

        logger.info("Relationships created successfully")

    async def _create_functions(self):
        """Create utility functions."""
        logger.info("Creating functions...")

        await self.client.query("""
            DEFINE FUNCTION fn::playbook_success_rate($playbook_id: record<playbooks>) {
                LET $total = (SELECT VALUE total_executions FROM $playbook_id)[0];
                LET $successful = (SELECT VALUE successful_executions FROM $playbook_id)[0];
                RETURN IF $total > 0 THEN $successful / $total ELSE 0;
            };
        """)

        await self.client.query("""
            DEFINE FUNCTION fn::step_success_rate($step_id: record<playbook_steps>) {
                LET $total = (SELECT VALUE total_executions FROM $step_id)[0];
                LET $successful = (SELECT VALUE successful_executions FROM $step_id)[0];
                RETURN IF $total > 0 THEN $successful / $total ELSE 0;
            };
        """)

        await self.client.query("""
            DEFINE FUNCTION fn::execution_duration($execution_id: record<playbook_executions>) {
                LET $exec = (SELECT started_at, completed_at FROM $execution_id)[0];
                RETURN IF $exec.completed_at AND $exec.started_at
                       THEN time::unix($exec.completed_at) - time::unix($exec.started_at)
                       ELSE NULL;
            };
        """)

        await self.client.query("""
            DEFINE FUNCTION fn::update_agent_heartbeat($agent_id: string) {
                UPDATE agent_capabilities SET
                    last_heartbeat = time::now(),
                    updated_at = time::now()
                WHERE agent_id = $agent_id;
            };
        """)

        logger.info("Functions created successfully")

    async def _create_indexes(self):
        """Create performance indexes."""
        logger.info("Creating indexes...")

        # Playbook indexes
        indexes = [
            "DEFINE INDEX playbook_name_idx ON TABLE playbooks COLUMNS name;",
            "DEFINE INDEX playbook_category_idx ON TABLE playbooks COLUMNS category;",
            "DEFINE INDEX playbook_status_idx ON TABLE playbooks COLUMNS status;",
            "DEFINE INDEX playbook_category_status_idx ON TABLE playbooks COLUMNS category, status;",
            "DEFINE INDEX playbook_public_idx ON TABLE playbooks COLUMNS is_public;",
            "DEFINE INDEX playbook_template_idx ON TABLE playbooks COLUMNS is_template;",

            # Step indexes
            "DEFINE INDEX step_playbook_idx ON TABLE playbook_steps COLUMNS playbook_id;",
            "DEFINE INDEX step_name_idx ON TABLE playbook_steps COLUMNS step_name;",
            "DEFINE INDEX step_type_idx ON TABLE playbook_steps COLUMNS step_type;",
            "DEFINE INDEX step_order_idx ON TABLE playbook_steps COLUMNS step_order;",
            "DEFINE INDEX step_unique_name ON TABLE playbook_steps COLUMNS playbook_id, step_name UNIQUE;",
            "DEFINE INDEX step_unique_order ON TABLE playbook_steps COLUMNS playbook_id, step_order UNIQUE;",

            # Variable indexes
            "DEFINE INDEX variable_playbook_idx ON TABLE playbook_variables COLUMNS playbook_id;",
            "DEFINE INDEX variable_unique_name ON TABLE playbook_variables COLUMNS playbook_id, variable_name UNIQUE;",

            # Execution indexes
            "DEFINE INDEX execution_playbook_idx ON TABLE playbook_executions COLUMNS playbook_id;",
            "DEFINE INDEX execution_id_idx ON TABLE playbook_executions COLUMNS execution_id UNIQUE;",
            "DEFINE INDEX execution_status_idx ON TABLE playbook_executions COLUMNS status;",

            # Step execution indexes
            "DEFINE INDEX step_exec_execution_idx ON TABLE step_executions COLUMNS execution_id;",
            "DEFINE INDEX step_exec_step_idx ON TABLE step_executions COLUMNS step_id;",
            "DEFINE INDEX step_exec_status_idx ON TABLE step_executions COLUMNS status;",

            # Agent capability indexes
            "DEFINE INDEX agent_cap_id_idx ON TABLE agent_capabilities COLUMNS agent_id UNIQUE;",
            "DEFINE INDEX agent_cap_type_idx ON TABLE agent_capabilities COLUMNS agent_type;",
            "DEFINE INDEX agent_cap_health_idx ON TABLE agent_capabilities COLUMNS health_status;"
        ]

        for index in indexes:
            try:
                await self.client.query(index)
            except Exception as e:
                logger.warning(f"Index creation failed: {index[:50]}... Error: {e}")

        logger.info("Indexes created successfully")

    async def _insert_sample_data(self):
        """Insert sample agent capabilities and test data."""
        logger.info("Inserting sample data...")

        # Insert default agent capabilities
        agents = [
            {
                "agent_id": "super_agent",
                "agent_type": "super",
                "available_tools": ["all_mcp_servers", "ptolemies-mcp", "taskmaster-ai"],
                "supported_workflows": ["all_types"],
                "max_concurrent": 10,
                "specializations": ["meta_coordination", "user_communication", "supervision"]
            },
            {
                "agent_id": "codifier_agent",
                "agent_type": "codifier",
                "available_tools": ["filesystem", "git", "ptolemies-mcp", "magic-mcp"],
                "supported_workflows": ["sequential", "pipeline", "self_feedback"],
                "max_concurrent": 5,
                "specializations": ["documentation", "knowledge_codification", "aar_generation"]
            },
            {
                "agent_id": "io_agent",
                "agent_type": "io",
                "available_tools": ["logfire-mcp", "memory", "fetch", "surrealdb-mcp"],
                "supported_workflows": ["loop", "conditional", "parallel"],
                "max_concurrent": 8,
                "specializations": ["monitoring", "observation", "validation", "progress_tracking"]
            },
            {
                "agent_id": "playbook_agent",
                "agent_type": "playbook",
                "available_tools": ["taskmaster-ai", "context7-mcp", "sequentialthinking"],
                "supported_workflows": ["all_types"],
                "max_concurrent": 6,
                "specializations": ["strategic_execution", "playbook_management", "orchestration"]
            }
        ]

        for agent in agents:
            await self.client.query("INSERT INTO agent_capabilities $agent", {"agent": agent})

        logger.info("Sample data inserted successfully")

    async def _register_migration(self):
        """Register this migration in the migrations table."""
        # Create migrations table if it doesn't exist
        await self.client.query("""
            DEFINE TABLE migrations SCHEMAFULL;
            DEFINE FIELD migration_id ON TABLE migrations TYPE string;
            DEFINE FIELD version ON TABLE migrations TYPE string;
            DEFINE FIELD description ON TABLE migrations TYPE string;
            DEFINE FIELD applied_at ON TABLE migrations TYPE datetime DEFAULT time::now();
        """)

        # Insert migration record
        await self.client.query("""
            INSERT INTO migrations {
                migration_id: $migration_id,
                version: $version,
                description: $description,
                applied_at: time::now()
            }
        """, {
            "migration_id": self.migration_id,
            "version": self.version,
            "description": self.description
        })

        logger.info(f"Migration {self.migration_id} registered")


async def run_migration(config: Optional[SurrealDBConfig] = None, rollback: bool = False) -> bool:
    """
    Run the playbook schema migration.

    Args:
        config: SurrealDB configuration
        rollback: If True, rollback the migration

    Returns:
        bool: Success status
    """
    if config is None:
        config = SurrealDBConfig()

    client = SurrealDBClient(config)

    try:
        await client.connect()
        migration = PlaybookSchemaMigration(client)

        if rollback:
            success = await migration.down()
            logger.info(f"Migration rollback {'succeeded' if success else 'failed'}")
        else:
            success = await migration.up()
            logger.info(f"Migration {'succeeded' if success else 'failed'}")

        return success

    except Exception as e:
        logger.error(f"Migration execution failed: {e}")
        return False

    finally:
        await client.close()


if __name__ == "__main__":
    # Run migration from command line
    import sys

    rollback = "--rollback" in sys.argv

    async def main():
        config = SurrealDBConfig()
        success = await run_migration(config, rollback=rollback)
        sys.exit(0 if success else 1)

    asyncio.run(main())
