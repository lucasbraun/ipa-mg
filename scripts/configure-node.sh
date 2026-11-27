#!/bin/sh
# Run on EACH host, including every VM created from a golden image.
set -eu
cd "$(dirname "$0")/.."

if [ "${1:-}" = "--help" ]; then
    printf '%s\n' 'Usage: ./scripts/configure-node.sh' \
        'Writes a stable, hashed host identifier to .env. Rerun on each new VM.'
    exit 0
fi
if [ "$#" -ne 0 ]; then
    printf '%s\n' 'Unexpected argument. Use --help.' >&2
    exit 1
fi

case "$(uname -s)" in
    Linux)
        if [ ! -s /etc/machine-id ]; then
            printf '%s\n' 'Missing /etc/machine-id. Initialize the VM identity first.' >&2
            exit 1
        fi
        identity=$(cat /etc/machine-id)
        ;;
    Darwin)
        # Run on macOS itself, not inside Rancher Desktop’s shared Linux VM.
        identity=$(ioreg -rd1 -c IOPlatformExpertDevice | awk -F '"' '/IOPlatformUUID/ {print $(NF-1); exit}')
        ;;
    *)
        printf '%s\n' 'Supported setup hosts: Linux and macOS.' >&2
        exit 1
        ;;
esac
[ -n "$identity" ] || { printf '%s\n' 'Could not determine host identity.' >&2; exit 1; }
if command -v sha256sum >/dev/null 2>&1; then
    digest=$(printf '%s' "fantastix:$identity" | sha256sum)
else
    digest=$(printf '%s' "fantastix:$identity" | shasum -a 256)
fi
server_id="vm-$(printf '%s' "$digest" | cut -c 1-12)"

# Preserve the user's port and bind-address settings and replace only SERVER_ID.
umask 077
temp=$(mktemp .env.XXXXXX)
trap 'rm -f "$temp"' EXIT HUP INT TERM
if [ -f .env ]; then
    sed '/^[[:space:]]*\(export[[:space:]][[:space:]]*\)\{0,1\}SERVER_ID[[:space:]]*=/d' .env > "$temp"
fi
printf '\nSERVER_ID=%s\n' "$server_id" >> "$temp"
mv "$temp" .env
printf 'Configured serving node: %s\n' "$server_id"
