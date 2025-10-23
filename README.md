# Flashing NXP Auto Linux Images to S32G2

Tools and scripts for flashing NXP Auto Linux images to the S32G274A-RDB2 board via SPI NOR flash and eMMC.

## Overview

This repository provides two main flashing methods:

1. **SPI NOR Flash** - Flash U-Boot bootloader to SPI NOR using S32 Flash Tool
2. **eMMC** - Flash full Linux images to eMMC using U-Boot over serial

## Prerequisites

- S32G274A-RDB2 board
- Serial connection (e.g., `/dev/ttyUSB0`)
- S32 Design Studio (for S32 Flash Tool)
- Docker (for TFTP server)
- Python 3 with pyserial (`pip3 install pyserial`)

## Method 1: SPI NOR Flash

Flash the U-Boot bootloader to SPI NOR flash using the S32 Flash Tool.

### Hardware Setup

1. Configure the board boot mode switches to boot from SPI NOR flash
2. Connect serial cable to the board

### Flashing

The S32 Flash Tool is included with S32 Design Studio. On Linux, it's typically located at:
```
/usr/local/NXP/S32DS.x.y.z/S32DS/tools/S32FlashTool/
```

Example command to read SPI flash:
```bash
S32FlashTool -fread -addr 0 -size 67108864 -i uart -p /dev/ttyUSB0 -b -f dump.bin
```

See `s32_flash_tool_commands.txt` for additional command examples.

## Method 2: eMMC Flash

Flash a complete Linux image to the board's eMMC using U-Boot and TFTP.

### Prerequisites

- Board must have U-Boot in SPI NOR flash (either factory default or flashed using Method 1)
- Board configured to boot from SPI NOR flash
- TFTP server running on host machine

### Step 1: Set Up TFTP Server

The `tftp_server` directory contains a Docker-based TFTP server:

```bash
cd tftp_server

# Place your image file in binaries/ directory
cp /path/to/fsl-image-auto-s32g274ardb2.sdcard binaries/

# Build and run the TFTP server
docker build -t tftp-server .
docker run -d --network host --name tftp tftp-server
```

See `tftp_server/README.md` for more details.

### Step 2: Flash to eMMC

Use the `emmc_flash.py` script to automate the flashing process:

```bash
python3 emmc_flash.py \
  -d /dev/ttyUSB0 \
  -i 192.168.55.3 \
  -n 255.255.255.0 \
  -s 192.168.55.1 \
  -f fsl-image-auto-s32g274ardb2.sdcard \
  -a A0000000
```

**Parameters:**
- `-d, --device`: Serial device (e.g., `/dev/ttyUSB0`)
- `-i, --ip`: IP address for the device running U-Boot
- `-n, --netmask`: Network mask (e.g., `255.255.255.0`)
- `-s, --server`: TFTP server IP address
- `-f, --file`: Image file path (for block calculation; must exist locally)
- `-a, --address`: Memory address for TFTP load (e.g., `A0000000`)

The script will:
1. Calculate the required number of blocks based on file size
2. Configure U-Boot network settings
3. Download the image via TFTP to RAM
4. Write the image to eMMC
5. Wait for each operation to complete (no timeout)

See `uboot_commands.txt` for the underlying U-Boot commands being executed.

## Network Configuration

The default network configuration assumes:
- Board IP: `192.168.55.3`
- Host/TFTP Server IP: `192.168.55.1`
- Netmask: `255.255.255.0`

Adjust these values based on your network setup.

## Troubleshooting

### Serial Connection Issues
- Verify the correct serial device (e.g., `/dev/ttyUSB0`)
- Check user permissions: `sudo usermod -a -G dialout $USER`
- Ensure no other program is using the serial port

### TFTP Issues
- Verify TFTP server is running: `docker ps`
- Check connectivity: `tftp localhost -c get <filename>`
- Ensure firewall allows UDP port 69
- Verify file exists in `tftp_server/binaries/`

### U-Boot Not Responding
- Verify board is booting from SPI NOR flash
- Check boot mode switches
- Press reset and watch for U-Boot prompt on serial console

## References

- **AN13185** - Flashing Binaries to S32G-VNP-RDB2
- **S32G-VNP-RDB2UG** - S32G-VNP-RDB2 User Guide
