id           = "radarr3"
external_id  = "radarr3"
name         = "radarr3"
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
  mount_flags = ["noatime"]
}

