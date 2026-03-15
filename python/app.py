import os
import re
import json
import time
import base64
import shutil
import asyncio
import requests
import platform
import subprocess
import threading
from threading import Thread
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer

load_dotenv()

# Environment variables
UPLOAD_URL = os.environ.get('UPLOAD_URL', '') 
PROJECT_URL = os.environ.get('PROJECT_URL', '') 
AUTO_ACCESS = os.environ.get('AUTO_ACCESS', 'false').lower() == 'true'
FILE_PATH = os.environ.get('FILE_PATH', '.cache')
SUB_PATH = os.environ.get('SUB_PATH', 'sub')
UUID = os.environ.get('UUID', 'f929c4da-dc2e-4e0d-9a6f-1799036af214')

# Komari 相關變數（替換原 NEZHA）
KOMARI_SERVER = os.environ.get('KOMARI_SERVER', '')   # 例如 http://your-panel-domain:25774
KOMARI_TOKEN  = os.environ.get('KOMARI_TOKEN', '')    # 面板新增節點後取得的 token

ARGO_DOMAIN = os.environ.get('ARGO_DOMAIN', '')
ARGO_AUTH = os.environ.get('ARGO_AUTH', '')
ARGO_PORT = int(os.environ.get('ARGO_PORT', '8001'))
S5_PORT_STR = os.environ.get('S5_PORT', '')
TUIC_PORT_STR = os.environ.get('TUIC_PORT', '')
HY2_PORT_STR = os.environ.get('HY2_PORT', '')
ANYTLS_PORT_STR = os.environ.get('ANYTLS_PORT', '')
REALITY_PORT_STR = os.environ.get('REALITY_PORT', '')
ANYREALITY_PORT_STR = os.environ.get('ANYREALITY_PORT', '')
CFIP = os.environ.get('CFIP', 'cdns.doon.eu.org')
CFPORT = int(os.environ.get('CFPORT', '443'))
PORT = int(os.environ.get('PORT', '3000'))
NAME = os.environ.get('NAME', '')
CHAT_ID = os.environ.get('CHAT_ID', '')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
DISABLE_ARGO = os.environ.get('DISABLE_ARGO', 'false').lower() == 'true'

# Create running folder
def create_directory():
    print('\033c', end='')
    if not os.path.exists(FILE_PATH):
        os.makedirs(FILE_PATH)
        print(f"{FILE_PATH} is created")
    else:
        print(f"{FILE_PATH} already exists")

# 端口變數處理
S5_PORT = int(S5_PORT_STR) if S5_PORT_STR and S5_PORT_STR.isdigit() else None
TUIC_PORT = int(TUIC_PORT_STR) if TUIC_PORT_STR and TUIC_PORT_STR.isdigit() else None
HY2_PORT = int(HY2_PORT_STR) if HY2_PORT_STR and HY2_PORT_STR.isdigit() else None
ANYTLS_PORT = int(ANYTLS_PORT_STR) if ANYTLS_PORT_STR and ANYTLS_PORT_STR.isdigit() else None
REALITY_PORT = int(REALITY_PORT_STR) if REALITY_PORT_STR and REALITY_PORT_STR.isdigit() else None
ANYREALITY_PORT = int(ANYREALITY_PORT_STR) if ANYREALITY_PORT_STR and ANYREALITY_PORT_STR.isdigit() else None

# Global variables
private_key = ''
public_key = ''
npm_path = os.path.join(FILE_PATH, 'npm')       # 不再使用，但保留變數名避免其他地方報錯
php_path = os.path.join(FILE_PATH, 'php')       # 同上
web_path = os.path.join(FILE_PATH, 'web')
bot_path = os.path.join(FILE_PATH, 'bot')
sub_path = os.path.join(FILE_PATH, 'sub.txt')
list_path = os.path.join(FILE_PATH, 'list.txt')
boot_log_path = os.path.join(FILE_PATH, 'boot.log')
config_path = os.path.join(FILE_PATH, 'config.json')
agent_path = os.path.join(FILE_PATH, 'komari-agent')  # 新增

# Delete nodes
def delete_nodes():
    try:
        if not UPLOAD_URL:
            return
        if not os.path.exists(sub_path):
            return
        try:
            with open(sub_path, 'r') as file:
                file_content = file.read()
        except:
            return None
        decoded = base64.b64decode(file_content).decode('utf-8')
        nodes = [line for line in decoded.split('\n') if any(protocol in line for protocol in ['vless://', 'vmess://', 'trojan://', 'hysteria2://', 'tuic://', 'anytls://', 'socks://'])]
        if not nodes:
            return
        try:
            requests.post(f"{UPLOAD_URL}/api/delete-nodes",
                          data=json.dumps({"nodes": nodes}),
                          headers={"Content-Type": "application/json"})
        except:
            return None
    except Exception as e:
        print(f"Error in delete_nodes: {e}")
        return None

