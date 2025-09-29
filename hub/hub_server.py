import socket
import struct
import time
from collections import defaultdict, deque

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# --- Constants ---
HUB_IP = "0.0.0.0"
HUB_PORT = 9000
SECRET_KEY = b"mysecretkey12345"  # 16 bytes = AES-128

PACKET_SIZE = 36  # 1(header) + 1(node_id) + 1(type) + 16(IV) + 16(ciphertext) + 1(crc)
ANOMALY_THRESHOLD = 20.0
ROLLING_WINDOW = 5

# --- Data Stores ---
sensor_history = defaultdict(lambda: deque(maxlen=ROLLING_WINDOW))

# --- Decryption ---
def decrypt_payload(iv, ct):
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ct) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    raw = unpadder.update(padded_data) + unpadder.finalize()
    value = struct.unpack("f", raw)[0]
    return value

# --- UDP Setup ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HUB_IP, HUB_PORT))

print(f"🛡️ Secure Hub Listening on {HUB_IP}:{HUB_PORT} ...\n")

# --- Main Loop ---
while True:
    data, addr = sock.recvfrom(1024)

    if len(data) != PACKET_SIZE:
        print(f"⚠️ Invalid packet size from {addr}: {len(data)} bytes")
        continue

    header = data[0]
    node_id = data[1]
    sensor_type = data[2]
    iv = data[3:19]
    ciphertext = data[19:35]
    recv_crc = data[35]

    # Validate CRC
    calc_crc = 0
    for b in data[:-1]:
        calc_crc ^= b
    if calc_crc != recv_crc:
        print(f"❌ CRC mismatch from Node {node_id}")
        continue

    # Validate header
    if header != 0xAA:
        print(f"🚫 Invalid header from Node {node_id}")
        continue

    try:
        value = decrypt_payload(iv, ciphertext)
    except Exception as e:
        print(f"❌ Decryption error from Node {node_id}: {e}")
        continue

    # Update rolling average
    sensor_history[node_id].append(value)
    avg = sum(sensor_history[node_id]) / len(sensor_history[node_id])

    # Detect anomaly
    if len(sensor_history[node_id]) >= 3 and abs(value - avg) > ANOMALY_THRESHOLD:
        print(f"🚨 Anomaly Detected! Node {node_id} | Value = {value:.2f}°C (Avg = {avg:.2f}°C)")
    else:
        print(f"✅ Node {node_id} | Value = {value:.2f}°C | Rolling Avg = {avg:.2f}°C | CRC OK")

