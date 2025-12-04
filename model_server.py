#!/usr/bin/env python3
"""
Model Server Launcher for ZombieCoder
Runs the complete system on port 8157
"""

import uvicorn
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

if __name__ == "__main__":
    # Run the complete server on port 8157
    uvicorn.run(
        "server.main_complete:app",
        host="127.0.0.1",
        port=8157,
        reload=False,
        log_level="info"
    )