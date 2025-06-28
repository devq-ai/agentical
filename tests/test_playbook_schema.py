"""
Test Script for Playbook Schema Validation

This script validates the SurrealDB playbook schema implementation,
including table creation, data insertion, and query functionality.

Usage:
    python -m pytest agentical/tests/test_playbook_schema.py -v

Or run directly:
    python agentical/tests/test_playbook_schema.py
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from agentical.db.surrealdb_client import SurrealDBClient, SurrealDBConfig
    from agentical.db.schemas.playbook_schema_manager import (
        PlaybookSchemaManager,
        AgentCapability,
        initialize_playbook_schema,
        validate_playbook_schema
    )
    from agentical.db.migrations.playbook_schema_001 import run_migration
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False


class TestPlaybookSchema:
    """Test suite for playbook schema functionality."""

    @pytest.fixture(scope="class")
    async def db_config(self):
        """Create test database configuration."""
        return SurrealDBConfig(
            url="ws://localhost:8000/rpc",
            username="root",
            password="root",
            namespace="test_agentical",
            database="playbook_test"
        )

    @pytest.fixture(scope="class")
    async def client(self, db_config):
        """Create and configure SurrealDB client."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("SurrealDB dependencies not available")

        client = SurrealDBClient(db_config)

        try:
            await client.connect()
            yield client
        finally:
            await client.close()

    @pytest.fixture(scope="class")
    async def schema_manager(self, client):
        """Create schema manager instance."""
        return PlaybookSchemaManager(client)

    @pytest.mark.asyncio
    async def test_schema_initialization(self, schema_manager):
        """Test complete schema initialization."""
        # Force clean initialization
        success = await schema_manager.initialize_schema(force=True)
        assert success, "Schema initialization should succeed"

        # Verify schema exists
        validation = await schema_manager.validate_schema()
        assert validation["valid"], f"Schema validation failed: {validation['errors']}"

        logger.info("✅ Schema initialization test passed")

    @pytest.mark.asyncio
    async def test_table_creation(self, client):
        """Test that all required tables are created."""
        expected_tables = [
            "playbooks",
            "playbook_steps",
            "playbook_variables",
            "playbook_executions",
            "step_executions",
            "playbook_aars",
            "playbook_templates",
            "agent_capabilities"
        ]

        # Get list of tables
        result = await client.query("INFO FOR DB")
        tables = list(result[0].get('tb', {}).keys()) if result else []

        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

        logger.info(f"✅ All {len(expected_tables)} tables created successfully")

    @pytest.mark.asyncio
    async def test_agent_capability_registration(self, schema_manager):
        """Test agent capability registration."""
        test_agent = AgentCapability(
            agent_id="test_agent",
            agent_type="test",
            available_tools=["tool1", "tool2"],
            supported_workflows=["sequential", "parallel"],
            max_concurrent=3,
            specializations=["testing", "validation"]
        )

        # Register agent
        success = await schema_manager.register_agent_capability(test_agent)
        assert success, "Agent registration should succeed"

        # Verify registration
        agents = await schema_manager.get_agent_pool(filter_healthy=False)
        test_agents = [a for a in agents if a.get("agent_id") == "test_agent"]

        assert len(test_agents) == 1, "Test agent should be registered"
        assert test_agents[0]["agent_type"] == "test"
        assert test_agents[0]["max_concurrent"] == 3

        logger.info("✅ Agent capability registration test passed")

    @pytest.mark.asyncio
    async def test_playbook_creation(self, client):
        """Test playbook creation and validation."""
        playbook_data = {
            "name": "Test Deployment Playbook",
            "description": "Test playbook for deployment automation",
            "category": "deployment",
            "purpose": "Automate application deployment process",
            "strategy": "Sequential execution with validation steps",
            "success_conditions": [
                "Application deployed successfully",
                "Health checks pass",
                "Documentation updated"
            ],
            "tags": ["deployment", "automation", "test"],
            "status": "active",
            "max_concurrent_executions": 2,
            "timeout_minutes": 60
        }

        # Insert playbook
        result = await client.query(
            "INSERT INTO playbooks $playbook RETURN id",
            {"playbook": playbook_data}
        )

        assert result and len(result) > 0, "Playbook insertion should succeed"
        playbook_id = result[0]["id"]

        # Verify playbook exists
        verify_result = await client.query(
            "SELECT * FROM playbooks WHERE id = $id",
            {"id": playbook_id}
        )

        assert len(verify_result) == 1, "Playbook should exist"
        playbook = verify_result[0]
        assert playbook["name"] == "Test Deployment Playbook"
        assert playbook["category"] == "deployment"
        assert len(playbook["success_conditions"]) == 3

        logger.info("✅ Playbook creation test passed")

    @pytest.mark.asyncio
    async def test_playbook_steps_creation(self, client):
        """Test playbook steps creation and dependencies."""
        # First create a playbook
        playbook_result = await client.query("""
            INSERT INTO playbooks {
                name: "Test Step Playbook",
                description: "Test playbook for step validation",
                category: "testing",
                purpose: "Test step execution flow",
                strategy: "Multi-step automated process"
            } RETURN id
        """)

        playbook_id = playbook_result[0]["id"]

        # Create steps
        steps_data = [
            {
                "playbook_id": playbook_id,
                "step_name": "initialize_environment",
                "step_type": "agent_task",
                "step_order": 1,
                "agent_type": "devops",
                "tool_name": "terraform",
                "description": "Initialize deployment environment",
                "success_indicators": ["Environment ready"]
            },
            {
                "playbook_id": playbook_id,
                "step_name": "deploy_application",
                "step_type": "agent_task",
                "step_order": 2,
                "agent_type": "code",
                "tool_name": "docker",
                "description": "Deploy application containers",
                "depends_on_steps": ["initialize_environment"],
                "success_indicators": ["Application running"]
            },
            {
                "playbook_id": playbook_id,
                "step_name": "validate_deployment",
                "step_type": "verification",
                "step_order": 3,
                "agent_type": "io",
                "tool_name": "logfire",
                "description": "Validate deployment success",
                "depends_on_steps": ["deploy_application"],
                "success_indicators": ["Health checks pass", "Metrics normal"]
            }
        ]

        # Insert steps
        for step in steps_data:
            result = await client.query(
                "INSERT INTO playbook_steps $step",
                {"step": step}
            )
            assert result, f"Step {step['step_name']} insertion should succeed"

        # Verify steps exist and ordering
        verify_result = await client.query(
            "SELECT * FROM playbook_steps WHERE playbook_id = $id ORDER BY step_order",
            {"id": playbook_id}
        )

        assert len(verify_result) == 3, "All steps should exist"
        assert verify_result[0]["step_name"] == "initialize_environment"
        assert verify_result[1]["step_name"] == "deploy_application"
        assert verify_result[2]["step_name"] == "validate_deployment"

        # Check dependencies
        deploy_step = verify_result[1]
        assert "initialize_environment" in deploy_step["depends_on_steps"]

        logger.info("✅ Playbook steps creation test passed")

    @pytest.mark.asyncio
    async def test_execution_tracking(self, client):
        """Test playbook execution tracking."""
        # Create a simple playbook first
        playbook_result = await client.query("""
            INSERT INTO playbooks {
                name: "Execution Test Playbook",
                description: "Test execution tracking",
                category: "testing",
                purpose: "Test execution flow",
                strategy: "Simple execution test"
            } RETURN id
        """)

        playbook_id = playbook_result[0]["id"]
        execution_id = f"exec_{uuid4().hex[:8]}"

        # Create execution record
        execution_data = {
            "playbook_id": playbook_id,
            "execution_id": execution_id,
            "triggered_by": "test",
            "status": "running",
            "started_at": datetime.now().isoformat()
        }

        result = await client.query(
            "INSERT INTO playbook_executions $execution RETURN id",
            {"execution": execution_data}
        )

        assert result, "Execution creation should succeed"
        db_execution_id = result[0]["id"]

        # Update execution status
        await client.query("""
            UPDATE playbook_executions SET
                status = "completed",
                completed_at = time::now(),
                overall_success = true,
                completed_steps = 1
            WHERE id = $id
        """, {"id": db_execution_id})

        # Verify execution tracking
        verify_result = await client.query(
            "SELECT * FROM playbook_executions WHERE execution_id = $exec_id",
            {"exec_id": execution_id}
        )

        assert len(verify_result) == 1, "Execution should exist"
        execution = verify_result[0]
        assert execution["status"] == "completed"
        assert execution["overall_success"] == True
        assert execution["completed_steps"] == 1

        logger.info("✅ Execution tracking test passed")

    @pytest.mark.asyncio
    async def test_performance_functions(self, client):
        """Test SurrealDB functions for performance calculations."""
        # Create test data
        playbook_result = await client.query("""
            INSERT INTO playbooks {
                name: "Performance Test Playbook",
                description: "Test performance calculations",
                category: "testing",
                purpose: "Test performance metrics",
                strategy: "Performance validation",
                total_executions: 10,
                successful_executions: 8,
                failed_executions: 2
            } RETURN id
        """)

        playbook_id = playbook_result[0]["id"]

        # Test success rate function
        result = await client.query(
            "SELECT fn::playbook_success_rate($id) as success_rate",
            {"id": playbook_id}
        )

        assert result, "Function call should succeed"
        success_rate = result[0]["success_rate"]
        assert success_rate == 0.8, f"Success rate should be 0.8, got {success_rate}"

        logger.info("✅ Performance functions test passed")

    @pytest.mark.asyncio
    async def test_agent_pool_discovery(self, schema_manager):
        """Test agent pool discovery functionality."""
        # Get current agent pool
        agents = await schema_manager.get_agent_pool()

        # Should have at least the default agents
        assert len(agents) >= 4, "Should have default agents registered"

        agent_types = {agent["agent_type"] for agent in agents}
        expected_types = {"super", "codifier", "io", "playbook"}

        assert expected_types.issubset(agent_types), "Should have all default agent types"

        # Test heartbeat update
        test_agent_id = agents[0]["agent_id"]
        success = await schema_manager.update_agent_heartbeat(test_agent_id)
        assert success, "Heartbeat update should succeed"

        logger.info("✅ Agent pool discovery test passed")

    @pytest.mark.asyncio
    async def test_schema_validation(self, schema_manager):
        """Test comprehensive schema validation."""
        validation = await schema_manager.validate_schema()

        assert validation["valid"], f"Schema should be valid: {validation['errors']}"
        assert len(validation["table_counts"]) > 0, "Should have table counts"
        assert len(validation["functions_status"]) > 0, "Should have function status"

        # Check that all expected tables have been created
        required_tables = [
            "playbooks", "playbook_steps", "playbook_variables",
            "playbook_executions", "step_executions", "playbook_aars"
        ]

        for table in required_tables:
            assert table in validation["table_counts"], f"Table {table} should exist"

        logger.info("✅ Schema validation test passed")

    @pytest.mark.asyncio
    async def test_cleanup_functionality(self, schema_manager):
        """Test data cleanup functionality."""
        # Insert old test data
        old_date = (datetime.now() - timedelta(days=100)).isoformat()

        await schema_manager.client.query("""
            INSERT INTO playbook_executions {
                execution_id: "old_test_execution",
                playbook_id: playbooks:test,
                status: "completed",
                created_at: $old_date
            }
        """, {"old_date": old_date})

        # Run cleanup (keep only 30 days)
        cleanup_results = await schema_manager.cleanup_old_data(days_old=30)

        assert "executions_deleted" in cleanup_results, "Should return cleanup results"

        logger.info("✅ Cleanup functionality test passed")


