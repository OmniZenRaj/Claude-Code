#!/usr/bin/env python3
"""
Browser Process Cleanup Script
Purpose: Kill only Chrome browser processes while preserving Playwright Node.js server
Author: KITEAI System
Created: 2025-01-22

CRITICAL: This script kills ONLY browser processes, NOT the Playwright MCP server processes.
This allows browser cleanup without breaking the Playwright connection.
"""

import sys
import argparse

try:
    import psutil
except ImportError:
    print("ERROR: psutil not installed. Install with: pip install psutil")
    sys.exit(1)

class BrowserProcessKiller:
    """Kill only Chrome browser processes while preserving Playwright Node.js server"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        
    def kill_browser_processes_only(self) -> int:
        """Kill ONLY Chrome browser processes with Playwright profile, preserve Node.js server"""
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info['name']
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                # Kill ONLY Chrome processes using the Playwright profile
                is_playwright_chrome = (
                    ('chrome' in proc_name.lower() or 'Google Chrome' in proc_name) and
                    'mcp-chrome-profile' in cmdline
                )
                
                # NEVER kill Node.js processes (Playwright MCP server)
                is_nodejs_server = (
                    'node' in proc_name.lower() and 
                    ('mcp-server-playwright' in cmdline or 'playwright' in cmdline)
                )
                
                if is_playwright_chrome and not is_nodejs_server:
                    if self.verbose:
                        print(f"Killing Chrome process: {proc_name} (PID: {proc.info['pid']})")
                    
                    if not self.dry_run:
                        proc.kill()
                        proc.wait(timeout=5)
                        
                    killed_count += 1
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except psutil.TimeoutExpired:
                if self.verbose:
                    print(f"Process {proc.info['pid']} did not terminate within timeout")
                continue
        
        print(f"Killed {killed_count} Chrome browser processes (preserved Node.js servers)")
        return killed_count

def main():
    """Main script function"""
    parser = argparse.ArgumentParser(description='Kill Chrome browser processes while preserving Playwright Node.js server')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        killer = BrowserProcessKiller(dry_run=args.dry_run, verbose=args.verbose)
        killed_count = killer.kill_browser_processes_only()
        
        if killed_count > 0:
            print(f"✓ Successfully killed {killed_count} Chrome browser processes")
            print("✓ Playwright Node.js server preserved")
            return 0
        else:
            print("ℹ No Chrome browser processes found to kill")
            return 0
            
    except KeyboardInterrupt:
        print("Process killing interrupted by user")
        return 1
    except Exception as e:
        print(f"Script failed: {e}")
        return 2

if __name__ == '__main__':
    sys.exit(main())