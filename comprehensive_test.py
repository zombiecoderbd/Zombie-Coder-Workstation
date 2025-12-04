#!/usr/bin/env python3
"""
Comprehensive test script to verify all ZombieCoder components
"""

import sys
import os
from pathlib import Path
import traceback

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

def test_core_components():
    """Test core architecture components"""
    results = {}
    
    print("Testing Core Components...")
    
    # Test agent workstation
    try:
        from server.core.agent_workstation import AgentWorkstation
        workstation = AgentWorkstation()
        results['agent_workstation'] = '✅ SUCCESS - AgentWorkstation initialized'
    except Exception as e:
        results['agent_workstation'] = f'❌ FAILED: {str(e)}'
        print(f"Agent Workstation Error: {traceback.format_exc()}")
    
    # Test agent manager
    try:
        from server.core.agent_manager import AgentManager
        manager = AgentManager()
        results['agent_manager'] = '✅ SUCCESS - AgentManager initialized'
    except Exception as e:
        results['agent_manager'] = f'❌ FAILED: {str(e)}'
        print(f"Agent Manager Error: {traceback.format_exc()}")
    
    # Test agent base
    try:
        from server.core.agent_base import AgentBase
        results['agent_base'] = '✅ SUCCESS - AgentBase imported'
    except Exception as e:
        results['agent_base'] = f'❌ FAILED: {str(e)}'
        print(f"Agent Base Error: {traceback.format_exc()}")
    
    return results

def test_database_components():
    """Test database layer components"""
    results = {}
    
    print("Testing Database Components...")
    
    # Test database manager
    try:
        from server.database.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        results['database_manager'] = '✅ SUCCESS - DatabaseManager initialized'
    except Exception as e:
        results['database_manager'] = f'❌ FAILED: {str(e)}'
        print(f"Database Manager Error: {traceback.format_exc()}")
    
    # Test chroma manager
    try:
        from server.database.chroma_manager import ChromaManager
        chroma_manager = ChromaManager()
        results['chroma_manager'] = '✅ SUCCESS - ChromaManager initialized'
    except Exception as e:
        results['chroma_manager'] = f'❌ FAILED: {str(e)}'
        print(f"Chroma Manager Error: {traceback.format_exc()}")
    
    return results

def test_cache_components():
    """Test cache layer components"""
    results = {}
    
    print("Testing Cache Components...")
    
    # Test cache manager
    try:
        from server.cache.cache_manager import CacheManager
        cache_manager = CacheManager()
        results['cache_manager'] = '✅ SUCCESS - CacheManager initialized'
    except Exception as e:
        results['cache_manager'] = f'❌ FAILED: {str(e)}'
        print(f"Cache Manager Error: {traceback.format_exc()}")
    
    # Test cache config
    try:
        from server.cache.config import CacheConfig
        cache_config = CacheConfig()
        results['cache_config'] = '✅ SUCCESS - CacheConfig initialized'
    except Exception as e:
        results['cache_config'] = f'❌ FAILED: {str(e)}'
        print(f"Cache Config Error: {traceback.format_exc()}")
    
    return results

def test_security_components():
    """Test security layer components"""
    results = {}
    
    print("Testing Security Components...")
    
    # Test security validator
    try:
        from server.security.validator import SecurityValidator
        validator = SecurityValidator()
        results['security_validator'] = '✅ SUCCESS - SecurityValidator initialized'
    except Exception as e:
        results['security_validator'] = f'❌ FAILED: {str(e)}'
        print(f"Security Validator Error: {traceback.format_exc()}")
    
    return results

def test_environment_components():
    """Test environment management components"""
    results = {}
    
    print("Testing Environment Components...")
    
    # Test environment manager
    try:
        from server.environment.environment_manager import EnvironmentManager
        env_manager = EnvironmentManager()
        results['environment_manager'] = '✅ SUCCESS - EnvironmentManager initialized'
    except Exception as e:
        results['environment_manager'] = f'❌ FAILED: {str(e)}'
        print(f"Environment Manager Error: {traceback.format_exc()}")
    
    return results

def test_proxy_components():
    """Test proxy server components"""
    results = {}
    
    print("Testing Proxy Components...")
    
    # Test proxy server
    try:
        from server.proxy.proxy_server import ProxyServer
        proxy_server = ProxyServer()
        results['proxy_server'] = '✅ SUCCESS - ProxyServer initialized'
    except Exception as e:
        results['proxy_server'] = f'❌ FAILED: {str(e)}'
        print(f"Proxy Server Error: {traceback.format_exc()}")
    
    return results

