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

def encrypt_float(value):
    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(struct.pack("f", value)) + padder.finalize()

    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()

    return iv, ct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

node_id = 7
sensor_type = 0x01

while True:
    temp = random.uniform(10.0, 100.0)
    iv, encrypted_payload = encrypt_float(temp)

    header = 0xAA
    packet = struct.pack("B", header) + struct.pack("B", node_id) + struct.pack("B", sensor_type) + iv + encrypted_payload

    crc = 0
    for b in packet:
        crc ^= b
    packet += struct.pack("B", crc)

    sock.sendto(packet, (HUB_IP, HUB_PORT))
    print(f"🔐 Sent encrypted temp = {temp:.2f}°C")
    time.sleep(2)
