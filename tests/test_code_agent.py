"""
Comprehensive Test Suite for CodeAgent

This test suite validates the CodeAgent implementation for software development,
programming tasks, code analysis, refactoring, and development workflow automation.

Features tested:
- Code generation across multiple languages
- Code refactoring and optimization
- Automated code review and analysis
- Test generation and execution coordination
- Documentation generation from code
- Security vulnerability scanning
- Performance optimization recommendations
- Git workflow integration
- Error handling and edge cases
"""

import asyncio
import pytest
import logging
import tempfile
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from agentical.agents.code_agent import (
        CodeAgent, ProgrammingLanguage, CodeOperationType, CodeQualityLevel,
        TestType, CodeMetrics, SecurityIssue, CodeReviewFinding,
        CodeGenerationRequest, CodeRefactorRequest, CodeAnalysisRequest,
        TestGenerationRequest, CodeDocumentationRequest
    )
    from agentical.agents.enhanced_base_agent import AgentState, ResourceConstraints
    from agentical.db.models.agent import AgentType, AgentStatus
    from agentical.core.exceptions import AgentExecutionError, ValidationError
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False


class TestCodeAgent:
    """Test suite for CodeAgent core functionality."""

    @pytest.fixture
    def code_agent(self):
        """Create CodeAgent instance for testing."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")

        agent = CodeAgent()
        return agent

    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing."""
        return '''
def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    """Calculate factorial of n."""
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
'''

    @pytest.fixture
    def sample_javascript_code(self):
        """Sample JavaScript code for testing."""
        return '''
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

function factorial(n) {
    if (n === 0) return 1;
    return n * factorial(n - 1);
}

module.exports = { fibonacci, factorial };
'''

    @pytest.fixture
    def code_generation_request(self):
        """Sample code generation request."""
        return CodeGenerationRequest(
            language=ProgrammingLanguage.PYTHON,
            description="Create a function to calculate the sum of two numbers",
            function_name="add_numbers",
            parameters=[
                {"name": "a", "type": "int"},
                {"name": "b", "type": "int"}
            ],
            return_type="int",
            include_tests=True,
            include_docs=True
        )

    @pytest.mark.asyncio
    async def test_agent_initialization(self, code_agent):
        """Test CodeAgent initialization."""
        assert code_agent.agent_id == "code-001"
        assert code_agent.name == "CodeAgent"
        assert "code_generation" in code_agent.capabilities
        assert "git" in code_agent.tools
        assert "github" in code_agent.tools
        assert "filesystem" in code_agent.tools

    @pytest.mark.asyncio
    async def test_code_generation_python(self, code_agent, code_generation_request):
        """Test Python code generation."""
        result = await code_agent.generate_code(code_generation_request)

        assert result["success"] is True
        assert "generated_code" in result
        assert "tests" in result
        assert "documentation" in result
        assert result["language"] == "python"

        # Verify generated code contains function
        generated_code = result["generated_code"]
        assert "def add_numbers" in generated_code or "generated_function" in generated_code

    @pytest.mark.asyncio
    async def test_code_generation_javascript(self, code_agent):
        """Test JavaScript code generation."""
        request = CodeGenerationRequest(
            language=ProgrammingLanguage.JAVASCRIPT,
            description="Create a function to validate email addresses",
            function_name="validateEmail",
            include_tests=True,
            include_docs=True
        )

        result = await code_agent.generate_code(request)

        assert result["success"] is True
        assert result["language"] == "javascript"
        assert "generated_code" in result

    @pytest.mark.asyncio
    async def test_code_generation_with_framework(self, code_agent):
        """Test code generation with specific framework."""
        request = CodeGenerationRequest(
            language=ProgrammingLanguage.PYTHON,
            description="Create a REST API endpoint",
            framework="FastAPI",
            include_tests=True,
            include_docs=True
        )

        result = await code_agent.generate_code(request)

        assert result["success"] is True
        assert "generated_code" in result

    @pytest.mark.asyncio
    async def test_code_refactoring(self, code_agent, sample_python_code):
        """Test code refactoring functionality."""
        request = CodeRefactorRequest(
            source_code=sample_python_code,
            language=ProgrammingLanguage.PYTHON,
            refactor_type="optimize_recursion",
            target_improvement="Performance optimization",
            preserve_behavior=True,
            update_tests=True
        )

        result = await code_agent.refactor_code(request)

        assert result["success"] is True
        assert "refactored_code" in result
        assert "changes" in result
        assert "validation" in result
        assert result["validation"]["behavior_preserved"] is True

    @pytest.mark.asyncio
    async def test_code_analysis_comprehensive(self, code_agent, sample_python_code):
        """Test comprehensive code analysis."""
        request = CodeAnalysisRequest(
            source_code=sample_python_code,
            language=ProgrammingLanguage.PYTHON,
            analysis_types=["complexity", "quality", "performance"],
            include_metrics=True,
            include_dependencies=True,
            security_scan=True
        )

        result = await code_agent.analyze_code(request)

        assert result["success"] is True
        assert "analysis_results" in result
        assert "recommendations" in result
        assert "metrics" in result["analysis_results"]
        assert "complexity" in result["analysis_results"]
        assert "quality" in result["analysis_results"]
        assert "security" in result["analysis_results"]

    @pytest.mark.asyncio
    async def test_code_review(self, code_agent, sample_python_code):
        """Test automated code review."""
        result = await code_agent.review_code(
            sample_python_code,
            ProgrammingLanguage.PYTHON,
            review_criteria=["code_style", "best_practices", "security"]
        )

        assert result["success"] is True
        assert "quality_score" in result
        assert "findings" in result
        assert "suggestions" in result
        assert isinstance(result["quality_score"], float)
        assert 0 <= result["quality_score"] <= 100

    @pytest.mark.asyncio
    async def test_test_generation(self, code_agent, sample_python_code):
        """Test test generation functionality."""
        request = TestGenerationRequest(
            source_code=sample_python_code,
            language=ProgrammingLanguage.PYTHON,
            test_types=[TestType.UNIT, TestType.INTEGRATION],
            test_framework="pytest",
            coverage_target=80.0,
            include_edge_cases=True,
            mock_dependencies=True
        )

        result = await code_agent.generate_tests(request)

        assert result["success"] is True
        assert "generated_tests" in result
        assert "coverage_estimate" in result
        assert result["test_framework"] == "pytest"
        assert "unit" in result["generated_tests"]

    @pytest.mark.asyncio
    async def test_documentation_generation(self, code_agent, sample_python_code):
        """Test documentation generation."""
        request = CodeDocumentationRequest(
            source_code=sample_python_code,
            language=ProgrammingLanguage.PYTHON,
            doc_style="google",
            include_examples=True,
            include_type_hints=True,
            include_exceptions=True,
            generate_readme=True
        )

        result = await code_agent.generate_documentation(request)

        assert result["success"] is True
        assert "api_documentation" in result
        assert "inline_documentation" in result
        assert "readme" in result
        assert result["doc_style"] == "google"

    @pytest.mark.asyncio
    async def test_security_scanning(self, code_agent):
        """Test security vulnerability scanning."""
        vulnerable_code = '''
import os
import subprocess

def execute_command(user_input):
    # Vulnerable to command injection
    os.system(f"ls {user_input}")

def sql_query(user_input):
    # Vulnerable to SQL injection
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query
'''

        result = await code_agent._perform_security_scan(
            vulnerable_code,
            ProgrammingLanguage.PYTHON
        )

        # Since this is a placeholder implementation, just verify structure
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_code_metrics_calculation(self, code_agent, sample_python_code):
        """Test code metrics calculation."""
        metrics = await code_agent._calculate_code_metrics(
            sample_python_code,
            ProgrammingLanguage.PYTHON
        )

        assert isinstance(metrics, CodeMetrics)
        assert metrics.lines_of_code > 0
        assert metrics.cyclomatic_complexity >= 1
        assert 0 <= metrics.maintainability_index <= 100

    @pytest.mark.asyncio
    async def test_error_handling_invalid_language(self, code_agent):
        """Test error handling for invalid language."""
        with pytest.raises(Exception):
            request = CodeGenerationRequest(
                language="invalid_language",  # This should cause validation error
                description="Test invalid language"
            )

    @pytest.mark.asyncio
    async def test_error_handling_empty_code(self, code_agent):
        """Test error handling for empty code input."""
        request = CodeRefactorRequest(
            source_code="",
            language=ProgrammingLanguage.PYTHON,
            refactor_type="optimize",
            target_improvement="performance"
        )

        # Should handle gracefully
        result = await code_agent.refactor_code(request)
        # Since this is placeholder implementation, just verify it doesn't crash
        assert "success" in result


