// =============================================================================
// Nomad CSI Volume Template
// =============================================================================
//
// Usage:
//   1. Copy this file to nomad_jobs/<category>/<service-name>/volume.hcl
//   2. Replace __VOL_NAME__ with the volume name (usually same as service name)
//   3. Replace __SIZE__ with capacity (e.g. "5GiB", "10GiB", "50GiB")
//   4. Set access_mode based on your needs (see below)
//   5. Volume is auto-created by CI when pushed (if path is in workflow filter)
//
// Access modes:
//   single-node-writer       : one node read/write (most services)
//   single-node-reader-only  : one node read-only
//   multi-node-single-writer : multiple nodes can mount, one writes (HA failover)
//
// Size guide:
//   Config-only (app state):  1-5 GiB
//   Small databases:          5-10 GiB
//   Media metadata/indexes:   10-20 GiB
//   Time-series / logs:       50-100 GiB
//
// =============================================================================

id           = "__VOL_NAME__"
external_id  = "__VOL_NAME__"
name         = "__VOL_NAME__"
type         = "csi"
plugin_id    = "org.democratic-csi.iscsi"
capacity_min = "__SIZE__"
capacity_max = "__SIZE__"

capability {
  access_mode     = "single-node-writer"
  attachment_mode = "file-system"
}

mount_options {
  fs_type     = "ext4"
  mount_flags = ["noatime"]
}
