id        = "alertmanager"
name      = "alertmanager"
type      = "csi"
plugin_id = "org.democratic-csi.iscsi"

capacity_max = "1GB"
capacity_min = "100MB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "file-system"
}

mount_options {
  fs_type = "ext4"
}

parameters {
  fsType = "ext4"
}