# Clean up old files
def cleanup_old_files():
    paths_to_delete = ['web', 'bot', 'npm', 'boot.log', 'list.txt']
    for file in paths_to_delete:
        file_path = os.path.join(FILE_PATH, file)
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            try:
                index_path = os.path.join(FILE_PATH, 'index.html')
                if os.path.exists(index_path):
                    with open(index_path, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(content)
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'Hello world!<br><br>You can visit /{SUB_PATH}(Default: /sub) get your nodes!')
            except Exception as e:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Hello world!<br><br>You can visit /{SUB_PATH}(Default: /sub) get your nodes!')
           
        elif self.path == f'/{SUB_PATH}':
            try:
                with open(sub_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(content)
            except:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

# Determine system architecture
def get_system_architecture():
    architecture = platform.machine().lower()
    if 'arm' in architecture or 'aarch64' in architecture:
        return 'arm'
    else:
        return 'amd'

# Download file based on architecture
def download_file(file_name, file_url):
    file_path = os.path.join(FILE_PATH, file_name)
    try:
        response = requests.get(file_url, stream=True, timeout=30)
        response.raise_for_status()
       
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
       
        print(f"Download {file_name} successfully")
        return True
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        print(f"Download {file_name} failed: {e}")
        return False

# Get files for architecture
def get_files_for_architecture(architecture):
    if architecture == 'arm':
        base_files = [
            {"fileName": "web", "fileUrl": "https://arm64.ssss.nyc.mn/sb"},
            {"fileName": "bot", "fileUrl": "https://arm64.ssss.nyc.mn/2go"}
        ]
        agent_url = "https://github.com/komari-monitor/komari-agent/releases/latest/download/komari-agent-linux-arm64"
    else:
        base_files = [
            {"fileName": "web", "fileUrl": "https://amd64.ssss.nyc.mn/sb"},
            {"fileName": "bot", "fileUrl": "https://amd64.ssss.nyc.mn/2go"}
        ]
        agent_url = "https://github.com/komari-monitor/komari-agent/releases/latest/download/komari-agent-linux-amd64"

    # 如果設定了 Komari 則下載 agent
    if KOMARI_SERVER and KOMARI_TOKEN:
        base_files.insert(0, {"fileName": "komari-agent", "fileUrl": agent_url})

    return base_files

# Authorize files with execute permission
def authorize_files(file_paths):
    for relative_file_path in file_paths:
        absolute_file_path = os.path.join(FILE_PATH, relative_file_path)
        if os.path.exists(absolute_file_path):
            try:
                os.chmod(absolute_file_path, 0o775)
                print(f"Empowerment success for {absolute_file_path}: 775")
            except Exception as e:
                print(f"Empowerment failed for {absolute_file_path}: {e}")

# Configure Argo tunnel
def argo_type():
    if DISABLE_ARGO:
        print("DISABLE_ARGO is set to true, disable argo tunnel")
        return
    if not ARGO_AUTH or not ARGO_DOMAIN:
        print("ARGO_DOMAIN or ARGO_AUTH variable is empty, use quick tunnels")
        return
    if "TunnelSecret" in ARGO_AUTH:
        with open(os.path.join(FILE_PATH, 'tunnel.json'), 'w') as f:
            f.write(ARGO_AUTH)
       
        tunnel_id = ARGO_AUTH.split('"')[11]
        tunnel_yml = f"""
tunnel: {tunnel_id}
credentials-file: {os.path.join(FILE_PATH, 'tunnel.json')}
protocol: http2
ingress:
  - hostname: {ARGO_DOMAIN}
    service: http://localhost:{ARGO_PORT}
    originRequest:
      noTLSVerify: true
  - service: http_status:404
"""
        with open(os.path.join(FILE_PATH, 'tunnel.yml'), 'w') as f:
            f.write(tunnel_yml)
    else:
        print("ARGO_AUTH mismatch TunnelSecret, use token connect to tunnel")

# Execute shell command and return output
def exec_cmd(command):
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return stdout + stderr
    except Exception as e:
        print(f"Error executing command: {e}")
        return str(e)

# Download and run necessary files
async def download_files_and_run():
    global private_key, public_key
   
    architecture = get_system_architecture()
    files_to_download = get_files_for_architecture(architecture)
   
    if not files_to_download:
        print("Can't find a file for the current architecture")
        return
   
    # Download all files
    download_success = True
    for file_info in files_to_download:
        if not download_file(file_info["fileName"], file_info["fileUrl"]):
            download_success = False
   
    if not download_success:
        print("Error downloading files")
        return
   
    # Authorize files
    files_to_authorize = ['komari-agent', 'web', 'bot'] if (KOMARI_SERVER and KOMARI_TOKEN) else ['web', 'bot']
    authorize_files(files_to_authorize)
   
    # Generate reality-keypair
    keypair_output = exec_cmd(f"{os.path.join(FILE_PATH, 'web')} generate reality-keypair")
   
    # Extract private and public keys
    private_key_match = re.search(r'PrivateKey:\s*(.*)', keypair_output)
    public_key_match = re.search(r'PublicKey:\s*(.*)', keypair_output)
   
    if private_key_match and public_key_match:
        private_key = private_key_match.group(1)
        public_key = public_key_match.group(1)
       
        print(f'Private Key: {private_key}')
        print(f'Public Key: {public_key}')
    else:
        print('Failed to extract privateKey or publicKey from output.')
        return
   
    # Generate private.key
    exec_cmd(f'openssl ecparam -genkey -name prime256v1 -out "{FILE_PATH}/private.key"')
   
    # Generate cert.pem
    exec_cmd(f'openssl req -new -x509 -days 3650 -key "{FILE_PATH}/private.key" -out "{FILE_PATH}/cert.pem" -subj "/CN=bing.com"')
   
    # Generate configuration file (sing-box config)
    config = {
        "log": {
            "disabled": True,
            "level": "info",
            "timestamp": True
        },
        "inbounds": [
            {
                "tag": "vmess-ws-in",
                "type": "vmess",
                "listen": "::",
                "listen_port": ARGO_PORT,
                "users": [
                    {
                        "uuid": UUID
                    }
                ],
                "transport": {
                    "type": "ws",
                    "path": "/vmess-argo",
                    "early_data_header_name": "Sec-WebSocket-Protocol"
                }
            }
        ],
        "endpoints": [
          {
              "type": "wireguard",
              "tag": "wireguard-out",
              "mtu": 1280,
              "address": [
                  "172.16.0.2/32",
                  "2606:4700:110:8dfe:d141:69bb:6b80:925/128"
              ],
              "private_key": "YFYOAdbw1bKTHlNNi+aEjBM3BO7unuFC5rOkMRAz9XY=",
              "peers": [
                  {
                    "address": "engage.cloudflareclient.com",
                    "port": 2408,
                    "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
                    "allowed_ips": ["0.0.0.0/0", "::/0"],
                    "reserved": [78, 135, 76]
                  }
              ]
          }
        ],
        "outbounds": [
            {
                "type": "direct",
                "tag": "direct"
            }
        ],
        "route": {
            "rule_set": [
                {
                    "tag": "netflix",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-netflix.srs",
                    "download_detour": "direct"
                },
                {
                    "tag": "openai",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/sing/geo/geosite/openai.srs",
                    "download_detour": "direct"
                }
            ],
            "rules": [
                {
                    "rule_set": ["openai", "netflix"],
                    "outbound": "wireguard-out"
                }
            ],
            "final": "direct"
        }
    }
   
    # 動態添加其他協議的 inbound
    if REALITY_PORT and REALITY_PORT > 0:
        reality_config = {
            "tag": "vless-in",
            "type": "vless",
            "listen": "::",
            "listen_port": REALITY_PORT,
            "users": [
                {
                    "uuid": UUID,
                    "flow": "xtls-rprx-vision"
                }
            ],
            "tls": {
                "enabled": True,
                "server_name": "www.iij.ad.jp",
                "reality": {
                    "enabled": True,
                    "handshake": {
                        "server": "www.iij.ad.jp",
                        "server_port": 443
                    },
                    "private_key": private_key,
                    "short_id": [""]
                }
            }
        }
        config["inbounds"].append(reality_config)
   
    if HY2_PORT and HY2_PORT > 0:
        hysteria_config = {
            "tag": "hysteria-in",
            "type": "hysteria2",
            "listen": "::",
            "listen_port": HY2_PORT,
            "users": [
                {
                    "password": UUID
                }
            ],
            "masquerade": "https://bing.com",
            "tls": {
                "enabled": True,
                "alpn": ["h3"],
                "certificate_path": f"{FILE_PATH}/cert.pem",
                "key_path": f"{FILE_PATH}/private.key"
            }
        }
        config["inbounds"].append(hysteria_config)
   
    if TUIC_PORT and TUIC_PORT > 0:
        tuic_config = {
            "tag": "tuic-in",
            "type": "tuic",
            "listen": "::",
            "listen_port": TUIC_PORT,
            "users": [
                {
                    "uuid": UUID
                }
            ],
            "congestion_control": "bbr",
            "tls": {
                "enabled": True,
                "alpn": ["h3"],
                "certificate_path": f"{FILE_PATH}/cert.pem",
                "key_path": f"{FILE_PATH}/private.key"
            }
        }
        config["inbounds"].append(tuic_config)
   
    if S5_PORT and
