import subprocess
import time
import random
import os
import signal

NODE_PATH = "../node"  # compiled C sensor node binary
NODE_ID = 4            # pick a new node ID for injection
DROP_PROBABILITY = 0.2
DELAY_PROBABILITY = 0.3

def start_node():
    print(f"🚀 Starting Node {NODE_ID}...")
    return subprocess.Popen([NODE_PATH, str(NODE_ID)])

def kill_node(proc):
    print(f"💀 Killing Node {NODE_ID} (simulated crash)...")
    proc.send_signal(signal.SIGINT)  # emulate Ctrl+C
    proc.wait()

def fault_loop():
    node_proc = start_node()

    try:
        while True:
            time.sleep(random.uniform(2, 4))

            action = random.choice(["drop", "delay", "crash", "nothing"])

            if action == "drop":
                print(f"🚫 Packet Drop Simulated (ignoring send)")
                kill_node(node_proc)  # simulate drop by kill + no restart for a few secs
                time.sleep(3)
                node_proc = start_node()

            elif action == "delay":
                print(f"⏱ Injecting Delay...")
                kill_node(node_proc)
                time.sleep(6)  # hub should flag it as offline
                node_proc = start_node()

            elif action == "crash":
                print(f"🔥 Random Crash & Reboot")
                kill_node(node_proc)
                time.sleep(2)
                node_proc = start_node()

            else:
                print("✅ Node behaving normally")

    except KeyboardInterrupt:
        kill_node(node_proc)
        print("🛑 Fault injector stopped.")

if __name__ == "__main__":
    fault_loop()
