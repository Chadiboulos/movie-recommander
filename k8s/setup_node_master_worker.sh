# scipt a executer sur tout les machine
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# sur la machine qui aura le noeud master
sudo kubeadm init
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml


# sur les machine worker
sudo kubeadm join <IP>--token meziqg.c0qqgasgzch8ncdf --discovery-token-ca-cert-hash sha256:<HASHCODE>