# GPU Acceleration Setup for AI Assistant

This guide explains how to set up and use GPU acceleration with our Docker-based AI assistant.

## Prerequisites

- A system with NVIDIA GPU
- Ubuntu operating system
- NVIDIA drivers installed for your GPU
- Docker and NVIDIA Container Toolkit

## Automated Setup

We've provided a setup script to help you install the NVIDIA Container Toolkit:

```bash
# Make the script executable (if not already)
chmod +x scripts/setup_nvidia_docker.sh

# Run the script
./scripts/setup_nvidia_docker.sh
```

The script will:
1. Check if NVIDIA drivers are installed
2. Install Docker if needed
3. Install NVIDIA Container Toolkit
4. Configure Docker to work with NVIDIA GPUs
5. Test GPU access with a simple container

## Manual Setup

If you prefer to set things up manually, follow these steps:

1. **Install NVIDIA GPU Drivers**
   ```bash
   sudo apt-get update
   sudo apt-get install -y nvidia-driver-<version>
   sudo reboot
   ```

2. **Install Docker Engine**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo systemctl enable --now docker
   ```

3. **Install NVIDIA Container Toolkit**
   ```bash
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
   ```

4. **Test GPU Access in Docker**
   ```bash
   docker pull nvidia/cuda:12.2.2-base-ubi8
   docker run --rm --gpus all nvidia/cuda:12.2.2-base-ubi8 nvidia-smi
   ```

## Building and Running with GPU Support

The `docker-compose.yml` file has been updated to include GPU support. To build and run the containers:

```bash
# Remove existing containers and volumes
docker-compose down -v

# Build and start containers with GPU support
docker-compose up --build
```

## Verifying GPU Usage

You can verify that your application is using the GPU by:

1. Running `nvidia-smi` on the host while the containers are running
2. Looking for GPU processes associated with your containers

## Troubleshooting

If you encounter issues:

1. **Error: "could not select device driver with capabilities: [[gpu]]"**
   - The NVIDIA Container Toolkit is not properly installed or configured
   - Re-run the setup script or manually configure the toolkit

2. **No GPU detected in container:**
   - Check that your NVIDIA drivers are working: `nvidia-smi`
   - Ensure the `--gpus all` flag is used or properly configured in docker-compose.yml

3. **Performance issues:**
   - Check GPU memory usage with `nvidia-smi`
   - You might need to adjust model parameters or batch sizes to fit in GPU memory

## Additional Resources

- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker GPU Documentation](https://docs.docker.com/config/containers/resource_constraints/#gpu)
