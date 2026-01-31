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


# Disque pour VM: vm-1
resource "libvirt_volume" "vm-1_disk" {
  name           = "vm-1.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.ubuntu_base.id
  format         = "qcow2"
}

# Cloud-init pour VM: vm-1
resource "libvirt_cloudinit_disk" "vm-1_init" {
  name = "cloudinit-vm-1-56756284.iso"
  pool = "default"

  user_data = templatefile(
    "${path.module}/cloud_init.cfg",
    {
      hostname    = "vm-1"
            user_name   = "vm-1"
      user_passwd = "$6$rounds=656000$gvdbztW6.mTqxvaG$44.waBh4e8/SWZl3j9d8L853k3iSx.Sw.t5aVVi3ITfsDlk9bS5LQREhCjzh7XgIdJDNSaatdPio6L76cbrZS1"
    }
  )
}

# VM: vm-1
resource "libvirt_domain" "vm-1" {
  name      = "vm-1"
    memory    = 512
  vcpu      = 1
  machine   = "pc"
  arch      = "x86_64"
  type      = "qemu"
        qemu_agent  = false

  disk {
    volume_id = libvirt_volume.vm-1_disk.id
  }

    network_interface {
        network_name  = "default"
        # Default to waiting for DHCP lease to avoid dependency on guest agent timing
        wait_for_lease = true
    }

  cloudinit = libvirt_cloudinit_disk.vm-1_init.id

  depends_on = [libvirt_volume.ubuntu_base]
}

# Outputs: IP addresses for each VM (resilient)

output "vm-1_ip" {
    value       = try(libvirt_domain.vm-1.network_interface[0].addresses[0], null)
    description = "IP address of vm-1 (may be null until guest agent reports)"
}
