#!/usr/bin/env python3
"""
Web Page Capture Tool - Main Entry Point
"""

import sys
import argparse

# Import functionality from existing scripts
from screenshot import run_interactive, run_cli, WebPageCapture

# Try importing GUI (will fail gracefully if tkinter is not available)
try:
    from gui import run_gui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

def main():
    """Main entry point for the application"""
    # Create command line parser
    parser = argparse.ArgumentParser(
        description='Web Page Capture Tool - Take screenshots of webpages and save as PNG, JPG, or PDF'
    )
    
    # Add basic arguments
    parser.add_argument('url', nargs='?', help='URL of the webpage to capture')
    parser.add_argument('--gui', action='store_true', help='Launch the graphical user interface')
    parser.add_argument('--format', choices=['png', 'jpg', 'pdf'], help='Output format (png, jpg, or pdf)')
    parser.add_argument('--output', help='Custom output path')
    parser.add_argument('--quality', type=int, help='JPEG quality (1-100)')
    parser.add_argument('--width', type=int, help='Viewport width')
    parser.add_argument('--height', type=int, help='Viewport height (defaults to full page)')
    parser.add_argument('--timeout', type=int, help='Page load timeout in seconds')
    parser.add_argument('--version', action='store_true', help='Show version information')
    
    # Parse arguments
    if len(sys.argv) > 1:
        args = parser.parse_args()
        
        # Handle version request
        if args.version:
            print("Web Page Capture Tool v0.1.0")
            return 0
            
        # GUI mode takes precedence if explicitly requested
        if args.gui:
            if not HAS_GUI:
                print("Error: GUI mode is not available. Please install tkinter.")
                return 1
            return run_gui()
            
        # If URL is provided, run in CLI mode
        if args.url:
            # Only pass along arguments that were actually provided
            cli_args = sys.argv[1:]
            return run_cli()
            
        # No URL and no --gui, show help
        parser.print_help()
        return 1
    else:
        # No arguments provided, check if GUI is available
        if HAS_GUI:
            print("Starting in GUI mode. Use --help for command line options.")
            return run_gui()
        else:
            # Fall back to interactive mode
            print("Starting in interactive mode. Use --help for command line options.")
            run_interactive()
            return 0

if __name__ == "__main__":
    sys.exit(main())
