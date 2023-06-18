server = false
ui = true
client_addr = "0.0.0.0"
advertise_addr = "{{ GetPrivateInterfaces | include \"network\" \"192.168.50.0/24\" | attr \"address\" }}"
advertise_addr_wan = "{{GetInterfaceIP \"tailscale0\"}}"
bind_addr = "{{ GetPrivateInterfaces | include \"network\" \"192.168.50.0/24\" | attr \"address\" }}"
translate_wan_addrs = true
data_dir = "/var/lib/consul"
datacenter = "homelab"
enable_syslog = true
leave_on_terminate = true
log_level = "WARN"
retry_join = ["192.168.50.219", "192.168.50.31", "192.168.50.120"]
telemetry {
  prometheus_retention_time = "60s"
}