class TestMigrationSystem:
    """Test migration system functionality."""

    @pytest.mark.asyncio
    async def test_migration_execution(self):
        """Test migration execution and rollback."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("SurrealDB dependencies not available")

        config = SurrealDBConfig(
            namespace="test_migration",
            database="migration_test"
        )

        # Test migration up
        success = await run_migration(config, rollback=False)
        assert success, "Migration should succeed"

        # Test migration rollback
        success = await run_migration(config, rollback=True)
        assert success, "Migration rollback should succeed"

        logger.info("✅ Migration system test passed")


async def run_tests():
    """Run all tests manually."""
    if not DEPENDENCIES_AVAILABLE:
        logger.error("❌ Cannot run tests - SurrealDB dependencies not available")
        return False

    try:
        # Test basic schema initialization
        config = SurrealDBConfig(
            namespace="test_agentical_manual",
            database="test_manual"
        )

        logger.info("🧪 Starting manual test execution...")

        # Initialize schema
        success = await initialize_playbook_schema(config, force=True)
        assert success, "Schema initialization failed"
        logger.info("✅ Schema initialization test passed")

        # Validate schema
        validation = await validate_playbook_schema(config)
        assert validation["valid"], f"Schema validation failed: {validation['errors']}"
        logger.info("✅ Schema validation test passed")

        # Test agent capability management
        client = SurrealDBClient(config)
        await client.connect()

        schema_manager = PlaybookSchemaManager(client)

        # Register test agent
        test_agent = AgentCapability(
            agent_id="manual_test_agent",
            agent_type="test",
            available_tools=["test_tool"],
            supported_workflows=["test_workflow"]
        )

        success = await schema_manager.register_agent_capability(test_agent)
        assert success, "Agent registration failed"
        logger.info("✅ Agent registration test passed")

        # Get agent pool
        agents = await schema_manager.get_agent_pool()
        assert len(agents) > 0, "Agent pool should not be empty"
        logger.info("✅ Agent pool discovery test passed")

        await client.close()

        logger.info("🎉 All manual tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    """Run tests directly."""
    import sys

    async def main():
        success = await run_tests()
        sys.exit(0 if success else 1)

    asyncio.run(main())
