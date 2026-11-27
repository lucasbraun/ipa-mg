# FANTASTIX

A small, fictional comic book shop for Mimir's platform IPA: three HTML pages,
one CSS file, a little vanilla JavaScript and original SVG illustrations drawn
in code. One Nginx container serves the site. There is no database, package
installation, frontend build step, checkout or external font/image dependency.

## Run on a Mac with Rancher Desktop

1. Start **Rancher Desktop** and wait until it is ready.
2. In **Settings → Container Engine**, use **dockerd (moby)** for the Docker CLI.
   Kubernetes is not needed by this project. You can leave its current setting
   alone. Switching engines changes which existing containers/images are visible;
   do not switch an engine that you are using for other work without considering that.
3. In Terminal:

   ```sh
   cd /Users/lbraun/coding/ipa/ipa-mg
   ./scripts/configure-node.sh
   docker --context rancher-desktop compose up -d --wait
   ```

4. Open **http://localhost:8080**. The same Compose file works on Apple Silicon
   and x86_64 with the corresponding Nginx image selected automatically.

Useful commands, run from this directory:

```sh
# Status and logs
docker --context rancher-desktop compose ps
docker --context rancher-desktop compose logs --tail 50 web

# Verify the response identity and health
curl -i http://localhost:8080/__node
curl http://localhost:8080/healthz

# Run the HTTP smoke test (if Python 3 is installed)
python3 tests/smoke.py

# Stop and remove this project's container/network
docker --context rancher-desktop compose down
```

If Docker is already connected to Rancher Desktop, `docker compose …` is enough.
The explicit `--context` form avoids changing your global Docker context. If port
8080 is occupied, use `HTTP_PORT=8081 docker --context rancher-desktop compose up -d`
and open port 8081 instead.

If Docker Hub's download CDN returns a 503 error, add the following to your
local `.env` and retry. It selects the public ECR mirror of the official image:

```dotenv
NGINX_IMAGE=public.ecr.aws/docker/library/nginx:1.28-alpine
```

## Files

| Path | Purpose |
| --- | --- |
| `site/index.html` | Home and featured collections |
| `site/collection.html` | Six sample items with working category filters |
| `site/about.html` | Shop story and fictional visitor information |
| `site/assets/style.css` | Responsive styling using local system fonts |
| `site/assets/*.svg` | Original comic-inspired illustrations, created in code |
| `site/assets/site.js` | Optional collection filtering; content works without JS |
| `compose.yaml` | Nginx, read-only source mounts, port, health check and restart policy |
| `nginx/templates/default.conf.template` | Nginx config and response identity |
| `scripts/configure-node.sh` | Generate the current host's fingerprint in `.env` |
| `tests/smoke.py` | HTTP, assets, links, health and identity verification |

Edit the HTML, CSS, JavaScript or SVG files and refresh the browser; no image
rebuild is needed. After changing `.env` or the Nginx template, recreate the
container with `docker compose up -d --force-recreate` (with the context option on
Rancher Desktop). The source directory is mounted read-only inside the container.

## Which VM served the page?

The footer on **each HTML page** shows a `vm-…` fingerprint. Nginx inserts it
into the HTML using server-side includes (SSI), in the same response as the page.
There is no separate browser request for the identity that could land on another
backend. It is also available as:

- Response header: `X-Served-By: vm-…`
- Plain-text endpoint: `GET /__node`

`configure-node.sh` hashes a namespaced host identifier with SHA-256 and uses its
first 12 hexadecimal characters. On Linux the input is `/etc/machine-id`; on
macOS it is the hardware UUID. The raw identifier and IP address are not sent to
the browser. This is a diagnostic label, not an authentication or security feature.
It is a **host fingerprint**, not the container IP, which can change on recreation.

**Run the setup script on every new VM.** Keep `.env` out of Git and remove it
from any reusable VM image. Image preparation must also ensure that cloned VMs
receive unique machine IDs. Rerunning the script cannot distinguish VMs that
incorrectly share the same machine ID. Recreating a container on the same host
keeps the fingerprint stable.

You can inspect distribution with repeated requests through the future load
balancer (replace the URL with its real HTTPS IP endpoint):

```sh
for i in $(seq 1 100); do
  curl --fail --silent --show-error https://LOAD_BALANCER_IP/__node || break
done | sort | uniq -c
```

Use the valid IP certificate; do not add `-k`. Check that all expected fingerprints
appear and evaluate their counts against the chosen balancing algorithm. The
site sets `Cache-Control: no-store` and does not set session cookies. The load
balancer must likewise avoid caching and forced session persistence for this test.
`/__node` complements the full-page and functional tests; it does not replace them.

## Later on the Linux VMs

Use the same repository and Compose file with Docker Engine and the Compose
plugin installed. Run `./scripts/configure-node.sh` on the VM itself, then set
these values in its local `.env`:

```dotenv
# Keep the SERVER_ID generated on this VM.
BIND_ADDRESS=THE_VM_PRIVATE_IP
HTTP_PORT=80
```

Run `docker compose up -d --wait`. The OCI load balancer can use HTTP to port 80
and `/healthz` for health checks. Restrict backend access to the load balancer
and health-check sources with OCI network rules and the host/container firewall
configuration. Public HTTPS and certificate handling belong on the load balancer;
this sample deliberately serves HTTP inside the private network.

The Compose file uses the versioned `nginx:1.28-alpine` tag. Record the actual
image version/digest used for the IPA and use the same image on all backends.
This repository supplies the sample application; the migration, deployment
script, VM image preparation and infrastructure remain Mimir's project work.

## Fictional content

FANTASTIX, its shop, prices and opening hours are fictional. Asterix, Lucky Luke
and Tintin are used as references to the comic collections; the SVG pictures are
original comic-inspired illustrations and do not reproduce official book covers.
No messages are sent and no orders or payments are accepted.

References: [Rancher Desktop container engines](https://docs.rancherdesktop.io/ui/preferences/container-engine/general/),
[official Nginx image](https://hub.docker.com/_/nginx),
[Compose environment interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/).
