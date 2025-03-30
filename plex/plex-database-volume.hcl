id           = "plex-database"
external_id  = "plex-database"
name         = "plex-database"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "20GiB"
capacity_max = "20GiB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "block-device"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime", "nodiratime", "discard", "data=ordered"]
}
