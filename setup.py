#!/usr/bin/env python3
import os
import sys
import subprocess

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        sys.exit(1)

def install_requests():
    """Install requests module (optional)"""
    try:
        import requests
    except ImportError:
        print("Installing requests module...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
            print("Requests installation complete")
        except subprocess.CalledProcessError:
            print("Error: Failed to install requests module. Please install it manually with 'pip install requests'")
            sys.exit(1)

def install_dnspython():
    """Install dnspython module (optional)"""
    try:
        import dns.message
    except ImportError:
        print("Installing dnspython module for DNS amplification attack...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "dnspython"], check=True)
            print("dnspython installation complete")
        except subprocess.CalledProcessError:
            print("Warning: Failed to install dnspython. DNS amplification attack will be unavailable.")
            print("You can install it manually with 'pip install dnspython'")

def main():
    print("""
[Victim Server]
                 |
                 |
    +------------+------------+
    |                         |
[Attacker 1]             [Attacker 2]
    |                         |
    |                         |
    v                         v
[Proxy/Spoofed IP]    [Proxy/Spoofed IP]
    |                         |
    +---+---+---+---+         +---+---+---+---+
    |   |   |   |   |         |   |   |   |   |
    v   v   v   v   v         v   v   v   v   v
 [HTTP] [SYN] [UDP] [Slowloris] [DNS] [HTTP] [SYN] [UDP] [Slowloris] [DNS]
        |       |       |       |     |       |       |       |       |
        +-------+-------+-------+-----+-------+-------+-------+-------+
                        |
                        |
                    [Router]
                        |
                        |
                    [Overload]
                        |
                        v
                 [Server Crashes]
          
Developed by ChillHack Hong Kong Web Development, Jake.
    Intelligent DDoS Simulation Tool
          Contact: info@chillhack.net
          Website: https://chillhack.net
    """)
    print("Setting up CDOS tool environment...")
    check_python()
    install_requests()
    install_dnspython()
    print("Environment setup complete! Run the tool with 'cdos -h'.")

if __name__ == "__main__":
    main()