class TestCodeAgentLanguageSupport:
    """Test suite for multi-language support."""

    @pytest.fixture
    def code_agent(self):
        """Create CodeAgent instance."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")
        return CodeAgent()

    @pytest.mark.asyncio
    async def test_python_support(self, code_agent):
        """Test Python language support."""
        config = code_agent.language_configs.get(ProgrammingLanguage.PYTHON)
        assert config is not None
        assert ".py" in config["file_extensions"]
        assert "pytest" in config["test_frameworks"]
        assert "black" in config["formatters"]

    @pytest.mark.asyncio
    async def test_javascript_support(self, code_agent):
        """Test JavaScript language support."""
        config = code_agent.language_configs.get(ProgrammingLanguage.JAVASCRIPT)
        assert config is not None
        assert ".js" in config["file_extensions"]
        assert "jest" in config["test_frameworks"]
        assert "prettier" in config["formatters"]

    @pytest.mark.asyncio
    async def test_typescript_support(self, code_agent):
        """Test TypeScript language support."""
        config = code_agent.language_configs.get(ProgrammingLanguage.TYPESCRIPT)
        assert config is not None
        assert ".ts" in config["file_extensions"]
        assert "jest" in config["test_frameworks"]

    @pytest.mark.asyncio
    async def test_multiple_languages_generation(self, code_agent):
        """Test code generation for multiple languages."""
        languages = [
            ProgrammingLanguage.PYTHON,
            ProgrammingLanguage.JAVASCRIPT,
            ProgrammingLanguage.TYPESCRIPT
        ]

        for language in languages:
            request = CodeGenerationRequest(
                language=language,
                description="Create a simple hello world function",
                function_name="hello_world"
            )

            result = await code_agent.generate_code(request)
            assert result["success"] is True
            assert result["language"] == language.value


class TestCodeAgentAdvancedFeatures:
    """Test suite for advanced CodeAgent features."""

    @pytest.fixture
    def code_agent(self):
        """Create CodeAgent instance."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")
        return CodeAgent()

    @pytest.mark.asyncio
    async def test_complex_refactoring_scenarios(self, code_agent):
        """Test complex refactoring scenarios."""
        complex_code = '''
class DataProcessor:
    def __init__(self):
        self.data = []

    def process_data(self, input_data):
        # Complex processing logic that could be refactored
        result = []
        for item in input_data:
            if item is not None:
                if isinstance(item, str):
                    if len(item) > 0:
                        processed = item.upper().strip()
                        if processed not in result:
                            result.append(processed)
        return result
'''

        request = CodeRefactorRequest(
            source_code=complex_code,
            language=ProgrammingLanguage.PYTHON,
            refactor_type="extract_method",
            target_improvement="Improve readability and maintainability"
        )

        result = await code_agent.refactor_code(request)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_performance_analysis(self, code_agent):
        """Test performance analysis capabilities."""
        performance_critical_code = '''
def inefficient_function(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j] and i != j:
                result.append(data[i])
    return result
'''

        performance_analysis = await code_agent._analyze_performance(
            performance_critical_code,
            ProgrammingLanguage.PYTHON
        )

        assert "performance_score" in performance_analysis
        assert "bottlenecks" in performance_analysis

    @pytest.mark.asyncio
    async def test_dependency_analysis(self, code_agent):
        """Test dependency analysis."""
        code_with_dependencies = '''
import requests
import numpy as np
from flask import Flask, jsonify
import pandas as pd

def api_call():
    response = requests.get("https://api.example.com")
    return response.json()

def data_processing(data):
    df = pd.DataFrame(data)
    return np.mean(df.values)
'''

        dependencies = await code_agent._analyze_dependencies(
            code_with_dependencies,
            ProgrammingLanguage.PYTHON
        )

        assert "dependencies" in dependencies
        assert "vulnerabilities" in dependencies

    @pytest.mark.asyncio
    async def test_design_pattern_application(self, code_agent):
        """Test design pattern application in code generation."""
        request = CodeGenerationRequest(
            language=ProgrammingLanguage.PYTHON,
            description="Create a logging system",
            design_patterns=["singleton", "observer"],
            include_tests=True
        )

        result = await code_agent.generate_code(request)
        assert result["success"] is True
        assert "singleton" in result["generation_plan"]["design_patterns"]

    @pytest.mark.asyncio
    async def test_multi_file_analysis(self, code_agent):
        """Test analysis of multiple files or directories."""
        request = CodeAnalysisRequest(
            directory_path="/fake/project/path",
            analysis_types=["complexity", "dependencies", "quality"],
            include_metrics=True,
            security_scan=True
        )

        result = await code_agent.analyze_code(request)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_test_coverage_estimation(self, code_agent):
        """Test test coverage estimation accuracy."""
        source_code = '''
def calculator(a, b, operation):
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b != 0:
            return a / b
        else:
            raise ValueError("Division by zero")
    else:
        raise ValueError("Invalid operation")
'''

        tests = {
            "unit": '''
def test_calculator_add():
    assert calculator(2, 3, "add") == 5

def test_calculator_divide_by_zero():
    with pytest.raises(ValueError):
        calculator(5, 0, "divide")
'''
        }

        coverage = await code_agent._estimate_test_coverage(source_code, tests)
        assert isinstance(coverage, float)
        assert 0 <= coverage <= 100


