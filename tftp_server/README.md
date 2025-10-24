# TFTP Server Docker Image

A Docker image based on Ubuntu 22.04 that runs an atftpd server to serve files from the `../binaries/` directory.

## Prerequisites

- Docker installed on your system
- Files to serve placed in the `../binaries/` directory (one level up from this directory)

## Building the Image

From the project root directory:
```bash
docker build -t tftp-server -f tftp_server/Dockerfile .
```

## Running the Container

```bash
docker run -d --network host --name tftp tftp-server
```

Options:
- `-d`: Run in detached mode (background)
- `--network host`: Use host networking (required for TFTP to work properly)
- `--name tftp`: Name the container "tftp" for easy reference

### From the host (using host networking)
```bash
# Using tftp client
tftp localhost -c get <filename>

# Or using atftp
atftp --get -r <filename> localhost
```

## Managing the Container

```bash
# View logs
docker logs tftp

# Stop the container
docker stop tftp

# Remove the container
docker rm tftp
```

## Notes

- The TFTP server uses atftpd running in daemon mode
- Files from the `../binaries/` directory are copied into `/tftpboot` at build time
- To update files, rebuild the image with the new contents in `../binaries/`
- TFTP runs on UDP port 69
- Host networking (`--network host`) is required due to TFTP's use of dynamic ports for data transfer
