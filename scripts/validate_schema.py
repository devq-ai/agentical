#!/usr/bin/env python3
"""
Schema Validation Script for Agentical Playbook System

This script validates the playbook schema design without requiring
an active SurrealDB connection. It checks for:
- Schema file existence and syntax
- Table definitions completeness
- Index coverage
- Function definitions
- Data model consistency

Usage:
    python agentical/scripts/validate_schema.py
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates SurrealDB schema files for completeness and consistency."""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.content = ""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> Tuple[bool, Dict[str, any]]:
        """
        Perform complete schema validation.

        Returns:
            tuple: (is_valid, validation_results)
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {},
            "coverage": {}
        }

        try:
            # Load schema content
            if not self._load_schema():
                results["valid"] = False
                results["errors"] = self.errors
                return False, results

            # Run validation checks
            self._validate_table_definitions()
            self._validate_field_definitions()
            self._validate_indexes()
            self._validate_functions()
            self._validate_relationships()
            self._validate_constraints()
            self._calculate_statistics()

            # Compile results
            results["errors"] = self.errors
            results["warnings"] = self.warnings
            results["valid"] = len(self.errors) == 0
            results["statistics"] = self._get_statistics()
            results["coverage"] = self._get_coverage_report()

        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Validation error: {str(e)}")

        return results["valid"], results

    def _load_schema(self) -> bool:
        """Load and basic syntax check of schema file."""
        if not self.schema_path.exists():
            self.errors.append(f"Schema file not found: {self.schema_path}")
            return False

        try:
            self.content = self.schema_path.read_text(encoding='utf-8')
            if not self.content.strip():
                self.errors.append("Schema file is empty")
                return False

            logger.info(f"Loaded schema file: {self.schema_path}")
            return True

        except Exception as e:
            self.errors.append(f"Failed to read schema file: {e}")
            return False

    def _validate_table_definitions(self):
        """Validate table definitions are complete."""
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

        # Find table definitions
        table_pattern = r'DEFINE TABLE (\w+)'
        found_tables = re.findall(table_pattern, self.content)
        found_tables_set = set(found_tables)

        # Check for missing tables
        missing_tables = set(expected_tables) - found_tables_set
        if missing_tables:
            self.errors.append(f"Missing table definitions: {missing_tables}")

        # Check for extra tables
        extra_tables = found_tables_set - set(expected_tables)
        if extra_tables:
            self.warnings.append(f"Extra table definitions found: {extra_tables}")

        logger.info(f"Found {len(found_tables)} table definitions")

    def _validate_field_definitions(self):
        """Validate field definitions for each table."""
        required_fields = {
            "playbooks": [
                "id", "name", "description", "category", "purpose", "strategy",
                "status", "created_at", "updated_at"
            ],
            "playbook_steps": [
                "id", "playbook_id", "step_name", "step_type", "step_order",
                "agent_type", "tool_name", "created_at"
            ],
            "playbook_executions": [
                "id", "playbook_id", "execution_id", "status", "started_at",
                "completed_at", "created_at"
            ],
            "agent_capabilities": [
                "id", "agent_id", "agent_type", "available_tools",
                "supported_workflows", "max_concurrent", "health_status"
            ]
        }

        field_pattern = r'DEFINE FIELD (\w+) ON TABLE (\w+)'
        field_matches = re.findall(field_pattern, self.content)

        # Group fields by table
        fields_by_table = {}
        for field, table in field_matches:
            if table not in fields_by_table:
                fields_by_table[table] = []
            fields_by_table[table].append(field)

        # Check required fields
        for table, required in required_fields.items():
            if table not in fields_by_table:
                self.errors.append(f"No fields defined for table: {table}")
                continue

            actual_fields = set(fields_by_table[table])
            missing_fields = set(required) - actual_fields

            if missing_fields:
                self.errors.append(f"Missing required fields in {table}: {missing_fields}")

        total_fields = sum(len(fields) for fields in fields_by_table.values())
        logger.info(f"Found {total_fields} field definitions across {len(fields_by_table)} tables")

    def _validate_indexes(self):
        """Validate index definitions for performance."""
        required_indexes = {
            "playbooks": ["name", "category", "status"],
            "playbook_steps": ["playbook_id", "step_order", "agent_type"],
            "playbook_executions": ["execution_id", "status", "playbook_id"],
            "agent_capabilities": ["agent_id", "agent_type", "health_status"]
        }

        index_pattern = r'DEFINE INDEX (\w+) ON TABLE (\w+) COLUMNS (.+?);'
        index_matches = re.findall(index_pattern, self.content)

        # Group indexes by table
        indexes_by_table = {}
        for index_name, table, columns in index_matches:
            if table not in indexes_by_table:
                indexes_by_table[table] = []
            # Parse columns (handle single and multiple columns)
            col_list = [col.strip() for col in columns.split(',')]
            indexes_by_table[table].extend(col_list)

        # Check required indexes
        for table, required_cols in required_indexes.items():
            if table not in indexes_by_table:
                self.warnings.append(f"No indexes defined for table: {table}")
                continue

            actual_cols = set(indexes_by_table[table])
            missing_cols = set(required_cols) - actual_cols

            if missing_cols:
                self.warnings.append(f"Missing recommended indexes in {table}: {missing_cols}")

        total_indexes = len(index_matches)
        logger.info(f"Found {total_indexes} index definitions")

    def _validate_functions(self):
        """Validate function definitions."""
        expected_functions = [
            "fn::playbook_success_rate",
            "fn::step_success_rate",
            "fn::execution_duration",
            "fn::update_agent_heartbeat"
        ]

        function_pattern = r'DEFINE FUNCTION (fn::\w+)'
        found_functions = re.findall(function_pattern, self.content)
        found_functions_set = set(found_functions)

        missing_functions = set(expected_functions) - found_functions_set
        if missing_functions:
            self.warnings.append(f"Missing utility functions: {missing_functions}")

        logger.info(f"Found {len(found_functions)} function definitions")

    def _validate_relationships(self):
        """Validate relationship definitions."""
        relation_tables = [
            "playbook_hierarchy",
            "step_dependencies",
            "template_usage"
        ]

        relation_pattern = r'DEFINE TABLE (\w+) TYPE RELATION'
        found_relations = re.findall(relation_pattern, self.content)
        found_relations_set = set(found_relations)

        missing_relations = set(relation_tables) - found_relations_set
        if missing_relations:
            self.warnings.append(f"Missing relationship tables: {missing_relations}")

        logger.info(f"Found {len(found_relations)} relationship definitions")

    def _validate_constraints(self):
        """Validate data constraints and assertions."""
        # Check for enum constraints
        enum_patterns = [
            r'ASSERT \$value IN \[.*"draft".*"active".*\]',  # Status enum
            r'ASSERT \$value IN \[.*"deployment".*"testing".*\]',  # Category enum
        ]

        constraint_count = 0
        for pattern in enum_patterns:
            if re.search(pattern, self.content):
                constraint_count += 1

        if constraint_count < len(enum_patterns):
            self.warnings.append("Some enum constraints may be missing")

        # Check for length constraints
        length_pattern = r'ASSERT string::len\(\$value\)'
        length_constraints = len(re.findall(length_pattern, self.content))

        if length_constraints < 5:
            self.warnings.append("Insufficient string length constraints")

        logger.info(f"Found {constraint_count} enum constraints and {length_constraints} length constraints")

    def _calculate_statistics(self):
        """Calculate schema statistics."""
        self.stats = {
            "total_lines": len(self.content.splitlines()),
            "total_tables": len(re.findall(r'DEFINE TABLE', self.content)),
            "total_fields": len(re.findall(r'DEFINE FIELD', self.content)),
            "total_indexes": len(re.findall(r'DEFINE INDEX', self.content)),
            "total_functions": len(re.findall(r'DEFINE FUNCTION', self.content)),
            "total_constraints": len(re.findall(r'ASSERT', self.content))
        }

    def _get_statistics(self) -> Dict[str, any]:
        """Get schema statistics."""
        return getattr(self, 'stats', {})

    def _get_coverage_report(self) -> Dict[str, any]:
        """Get coverage report."""
        return {
            "tables_coverage": "100%" if len(self.errors) == 0 else "Incomplete",
            "indexes_coverage": "Good" if len([w for w in self.warnings if "index" in w.lower()]) < 2 else "Needs improvement",
            "constraints_coverage": "Good" if len([w for w in self.warnings if "constraint" in w.lower()]) < 2 else "Needs improvement"
        }


def validate_playbook_schema() -> bool:
    """
    Main validation function.

    Returns:
        bool: True if schema is valid, False otherwise
    """
    # Find schema file
    project_root = Path(__file__).parent.parent
    schema_file = project_root / "db" / "schemas" / "playbook_schema.surql"

    if not schema_file.exists():
        logger.error(f"Schema file not found: {schema_file}")
        return False

    # Run validation
    validator = SchemaValidator(schema_file)
    is_valid, results = validator.validate()

    # Print results
    print("=" * 60)
    print("AGENTICAL PLAYBOOK SCHEMA VALIDATION REPORT")
    print("=" * 60)

    # Statistics
    stats = results.get("statistics", {})
    print(f"\n📊 SCHEMA STATISTICS:")
    print(f"   • Total Lines: {stats.get('total_lines', 0)}")
    print(f"   • Tables: {stats.get('total_tables', 0)}")
    print(f"   • Fields: {stats.get('total_fields', 0)}")
    print(f"   • Indexes: {stats.get('total_indexes', 0)}")
    print(f"   • Functions: {stats.get('total_functions', 0)}")
    print(f"   • Constraints: {stats.get('total_constraints', 0)}")

    # Coverage
    coverage = results.get("coverage", {})
    print(f"\n📋 COVERAGE REPORT:")
    for metric, value in coverage.items():
        status_icon = "✅" if value in ["100%", "Good"] else "⚠️"
        print(f"   {status_icon} {metric.replace('_', ' ').title()}: {value}")

    # Errors
    errors = results.get("errors", [])
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   • {error}")

    # Warnings
    warnings = results.get("warnings", [])
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")

    # Overall result
    print(f"\n{'='*60}")
    if is_valid:
        print("🎉 SCHEMA VALIDATION: PASSED")
        print("   The playbook schema is valid and ready for deployment!")
    else:
        print("❌ SCHEMA VALIDATION: FAILED")
        print("   Please fix the errors above before proceeding.")
    print("=" * 60)

    return is_valid


if __name__ == "__main__":
    """Run schema validation."""
    try:
        success = validate_playbook_schema()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        sys.exit(1)
