type = "csi"
id = "example"
name = "example"
plugin_id = "nfsofficial"
external_id = "example"
capability {
  access_mode = "multi-node-multi-writer"
  attachment_mode = "file-system"
}
context {
  server = "192.168.50.208"
  share = "/mnt/pool0/share/example"
  mountPermissions = "0"  
}
mount_options {
  fs_type = "nfs"
  mount_flags = [ "timeo=30", "intr", "vers=3", "_netdev" , "nolock" ]
}
