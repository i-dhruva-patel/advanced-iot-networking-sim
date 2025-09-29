import socket
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque, defaultdict
import random
import time

# Constants
HUB_PORT = 9000
PACKET_FORMAT = "<BBBfB"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)
MAX_POINTS = 50
ANOMALY_THRESHOLD = 20.0

# Data stores
sensor_data = defaultdict(lambda: deque(maxlen=MAX_POINTS))
node_colors = {}
anomalies = defaultdict(list)  # node_id: list of (index, value)

def generate_color():
    return (random.random(), random.random(), random.random())

# UDP Receiver thread
def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", HUB_PORT))
    print(f"📡 Listening on port {HUB_PORT}...")

    while True:
        data, addr = sock.recvfrom(1024)
        if len(data) != PACKET_SIZE:
            continue

        header, node_id, sensor_type, value, crc = struct.unpack(PACKET_FORMAT, data)
        if header != 0xAA:
            continue

        sensor_data[node_id].append(value)

        # Rolling average for anomaly detection
        vals = list(sensor_data[node_id])
        avg = sum(vals) / len(vals)
        if abs(value - avg) > ANOMALY_THRESHOLD and len(vals) >= 3:
            anomalies[node_id].append((len(vals) - 1, value))  # index and value

        if node_id not in node_colors:
            node_colors[node_id] = generate_color()

# Plotting setup
fig, ax = plt.subplots()

def animate(frame):
    ax.clear()
    ax.set_title("🌡️ Real-Time Sensor Data (Anomalies in 🔴)")
    ax.set_xlabel("Latest Samples")
    ax.set_ylabel("Sensor Value (°C)")
    ax.grid(True)

    for node_id, values in sensor_data.items():
        x_vals = list(range(len(values)))
        y_vals = list(values)
        color = node_colors[node_id]

        # Plot main line
        ax.plot(x_vals, y_vals, label=f"Node {node_id}", color=color)

        # Plot anomalies as red dots
        for idx, val in anomalies[node_id]:
            if idx < len(x_vals):
                ax.plot(x_vals[idx], y_vals[idx], 'ro')  # red circle

    ax.legend(loc="upper left")

# Launch
if __name__ == "__main__":
    import threading
    threading.Thread(target=udp_listener, daemon=True).start()
    ani = animation.FuncAnimation(fig, animate, interval=1000)
    plt.show()

