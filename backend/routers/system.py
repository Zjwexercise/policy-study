import socket
import io
import base64
import qrcode
from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])

def get_lan_ip():
    """获取本机真实物理局域网 IPv4 地址（排除 TUN、VMware、VirtualBox 等虚拟网卡）"""
    try:
        addrs = [a[4][0] for a in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
        valid = []
        for ip in addrs:
            if ip.startswith('127.') or ip.startswith('169.254.') or ip.startswith('198.18.'):
                continue
            # 排除常见虚拟机网段
            if ip.startswith('192.168.56.') or ip.startswith('192.168.88.') or ip.startswith('192.168.119.'):
                continue
            if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                valid.append(ip)
        if valid:
            return valid[0]
        # 回退逻辑
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('114.114.114.114', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

@router.get("/network-info")
def get_network_info(port: int = 8000):
    lan_ip = get_lan_ip()
    local_url = f"http://localhost:{port}"
    mobile_url = f"http://{lan_ip}:{port}"

    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=2,
    )
    qr.add_data(mobile_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode()

    return {
        "lan_ip": lan_ip,
        "port": port,
        "local_url": local_url,
        "mobile_url": mobile_url,
        "qr_code": qr_base64
    }
