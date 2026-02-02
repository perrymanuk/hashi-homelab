type = "csi"
id = "wazuh-dashboard"
name = "wazuh-dashboard"
plugin_id = "org.democratic-csi.iscsi"

capability {
  access_mode = "single-node-writer"
  attachment_mode = "file-system"
}

# iSCSI volume will be created via democratic-csi
# No additional context needed - managed by TrueNAS/democratic-csi
