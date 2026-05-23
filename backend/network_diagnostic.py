"""
网络连接诊断工具
帮助排查为什么其他电脑无法连接后端服务
"""

import socket
import subprocess
import sys
from pathlib import Path


def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        # 创建一个UDP socket连接到外部DNS
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def check_port(port=5000):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('127.0.0.1', port))
        return result == 0


def check_firewall():
    """检查防火墙状态(Windows)"""
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout
    except Exception as e:
        return f"无法检查防火墙: {e}"


def test_connection(host, port=5000):
    """测试连接到指定主机和端口"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            result = s.connect_ex((host, port))
            if result == 0:
                return True, "连接成功"
            else:
                return False, f"连接失败 (错误码: {result})"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 70)
    print("🔍 网络连接诊断工具")
    print("=" * 70)
    
    # 1. 获取本机IP
    local_ip = get_local_ip()
    print(f"\n📍 本机局域网IP: {local_ip}")
    print(f"   其他设备应访问: http://{local_ip}:5000")
    
    # 2. 检查端口
    print(f"\n🔌 检查端口 5000...")
    if check_port(5000):
        print("   ✅ 端口 5000 正在监听")
    else:
        print("   ❌ 端口 5000 未被监听")
        print("   💡 提示: 请先启动后端服务: cd backend && python app.py")
    
    # 3. 检查防火墙
    print(f"\n🛡️  防火墙状态:")
    firewall_status = check_firewall()
    if "ON" in firewall_status:
        print("   ⚠️  防火墙已开启")
        print("   💡 可能需要添加入站规则允许5000端口")
    else:
        print("   ✅ 防火墙已关闭或未检测到")
    
    # 4. 测试本地连接
    print(f"\n🧪 测试本地连接...")
    success, msg = test_connection('127.0.0.1', 5000)
    if success:
        print(f"   ✅ localhost:5000 - {msg}")
    else:
        print(f"   ❌ localhost:5000 - {msg}")
    
    # 5. 测试局域网连接
    print(f"\n🧪 测试局域网连接...")
    success, msg = test_connection(local_ip, 5000)
    if success:
        print(f"   ✅ {local_ip}:5000 - {msg}")
    else:
        print(f"   ❌ {local_ip}:5000 - {msg}")
        print("   💡 可能的原因:")
        print("      1. Flask未绑定到0.0.0.0")
        print("      2. 防火墙阻止了连接")
        print("      3. 路由器AP隔离 enabled")
    
    # 6. 提供解决方案
    print("\n" + "=" * 70)
    print("📋 解决方案清单")
    print("=" * 70)
    
    print("\n✅ 步骤1: 确认后端服务正在运行")
    print("   命令: cd backend && python app.py")
    print("   应该看到: 服务地址: http://0.0.0.0:5000")
    
    print("\n✅ 步骤2: 检查config.py配置")
    config_path = Path(__file__).parent / 'config.py'
    if config_path.exists():
        print(f"   文件位置: {config_path}")
        print("   确认 HOST = '0.0.0.0' (不是 '127.0.0.1')")
    
    print("\n✅ 步骤3: Windows防火墙设置")
    print("   方法1: 临时关闭防火墙测试")
    print("   方法2: 添加入站规则")
    print("          控制面板 → Windows Defender 防火墙")
    print("          → 高级设置 → 入站规则 → 新建规则")
    print("          → 端口 → TCP 5000 → 允许连接")
    
    print("\n✅ 步骤4: 朋友电脑的访问地址")
    print(f"   正确地址: http://{local_ip}:5000/api/health")
    print("   错误地址: http://127.0.0.1:5000 (只能本机访问)")
    print("   错误地址: http://localhost:5000 (只能本机访问)")
    
    print("\n✅ 步骤5: 前端配置修改")
    frontend_api_path = Path(__file__).parent.parent / 'frontend' / 'js' / 'api.js'
    if frontend_api_path.exists():
        print(f"   编辑文件: {frontend_api_path}")
        print(f"   修改 BASE_URL 为: 'http://{local_ip}:5000/api'")
    
    print("\n✅ 步骤6: 检查网络环境")
    print("   - 确保两台电脑在同一局域网(同一WiFi)")
    print("   - 检查路由器是否开启AP隔离(需关闭)")
    print("   - 尝试ping对方IP测试连通性")
    
    print("\n" + "=" * 70)
    print("💡 快速测试命令:")
    print(f"   curl http://{local_ip}:5000/api/health")
    print(f"   或在浏览器访问: http://{local_ip}:5000/api/health")
    print("=" * 70)


if __name__ == '__main__':
    main()
