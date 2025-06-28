#!/usr/bin/env python3
"""
Test Structure Verification for Agent Pool Discovery System

This script verifies that our comprehensive test suite has proper structure,
coverage, and organization without requiring full module dependencies.
It validates the test file structure and completeness.
"""

import ast
import os
import sys
import inspect
from typing import Dict, List, Set, Any
from pathlib import Path

class TestStructureAnalyzer:
    """Analyzes test file structure and coverage."""

    def __init__(self, test_file_path: str):
        self.test_file_path = test_file_path
        self.test_classes = {}
        self.test_methods = {}
        self.fixtures = {}
        self.imports = []
        self.coverage_areas = set()

    def parse_test_file(self) -> Dict[str, Any]:
        """Parse the test file and extract structure information."""
        try:
            with open(self.test_file_path, 'r') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._analyze_test_class(node)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    self._analyze_function(node)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._analyze_import(node)

            return self._generate_analysis_report()

        except Exception as e:
            return {"error": f"Failed to parse test file: {e}"}

    def _analyze_test_class(self, node: ast.ClassDef):
        """Analyze a test class."""
        class_name = node.name
        methods = []
        fixtures = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name
                if method_name.startswith('test_'):
                    methods.append(method_name)
                    # Determine coverage area from method name
                    self._categorize_test_method(method_name)
                elif self._is_fixture(item):
                    fixtures.append(method_name)
            elif isinstance(item, ast.AsyncFunctionDef):
                method_name = item.name
                if method_name.startswith('test_'):
                    methods.append(method_name)
                    # Determine coverage area from method name
                    self._categorize_test_method(method_name)
                elif self._is_fixture(item):
                    fixtures.append(method_name)

        self.test_classes[class_name] = {
            'methods': methods,
            'fixtures': fixtures,
            'method_count': len(methods)
        }

    def _is_fixture(self, node):
        """Check if a function is a pytest fixture."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute):
                if hasattr(decorator, 'attr') and decorator.attr == 'fixture':
                    return True
            elif isinstance(decorator, ast.Name):
                if hasattr(decorator, 'id') and decorator.id == 'fixture':
                    return True
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if hasattr(decorator.func, 'attr') and decorator.func.attr == 'fixture':
                        return True
                elif isinstance(decorator.func, ast.Name):
                    if hasattr(decorator.func, 'id') and decorator.func.id == 'fixture':
                        return True
        return False

    def _analyze_function(self, node):
        """Analyze standalone functions."""
        func_name = node.name

        if self._is_fixture(node):
            self.fixtures[func_name] = {'type': 'standalone'}
        elif func_name.startswith('test_'):
            self.test_methods[func_name] = {'type': 'standalone'}
            self._categorize_test_method(func_name)

    def _analyze_import(self, node):
        """Analyze import statements."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                self.imports.append(f"{module}.{alias.name}")

    def _categorize_test_method(self, method_name: str):
        """Categorize test method by coverage area."""
        method_lower = method_name.lower()

        if 'initialization' in method_lower or 'init' in method_lower:
            self.coverage_areas.add('initialization')
        elif 'registration' in method_lower or 'register' in method_lower:
            self.coverage_areas.add('registration')
        elif 'heartbeat' in method_lower:
            self.coverage_areas.add('heartbeat')
        elif 'load' in method_lower and 'balanc' in method_lower:
            self.coverage_areas.add('load_balancing')
        elif 'load' in method_lower:
            self.coverage_areas.add('load_management')
        elif 'capability' in method_lower or 'capabilit' in method_lower:
            self.coverage_areas.add('capability_matching')
        elif 'filter' in method_lower:
            self.coverage_areas.add('filtering')
        elif 'statistics' in method_lower or 'stats' in method_lower:
            self.coverage_areas.add('statistics')
        elif 'performance' in method_lower or 'perf' in method_lower:
            self.coverage_areas.add('performance')
        elif 'concurrent' in method_lower or 'concurrency' in method_lower:
            self.coverage_areas.add('concurrency')
        elif 'stress' in method_lower:
            self.coverage_areas.add('stress_testing')
        elif 'benchmark' in method_lower:
            self.coverage_areas.add('benchmarking')
        elif 'error' in method_lower or 'exception' in method_lower:
            self.coverage_areas.add('error_handling')
        elif 'integration' in method_lower:
            self.coverage_areas.add('integration')
        elif 'api' in method_lower or 'endpoint' in method_lower:
            self.coverage_areas.add('api_testing')
        elif 'discovery' in method_lower or 'discover' in method_lower:
            self.coverage_areas.add('discovery')
        elif 'health' in method_lower:
            self.coverage_areas.add('health_monitoring')
        elif 'cache' in method_lower:
            self.coverage_areas.add('caching')
        elif 'algorithm' in method_lower:
            self.coverage_areas.add('algorithms')
        elif 'matching' in method_lower or 'match' in method_lower:
            self.coverage_areas.add('matching')
        elif 'workflow' in method_lower:
            self.coverage_areas.add('workflow')
        elif 'lifecycle' in method_lower:
            self.coverage_areas.add('lifecycle')
        elif 'edge' in method_lower or 'boundary' in method_lower:
            self.coverage_areas.add('edge_cases')
        else:
            self.coverage_areas.add('general')

    def _generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        total_test_methods = sum(
            len(cls_info['methods']) for cls_info in self.test_classes.values()
        ) + len(self.test_methods)

        total_fixtures = len(self.fixtures) + sum(
            len(cls_info['fixtures']) for cls_info in self.test_classes.values()
        )

        # Expected coverage areas for comprehensive testing
        expected_areas = {
            'initialization', 'registration', 'heartbeat', 'load_balancing',
            'load_management', 'capability_matching', 'filtering', 'statistics',
            'performance', 'concurrency', 'stress_testing', 'benchmarking',
            'error_handling', 'integration', 'api_testing', 'discovery',
            'health_monitoring', 'caching', 'algorithms', 'matching',
            'workflow', 'lifecycle', 'edge_cases'
        }

        missing_areas = expected_areas - self.coverage_areas

        return {
            'file_path': self.test_file_path,
            'summary': {
                'test_classes': len(self.test_classes),
                'total_test_methods': total_test_methods,
                'total_fixtures': total_fixtures,
                'coverage_areas': len(self.coverage_areas),
                'imports': len(self.imports)
            },
            'test_classes': self.test_classes,
            'standalone_tests': self.test_methods,
            'fixtures': self.fixtures,
            'coverage_areas': sorted(list(self.coverage_areas)),
            'missing_coverage': sorted(list(missing_areas)),
            'imports': self.imports[:10],  # First 10 imports for brevity
            'quality_score': self._calculate_quality_score(total_test_methods, missing_areas)
        }

    def _calculate_quality_score(self, total_tests: int, missing_areas: Set[str]) -> Dict[str, Any]:
        """Calculate test suite quality score."""
        # Base scoring
        test_coverage_score = min(100, (total_tests / 50) * 100)  # 50+ tests = 100%
        area_coverage_score = ((23 - len(missing_areas)) / 23) * 100  # 23 expected areas

        # Bonus points
        fixture_bonus = min(10, len(self.fixtures) / 2)  # Up to 10 bonus points for fixtures
        class_organization_bonus = min(10, len(self.test_classes) * 2)  # Up to 10 for organization

        overall_score = (test_coverage_score * 0.4 +
                        area_coverage_score * 0.4 +
                        fixture_bonus * 0.1 +
                        class_organization_bonus * 0.1)

        return {
            'overall_score': round(overall_score, 1),
            'test_coverage': round(test_coverage_score, 1),
            'area_coverage': round(area_coverage_score, 1),
            'fixture_bonus': round(fixture_bonus, 1),
            'organization_bonus': round(class_organization_bonus, 1),
            'grade': self._get_grade(overall_score)
        }

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

