# Docker Setup — Homelab Monitoring Stack

## Overview

This project is a hands-on learning environment for container fundamentals,
built as the foundation for a home lab monitoring stack. It consists of a
custom Python metrics exporter and an nginx container, deployed with
Docker Compose on a single Linux host. The goal was to understand how
containers actually work at the kernel level — networking, process
isolation, image layers, and data persistence — rather than just running
pre-made images.

## Environment

- OS: Ubuntu 26.04 (Dell Precision 5690)
- Docker Engine: 29.9.0
- Storage driver: overlayfs — how Docker stores image layers and the
  container writable layer on the filesystem
- Cgroup driver: systemd — how Docker registers resource limits with the
  init system
- Kernel: 7.0.0-38-generic

## Architecture

Two services on a user-defined bridge network (`monitor-net`):

- **exporter** — a Python application exposing custom metrics on port 8000
  inside the container, published on host port 8001 (`8001:8000`).
  Runs with `restart: unless-stopped`.
- **nginx-test** — an nginx container serving on container port 80,
  published on host port 8080 (`8080:80`).

Both containers join `monitor-net`, a user-defined bridge network created
by Compose. Docker runs an embedded DNS server (127.0.0.11) on this
network, so containers resolve each other by service name — `nginx-test`
reaches the exporter at `http://exporter:8000/metrics` without knowing
its IP.

The `depends_on` directive controls startup order (exporter starts first),
but it does NOT wait for the exporter to be ready — it only guarantees
that the container has started.

Default gateway for containers is the docker0 bridge at 172.17.0.1.

## Key Concepts Applied

### Containers vs virtual machines

Containers share the host kernel — they are regular Linux processes with
isolated views (namespaces), resource limits (cgroups), and a layered
filesystem (overlayfs). VMs run a full guest OS with their own kernel,
which is why a container starts in milliseconds and a VM boots in minutes.

### Network namespaces, veth, and the docker0 bridge

Each container gets its own network namespace: its own interfaces, routing
table, and IP stack. Docker connects it to the host through a virtual
Ethernet pair (veth) — one end lives in the container as `eth0`, the other
is plugged into the `docker0` bridge, which acts as a Layer 2 switch.
Containers on the same bridge communicate directly at L2, without passing
through the gateway.

### Published ports (DNAT) and outbound traffic (MASQUERADE)

Publishing a port with `-p 8080:80` creates a DNAT rule in iptables: every
packet arriving at the host on port 8080 is rewritten to the container IP
and port. Outbound traffic from containers passes a MASQUERADE rule that
rewrites the source address to the host IP; conntrack reverses the
translation for reply packets. Both the veth pair and the DNAT rule live
exactly as long as the container.

### Image layers, copy-on-write, and build cache

Only filesystem-modifying instructions (RUN, COPY, ADD) create layers;
metadata instructions (ENV, CMD, EXPOSE) do not. Each container adds a
thin writable layer on top of the read-only image layers — modifying a
file triggers copy-on-write into that layer. Build cache is validated
instruction by instruction: the first change invalidates everything below
it, so rarely-changed, expensive operations (dependency installation)
must come before frequently-changed ones (application code). Verified
empirically: a rebuild with cached layers took 0.1s versus 32s for a
full one.

### Multi-stage build

A builder stage with the toolchain (gcc) compiles the artifact, and only
the resulting binary is copied into a clean runtime stage. The final image
was 3.88 MB instead of roughly 200 MB — no compiler, no build tools in
production, faster pulls, smaller attack surface.

### Volumes vs bind mounts

A named volume is managed by Docker and stored under
`/var/lib/docker/volumes/`; it survives container removal and is seeded
with image content on first mount. A bind mount maps an arbitrary host
path chosen by the user, supports read-only mode (`:ro` restricts the
container, not the host), and is convenient for configuration files.
Data written to the container's own writable layer is lost on `docker rm`.

## How to Run

```bash
docker compose up -d                        # start in background
docker compose ps                           # check status
curl http://localhost:8001/metrics          # verify exporter
curl -o /dev/null -w "%{http_code}\n" http://localhost:8080   # verify nginx
docker compose down                         # stop and clean up