def check_required_files():
    """Check if all required files exist"""
    results = {}
    
    print("Checking Required Files...")
    
    required_files = [
        'server/core/agent_workstation.py',
        'server/core/agent_manager.py',
        'server/core/agent_base.py',
        'server/database/database_manager.py',
        'server/database/chroma_manager.py',
        'server/cache/cache_manager.py',
        'server/cache/config.py',
        'server/security/validator.py',
        'server/environment/environment_manager.py',
        'server/proxy/proxy_server.py',
        'server/agents/virtual_sir_agent.py',
        'server/agents/coding_agent.py',
        'config/config.yaml',
        'config/registry.yaml',
        'config/personality.yaml',
        'scripts/start_complete.sh',
        'scripts/start_complete.bat',
        'scripts/start_server.sh',
        'scripts/start_server.bat',
        'requirements.txt'
    ]
    
    base_path = Path(__file__).parent
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            results[file_path] = '✅ EXISTS'
        else:
            results[file_path] = '❌ MISSING'
    
    return results

def check_directories():
    """Check if required directories exist"""
    results = {}
    
    print("Checking Required Directories...")
    
    required_dirs = [
        'data',
        'logs', 
        'workspace',
        'server/core',
        'server/database',
        'server/cache',
        'server/security',
        'server/environment',
        'server/proxy',
        'server/agents',
        'server/models',
        'server/routing',
        'server/tools',
        'server/rag',
        'server/monitoring',
        'config',
        'scripts',
        'mini-services/chat_service',
        'mini-services/monitoring_service',
        'mini-services/rag_service'
    ]
    
    base_path = Path(__file__).parent
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            results[dir_name] = '✅ EXISTS'
        else:
            results[dir_name] = '❌ MISSING'
    
    return results

def main():
    """Main comprehensive test function"""
    print("🧟‍♂️ ZombieCoder Comprehensive System Test")
    print("=" * 60)
    
    # Run all tests
    core_results = test_core_components()
    database_results = test_database_components()
    cache_results = test_cache_components()
    security_results = test_security_components()
    environment_results = test_environment_components()
    proxy_results = test_proxy_components()
    file_results = check_required_files()
    dir_results = check_directories()
    
    # Display results
    print("\n📋 Core Components:")
    for component, status in core_results.items():
        print(f"  {component}: {status}")
    
    print("\n🗄️ Database Components:")
    for component, status in database_results.items():
        print(f"  {component}: {status}")
    
    print("\nキャッシング Cache Components:")
    for component, status in cache_results.items():
        print(f"  {component}: {status}")
    
    print("\n🛡️ Security Components:")
    for component, status in security_results.items():
        print(f"  {component}: {status}")
    
    print("\n🌍 Environment Components:")
    for component, status in environment_results.items():
        print(f"  {component}: {status}")
    
    print("\n🌐 Proxy Components:")
    for component, status in proxy_results.items():
        print(f"  {component}: {status}")
    
    print("\n📄 Required Files:")
    for file_path, status in file_results.items():
        print(f"  {file_path}: {status}")
    
    print("\n📁 Required Directories:")
    for dir_name, status in dir_results.items():
        print(f"  {dir_name}: {status}")
    
    # Summary
    all_results = {
        **core_results, **database_results, **cache_results,
        **security_results, **environment_results, **proxy_results
    }
    
    successful_components = sum(1 for status in all_results.values() if 'SUCCESS' in status)
    total_components = len(all_results)
    
    existing_files = sum(1 for status in file_results.values() if 'EXISTS' in status)
    total_files = len(file_results)
    
    existing_dirs = sum(1 for status in dir_results.values() if 'EXISTS' in status)
    total_dirs = len(dir_results)
    
    print(f"\n📊 Summary:")
    print(f"  Core Components: {successful_components}/{total_components} successful")
    print(f"  Required Files: {existing_files}/{total_files} exist")
    print(f"  Required Directories: {existing_dirs}/{total_dirs} exist")
    
    total_checks = total_components + total_files + total_dirs
    passed_checks = successful_components + existing_files + existing_dirs
    
    print(f"  Overall: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\n🎉 All components are ready for production!")
        print("📦 System is production-ready!")
        return 0
    else:
        print(f"\n⚠️  {total_checks - passed_checks} components need attention")
        return 1

if __name__ == "__main__":
    exit(main())