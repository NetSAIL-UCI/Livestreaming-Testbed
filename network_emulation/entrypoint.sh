#!/bin/bash
set -e

echo "=== Traffic Shaper Container Starting ==="

# Detect network interfaces (first 2 non-loopback interfaces)
# Strip "@ifXX" suffix that Docker adds to interface names
INTERFACES_RAW=($(ip -o link show | awk -F': ' '{print $2}' | grep -v lo | head -2))

if [ ${#INTERFACES_RAW[@]} -lt 2 ]; then
    echo "ERROR: Need at least 2 network interfaces, found ${#INTERFACES_RAW[@]}"
    exit 1
fi

# Extract interface name without "@ifXX" suffix
CLIENT_IF=$(echo ${INTERFACES_RAW[0]} | cut -d'@' -f1)
SERVER_IF=$(echo ${INTERFACES_RAW[1]} | cut -d'@' -f1)

export CLIENT_IF
export SERVER_IF

echo "Detected interfaces:"
echo "  CLIENT_IF: $CLIENT_IF"
echo "  SERVER_IF: $SERVER_IF"

# Apply initial trivial tc rule (passthrough)
echo "Applying initial passthrough configuration..."

# Clear existing rules on client interface
tc qdisc del dev $CLIENT_IF root 2>/dev/null || true
tc qdisc add dev $CLIENT_IF root handle 1: prio
tc qdisc add dev $CLIENT_IF parent 1:1 handle 2: netem delay 0ms
tc filter add dev $CLIENT_IF protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:1

# Clear existing rules on server interface
tc qdisc del dev $SERVER_IF root 2>/dev/null || true
tc qdisc add dev $SERVER_IF root handle 1: prio
tc qdisc add dev $SERVER_IF parent 1:1 handle 2: netem delay 0ms
tc filter add dev $SERVER_IF protocol ip parent 1:0 prio 1 u32 match ip dst 0.0.0.0/0 flowid 1:1

echo "Initial configuration applied. Traffic shaper ready."
echo "Use scripts/apply_static_profile.py or scripts/replay_trace.py to configure network conditions."

# Start a simple status server (optional)
python3 -m http.server 8888 &
STATUS_PID=$!

# Keep container running
trap "kill $STATUS_PID 2>/dev/null || true; exit" SIGTERM SIGINT
wait

