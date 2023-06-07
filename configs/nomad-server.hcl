data_dir = "/appdata/nomad/"
datacenter = "dc1"
log_level = "warn"
region = "home"
bind_addr = "{{ GetInterfaceIP \"tailscale0\" }}"

server {
  enabled               = true
  authoritative_region  = "home"
  heartbeat_grace       = "300s"
  min_heartbeat_ttl     = "20s"
}

client {
  enabled = true
  # You will need to adjust this for the CIDR for your lan
  network_interface = "{{ GetPrivateInterfaces | include \"network\" \"192.168.50.0/24\" | attr \"name\" }}"

  options {
    docker.auth.config = "/root/.docker/config.json"
    docker.privileged.enabled = true
    driver.raw_exec.enable = "1"
    docker.volumes.enabled = true
  }

  meta {
    server = "usually the name"
    hardware = "vm/nuk/pi/pi4/etc"
    shared_mount = "true"
    dns = "true"
    keepalived_priority = "100"
  }

# You will need to adjust this for the CIDR for your lan
  host_network "lan" {
    cidr = "192.168.50.0/24"
  }

  host_network "tailscale" {
    cidr = "100.0.0.0/8"
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
  http = "{{ GetInterfaceIP \"tailscale0\" }}:4646"
  rpc = "{{ GetInterfaceIP \"tailscale0\" }}:4647"
  serf = "{{ GetInterfaceIP \"tailscale0\" }}:4648"
}

consul {
  # The address to the Consul agent.
  address = "{{ GetInterfaceIP \"tailscale0\" }}:8500"

  # The service name to register the server and client with Consul.
  client_service_name = "nomad-client"

  # Enables automatically registering the services.
  auto_advertise = true

  # Enabling the server and client to bootstrap using Consul.
  server_auto_join = true
  client_auto_join = true
}

# I have switched to using github secrets rather than vault
#vault {
#  enabled = true
#  address = "http://vault.service.home:8200"
#  allow_unauthenticated = true
#  create_from_role = "nomad-cluster"
#}

plugin "docker" {
  config {
    allow_caps = ["CHOWN","DAC_OVERRIDE","FSETID","FOWNER","MKNOD","NET_RAW","SETGID","SETUID","SETFCAP","SETPCAP"," NET_BIND_SERVICE","SYS_CHROOT","KILL","AUDIT_WRITE","NET_ADMIN"]
    # extra Docker labels to be set by Nomad on each Docker container with the appropriate value
    extra_labels = ["job_name", "task_group_name", "task_name", "namespace", "node_name"]
    allow_privileged = true
    volumes {
      enabled      = true
      selinuxlabel = "z"
    }
  }
}
