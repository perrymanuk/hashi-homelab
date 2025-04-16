id           = "overseerr"
external_id  = "overseerr"
name         = "overseerr"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "2GiB"
capacity_max = "2GiB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "block-device"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime"]
}