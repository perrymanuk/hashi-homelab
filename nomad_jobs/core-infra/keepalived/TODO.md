# Keepalived Improvements TODO

## Problem
The osixia/keepalived image uses environment variables (env.yaml) to generate keepalived.conf at startup. This doesn't support dynamic config reloads via SIGHUP because the conf isn't regenerated from env vars on signal.

Combined with Nomad templates that use `change_mode = "restart"` and dynamic Consul service lookups, this causes restart loops.

## Proposed Solution
Replace osixia/keepalived with plain keepalived using a direct config template:

```hcl
config {
  image = "osixia/keepalived:2.0.20"  # or alpine + keepalived
  volumes = [
    "local/keepalived.conf:/etc/keepalived/keepalived.conf"
  ]
}

template {
  destination = "local/keepalived.conf"
  change_mode = "signal"
  change_signal = "SIGHUP"
  data = <<EOH
vrrp_instance VI_1 {
  state BACKUP
  interface {{ sockaddr "GetPrivateInterfaces | include \"network\" \"192.168.50.0/24\" | attr \"name\"" }}
  virtual_router_id 51
  priority 100
  nopreempt
  virtual_ipaddress {
    192.168.50.50/24
  }
}
EOH
}
```

## Alternatives Considered
- **vip-manager** - lightweight, single purpose
- **kube-vip** - modern, supports ARP/BGP
- **ucarp** - simple CARP implementation

## Affected Jobs
- `nomad_jobs/core-infra/coredns/nomad.job` (keepalived-dns sidecar)
- `nomad_jobs/core-infra/traefik/nomad.job` (keepalived-traefik sidecar)
