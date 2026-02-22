id           = "3dprints"
external_id  = "3dprints"
name         = "3dprints"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "40GiB"
capacity_max = "40GiB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "block-device"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime"]
}
