id           = "actualbudget-data"
external_id  = "actualbudget-data"
name         = "actualbudget-data"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "5GiB"
capacity_max = "5GiB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "block-device"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime", "nodiratime", "data=ordered"]
}