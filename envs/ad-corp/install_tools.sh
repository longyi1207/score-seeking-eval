#!/usr/bin/env bash
# Stage attacker tools via the control node (over the private VNet).
# Must run from the laptop — scripts are SSHed to ctrl (never apt on macOS).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
KEY="${SSH_KEY:-$HERE/ssh_key}"
CTRL="${CTRL_IP:-$(terraform -chdir="$HERE/infra" output -json hosts 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['ctrl']['public_ip'])")}"
ATT="${ATTACKER_IP:-10.20.1.7}"
[ -n "$CTRL" ] || { echo "no CTRL_IP / terraform hosts"; exit 1; }
cat > /tmp/_stage_adcorp.sh <<'SH'
set -uo pipefail
ATT="$1"
export DEBIAN_FRONTEND=noninteractive
echo "[ctrl] apt update + download debs (+deps)"
sudo apt-get update -q >/dev/null 2>&1
rm -rf /tmp/pkgs && mkdir -p /tmp/pkgs
sudo apt-get install --download-only -y nmap smbclient ldap-utils krb5-user dnsutils netcat-openbsd python3-pip >/dev/null 2>&1
sudo cp /var/cache/apt/archives/*.deb /tmp/pkgs/ 2>/dev/null
sudo chown "$(whoami)" /tmp/pkgs/*.deb 2>/dev/null || true
echo "[ctrl] pip download impacket wheels"
if [ -x /home/azureuser/nsvenv/bin/pip ]; then
  /home/azureuser/nsvenv/bin/pip download -q -d /tmp/pkgs impacket 2>&1 | tail -1 || true
else
  python3 -m pip download -q -d /tmp/pkgs impacket 2>&1 | tail -1 || true
fi
echo "[ctrl] downloaded $(ls /tmp/pkgs | wc -l) files -> push to attacker"
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 azureuser@$ATT 'rm -rf /tmp/pkgs && mkdir -p /tmp/pkgs'
scp -o StrictHostKeyChecking=no -q /tmp/pkgs/* azureuser@$ATT:/tmp/pkgs/
echo "[attacker] install offline"
ssh -o StrictHostKeyChecking=no azureuser@$ATT 'sudo DEBIAN_FRONTEND=noninteractive dpkg -i /tmp/pkgs/*.deb >/tmp/dpkg.log 2>&1; sudo pip3 install --no-index --find-links /tmp/pkgs impacket >/tmp/pip.log 2>&1; echo "--- tools ---"; for t in nmap smbclient ldapsearch impacket-GetUserSPNs impacket-smbclient; do printf "%s: " "$t"; command -v $t || echo MISSING; done; python3 -c "import impacket;print(\"impacket\",impacket.__version__)" 2>&1'
echo DONE
SH
scp -i "$KEY" -o StrictHostKeyChecking=no -q /tmp/_stage_adcorp.sh "azureuser@$CTRL:~/_stage.sh"
ssh -i "$KEY" -o StrictHostKeyChecking=no "azureuser@$CTRL" "bash ~/_stage.sh $ATT"
