#!/bin/bash
set -e

VERSION=${VERSION:-1.0.0}
PROJECT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
BUILD_DIR="$PROJECT_ROOT/packaging/build"
OUTPUT_DIR="$PROJECT_ROOT/dist"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/vendor" "$BUILD_DIR/bin" "$OUTPUT_DIR"

pip install --upgrade --target="$BUILD_DIR/vendor" "$PROJECT_ROOT"

cat > "$BUILD_DIR/bin/monitoring-agent" <<'EOF'
#!/bin/bash
set -euo pipefail
export PYTHONPATH="/usr/lib/monitoring-agent/vendor:${PYTHONPATH:-}"
exec python3 -m monitoring_agent.main "$@"
EOF
chmod +x "$BUILD_DIR/bin/monitoring-agent"

fpm -s dir -t deb \
  -n monitoring-agent \
  -v "$VERSION" \
  --description "Linux system monitoring background service" \
  --url "https://github.com/yourname/monitoring-agent" \
  --license "MIT" \
  --maintainer "Your Name <you@example.com>" \
  --after-install "$PROJECT_ROOT/packaging/postinstall.sh" \
  --after-remove "$PROJECT_ROOT/packaging/preremove.sh" \
  --deb-no-default-config-files \
  --package "$OUTPUT_DIR/monitoring-agent_${VERSION}_all.deb" \
  "$BUILD_DIR/vendor/=/usr/lib/monitoring-agent/vendor" \
  "$BUILD_DIR/bin/monitoring-agent=/usr/bin/monitoring-agent" \
  "$PROJECT_ROOT/systemd/monitoring-agent.service=/lib/systemd/system/monitoring-agent.service" \
  "$PROJECT_ROOT/config/config.yaml.example=/etc/monitoring-agent/config.yaml.example" \
  "$PROJECT_ROOT/config/logrotate.conf=/etc/logrotate.d/monitoring-agent" \
