# Count messages per topic for a fixed window inside the stack (rclpy, because ros2 topic echo and hz are unreliable via docker exec here).
# Usage: python3 topic_rates.py [window_seconds]
import sys
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

DEFAULT_WINDOW_S = 30.0
DISCOVERY_WARMUP_S = 3.0   # time for DDS discovery to match the publishers before counting starts
SPIN_TIMEOUT_S = 0.1       # longest single wait for a callback, so the loop checks its deadline often
QUEUE_DEPTH = 10           # subscription history depth (ROS 2 default)
TOPICS = {"/status_frames": Image, "/failsafe_md": String, "/red_zone_alert": String}


def spin_until(node, deadline):
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=SPIN_TIMEOUT_S)


window_s = float(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WINDOW_S
rclpy.init()
node = Node("topic_rate_probe")
counts = {topic: 0 for topic in TOPICS}


def make_counter(topic):
    def count_message(_message):
        counts[topic] += 1
    return count_message


for topic, message_type in TOPICS.items():
    node.create_subscription(message_type, topic, make_counter(topic), QUEUE_DEPTH)

# Spin through the warm-up so messages queued during discovery are delivered (and discarded) before the reset;
# a plain sleep would leave them queued and they would land in the measured window.
spin_until(node, time.monotonic() + DISCOVERY_WARMUP_S)
for topic in counts:
    counts[topic] = 0   # reset in place; the callbacks hold this same dict
spin_until(node, time.monotonic() + window_s)
for topic, count in counts.items():
    print(f"{topic}: {count} msgs in {window_s:.0f} s = {count / window_s:.2f} Hz")
node.destroy_node()
rclpy.shutdown()
