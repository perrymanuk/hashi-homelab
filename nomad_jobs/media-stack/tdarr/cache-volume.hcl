id           = "tdarr-cache"
external_id  = "tdarr-cache"
name         = "tdarr-cache"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "150GiB"
capacity_max = "150GiB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "block-device"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime"]
}
