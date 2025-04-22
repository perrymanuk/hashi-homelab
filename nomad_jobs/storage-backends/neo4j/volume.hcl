# Neo4j graph database storage volume
id           = "neo4j-data"
name         = "neo4j-data"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "8GiB"
capacity_max = "8GiB"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "block-device"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime"]
}
