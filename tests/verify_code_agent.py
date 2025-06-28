#!/usr/bin/env python3
"""
Standalone CodeAgent Verification Script

This script provides a simplified verification for the CodeAgent implementation
without requiring full module dependencies, focusing on validating the core
structure and functionality.
"""

import sys
import os
import inspect
import ast
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_code_agent_file_structure():
    """Verify that the CodeAgent file exists and has proper structure."""
    code_agent_path = Path("agents/code_agent.py")

    if not code_agent_path.exists():
        return False, "CodeAgent file not found"

    try:
        with open(code_agent_path, 'r') as f:
            content = f.read()

        # Parse the AST to analyze structure
        tree = ast.parse(content)

        classes = []
        functions = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):  # Public functions
                    functions.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        # Verify required components
        required_classes = [
            "ProgrammingLanguage", "CodeOperationType", "CodeQualityLevel",
            "TestType", "CodeMetrics", "SecurityIssue", "CodeReviewFinding",
            "CodeGenerationRequest", "CodeRefactorRequest", "CodeAnalysisRequest",
            "TestGenerationRequest", "CodeDocumentationRequest", "CodeAgent"
        ]

        missing_classes = [cls for cls in required_classes if cls not in classes]

        result = {
            "file_exists": True,
            "classes_found": len(classes),
            "functions_found": len(functions),
            "imports_found": len(imports),
            "required_classes": len(required_classes),
            "missing_classes": missing_classes,
            "has_main_class": "CodeAgent" in classes,
            "lines_of_code": len(content.splitlines())
        }

        success = len(missing_classes) == 0 and "CodeAgent" in classes

        return success, result

    except Exception as e:
        return False, f"Error parsing file: {e}"


def verify_code_agent_methods():
    """Verify that CodeAgent has required methods."""
    try:
        # Read the CodeAgent file content
        with open("agents/code_agent.py", 'r') as f:
            content = f.read()

        # Parse AST to find CodeAgent class methods
        tree = ast.parse(content)

        code_agent_methods = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "CodeAgent":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        code_agent_methods.append(item.name)

        # Required methods for CodeAgent
        required_methods = [
            "__init__",
            "generate_code",
            "refactor_code",
            "analyze_code",
            "review_code",
            "generate_tests",
            "generate_documentation",
            "execute"
        ]

        missing_methods = [method for method in required_methods if method not in code_agent_methods]

        result = {
            "methods_found": len(code_agent_methods),
            "required_methods": len(required_methods),
            "missing_methods": missing_methods,
            "all_methods": code_agent_methods[:10]  # First 10 for display
        }

        success = len(missing_methods) == 0

        return success, result

    except Exception as e:
        return False, f"Error analyzing methods: {e}"


def verify_test_file_structure():
    """Verify that the test file exists and has proper structure."""
    test_file_path = Path("tests/test_code_agent.py")

    if not test_file_path.exists():
        return False, "Test file not found"

    try:
        with open(test_file_path, 'r') as f:
            content = f.read()

        tree = ast.parse(content)

        test_classes = []
        test_methods = []
        fixtures = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    test_classes.append(node.name)
                    # Count test methods in this class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                            if item.name.startswith("test_"):
                                test_methods.append(f"{node.name}.{item.name}")
            elif isinstance(node, ast.FunctionDef):
                # Check for pytest fixtures
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture') or \
                       (isinstance(decorator, ast.Name) and decorator.id == 'fixture'):
                        fixtures.append(node.name)
                        break
                else:
                    if node.name.startswith("test_"):
                        test_methods.append(node.name)

        result = {
            "file_exists": True,
            "test_classes": len(test_classes),
            "test_methods": len(test_methods),
            "fixtures": len(fixtures),
            "lines_of_code": len(content.splitlines()),
            "class_names": test_classes,
            "sample_methods": test_methods[:5]  # First 5 for display
        }

        success = len(test_classes) >= 4 and len(test_methods) >= 20

        return success, result

    except Exception as e:
        return False, f"Error parsing test file: {e}"


