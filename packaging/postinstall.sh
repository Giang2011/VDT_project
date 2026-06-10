#!/bin/bash
set -e
systemctl daemon-reload
systemctl enable monitoring-agent
mkdir -p /var/log/monitoring-agent
echo "monitoring-agent installed. Start with: systemctl start monitoring-agent"
