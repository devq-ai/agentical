#!/usr/bin/env python3
"""
Agentical Agent Infrastructure Integration Test

This test validates the complete integration of our agent orchestration layer
with existing DevQ.ai infrastructure:

1. Infrastructure connectivity (Ptolemies, MCP servers, SurrealDB)
2. Agent initialization and execution
3. SuperAgent coordination capabilities
4. Knowledge base integration
5. Tool coordination via MCP servers

Run this test to validate that the Agentical orchestration layer is properly
integrated with the production-ready infrastructure.
"""

import asyncio
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the agentical package to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our agent infrastructure
try:
    from agentical.agents.base_agent import (
        BaseAgent, 
        AgentMetadata, 
        AgentCapability, 
        agent_registry,
        AgentStatus
    )
    from agentical.agents.super_agent import SuperAgent
except ImportError as e:
    logger.error(f"Failed to import agent modules: {e}")
    sys.exit(1)


class TestAgent(BaseAgent):
    """Simple test agent for validation"""
    
    def __init__(self, agent_id: str = "test_agent"):
        capabilities = [
            AgentCapability(
                name="test_operation",
                description="Simple test operation for validation",
                required_tools=["memory", "filesystem"],
                knowledge_domains=["testing"]
            )
        ]
        
        metadata = AgentMetadata(
            id=agent_id,
            name="Test Agent",
            description="Simple agent for testing infrastructure integration",
            capabilities=capabilities,
            available_tools=["memory", "filesystem", "git"],
            system_prompts=["You are a test agent for validation purposes."],
            tags=["test", "validation"]
        )
        
        super().__init__(metadata)
    
    async def _execute_operation(self, context) -> Dict[str, Any]:
        """Execute test operation"""
        operation = context.operation
        
        if operation == "test_operation":
            return {
                "status": "success",
                "message": "Test operation completed successfully",
                "infrastructure_available": {
                    "ptolemies": self.infrastructure.ptolemies_available,
                    "mcp_servers": len(self.infrastructure.mcp_servers.get("mcp_servers", {})) if self.infrastructure.mcp_servers else 0
                },
                "context_received": {
                    "knowledge_context": bool(context.knowledge_context),
                    "parameters": context.parameters
                }
            }
        else:
            return {"error": f"Unknown operation: {operation}"}


