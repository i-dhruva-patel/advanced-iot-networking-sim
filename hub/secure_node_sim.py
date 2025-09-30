import socket
import struct
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import time
import random

HUB_IP = "127.0.0.1"
HUB_PORT = 9000

SECRET_KEY = b"mysecretkey12345"  # 16 bytes AES-128

def encrypt_float(value, key):
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(struct.pack("f", value)) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()
    return iv, ct

def calculate_crc(data):
    crc = 0
    for b in data:
        crc ^= b
    return crc

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

node_id = 7
sensor_type = 0x01

print(f"🔐 Secure node {node_id} sending to {HUB_IP}:{HUB_PORT}...")

while True:
    temp = random.uniform(10.0, 100.0)
    iv, encrypted_payload = encrypt_float(temp, SECRET_KEY)

    header = 0xAA
    # Build packet: header, node_id, sensor_type, IV, ciphertext
    packet = struct.pack("B", header) + struct.pack("B", node_id) + struct.pack("B", sensor_type)
    packet += iv + encrypted_payload  # total = 3 + 16 + 16 = 35 bytes before CRC

    crc = calculate_crc(packet)
    packet += struct.pack("B", crc)  # final 36 bytes

    sock.sendto(packet, (HUB_IP, HUB_PORT))
    print(f"🔐 Sent encrypted temp = {temp:.2f}°C")
    time.sleep(2)

