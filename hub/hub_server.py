import socket
import struct
from collections import deque, defaultdict

HUB_IP = "0.0.0.0"
HUB_PORT = 9000
PACKET_FORMAT = "<BBBfB"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)
ANOMALY_THRESHOLD = 20.0  # degrees Celsius

SENSOR_TYPE_MAP = {
    0x01: "Temperature",
    0x02: "Humidity",
    0x03: "Motion",
}

sensor_history = defaultdict(lambda: deque(maxlen=5))

def calculate_crc(data):
    crc = 0
    for b in data[:-1]:
        crc ^= b
    return crc

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HUB_IP, HUB_PORT))

print(f"🛠️ Hub server listening on {HUB_IP}:{HUB_PORT} ...\n")

while True:
    data, addr = sock.recvfrom(1024)

    if len(data) != PACKET_SIZE:
        print(f"⚠️ Invalid packet size from {addr}, got {len(data)} bytes")
        continue

    unpacked = struct.unpack(PACKET_FORMAT, data)
    header, node_id, sensor_type, value, recv_crc = unpacked

    if header != 0xAA:
        print(f"🚫 Invalid header from Node {node_id}")
        continue

    calc_crc = calculate_crc(data)
    if calc_crc != recv_crc:
        print(f"❌ CRC mismatch from Node {node_id}: expected {recv_crc}, got {calc_crc}")
        continue

    sensor_name = SENSOR_TYPE_MAP.get(sensor_type, "Unknown")

    # Update history and calculate rolling average
    sensor_history[node_id].append(value)
    avg = sum(sensor_history[node_id]) / len(sensor_history[node_id])

    # Check for anomaly
    if abs(value - avg) > ANOMALY_THRESHOLD and len(sensor_history[node_id]) >= 3:
        print(f"🚨 Anomaly Detected! Node {node_id} | {sensor_name} = {value:.2f}°C (Avg = {avg:.2f}°C)")
    else:
        print(f"✅ Node {node_id} | {sensor_name} = {value:.2f}°C | Rolling Avg = {avg:.2f}°C | CRC OK")

