# CDOS - Intelligent DDoS Simulation Tool

```
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
```
<img width="1063" height="1063" alt="Purple minimalist Tech Company Logo" src="https://github.com/user-attachments/assets/cc027882-8037-4501-95ca-0e0f30f8fea5" />

## Overview
CDOS is an intelligent DDoS simulation tool designed for testing network resilience. It supports multiple attack types (HTTP, SYN, UDP, Slowloris, DNS amplification) and features proxy support, IP spoofing (with root privileges), and customizable User-Agent lists.

**Note**: This tool is for educational and authorized testing purposes only. Unauthorized use against systems you do not own or have explicit permission to test is illegal.

## Prerequisites
- **Python**: Version 3.6 or higher.
- **Dependencies**: `requests`, `dnspython`, and `setuptools` (automatically installed by `setup.py`).
- **Operating System**: Linux/Unix-like systems (for threading and socket operations).
- **Root Privileges**: Required for IP spoofing (`--spoof` option).

## Installation
To set up and install the CDOS tool, follow these steps:

1. **Clone or Download the Repository**:
   Ensure you have the `cdos.py` and `setup.py` files in your working directory.

2. **Set Up a Virtual Environment** (recommended to avoid system-wide changes):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Run the Setup Script**:
   ```bash
   python3 setup.py
   ```
   This will:
   - Check for Python 3.6 or higher.
   - Install required dependencies (`setuptools`, `requests`, `dnspython`).
   - Set up the `cdos` command.

4. **Handle Missing `setuptools`**:
   If you encounter an error like `ImportError: cannot import name 'setup' from 'setuptools'`, install `setuptools` manually:
   ```bash
   pip3 install setuptools
   ```
   Then rerun:
   ```bash
   python3 setup.py
   ```

5. **Verify Installation**:
   After successful installation, test the `cdos` command:
   ```bash
   cdos -h
   ```
   This should display the help menu for the CDOS tool, confirming that the installation was successful.

## Usage
Run the tool with the `cdos` command followed by the required arguments:
```bash
cdos -t <target_file_or_ip> [options]
```

### Options
- `-t, --target-file`: Target IP/domain list file (TXT) or single target (required).
- `-p, --proxy-file`: Proxy IP list file (TXT, format: IP:Port).
- `-r, --agent-file`: Custom User-Agent list file (TXT).
- `--threads`: Number of worker threads (default: 1000).
- `--workers-per-port`: Number of workers per port (default: 1).
- `--spoof`: Enable IP spoofing (requires root privileges).

### Usage Examples
- Basic Attack:
  ```bash
  cdos -t targets.txt
  ```
- Distributed DDoS with Proxies:
  ```bash
  cdos -t targets.txt -p proxies.txt
  ```
- Custom User-Agent List:
  ```bash
  cdos -t targets.txt -p proxies.txt -r agent_list.txt
  ```
- Specify Threads and Workers per Port:
  ```bash
  cdos -t targets.txt --threads 500 --workers-per-port 10
  ```
- Enable IP Spoofing (requires root):
  ```bash
  sudo cdos -t targets.txt --spoof
  ```

## Notes
- **Root Privileges**: The `--spoof` option requires running the tool with `sudo` due to raw socket operations.
- **Virtual Environment**: Using a virtual environment (`venv`) is strongly recommended to avoid conflicts with system-wide Python packages.
- **DNS Amplification**: Requires the `dnspython` library. If installation fails, the tool will skip DNS attacks and use HTTP instead.
- **Thread Limits**: The tool checks the system thread limit (`/proc/sys/kernel/threads-max`) and adjusts if necessary.

## Troubleshooting
- **If `cdos` Command Not Found**:
  Ensure the virtual environment is activated or add the Python `bin` directory to your `PATH`:
  ```bash
  export PATH=$PATH:$(pwd)/venv/bin
  ```
  For system-wide installation, check `/usr/local/bin` or `~/.local/bin`:
  ```bash
  export PATH=$PATH:~/.local/bin
  ```

- **Dependency Installation Issues**:
  Manually install dependencies:
  ```bash
  pip3 install setuptools requests dnspython
  ```

- **Permission Errors**:
  If you encounter permission issues, try:
  ```bash
  sudo python3 setup.py
  ```

## Contact
For support or inquiries:
- **Email**: info@chillhack.net
- **Website**: https://chillhack.net

Developed by ChillHack Hong Kong Web Development, Jake.
