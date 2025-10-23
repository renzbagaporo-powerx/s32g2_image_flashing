FROM ubuntu:22.04

# Install atftpd (standalone TFTP server)
RUN apt-get update && \
    apt-get install -y --no-install-recommends atftpd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create TFTP directory
RUN mkdir -p /tftpboot

# Copy binaries directory to TFTP root
COPY binaries/ /tftpboot/

# Expose TFTP port
EXPOSE 69/udp

# Start TFTP server
CMD ["atftpd", "--daemon", "--no-fork", "--verbose=7", "--trace", "--logfile=-", "--port=69", "/tftpboot"]
