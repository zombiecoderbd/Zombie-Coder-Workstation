#!/usr/bin/env python3
"""
Test script to verify ZombieCoder components
"""

import sys
import os
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

def test_imports():
    """Test importing key components"""
    results = {}
    
    # Test core components
    try:
        from server.core.agent_base import AgentBase
        from server.core.agent_manager import AgentManager
        from server.core.agent_workstation import AgentWorkstation
        results['core'] = '✅ SUCCESS'
    except Exception as e:
        results['core'] = f'❌ FAILED: {str(e)}'
    
    # Test database components
    try:
        from server.database.database_manager import DatabaseManager
        # Try to import ChromaDB (may fail due to missing dependencies)
        try:
            from server.database.chroma_manager import ChromaManager
        except ImportError as e:
            if 'chromadb' in str(e):
                # ChromaDB is optional, continue without it
                pass
            else:
                raise e
        results['database'] = '✅ SUCCESS'
    except Exception as e:
        results['database'] = f'❌ FAILED: {str(e)}'
    
    # Test cache components
    try:
        from server.cache.cache_manager import CacheManager
        from server.cache.config import CacheConfig
        results['cache'] = '✅ SUCCESS'
    except Exception as e:
        results['cache'] = f'❌ FAILED: {str(e)}'
    
    # Test security components
    try:
        from server.security.validator import SecurityValidator
        results['security'] = '✅ SUCCESS'
    except Exception as e:
        results['security'] = f'❌ FAILED: {str(e)}'
    
    # Test environment components
    try:
        from server.environment.environment_manager import EnvironmentManager
        results['environment'] = '✅ SUCCESS'
    except Exception as e:
        results['environment'] = f'❌ FAILED: {str(e)}'
    
    # Test proxy components
    try:
        from server.proxy.proxy_server import ProxyServer
        results['proxy'] = '✅ SUCCESS'
    except Exception as e:
        results['proxy'] = f'❌ FAILED: {str(e)}'
    
    return results

def check_directories():
    """Check if required directories exist"""
    required_dirs = [
        'data',
        'logs', 
        'workspace',
        'server/cache',
        'server/database',
        'server/security',
        'server/environment',
        'server/proxy',
        'mini_services/chat_service',
        'mini_services/monitoring_service',
        'mini_services/rag_service'
    ]
    
    results = {}
    base_path = Path(__file__).parent
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            results[dir_name] = '✅ EXISTS'
        else:
            results[dir_name] = '❌ MISSING'
    
    return results

def main():
    """Main test function"""
    print("🧟‍♂️ ZombieCoder Component Test")
    print("=" * 50)
    
    print("\n📋 Testing Component Imports:")
    import_results = test_imports()
    for component, status in import_results.items():
        print(f"  {component.capitalize()}: {status}")
    
    print("\n📂 Checking Directory Structure:")
    dir_results = check_directories()
    for dir_name, status in dir_results.items():
        print(f"  {dir_name}: {status}")
    
    # Summary
    successful_imports = sum(1 for status in import_results.values() if 'SUCCESS' in status)
    total_imports = len(import_results)
    
    existing_dirs = sum(1 for status in dir_results.values() if 'EXISTS' in status)
    total_dirs = len(dir_results)
    
    print(f"\n📊 Summary:")
    print(f"  Component Imports: {successful_imports}/{total_imports} successful")
    print(f"  Directories: {existing_dirs}/{total_dirs} exist")
    
    if successful_imports == total_imports and existing_dirs == total_dirs:
        print("\n🎉 All components are ready!")
        return 0
    else:
        print("\n⚠️  Some components need attention")
        return 1

if __name__ == "__main__":
    exit(main())