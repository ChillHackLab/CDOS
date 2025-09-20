#!/usr/bin/env python3
import os
import sys
import subprocess
import setuptools
from setuptools import setup, find_packages

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        sys.exit(1)

def install_requirements():
    """Install required modules (setuptools, requests, dnspython)"""
    requirements = ['setuptools', 'requests', 'dnspython']
    for package in requirements:
        try:
            if package == 'dnspython':
                __import__('dns.message')
            else:
                __import__(package)
        except ImportError:
            print(f"Installing {package} module...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"{package} installation complete")
            except subprocess.CalledProcessError:
                if package == 'dnspython':
                    print("Warning: Failed to install dnspython. DNS amplification attack will be unavailable.")
                    print("You can install it manually with 'pip install dnspython'")
                else:
                    print(f"Error: Failed to install {package}. Please install it manually with 'pip install {package}'")
                    sys.exit(1)

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
    install_requirements()
    print("Installing CDOS tool...")
    setup(
        name="cdos",
        version="1.0.0",
        description="Intelligent DDoS Simulation Tool",
        author="Jake, ChillHack Hong Kong Web Development",
        author_email="info@chillhack.net",
        url="https://chillhack.net",
        packages=find_packages(),
        py_modules=['cdos'],
        install_requires=['requests', 'dnspython'],
        entry_points={
            'console_scripts': [
                'cdos=cdos:main',
            ],
        },
        classifiers=[
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ],
        license="MIT",
    )
    print("Environment setup complete! You can now run the tool with the 'cdos' command.")

if __name__ == "__main__":
    # Automatically run the install command
    sys.argv.extend(['install'])
    main()
