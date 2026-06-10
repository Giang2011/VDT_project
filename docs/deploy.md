# Deployment Guide — System Monitoring Agent

## 1. Prerequisites

Before deploying `monitoring-agent`, make sure the target system has the following:

- A Linux distribution with `systemd`
- Python 3.10 or newer
- `pip` and build tools available for local testing
- `fpm` installed for package creation
- Root or sudo access for installation, log directory creation, and service management

### Installing prerequisites on a Debian/Ubuntu build machine

```bash
sudo apt update
sudo apt install -y python3 python3-pip ruby ruby-dev build-essential
sudo gem install fpm
```

### Installing prerequisites on a RHEL/Fedora build machine

```bash
sudo dnf install -y python3 python3-pip ruby ruby-devel gcc make redhat-rpm-config
sudo gem install fpm
```

## 2. Build the `.deb` Package

Use the packaging script from the project root.

### Step-by-step

1. Install Python dependencies for building the project.
2. Run the Debian build script.
3. Confirm that the `.deb` file is written to the root `dist/` directory.

```bash
cd packaging
bash build_deb.sh
```

### What the script does

- Installs the Python package into a temporary build directory
- Creates a Debian package with `fpm`
- Bundles the application code, systemd service file, config template, and logrotate file
- Runs the post-install and pre-remove maintainer scripts

## 3. Install and Verify on Debian/Ubuntu

After building the package, install it on the target machine.

### Installation

```bash
sudo dpkg -i ../dist/monitoring-agent_1.0.0_amd64.deb
```

If dependencies are missing, fix them with:

```bash
sudo apt -f install
```

### Verify installation

Check that the service exists and is enabled:

```bash
systemctl status monitoring-agent
systemctl is-enabled monitoring-agent
```

Start the service if needed:

```bash
sudo systemctl start monitoring-agent
```

View logs:

```bash
journalctl -u monitoring-agent -f
```

Confirm the log file exists:

```bash
sudo ls -l /var/log/monitoring-agent/agent.log
```

## 4. Build the `.rpm` Package

The RPM build process is similar.

### Step-by-step

1. Install the same Python and `fpm` prerequisites.
2. Run the RPM build script.
3. Confirm that the `.rpm` file is written to the root `dist/` directory.

```bash
cd packaging
bash build_rpm.sh
```

## 5. Install and Verify on RHEL/Fedora

### Installation

```bash
sudo rpm -i ../dist/monitoring-agent-1.0.0-1.x86_64.rpm
```

If you prefer the package manager:

```bash
sudo dnf install ../dist/monitoring-agent-1.0.0-1.x86_64.rpm
```

### Verify installation

Check service status:

```bash
systemctl status monitoring-agent
systemctl is-enabled monitoring-agent
```

Start the service:

```bash
sudo systemctl start monitoring-agent
```

Follow the logs:

```bash
journalctl -u monitoring-agent -f
```

## 6. Manual Development Run

For local development, run the agent directly from the source tree.

### Recommended steps

1. Create and activate a virtual environment.
2. Install dependencies.
3. Copy or edit a config file for local paths.
4. Run the agent with the `--config` option.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m monitoring_agent.main --config config/config.yaml.example
```

If the example config contains paths that do not exist on your system, adjust them before running.

## 7. Demo Checklist

Use the following checklist when recording the demo video:

- Show the project structure and explain the main modules
- Show the sample configuration file and explain important keys
- Build the `.deb` package successfully
- Install the package on a Linux VM or container
- Show `systemctl status monitoring-agent`
- Show live log output with `journalctl -u monitoring-agent -f`
- Trigger a filesystem event in a watched directory and show the log entry
- Demonstrate a threshold warning by lowering a limit in the config
- Show the log file in `/var/log/monitoring-agent/`
- Stop the service cleanly and show that it shuts down without errors

## 8. Suggested Verification Commands

```bash
systemctl status monitoring-agent
journalctl -u monitoring-agent --no-pager | tail -n 50
sudo cat /var/log/monitoring-agent/agent.log
```

These commands help confirm that the agent is running, producing logs, and responding correctly to configuration and filesystem activity.
