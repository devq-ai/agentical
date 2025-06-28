"""
Tests for Agentical API System
"""

import pytest
from pathlib import Path

class TestAPIStructure:
    """Test suite for API structure"""
    
    def test_main_app_exists(self):
        """Test that main FastAPI app exists"""
        main_file = Path(__file__).parent.parent / "main.py"
        assert main_file.exists(), "main.py should exist"
    
    def test_api_directory_exists(self):
        """Test that API directory exists"""
        api_dir = Path(__file__).parent.parent / "api"
        assert api_dir.exists(), "API directory should exist"
    
    def test_api_endpoints_exist(self):
        """Test that API endpoint files exist"""
        api_dir = Path(__file__).parent.parent / "api"
        
        # Check for key endpoint files
        expected_files = [
            "v1/endpoints/agents.py",
            "v1/endpoints/health.py"
        ]
        
        existing_files = 0
        for file_path in expected_files:
            if (api_dir / file_path).exists():
                existing_files += 1
        
        assert existing_files >= 1, "At least one API endpoint file should exist"
    
    def test_frontend_structure(self):
        """Test frontend structure exists"""
        frontend_dir = Path(__file__).parent.parent / "frontend"
        assert frontend_dir.exists(), "Frontend directory should exist"
        
        package_json = frontend_dir / "package.json"
        assert package_json.exists(), "Frontend package.json should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