class AgentIntegrationTester:
    """Comprehensive integration tester for agent infrastructure"""
    
    def __init__(self):
        self.test_results = {}
        self.super_agent = None
        self.test_agent = None
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete integration test suite"""
        logger.info("🚀 Starting Agentical Agent Infrastructure Integration Tests")
        logger.info("=" * 80)
        
        # Test 1: Infrastructure Discovery
        self.test_results["infrastructure_discovery"] = await self.test_infrastructure_discovery()
        
        # Test 2: Agent Registry
        self.test_results["agent_registry"] = await self.test_agent_registry()
        
        # Test 3: Base Agent Functionality
        self.test_results["base_agent"] = await self.test_base_agent_functionality()
        
        # Test 4: SuperAgent Initialization
        self.test_results["super_agent_init"] = await self.test_super_agent_initialization()
        
        # Test 5: SuperAgent Operations
        self.test_results["super_agent_operations"] = await self.test_super_agent_operations()
        
        # Test 6: Knowledge Integration
        self.test_results["knowledge_integration"] = await self.test_knowledge_integration()
        
        # Test 7: Tool Coordination
        self.test_results["tool_coordination"] = await self.test_tool_coordination()
        
        # Test 8: Multi-Agent Coordination
        self.test_results["multi_agent_coordination"] = await self.test_multi_agent_coordination()
        
        # Generate overall assessment
        self.test_results["overall_assessment"] = self.generate_overall_assessment()
        
        return self.test_results
    
    async def test_infrastructure_discovery(self) -> Dict[str, Any]:
        """Test infrastructure discovery and connectivity"""
        logger.info("🔍 Testing Infrastructure Discovery...")
        
        test_result = {
            "test_name": "Infrastructure Discovery",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test agent can discover infrastructure
            test_agent = TestAgent("infra_test_agent")
            
            infrastructure = test_agent.infrastructure
            
            test_result["details"] = {
                "ptolemies_available": infrastructure.ptolemies_available,
                "ptolemies_path": infrastructure.ptolemies_path,
                "mcp_servers_loaded": bool(infrastructure.mcp_servers),
                "mcp_server_count": len(infrastructure.mcp_servers.get("mcp_servers", {})) if infrastructure.mcp_servers else 0,
                "surrealdb_configured": bool(infrastructure.surrealdb_config.get("url"))
            }
            
            # Assess infrastructure readiness
            if (infrastructure.ptolemies_available and 
                infrastructure.mcp_servers and 
                len(infrastructure.mcp_servers.get("mcp_servers", {})) > 10):
                test_result["status"] = "success"
            else:
                test_result["status"] = "partial"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ Infrastructure Discovery: {test_result['status']}")
        return test_result
    
    async def test_agent_registry(self) -> Dict[str, Any]:
        """Test agent registry functionality"""
        logger.info("🔍 Testing Agent Registry...")
        
        test_result = {
            "test_name": "Agent Registry",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test agent registration
            test_agent = TestAgent("registry_test_agent")
            
            # Check if SuperAgent is already registered
            super_agent = agent_registry.get_agent("super_agent")
            
            # Test agent listing
            agents_list = agent_registry.list_agents()
            
            test_result["details"] = {
                "super_agent_registered": bool(super_agent),
                "test_agent_created": bool(test_agent),
                "total_agents_listed": len(agents_list),
                "agent_types_available": len(agent_registry.agent_types)
            }
            
            if super_agent and len(agents_list) > 0:
                test_result["status"] = "success"
            else:
                test_result["status"] = "partial"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ Agent Registry: {test_result['status']}")
        return test_result
    
    async def test_base_agent_functionality(self) -> Dict[str, Any]:
        """Test base agent functionality"""
        logger.info("🔍 Testing Base Agent Functionality...")
        
        test_result = {
            "test_name": "Base Agent Functionality",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Create and test a base agent
            self.test_agent = TestAgent("functionality_test_agent")
            
            # Test agent status
            status = await self.test_agent.get_status()
            
            # Test agent execution
            execution_result = await self.test_agent.execute(
                "test_operation", 
                {"test_param": "test_value"}
            )
            
            # Test capabilities
            capabilities = await self.test_agent.get_capabilities()
            
            test_result["details"] = {
                "agent_status": status,
                "execution_success": execution_result.success,
                "execution_time": execution_result.execution_time,
                "capabilities_count": len(capabilities),
                "infrastructure_integration": execution_result.result.get("infrastructure_available", {}),
                "knowledge_queries": execution_result.knowledge_queries
            }
            
            if execution_result.success and len(capabilities) > 0:
                test_result["status"] = "success"
            else:
                test_result["status"] = "partial"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ Base Agent Functionality: {test_result['status']}")
        return test_result
    
    async def test_super_agent_initialization(self) -> Dict[str, Any]:
        """Test SuperAgent initialization"""
        logger.info("🔍 Testing SuperAgent Initialization...")
        
        test_result = {
            "test_name": "SuperAgent Initialization",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Get or create SuperAgent
            self.super_agent = agent_registry.get_agent("super_agent")
            
            if not self.super_agent:
                self.super_agent = SuperAgent()
                agent_registry.register_agent(self.super_agent)
            
            # Test SuperAgent properties
            status = await self.super_agent.get_status()
            capabilities = await self.super_agent.get_capabilities()
            
            test_result["details"] = {
                "super_agent_found": bool(self.super_agent),
                "agent_id": self.super_agent.metadata.id,
                "capabilities_count": len(capabilities),
                "available_tools_count": len(self.super_agent.metadata.available_tools),
                "status": status,
                "infrastructure_ready": status.get("infrastructure", {})
            }
            
            if self.super_agent and len(capabilities) >= 5:
                test_result["status"] = "success"
            else:
                test_result["status"] = "partial"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ SuperAgent Initialization: {test_result['status']}")
        return test_result
    
    async def test_super_agent_operations(self) -> Dict[str, Any]:
        """Test SuperAgent operations"""
        logger.info("🔍 Testing SuperAgent Operations...")
        
        test_result = {
            "test_name": "SuperAgent Operations",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.super_agent:
                self.super_agent = agent_registry.get_agent("super_agent")
            
            operations_to_test = [
                ("intelligent_routing", {"request": "Test routing request"}),
                ("knowledge_synthesis", {"query": "Test knowledge query"}),
                ("multimodal_coordination", {"request_type": "test", "components": []}),
                ("general_request", {"request": "Test general request"})
            ]
            
            operation_results = {}
            
            for operation, params in operations_to_test:
                try:
                    result = await self.super_agent.execute(operation, params)
                    operation_results[operation] = {
                        "success": result.success,
                        "execution_time": result.execution_time,
                        "result_type": type(result.result).__name__
                    }
                except Exception as e:
                    operation_results[operation] = {"error": str(e)}
            
            test_result["details"] = {
                "operations_tested": len(operations_to_test),
                "operation_results": operation_results,
                "successful_operations": sum(1 for r in operation_results.values() if r.get("success", False))
            }
            
            successful_count = test_result["details"]["successful_operations"]
            if successful_count >= len(operations_to_test) * 0.75:  # 75% success rate
                test_result["status"] = "success"
            elif successful_count > 0:
                test_result["status"] = "partial"
            else:
                test_result["status"] = "error"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ SuperAgent Operations: {test_result['status']}")
        return test_result
    
    async def test_knowledge_integration(self) -> Dict[str, Any]:
        """Test knowledge base integration"""
        logger.info("🔍 Testing Knowledge Integration...")
        
        test_result = {
            "test_name": "Knowledge Integration",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.super_agent:
                self.super_agent = agent_registry.get_agent("super_agent")
            
            # Test knowledge synthesis
            knowledge_result = await self.super_agent.execute(
                "knowledge_synthesis",
                {
                    "query": "FastAPI development best practices",
                    "synthesis_type": "summary"
                }
            )
            
            test_result["details"] = {
                "knowledge_synthesis_success": knowledge_result.success,
                "ptolemies_available": knowledge_result.result.get("knowledge_base_status") == "production_ready",
                "documents_available": knowledge_result.result.get("documents_available", 0),
                "synthesis_result": knowledge_result.result.get("synthesis_placeholder", {}),
                "infrastructure_integration": knowledge_result.result.get("infrastructure_integration", {})
            }
            
            if (knowledge_result.success and 
                test_result["details"]["documents_available"] == 597):
                test_result["status"] = "success"
            else:
                test_result["status"] = "partial"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ Knowledge Integration: {test_result['status']}")
        return test_result
    
    async def test_tool_coordination(self) -> Dict[str, Any]:
        """Test MCP tool coordination"""
        logger.info("🔍 Testing Tool Coordination...")
        
        test_result = {
            "test_name": "Tool Coordination",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.super_agent:
                self.super_agent = agent_registry.get_agent("super_agent")
            
            # Test multimodal coordination which uses multiple tools
            coordination_result = await self.super_agent.execute(
                "multimodal_coordination",
                {
                    "request_type": "development_workflow",
                    "components": ["code", "git", "documentation"]
                }
            )
            
            test_result["details"] = {
                "coordination_success": coordination_result.success,
                "tool_coordination": coordination_result.result.get("tool_coordination", {}),
                "mcp_servers_available": coordination_result.result.get("infrastructure_status", {}).get("mcp_servers_available", 0),
                "coordination_ready": coordination_result.result.get("infrastructure_status", {}).get("coordination_ready", False)
            }
            
            if (coordination_result.success and 
                test_result["details"]["mcp_servers_available"] > 10):
                test_result["status"] = "success"
            else:
                test_result["status"] = "partial"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ Tool Coordination: {test_result['status']}")
        return test_result
    
    async def test_multi_agent_coordination(self) -> Dict[str, Any]:
        """Test multi-agent coordination"""
        logger.info("🔍 Testing Multi-Agent Coordination...")
        
        test_result = {
            "test_name": "Multi-Agent Coordination",
            "status": "unknown",
            "details": {}
        }
        
        try:
            if not self.super_agent:
                self.super_agent = agent_registry.get_agent("super_agent")
            
            # Register test agent if not already done
            if not self.test_agent:
                self.test_agent = TestAgent("coordination_test_agent")
                agent_registry.register_agent(self.test_agent)
            
            # Test agent coordination
            coordination_result = await self.super_agent.execute(
                "coordinate_agents",
                {
                    "workflow_type": "sequential",
                    "agents": ["test_agent", "super_agent"],
                    "coordination_strategy": "test"
                }
            )
            
            test_result["details"] = {
                "coordination_success": coordination_result.success,
                "workflow_type": coordination_result.result.get("workflow_type"),
                "agents_coordinated": coordination_result.result.get("agents_coordinated", 0),
                "coordination_results": coordination_result.result.get("results", {}),
                "infrastructure_used": coordination_result.result.get("infrastructure_used", {})
            }
            
            if coordination_result.success:
                test_result["status"] = "success"
            else:
                test_result["status"] = "partial"
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
        
        logger.info(f"✅ Multi-Agent Coordination: {test_result['status']}")
        return test_result
    
    def generate_overall_assessment(self) -> Dict[str, Any]:
        """Generate overall assessment of integration tests"""
        logger.info("🔍 Generating Overall Assessment...")
        
        test_statuses = []
        success_count = 0
        partial_count = 0
        error_count = 0
        
        for test_name, result in self.test_results.items():
            if test_name == "overall_assessment":
                continue
                
            status = result.get("status", "unknown")
            test_statuses.append(status)
            
            if status == "success":
                success_count += 1
            elif status == "partial":
                partial_count += 1
            elif status == "error":
                error_count += 1
        
        total_tests = len(test_statuses)
        success_rate = success_count / total_tests if total_tests > 0 else 0
        
        # Determine overall status
        if success_rate >= 0.9:
            overall_status = "excellent"
        elif success_rate >= 0.75:
            overall_status = "good"
        elif success_rate >= 0.5:
            overall_status = "acceptable"
        else:
            overall_status = "needs_improvement"
        
        assessment = {
            "overall_status": overall_status,
            "total_tests": total_tests,
            "success_count": success_count,
            "partial_count": partial_count,
            "error_count": error_count,
            "success_rate": round(success_rate * 100, 2),
            "integration_readiness": success_rate >= 0.75,
            "recommendations": self.generate_recommendations(success_rate, test_statuses)
        }
        
        return assessment
    
    def generate_recommendations(self, success_rate: float, test_statuses: List[str]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if success_rate >= 0.9:
            recommendations.append("🎉 Excellent integration! Ready for production development.")
            recommendations.append("✅ All infrastructure components working optimally.")
            recommendations.append("🚀 Proceed with advanced agent development and workflows.")
        elif success_rate >= 0.75:
            recommendations.append("✅ Good integration status. Minor optimizations needed.")
            recommendations.append("🔧 Review partial test results for improvement opportunities.")
            recommendations.append("🚀 Ready for development with monitoring.")
        elif success_rate >= 0.5:
            recommendations.append("⚠️ Acceptable integration but improvements needed.")
            recommendations.append("🔧 Address failed tests before proceeding to complex workflows.")
            recommendations.append("📊 Monitor infrastructure stability during development.")
        else:
            recommendations.append("❌ Integration needs significant improvement.")
            recommendations.append("🔧 Address infrastructure connectivity issues.")
            recommendations.append("📋 Review configuration and setup requirements.")
        
        # Specific recommendations based on test results
        if "error" in test_statuses:
            recommendations.append("🐛 Debug error conditions in failed tests.")
        
        if test_statuses.count("partial") > 2:
            recommendations.append("🔧 Optimize partial test results for better performance.")
        
        return recommendations
    
    def print_test_results(self):
        """Print formatted test results"""
        print("\n" + "=" * 80)
        print("🎯 AGENTICAL AGENT INFRASTRUCTURE INTEGRATION TEST RESULTS")
        print("=" * 80)
        
        for test_name, result in self.test_results.items():
            if test_name == "overall_assessment":
                continue
                
            print(f"\n📋 {result['test_name']}")
            print("-" * 50)
            status = result['status'].upper()
            status_icon = "✅" if status == "SUCCESS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"Status: {status_icon} {status}")
            
            # Print key details
            details = result.get("details", {})
            for key, value in details.items():
                if isinstance(value, dict):
                    print(f"  {key}: {len(value)} items" if value else f"  {key}: empty")
                elif isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                else:
                    print(f"  {key}: {value}")
            
            if "error" in result:
                print(f"  ERROR: {result['error']}")
        
        # Print overall assessment
        assessment = self.test_results.get("overall_assessment", {})
        print(f"\n🎯 OVERALL ASSESSMENT")
        print("-" * 50)
        
        overall_status = assessment.get("overall_status", "unknown").upper()
        status_icons = {
            "EXCELLENT": "🌟",
            "GOOD": "✅", 
            "ACCEPTABLE": "⚠️",
            "NEEDS_IMPROVEMENT": "❌"
        }
        status_icon = status_icons.get(overall_status, "❓")
        
        print(f"Integration Status: {status_icon} {overall_status}")
        print(f"Success Rate: {assessment.get('success_rate', 0)}%")
        print(f"Tests Passed: {assessment.get('success_count', 0)}/{assessment.get('total_tests', 0)}")
        print(f"Ready for Development: {'✅ YES' if assessment.get('integration_readiness', False) else '❌ NO'}")
        
        recommendations = assessment.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("\n" + "=" * 80)


async def main():
    """Main test execution function"""
    tester = AgentIntegrationTester()
    
    try:
        # Run all integration tests
        results = await tester.run_all_tests()
        
        # Print results
        tester.print_test_results()
        
        # Return appropriate exit code
        assessment = results.get("overall_assessment", {})
        if assessment.get("integration_readiness", False):
            print("\n🚀 Integration tests passed! Agentical orchestration layer ready for development.")
            return 0
        else:
            print("\n⚠️ Integration tests indicate improvements needed before full development.")
            return 1
            
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        print(f"\n❌ Integration test suite failed: {e}")
        return 2


if __name__ == "__main__":
    # Run integration tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)