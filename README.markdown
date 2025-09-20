# CDOS - ChillHack Denial of Service Attacking Tool

![ChillHack Logo](https://chillhack.net/wp-content/uploads/2025/09/Purple-Minimalist-Tech-Company-Logo-1_20250915_090422_0000.png)

## Introduction

CDOS (ChillHack Denial of Service Attacking Tool) is a robust, multi-vector DDoS simulation tool designed for ethical cybersecurity testing and research. Developed by ChillHack Hong Kong Web Development, it supports HTTP Flood, SYN Flood, UDP Flood, Slowloris, and DNS Amplification attacks to simulate real-world attack scenarios. Intended for authorized use only, CDOS helps security professionals evaluate network resilience in controlled environments.

## Overview

CDOS is crafted for ethical penetration testing, cybersecurity training, and educational purposes. It simulates distributed denial-of-service (DDoS) attacks with advanced features like proxy support, IP spoofing, and dynamic attack switching. Key capabilities include:

- **Multi-Vector Attacks**: HTTP, SYN, UDP, Slowloris, and DNS Amplification.
- **Port Scanning**: Auto-detects open ports or defaults to 80, 443, 53.
- **Proxy and Spoofing**: Routes traffic through proxies or spoofed IPs (requires root privileges).
- **Threaded Workers**: Configurable threads and workers per port for distributed attacks.
- **Real-Time Dashboard**: Monitors worker status, packet counts, and failures.
- **User-Agent Rotation**: Mimics legitimate traffic with customizable User-Agents.

**Warning**: CDOS is for authorized use only. Unauthorized use violates laws such as the Computer Fraud and Abuse Act (CFAA) or equivalent regulations. Always obtain explicit permission before testing.

## Ethical Disclaimer

CDOS is intended for:
- Authorized penetration testing on systems you own or have written permission to test.
- Cybersecurity research and training in controlled environments.
- Educational purposes to understand DDoS mechanics.

**Misuse is illegal and unethical.** ChillHack is not liable for damages or legal consequences from improper use.

## Installation

### Prerequisites
- Python 3.8+ (tested on 3.12).
- Root privileges for IP spoofing (use `sudo`).
- Optional: `dnspython` for DNS Amplification attacks.

### Setup Steps
1. **Clone the Repository**:
   ```
   git clone https://github.com/chillhack-hongkong/cdos.git
   cd cdos
   ```

2. **Install Dependencies**:
   ```
   pip install dnspython requests
   ```
   - `dnspython`: Enables DNS Amplification (falls back to HTTP if absent).
   - `requests`: Required for HTTP-based attacks.

3. **Prepare Input Files** (Optional):
   - **Targets** (`targets.txt`): List IPs or domains (e.g., `example.com`).
   - **Proxies** (`proxies.txt`): Format `IP:Port` (e.g., `127.0.0.1:8080`).
   - **User-Agents** (`agents.txt`): One User-Agent per line.

4. **Run the Tool**:
   See [Usage](#usage) for commands.

## Usage

### Command-Line Options
Run `python3 cdos.py --help` for full details.

| Flag | Description | Example |
|------|-------------|---------|
| `-t, --target-file` | **Required**. Target file or single IP/domain. | `python3 cdos.py -t example.com` |
| `-p, --proxy-file` | Proxy list file for anonymity. | `python3 cdos.py -t targets.txt -p proxies.txt` |
| `-r, --agent-file` | Custom User-Agent list. | `python3 cdos.py -t targets.txt -r agents.txt` |
| `--threads` | Number of worker threads (default: 1000). | `python3 cdos.py -t targets.txt --threads 500` |
| `--workers-per-port` | Workers per open port (default: 1). | `python3 cdos.py -t targets.txt --workers-per-port 10` |
| `--spoof` | Enable IP spoofing (requires sudo). | `sudo python3 cdos.py -t targets.txt --spoof` |

### Example Commands
- **Basic Attack**:
  ```
  python3 cdos.py -t targets.txt
  ```
- **Distributed with Proxies**:
  ```
  python3 cdos.py -t targets.txt -p proxies.txt --threads 2000
  ```
- **With IP Spoofing**:
  ```
  sudo python3 cdos.py -t targets.txt --spoof --workers-per-port 5
  ```

### Attack Flow
1. Loads targets from file or single input.
2. Scans ports (1-65535) or defaults to 80, 443, 53 if none found.
3. Assigns workers to ports, selecting attacks based on port type (e.g., DNS on 53, HTTP on 80/443).
4. Executes attacks, rotating to next type on failure (e.g., 403, 429, 503 errors).
5. Displays real-time worker stats in a CLI dashboard.
6. Stops on `Ctrl+C`, logging duration and stats.

### Attack Vectors
| Attack Type | Description | Target Ports | Spoofing Support |
|-------------|-------------|--------------|------------------|
| **HTTP Flood** | Rapid GET requests to overwhelm web servers. | 80, 443 | No |
| **SYN Flood** | Incomplete TCP handshakes to exhaust connections. | Any | Yes |
| **UDP Flood** | Large UDP packets to saturate bandwidth. | Any | Yes |
| **Slowloris** | Slow HTTP headers to tie up connections. | 80, 443 | No |
| **DNS Amplification** | Spoofed DNS queries to amplify traffic. | 53 | Yes |

## Logging and Monitoring
- **Logs**: Console output with INFO, WARNING, and ERROR levels, including timestamps.
- **Dashboard**: Updates every 0.1s, showing:
  ```
  Target: example.com | Worker Status:
  ----------------------------------------------------------------------
  Worker   Port  Attack Sent  Failed User-Agent
  ----------------------------------------------------------------------
  Worker 1 80    http  150   5      Mozilla/5.0 (Windows NT 10.0;...)
  Worker 2 443   syn   200   0      N/A
  ```
- **Stats**: Tracks sent and failed packets per worker; logs attack duration on stop.

## Troubleshooting
| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| `PermissionError` | IP spoofing without root privileges. | Run with `sudo`. |
| `No open ports found` | Firewall or invalid target. | Verify target or use default ports. |
| `DNS attack unavailable` | Missing `dnspython` library. | Install: `pip install dnspython`. |
| `Thread limit exceeded` | High `--threads` value. | Reduce threads or check `/proc/sys/kernel/threads-max`. |
| Proxy failures | Invalid proxies in list. | Test proxies; tool skips unconnectable ones. |

- **Debug Mode**: Modify script to set `logging.basicConfig(level=logging.DEBUG)` for verbose output.
- **System Limits**: CDOS adjusts threads if exceeding kernel limits.

## Contributing
Contributions are welcome! To contribute:
1. Fork and clone: `git clone https://github.com/your-username/cdos.git`.
2. Install dev dependencies: `pip install -r requirements-dev.txt` (create if needed).
3. Add features or tests using `unittest`.
4. Submit a pull request to `main` with clear commit messages.

Guidelines:
- Adhere to PEP 8 style.
- Document new features in the README.
- Avoid breaking changes without discussion.

## License
MIT License. See [LICENSE](LICENSE) file.

Copyright (c) 2025 ChillHack Hong Kong Web Development.

## Contact
- **Developer**: Jake, ChillHack Team
- **Email**: info@chillhack.net
- **Website**: https://chillhack.net
- **Support**: Open issues on GitHub.

**Stay ethical. Test responsibly.**

---

*Generated on September 20, 2025.*