def verify_test_structure():
    """Main verification function."""
    print("🔍 Verifying Agent Pool Discovery Test Structure...")
    print("=" * 60)

    # Find test file
    test_file = "tests/test_agent_pool_discovery.py"

    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False

    # Analyze test structure
    analyzer = TestStructureAnalyzer(test_file)
    analysis = analyzer.parse_test_file()

    if 'error' in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return False

    # Print analysis results
    summary = analysis['summary']
    quality = analysis['quality_score']

    print(f"📋 TEST SUITE ANALYSIS")
    print("-" * 40)
    print(f"Test Classes: {summary['test_classes']}")
    print(f"Test Methods: {summary['total_test_methods']}")
    print(f"Fixtures: {summary['total_fixtures']}")
    print(f"Coverage Areas: {summary['coverage_areas']}")
    print(f"Imports: {summary['imports']}")

    print(f"\n📊 QUALITY METRICS")
    print("-" * 40)
    print(f"Overall Score: {quality['overall_score']}/100 (Grade: {quality['grade']})")
    print(f"Test Coverage: {quality['test_coverage']}/100")
    print(f"Area Coverage: {quality['area_coverage']}/100")
    print(f"Organization: {quality['organization_bonus']}/10")
    print(f"Fixture Usage: {quality['fixture_bonus']}/10")

    print(f"\n🎯 TEST CLASSES")
    print("-" * 40)
    for class_name, class_info in analysis['test_classes'].items():
        print(f"  {class_name}: {class_info['method_count']} tests")

    print(f"\n🏷️  COVERAGE AREAS")
    print("-" * 40)
    for area in analysis['coverage_areas']:
        print(f"  ✅ {area.replace('_', ' ').title()}")

    if analysis['missing_coverage']:
        print(f"\n⚠️  MISSING COVERAGE")
        print("-" * 40)
        for area in analysis['missing_coverage']:
            print(f"  ❌ {area.replace('_', ' ').title()}")

    print(f"\n🧪 SAMPLE TEST METHODS")
    print("-" * 40)
    method_count = 0
    for class_name, class_info in analysis['test_classes'].items():
        for method in class_info['methods'][:3]:  # Show first 3 methods per class
            print(f"  {class_name}.{method}")
            method_count += 1
            if method_count >= 10:  # Limit output
                break
        if method_count >= 10:
            break

    # Comprehensive test requirements check
    required_classes = {
        'TestAgentPoolDiscovery': 'Core discovery functionality',
        'TestCapabilityMatcher': 'Capability matching algorithms',
        'TestAgentPoolAPI': 'API endpoint testing',
        'TestIntegrationScenarios': 'Integration test scenarios'
    }

    print(f"\n✅ REQUIRED TEST CLASSES")
    print("-" * 40)
    all_required_present = True
    for req_class, description in required_classes.items():
        if req_class in analysis['test_classes']:
            method_count = analysis['test_classes'][req_class]['method_count']
            print(f"  ✅ {req_class}: {method_count} tests - {description}")
        else:
            print(f"  ❌ {req_class}: Missing - {description}")
            all_required_present = False

    # Final assessment
    print(f"\n📈 ASSESSMENT")
    print("=" * 60)

    if quality['overall_score'] >= 85 and all_required_present:
        print("🎉 EXCELLENT: Comprehensive test suite with excellent coverage!")
        result = True
    elif quality['overall_score'] >= 70 and all_required_present:
        print("✅ GOOD: Well-structured test suite with good coverage")
        result = True
    elif quality['overall_score'] >= 60:
        print("⚠️ ADEQUATE: Test suite needs improvement in some areas")
        result = True
    else:
        print("❌ INSUFFICIENT: Test suite requires significant improvements")
        result = False

    # Recommendations
    if analysis['missing_coverage']:
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        print("Consider adding tests for these areas:")
        for area in analysis['missing_coverage'][:5]:  # Top 5 missing areas
            print(f"  • {area.replace('_', ' ').title()}")

    if summary['total_fixtures'] < 10:
        print("  • Add more test fixtures for better test organization")

    if summary['total_test_methods'] < 30:
        print("  • Expand test coverage with more test methods")

    print("=" * 60)
    return result

def main():
    """Main entry point."""
    try:
        success = verify_test_structure()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
