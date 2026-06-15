#!/bin/bash
set -e
mkdir -p /var/log/monitoring-agent
systemctl daemon-reload || true
systemctl enable monitoring-agent || true
echo "monitoring-agent installed. Start with: systemctl start monitoring-agent"
