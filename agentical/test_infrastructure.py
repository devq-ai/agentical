#!/usr/bin/env python3
"""
Agentical Infrastructure Discovery and Testing Script

This script tests connections to existing DevQ.ai infrastructure:
- Ptolemies Knowledge Base (597 production documents)
- MCP Server Ecosystem (22+ operational servers)
- SurrealDB configuration

Run this to validate infrastructure before building the orchestration layer.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import httpx
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class InfrastructureDiscovery:
    """Discover and test existing DevQ.ai infrastructure"""
    
    def __init__(self):
        self.results = {}
        self.project_root = self._find_project_root()
        logger.info(f"Project root detected: {self.project_root}")
        
    def _find_project_root(self) -> Path:
        """Find the DevQ.ai project root directory"""
        current = Path(__file__).parent
        
        # Look for devqai directory
        while current.parent != current:
            if (current / "ptolemies").exists() and (current / "mcp").exists():
                return current
            if current.name == "devqai":
                return current
            current = current.parent
            
        # Fallback to current directory
        return Path(__file__).parent
    
    async def discover_ptolemies(self) -> Dict[str, Any]:
        """Discover and test Ptolemies knowledge base"""
        logger.info("🔍 Discovering Ptolemies Knowledge Base...")
        
        result = {
            "name": "Ptolemies Knowledge Base",
            "status": "unknown",
            "details": {}
        }
        
        # Check for Ptolemies directory
        ptolemies_path = self.project_root / "ptolemies"
        if ptolemies_path.exists():
            result["details"]["path"] = str(ptolemies_path)
            result["details"]["path_exists"] = True
            
            # Check README for status
            readme_path = ptolemies_path / "README.md"
            if readme_path.exists():
                try:
                    readme_content = readme_path.read_text()
                    if "597 high-quality documents" in readme_content:
                        result["details"]["documents"] = 597
                        result["details"]["production_ready"] = True
                        result["status"] = "production_ready"
                    
                    if "PRODUCTION READY - COMPLETE" in readme_content:
                        result["details"]["crawling_complete"] = True
                        
                except Exception as e:
                    result["details"]["readme_error"] = str(e)
            
            # Check for source code structure
            src_path = ptolemies_path / "src" / "ptolemies"
            if src_path.exists():
                result["details"]["source_available"] = True
                
                # Check for MCP server
                mcp_path = src_path / "mcp"
                if mcp_path.exists():
                    result["details"]["mcp_server_available"] = True
                    
                # Check for database client
                db_path = src_path / "db"
                if db_path.exists():
                    result["details"]["database_client_available"] = True
            
            # Check for production scripts
            if (ptolemies_path / "production_crawl.py").exists():
                result["details"]["production_scripts"] = True
            
            # Check for environment file
            if (ptolemies_path / ".env").exists():
                result["details"]["environment_configured"] = True
                
            if result["status"] == "unknown" and result["details"].get("path_exists"):
                result["status"] = "accessible"
                
        else:
            result["status"] = "not_found"
            result["details"]["searched_path"] = str(ptolemies_path)
            
        logger.info(f"✅ Ptolemies Status: {result['status']}")
        return result
    
    async def discover_mcp_servers(self) -> Dict[str, Any]:
        """Discover and test MCP server ecosystem"""
        logger.info("🔍 Discovering MCP Server Ecosystem...")
        
        result = {
            "name": "MCP Server Ecosystem",
            "status": "unknown",
            "details": {}
        }
        
        # Check for MCP directory
        mcp_path = self.project_root / "mcp"
        if mcp_path.exists():
            result["details"]["path"] = str(mcp_path)
            result["details"]["path_exists"] = True
            
            # Load MCP servers configuration
            config_path = mcp_path / "mcp-servers.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        
                    servers = config.get("mcp_servers", {})
                    result["details"]["config_loaded"] = True
                    result["details"]["total_servers"] = len(servers)
                    result["details"]["server_list"] = list(servers.keys())
                    
                    # Check for key servers
                    key_servers = [
                        "ptolemies-mcp", "surrealdb-mcp", "bayes-mcp", 
                        "darwin-mcp", "filesystem", "git", "memory",
                        "fetch", "sequentialthinking", "github-mcp"
                    ]
                    
                    available_key_servers = [s for s in key_servers if s in servers]
                    result["details"]["key_servers_available"] = len(available_key_servers)
                    result["details"]["key_servers"] = available_key_servers
                    
                    if len(servers) > 0:
                        result["status"] = "configured"
                        
                except Exception as e:
                    result["details"]["config_error"] = str(e)
                    result["status"] = "error"
            else:
                result["details"]["config_missing"] = True
                
            # Check for server directories
            servers_path = mcp_path / "mcp-servers"
            if servers_path.exists():
                result["details"]["server_implementations"] = True
                
        else:
            result["status"] = "not_found"
            result["details"]["searched_path"] = str(mcp_path)
            
        logger.info(f"✅ MCP Servers Status: {result['status']} ({result['details'].get('total_servers', 0)} servers)")
        return result
    
    async def test_surrealdb_config(self) -> Dict[str, Any]:
        """Test SurrealDB configuration"""
        logger.info("🔍 Testing SurrealDB Configuration...")
        
        result = {
            "name": "SurrealDB Configuration",
            "status": "unknown",
            "details": {}
        }
        
        # Check environment variables
        surrealdb_vars = {
            "SURREALDB_URL": os.getenv("SURREALDB_URL"),
            "SURREALDB_USERNAME": os.getenv("SURREALDB_USERNAME"),
            "SURREALDB_PASSWORD": os.getenv("SURREALDB_PASSWORD"),
            "SURREALDB_NAMESPACE": os.getenv("SURREALDB_NAMESPACE"),
            "SURREALDB_DATABASE": os.getenv("SURREALDB_DATABASE")
        }
        
        configured_vars = {k: v for k, v in surrealdb_vars.items() if v is not None}
        result["details"]["environment_variables"] = configured_vars
        result["details"]["configured_vars_count"] = len(configured_vars)
        
        if len(configured_vars) >= 3:  # URL, username, password minimum
            result["status"] = "configured"
        elif len(configured_vars) > 0:
            result["status"] = "partial"
        else:
            result["status"] = "not_configured"
            
        logger.info(f"✅ SurrealDB Status: {result['status']} ({len(configured_vars)} vars configured)")
        return result
    
    async def test_api_connectivity(self) -> Dict[str, Any]:
        """Test API connectivity to services"""
        logger.info("🔍 Testing API Connectivity...")
        
        result = {
            "name": "API Connectivity",
            "status": "unknown",
            "details": {}
        }
        
        # Test common service ports
        test_urls = {
            "SurrealDB": "http://localhost:8000",
            "Ptolemies API": "http://localhost:8001",
            "Alternative SurrealDB": "http://localhost:8080"
        }
        
        connectivity_results = {}
        
        async with httpx.AsyncClient(timeout=2.0) as client:
            for service, url in test_urls.items():
                try:
                    response = await client.get(url)
                    connectivity_results[service] = {
                        "url": url,
                        "status_code": response.status_code,
                        "accessible": True
                    }
                except httpx.RequestError as e:
                    connectivity_results[service] = {
                        "url": url,
                        "error": str(e),
                        "accessible": False
                    }
        
        result["details"]["connectivity_tests"] = connectivity_results
        accessible_services = [s for s, r in connectivity_results.items() if r["accessible"]]
        result["details"]["accessible_services"] = accessible_services
        
        if len(accessible_services) > 0:
            result["status"] = "partial"
        else:
            result["status"] = "no_connectivity"
            
        logger.info(f"✅ API Connectivity: {len(accessible_services)}/{len(test_urls)} services accessible")
        return result
    
    async def run_full_discovery(self) -> Dict[str, Any]:
        """Run complete infrastructure discovery"""
        logger.info("🚀 Starting Agentical Infrastructure Discovery")
        logger.info("=" * 60)
        
        # Run all discovery tasks
        self.results["ptolemies"] = await self.discover_ptolemies()
        self.results["mcp_servers"] = await self.discover_mcp_servers()
        self.results["surrealdb"] = await self.test_surrealdb_config()
        self.results["api_connectivity"] = await self.test_api_connectivity()
        
        # Overall assessment
        self.results["summary"] = self._generate_summary()
        
        return self.results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate overall infrastructure summary"""
        summary = {
            "overall_status": "unknown",
            "ready_for_development": False,
            "critical_components": {},
            "recommendations": []
        }
        
        # Assess critical components
        critical_status = {}
        
        # Ptolemies assessment
        ptolemies_status = self.results["ptolemies"]["status"]
        critical_status["ptolemies"] = ptolemies_status in ["production_ready", "accessible"]
        
        # MCP servers assessment
        mcp_status = self.results["mcp_servers"]["status"]
        mcp_count = self.results["mcp_servers"]["details"].get("total_servers", 0)
        critical_status["mcp_servers"] = mcp_status == "configured" and mcp_count > 10
        
        # SurrealDB assessment
        surrealdb_status = self.results["surrealdb"]["status"]
        critical_status["surrealdb"] = surrealdb_status in ["configured", "partial"]
        
        summary["critical_components"] = critical_status
        
        # Overall status
        if all(critical_status.values()):
            summary["overall_status"] = "ready"
            summary["ready_for_development"] = True
        elif any(critical_status.values()):
            summary["overall_status"] = "partial"
        else:
            summary["overall_status"] = "not_ready"
            
        # Generate recommendations
        if not critical_status["ptolemies"]:
            summary["recommendations"].append("Ensure Ptolemies knowledge base is accessible")
            
        if not critical_status["mcp_servers"]:
            summary["recommendations"].append("Verify MCP server configuration and availability")
            
        if not critical_status["surrealdb"]:
            summary["recommendations"].append("Configure SurrealDB environment variables")
            
        if summary["ready_for_development"]:
            summary["recommendations"].append("✅ Ready to begin Agentical development!")
            
        return summary
    
    def print_results(self):
        """Print formatted discovery results"""
        print("\n" + "=" * 80)
        print("🎯 AGENTICAL INFRASTRUCTURE DISCOVERY RESULTS")
        print("=" * 80)
        
        for component_name, component_data in self.results.items():
            if component_name == "summary":
                continue
                
            print(f"\n📋 {component_data['name']}")
            print("-" * 50)
            print(f"Status: {component_data['status'].upper()}")
            
            # Print key details
            details = component_data.get("details", {})
            for key, value in details.items():
                if isinstance(value, (list, dict)):
                    print(f"  {key}: {len(value) if isinstance(value, list) else 'configured'}")
                else:
                    print(f"  {key}: {value}")
        
        # Print summary
        print(f"\n🎯 OVERALL ASSESSMENT")
        print("-" * 50)
        summary = self.results["summary"]
        print(f"Status: {summary['overall_status'].upper()}")
        print(f"Ready for Development: {'✅ YES' if summary['ready_for_development'] else '❌ NO'}")
        
        print(f"\n📊 Critical Components:")
        for component, status in summary["critical_components"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}")
        
        if summary["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"  • {rec}")
        
        print("\n" + "=" * 80)


async def main():
    """Main discovery function"""
    discovery = InfrastructureDiscovery()
    
    try:
        results = await discovery.run_full_discovery()
        discovery.print_results()
        
        # Return success code based on readiness
        if results["summary"]["ready_for_development"]:
            print("\n🚀 Infrastructure ready! Proceed with Agentical development.")
            return 0
        else:
            print("\n⚠️  Infrastructure needs configuration before development.")
            return 1
            
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        print(f"\n❌ Infrastructure discovery failed: {e}")
        return 2


if __name__ == "__main__":
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Run discovery
    exit_code = asyncio.run(main())
    sys.exit(exit_code)