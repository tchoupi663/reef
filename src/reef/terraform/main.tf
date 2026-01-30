terraform {
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.7.6"
    }
  }
}

variable "libvirt_uri" {
  description = "URI of the libvirt daemon on the manager (with SSH credentials)"
  type        = string
  default     = "qemu:///system"
}

provider "libvirt" {
  uri = var.libvirt_uri
}

# Image Ubuntu de base
resource "libvirt_volume" "ubuntu_base" {
  name   = "ubuntu-base.qcow2"
  pool   = "default"
  source = "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
  format = "qcow2"
}


# Disque pour VM: testtt
resource "libvirt_volume" "testtt_disk" {
  name           = "testtt.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.ubuntu_base.id
  format         = "qcow2"
}

# Cloud-init pour VM: testtt
resource "libvirt_cloudinit_disk" "testtt_init" {
  name = "cloudinit-testtt-35137864.iso"
  pool = "default"

  user_data = templatefile(
    "${path.module}/cloud_init.cfg",
    {
      hostname    = "testtt"
            user_name   = "testtt"
      user_passwd = "$6$rounds=656000$IOhY7aQGQBmYapm1$1TubGoAfloYrYkBUgOLltnkbYkYBAJS3iEDDl0vkuEVZ2VUZqQCUhTXk0SB/sKJ6M.EDxKLzT7AtAuw0mNtT7."
    }
  )
}

# VM: testtt
resource "libvirt_domain" "testtt" {
  name      = "testtt"
    memory    = 512
  vcpu      = 1
  machine   = "pc"
  arch      = "x86_64"
  type      = "qemu"
        qemu_agent  = false

  disk {
    volume_id = libvirt_volume.testtt_disk.id
  }

    network_interface {
        network_name  = "default"
        # Default to waiting for DHCP lease to avoid dependency on guest agent timing
        wait_for_lease = true
    }

  cloudinit = libvirt_cloudinit_disk.testtt_init.id

  depends_on = [libvirt_volume.ubuntu_base]
}

# Outputs: IP addresses for each VM (resilient)

output "testtt_ip" {
    value       = try(libvirt_domain.testtt.network_interface[0].addresses[0], null)
    description = "IP address of testtt (may be null until guest agent reports)"
}
