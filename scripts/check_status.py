#!/usr/bin/env python3
"""
ZombieCoder Status Checker
Verify all components are working properly
"""

import asyncio
import aiohttp
import sys
from typing import Dict, Any

async def check_service(url: str, name: str) -> Dict[str, Any]:
    """Check if a service is responding"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'name': name,
                        'status': 'healthy',
                        'response': data,
                        'url': url
                    }
                else:
                    return {
                        'name': name,
                        'status': 'unhealthy',
                        'error': f'Status code: {response.status}',
                        'url': url
                    }
    except Exception as e:
        return {
            'name': name,
            'status': 'unhealthy',
            'error': str(e),
            'url': url
        }

async def main():
    """Main status checker"""
    print("🧟‍♂️ ZombieCoder Local AI - System Status Checker")
    print("=" * 50)
    
    # Define services to check
    services = [
        ('http://localhost:8000/api/health', 'Main Server'),
        ('http://localhost:3000/health', 'Proxy Server'),
        ('http://localhost:3001/health', 'RAG Service'),
        ('http://localhost:3002/health', 'Monitoring Service'),
        ('http://localhost:3003/health', 'Chat Service'),
    ]
    
    # Check all services concurrently
    tasks = [check_service(url, name) for url, name in services]
    results = await asyncio.gather(*tasks)
    
    # Display results
    healthy_count = 0
    total_count = len(results)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'healthy' else "❌"
        print(f"\n{status_icon} {result['name']}")
        print(f"   URL: {result['url']}")
        print(f"   Status: {result['status']}")
        
        if result['status'] == 'healthy':
            healthy_count += 1
            if 'response' in result:
                if isinstance(result['response'], dict) and 'status' in result['response']:
                    print(f"   Response: {result['response']['status']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    print(f"Overall Status: {healthy_count}/{total_count} services healthy")
    
    if healthy_count == total_count:
        print("🎉 All services are running perfectly!")
        return 0
    else:
        print("⚠️  Some services are not responding. Please check the logs.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)