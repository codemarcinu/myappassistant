#!/bin/bash
set -e

echo "=== Setting up NVIDIA Container Toolkit for Docker ==="
echo ""

# Check if NVIDIA drivers are installed
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️ NVIDIA drivers don't appear to be installed or working properly."
    echo "Please install the appropriate NVIDIA drivers for your GPU before continuing."
    echo "You can run: sudo apt-get update && sudo apt-get install -y nvidia-driver-<version>"
    echo "Then reboot your system and run this script again."
    exit 1
fi

echo "✅ NVIDIA drivers found"
nvidia-smi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "⚠️ Docker is not installed. Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y docker.io
    sudo systemctl enable --now docker
else
    echo "✅ Docker is already installed"
fi

# Add current user to docker group if not already a member
if ! groups | grep -q docker; then
    echo "Adding current user to docker group..."
    sudo usermod -aG docker $USER
    echo "⚠️ You may need to log out and log back in for group changes to take effect"
fi

# Install NVIDIA Container Toolkit
echo "Installing NVIDIA Container Toolkit..."

# Add NVIDIA's GPG key and repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Update package lists and install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure the runtime and restart Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo ""
echo "=== Testing NVIDIA GPU Access in Docker ==="
echo ""

# Pull a CUDA test image and verify GPU access
docker pull nvidia/cuda:12.2.2-base-ubi8
docker run --rm --gpus all nvidia/cuda:12.2.2-base-ubi8 nvidia-smi

echo ""
echo "✅ NVIDIA Container Toolkit setup complete!"
echo "You can now build and run your Docker containers with GPU support"
echo ""
echo "Use 'docker-compose up --build' to build and run your containers with GPU support"