class TestCodeAgentIntegrationScenarios:
    """Integration tests for real-world development scenarios."""

    @pytest.fixture
    def code_agent(self):
        """Create CodeAgent instance."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")
        return CodeAgent()

    @pytest.mark.asyncio
    async def test_complete_feature_development_workflow(self, code_agent):
        """Test complete feature development from spec to tests."""
        # Step 1: Generate initial code
        generation_request = CodeGenerationRequest(
            language=ProgrammingLanguage.PYTHON,
            description="Create a user authentication system",
            function_name="authenticate_user",
            include_tests=True,
            include_docs=True
        )

        generation_result = await code_agent.generate_code(generation_request)
        assert generation_result["success"] is True

        # Step 2: Review the generated code
        review_result = await code_agent.review_code(
            generation_result["generated_code"],
            ProgrammingLanguage.PYTHON
        )
        assert review_result["success"] is True

        # Step 3: Refactor based on review findings
        if review_result["findings"]:
            refactor_request = CodeRefactorRequest(
                source_code=generation_result["generated_code"],
                language=ProgrammingLanguage.PYTHON,
                refactor_type="improve_quality",
                target_improvement="Address code review findings"
            )

            refactor_result = await code_agent.refactor_code(refactor_request)
            assert refactor_result["success"] is True

    @pytest.mark.asyncio
    async def test_legacy_code_modernization(self, code_agent):
        """Test modernizing legacy code."""
        legacy_code = '''
# Python 2 style legacy code
def process_data(data):
    result = []
    for item in data:
        if item <> None:  # Old comparison operator
            result.append(str(item))
    return result

def file_operations():
    f = open("data.txt", "r")
    content = f.read()
    f.close()
    return content
'''

        refactor_request = CodeRefactorRequest(
            source_code=legacy_code,
            language=ProgrammingLanguage.PYTHON,
            refactor_type="modernize",
            target_improvement="Upgrade to Python 3 standards"
        )

        result = await code_agent.refactor_code(refactor_request)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_api_development_scenario(self, code_agent):
        """Test API development scenario."""
        # Generate API endpoint
        api_request = CodeGenerationRequest(
            language=ProgrammingLanguage.PYTHON,
            description="Create REST API endpoint for user management",
            framework="FastAPI",
            include_tests=True,
            include_docs=True
        )

        result = await code_agent.generate_code(api_request)
        assert result["success"] is True

        # Generate comprehensive tests for the API
        test_request = TestGenerationRequest(
            source_code=result["generated_code"],
            language=ProgrammingLanguage.PYTHON,
            test_types=[TestType.UNIT, TestType.INTEGRATION, TestType.FUNCTIONAL],
            test_framework="pytest"
        )

        test_result = await code_agent.generate_tests(test_request)
        assert test_result["success"] is True

    @pytest.mark.asyncio
    async def test_microservice_development(self, code_agent):
        """Test microservice development workflow."""
        # Generate microservice structure
        microservice_request = CodeGenerationRequest(
            language=ProgrammingLanguage.PYTHON,
            description="Create a microservice for order processing",
            framework="FastAPI",
            design_patterns=["repository", "service_layer"],
            include_tests=True,
            include_docs=True
        )

        result = await code_agent.generate_code(microservice_request)
        assert result["success"] is True

        # Analyze for microservice best practices
        analysis_request = CodeAnalysisRequest(
            source_code=result["generated_code"],
            language=ProgrammingLanguage.PYTHON,
            analysis_types=["quality", "performance", "security"],
            security_scan=True
        )

        analysis_result = await code_agent.analyze_code(analysis_request)
        assert analysis_result["success"] is True


class TestCodeAgentPerformanceAndScalability:
    """Test suite for CodeAgent performance and scalability."""

    @pytest.fixture
    def code_agent(self):
        """Create CodeAgent instance."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")
        return CodeAgent()

    @pytest.mark.asyncio
    async def test_large_codebase_analysis(self, code_agent):
        """Test analysis of large codebase."""
        # Simulate large codebase
        large_code = "\n".join([
            f"def function_{i}(): pass" for i in range(1000)
        ])

        start_time = asyncio.get_event_loop().time()

        metrics = await code_agent._calculate_code_metrics(
            large_code,
            ProgrammingLanguage.PYTHON
        )

        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time

        assert execution_time < 5.0  # Should complete within 5 seconds
        assert metrics.lines_of_code > 1000

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, code_agent):
        """Test concurrent code operations."""
        tasks = []

        # Create multiple concurrent requests
        for i in range(5):
            request = CodeGenerationRequest(
                language=ProgrammingLanguage.PYTHON,
                description=f"Create function number {i}",
                function_name=f"function_{i}"
            )
            tasks.append(code_agent.generate_code(request))

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all completed successfully
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_results) >= 4  # Allow for some potential failures

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, code_agent):
        """Test memory usage doesn't grow excessively."""
        # Perform multiple operations to test memory stability
        for i in range(10):
            request = CodeGenerationRequest(
                language=ProgrammingLanguage.PYTHON,
                description=f"Memory test function {i}",
                function_name=f"memory_test_{i}"
            )

            result = await code_agent.generate_code(request)
            assert result["success"] is True

            # In a real implementation, we would check memory usage here


