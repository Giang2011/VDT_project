#!/bin/bash
systemctl stop monitoring-agent  || true
systemctl disable monitoring-agent || true