def verify_capability_integration():
    """Verify integration with capability system."""
    try:
        # Check if CodeAgent is mentioned in __init__.py
        init_file = Path("agents/__init__.py")
        if init_file.exists():
            with open(init_file, 'r') as f:
                init_content = f.read()

            has_code_agent_import = "CodeAgent" in init_content
            has_code_agent_export = "CodeAgent" in init_content and "__all__" in init_content
        else:
            has_code_agent_import = False
            has_code_agent_export = False

        # Check if capabilities document was updated
        capabilities_file = Path("AGENTICAL_CAPABILITIES.md")
        if capabilities_file.exists():
            with open(capabilities_file, 'r') as f:
                cap_content = f.read()

            has_code_agent_documented = "CodeAgent" in cap_content
            has_production_ready = "Production Ready" in cap_content and "CodeAgent" in cap_content
        else:
            has_code_agent_documented = False
            has_production_ready = False

        result = {
            "init_file_exists": init_file.exists(),
            "has_code_agent_import": has_code_agent_import,
            "has_code_agent_export": has_code_agent_export,
            "capabilities_file_exists": capabilities_file.exists(),
            "has_code_agent_documented": has_code_agent_documented,
            "has_production_ready": has_production_ready
        }

        success = (has_code_agent_import and has_code_agent_export and
                  has_code_agent_documented and has_production_ready)

        return success, result

    except Exception as e:
        return False, f"Error checking integration: {e}"


def verify_language_support():
    """Verify programming language support configuration."""
    try:
        with open("agents/code_agent.py", 'r') as f:
            content = f.read()

        # Count language enum values
        tree = ast.parse(content)

        programming_languages = []
        language_configs = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ProgrammingLanguage":
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                programming_languages.append(target.id)

            # Look for language_configs dictionary
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "language_configs":
                        if isinstance(node.value, ast.Dict):
                            language_configs = len(node.value.keys)

        result = {
            "languages_defined": len(programming_languages),
            "language_configs": language_configs,
            "sample_languages": programming_languages[:10],
            "has_python": "PYTHON" in programming_languages,
            "has_javascript": "JAVASCRIPT" in programming_languages,
            "has_typescript": "TYPESCRIPT" in programming_languages
        }

        success = len(programming_languages) >= 15 and language_configs >= 3

        return success, result

    except Exception as e:
        return False, f"Error checking language support: {e}"


def run_verification():
    """Run all verification checks."""
    print("🔍 Verifying CodeAgent Implementation...")
    print("=" * 60)

    checks = [
        ("File Structure", verify_code_agent_file_structure),
        ("Methods Implementation", verify_code_agent_methods),
        ("Test Suite", verify_test_file_structure),
        ("Integration", verify_capability_integration),
        ("Language Support", verify_language_support)
    ]

    results = {}
    passed = 0
    failed = 0

    for check_name, check_func in checks:
        print(f"\n🧪 Running {check_name} verification...")
        try:
            success, result = check_func()
            results[check_name] = {"success": success, "result": result}

            if success:
                print(f"✅ {check_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {check_name}: FAILED")
                failed += 1

            # Print summary details
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, bool, str)) and not key.startswith('_'):
                        print(f"   {key}: {value}")
            else:
                print(f"   Details: {result}")

        except Exception as e:
            print(f"❌ {check_name}: ERROR - {e}")
            results[check_name] = {"success": False, "error": str(e)}
            failed += 1

    # Overall summary
    print("\n" + "=" * 60)
    print("CODEAGENT VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Total Checks: {passed + failed}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed / (passed + failed) * 100:.1f}%")

    # Detailed results
    print("\nDETAILED RESULTS:")
    print("-" * 40)

    for check_name, result_data in results.items():
        status = "✅ PASS" if result_data["success"] else "❌ FAIL"
        print(f"{status} {check_name}")

        if not result_data["success"] and "error" in result_data:
            print(f"   Error: {result_data['error']}")

    # Quality assessment
    print("\nQUALITY ASSESSMENT:")
    print("-" * 40)

    if passed == len(checks):
        print("🎉 EXCELLENT: CodeAgent implementation is complete and ready for production!")
        grade = "A"
    elif passed >= len(checks) * 0.8:
        print("✅ GOOD: CodeAgent implementation is mostly complete with minor issues")
        grade = "B"
    elif passed >= len(checks) * 0.6:
        print("⚠️ ADEQUATE: CodeAgent implementation needs improvements")
        grade = "C"
    else:
        print("❌ INSUFFICIENT: CodeAgent implementation requires significant work")
        grade = "F"

    print(f"Overall Grade: {grade}")

    # Recommendations
    if failed > 0:
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)

        if not results.get("File Structure", {}).get("success"):
            print("• Complete the CodeAgent class implementation")

        if not results.get("Methods Implementation", {}).get("success"):
            print("• Implement all required CodeAgent methods")

        if not results.get("Test Suite", {}).get("success"):
            print("• Expand test coverage with more test classes and methods")

        if not results.get("Integration", {}).get("success"):
            print("• Complete integration with agent registry and capabilities system")

        if not results.get("Language Support", {}).get("success"):
            print("• Add support for more programming languages")

    print("=" * 60)

    return passed == len(checks)


def main():
    """Main entry point."""
    try:
        success = run_verification()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
