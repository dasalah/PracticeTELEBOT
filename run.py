#!/usr/bin/env python3
"""
Event Registration Telegram Bot
Run script for the comprehensive event registration system
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 ربات متوقف شد.")
    except Exception as e:
        print(f"❌ خطا: {e}")
        sys.exit(1)