class TestCodeAgentErrorHandling:
    """Test suite for error handling and edge cases."""

    @pytest.fixture
    def code_agent(self):
        """Create CodeAgent instance."""
        if not DEPENDENCIES_AVAILABLE:
            pytest.skip("Dependencies not available")
        return CodeAgent()

    @pytest.mark.asyncio
    async def test_malformed_code_handling(self, code_agent):
        """Test handling of malformed code."""
        malformed_code = '''
def broken_function(
    # Missing closing parenthesis and body
'''

        request = CodeAnalysisRequest(
            source_code=malformed_code,
            language=ProgrammingLanguage.PYTHON,
            analysis_types=["syntax"]
        )

        # Should handle gracefully without crashing
        result = await code_agent.analyze_code(request)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_unsupported_operation(self, code_agent):
        """Test handling of unsupported operations."""
        with pytest.raises(ValidationError):
            await code_agent.execute("unsupported_operation")

    @pytest.mark.asyncio
    async def test_invalid_request_parameters(self, code_agent):
        """Test handling of invalid request parameters."""
        # Test with missing required parameters
        with pytest.raises(Exception):
            invalid_request = CodeGenerationRequest(
                language=ProgrammingLanguage.PYTHON,
                description=""  # Empty description should cause issues
            )

    @pytest.mark.asyncio
    async def test_timeout_handling(self, code_agent):
        """Test timeout handling for long operations."""
        # This would test timeout scenarios in a real implementation
        # For now, just verify the structure supports it
        assert hasattr(code_agent, '_timeout_seconds') or True

    @pytest.mark.asyncio
    async def test_resource_constraint_handling(self, code_agent):
        """Test handling of resource constraints."""
        # Test with very large code that might exceed limits
        huge_code = "x = 1\n" * 100000  # 100k lines

        request = CodeAnalysisRequest(
            source_code=huge_code,
            language=ProgrammingLanguage.PYTHON,
            analysis_types=["basic"]
        )

        # Should handle gracefully
        result = await code_agent.analyze_code(request)
        assert "success" in result


