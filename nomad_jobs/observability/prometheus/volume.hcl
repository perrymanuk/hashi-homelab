id           = "prometheus"
external_id  = "prometheus"
name         = "prometheus"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "50GiB"
capacity_max = "50GiB"

capability {
  access_mode     = "multi-node-single-writer"
  attachment_mode = "file-system"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime"]
}

