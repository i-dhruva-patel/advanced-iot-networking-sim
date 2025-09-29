import socket
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque, defaultdict
import random
import time

HUB_PORT = 9000
PACKET_FORMAT = "<BBBfB"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

MAX_POINTS = 50  # number of recent values to display per node
NUM_NODES = 10   # maximum node count expected

sensor_data = defaultdict(lambda: deque(maxlen=MAX_POINTS))
node_colors = {}

def generate_color():
    return (random.random(), random.random(), random.random())

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

        if node_id not in node_colors:
            node_colors[node_id] = generate_color()

# Set up plot
fig, ax = plt.subplots()
lines = {}

def animate(frame):
    ax.clear()
    ax.set_title("🌡️ Live Sensor Data from Nodes")
    ax.set_xlabel("Latest Samples")
    ax.set_ylabel("Sensor Value (°C)")
    ax.grid(True)

    for node_id, values in sensor_data.items():
        if node_id not in lines:
            lines[node_id], = ax.plot([], [], label=f"Node {node_id}", color=node_colors[node_id])

        x_vals = list(range(len(values)))
        y_vals = list(values)
        ax.plot(x_vals, y_vals, label=f"Node {node_id}", color=node_colors[node_id])

    ax.legend(loc="upper left")

if __name__ == "__main__":
    import threading
    listener_thread = threading.Thread(target=udp_listener, daemon=True)
    listener_thread.start()

    ani = animation.FuncAnimation(fig, animate, interval=1000)
    plt.show()