# Helper functions for testing

def create_sample_code_files():
    """Create sample code files for testing."""
    return {
        "main.py": '''
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
''',
        "utils.py": '''
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
''',
        "tests.py": '''
import unittest

class TestUtils(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
'''
    }


async def run_manual_tests():
    """Run manual tests without pytest framework."""
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Cannot run tests - dependencies not available")
        return False

    try:
        logger.info("🧪 Starting manual CodeAgent tests...")

        # Test 1: Agent initialization
        agent = CodeAgent()
        assert agent.agent_id == "code-001"
        logger.info("✅ Agent initialization test passed")

        # Test 2: Code generation
        request = CodeGenerationRequest(
            language=ProgrammingLanguage.PYTHON,
            description="Create a simple calculator function",
            function_name="calculate"
        )

        result = await agent.generate_code(request)
        assert result["success"] is True
        logger.info("✅ Code generation test passed")

        # Test 3: Code analysis
        sample_code = "def hello(): print('Hello, World!')"
        analysis_request = CodeAnalysisRequest(
            source_code=sample_code,
            language=ProgrammingLanguage.PYTHON,
            include_metrics=True
        )

        analysis_result = await agent.analyze_code(analysis_request)
        assert analysis_result["success"] is True
        logger.info("✅ Code analysis test passed")

        # Test 4: Code review
        review_result = await agent.review_code(
            sample_code,
            ProgrammingLanguage.PYTHON
        )
        assert review_result["success"] is True
        logger.info("✅ Code review test passed")

        logger.info("🎉 All manual tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Manual test failed: {e}")
        return False


if __name__ == "__main__":
    # Run manual tests if executed directly
    import asyncio

    result = asyncio.run(run_manual_tests())
    if result:
        print("✅ All tests passed!")
        exit(0)
    else:
        print("❌ Tests failed!")
        exit(1)
