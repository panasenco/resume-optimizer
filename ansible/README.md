## Install Ansible on Debian/Ubuntu

```
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install -y ansible
```

## Usage

On your local Debian/Ubuntu machine:

```
ansible-playbook --ask-become-pass ansible/personal-computer.yml -e "is_development=yes"
```