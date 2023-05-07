data_dir = "/appdata/nomad/"
datacenter = var.datacenter
log_level = "warn"
region = "home"
bind_addr = "0.0.0.0"

server {
  enabled          = true
  authoritative_region  = "home"
  bootstrap_expect = 1
  heartbeat_grace = "300s"
  min_heartbeat_ttl = "20s"
}

acl {
  enabled = true
  token_ttl = "30s"
  policy_ttl = "60s"
}

client {
  enabled = true
  network_interface = ""

  options {
    docker.auth.config = "/root/.docker/config.json"
    docker.privileged.enabled = true
    driver.raw_exec.enable = "1"
  }

  meta {
    server = ""
    hardware = "pi4"
  }
}

telemetry {
  disable_hostname = true
  prometheus_metrics = true
  publish_allocation_metrics = true
  publish_node_metrics = true
  use_node_name = false
}

advertise {
  http = ":4646"
  rpc = ":4647"
  serf = ":4648"
}

consul {
  address = "127.0.0.1:8500"
  client_service_name = "nomad-client"
  auto_advertise = true
  server_auto_join = true
  client_auto_join = true
}

