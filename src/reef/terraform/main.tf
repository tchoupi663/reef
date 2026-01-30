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


# Disque pour VM: test4
resource "libvirt_volume" "test4_disk" {
  name           = "test4.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.ubuntu_base.id
  format         = "qcow2"
}

# Cloud-init pour VM: test4
resource "libvirt_cloudinit_disk" "test4_init" {
  name = "cloudinit-test4-34255094.iso"
  pool = "default"

  user_data = templatefile(
    "${path.module}/cloud_init.cfg",
    {
      hostname    = "test4"
            user_name   = "test4"
      user_passwd = "$6$rounds=656000$DfjH7GwG8/21c8NT$psC61vCRCAOImu.ljSjvK/vy9Wdl3x6hSflP2lSPcINFzyupAccpKIRTg7fflcxWZMlPj8VSu1lEmxL8PIUXm/"
    }
  )
}

# VM: test4
resource "libvirt_domain" "test4" {
  name      = "test4"
    memory    = 512
  vcpu      = 1
  machine   = "pc"
  arch      = "x86_64"
  type      = "qemu"
        qemu_agent  = false

  disk {
    volume_id = libvirt_volume.test4_disk.id
  }

    network_interface {
        network_name  = "default"
        # Default to waiting for DHCP lease to avoid dependency on guest agent timing
        wait_for_lease = true
    }

  cloudinit = libvirt_cloudinit_disk.test4_init.id

  depends_on = [libvirt_volume.ubuntu_base]
}

# Outputs: IP addresses for each VM (resilient)

output "test4_ip" {
    value       = try(libvirt_domain.test4.network_interface[0].addresses[0], null)
    description = "IP address of test4 (may be null until guest agent reports)"
}
