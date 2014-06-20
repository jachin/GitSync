# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.ssh.forward_agent = true

  config.vm.define "server" do |server|
    server.vm.network "private_network", ip: "10.10.10.11"
    server.vm.host_name = "anita.vm"
    server.vm.box = "hashicorp/precise32"
    server.vm.provision :shell, path: "bootstrap_server.sh"
  end

  config.vm.define "client", primary: true do |client|
    client.vm.network "private_network", ip: "10.10.10.10"
    client.vm.host_name = "luca.vm"
    client.vm.box = "hashicorp/precise32"
    client.vm.provision :shell, path: "bootstrap_client.sh"
  end

end
