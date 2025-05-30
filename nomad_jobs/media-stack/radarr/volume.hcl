id           = "radarr-config"
external_id  = "radarr-config"
name         = "radarr-config"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "10GiB"
capacity_max = "10GiB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "block-device"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime", "nodiratime", "data=ordered"]
}

