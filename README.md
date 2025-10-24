# Flashing NXP Auto Linux Images to S32G2

Tools and scripts for flashing NXP Auto Linux images to the S32G274A-RDB2 board via SPI NOR flash and eMMC.

## Overview

This repository provides two main flashing methods:

1. **SPI NOR Flash** - Flash U-Boot bootloader to SPI NOR using S32 Flash Tool
2. **eMMC** - Flash full Linux images to eMMC using U-Boot over serial

## Prerequisites

- S32G-VNP-RDB2 board
- S32 Design Studio (for S32 Flash Tool)
- Docker (for TFTP server)
- Python 3 with pyserial (`pip3 install pyserial`)

## Method 1: SPI NOR Flash

Flash the U-Boot bootloader to SPI NOR flash using the S32 Flash Tool.

### Hardware Setup

1. Configure the board boot mode switches to boot from serial (see section 3.6 of the S32G-VNP-RDB2 User Guide)
2. Connect host to the board via its UART0 USB port
   - The following instructions assume the device appears as `/dev/ttyUSB0`
   - Use `dmesg | grep tty` to find the actual device name if different

### Flashing

The S32 Flash Tool is included with S32 Design Studio. On Linux, it's typically located at:
```
/usr/local/NXP/S32DS.x.y.z/S32DS/tools/S32FlashTool/
```

Where `x.y.z` is your S32 Design Studio version.

**Setup:** Export the tool location for convenience:
```bash
export S32FT_DIR=/usr/local/NXP/S32DS.x.y.z/S32DS/tools/S32FlashTool
```

#### Step 1: Load the Flasher Firmware

The S32 Flash Tool requires specific firmware to be running on the chip before any SPI flash operations. This firmware must be uploaded first.

```bash
$S32FT_DIR/bin/S32FlashTool \
  -t $S32FT_DIR/targets/S32G2xx.bin \
  -a $S32FT_DIR/flash/MX25UW51245G.bin \
  -i uart -p /dev/ttyUSB0
```

**Note:** This step must be repeated each time the board is power cycled or reset.

#### Step 2: Flash Your Image

Choose one of the following images to flash:

**Option A: NXP Auto Linux BSP 44.0 Image**

```bash
# Erase flash
$S32FT_DIR/bin/S32FlashTool \
  -t $S32FT_DIR/targets/S32G2xx.bin \
  -ferase -addr 0 \
  -f ./binaries/fsl-image-flash-s32g274ardb2.flashimage \
  -i uart -p /dev/ttyUSB0

# Flash the image
$S32FT_DIR/bin/S32FlashTool \
  -t $S32FT_DIR/targets/S32G2xx.bin \
  -fwrite \
  -f ./binaries/fsl-image-flash-s32g274ardb2.flashimage \
  -addr 0 \
  -i uart -p /dev/ttyUSB0
```

**Option B: Factory Image (Restore to Original)**

```bash
# Erase flash
$S32FT_DIR/bin/S32FlashTool \
  -t $S32FT_DIR/targets/S32G2xx.bin \
  -ferase -addr 0 \
  -f ./binaries/rdb2-spi-flash-dump.bin \
  -i uart -p /dev/ttyUSB0

# Flash the image
$S32FT_DIR/bin/S32FlashTool \
  -t $S32FT_DIR/targets/S32G2xx.bin \
  -fwrite \
  -f ./binaries/rdb2-spi-flash-dump.bin \
  -addr 0 \
  -i uart -p /dev/ttyUSB0
```

## Method 2: eMMC Flash

Flash a complete Linux image to the board's eMMC using U-Boot and TFTP.

### Prerequisites

- Board must have U-Boot in SPI NOR flash (either factory default or flashed using Method 1)
- Board configured to boot from SPI NOR flash
- TFTP server running on host machine

### Step 1: Set Up TFTP Server

The `tftp_server` directory contains a Docker-based TFTP server:

```bash
# Place your image file in binaries/ directory
cp /path/to/fsl-image-auto-s32g274ardb2.sdcard binaries/

# Build and run the TFTP server
docker build -t tftp-server -f tftp_server/Dockerfile .
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

## Misc

### Troubleshooting

**Serial Connection Issues**
- Verify the correct serial device (e.g., `/dev/ttyUSB0`)
- Check user permissions: `sudo usermod -a -G dialout $USER`
- Ensure no other program is using the serial port

**TFTP Issues**
- Verify TFTP server is running: `docker ps`
- Check connectivity: `tftp localhost -c get <filename>`
- Ensure firewall allows UDP port 69
- Verify file exists in `binaries/`

**U-Boot Not Responding**
- Verify board is booting from SPI NOR flash
- Check boot mode switches
- Press reset and watch for U-Boot prompt on serial console

**Binary Files Are Small (LFS Pointers)**

If binary files in the `binaries/` directory appear to be only ~130 bytes, they are Git LFS pointer files, not the actual binaries.

To download the actual binary files:
```bash
# Pull all LFS files
git lfs pull

# Or pull specific files only
git lfs pull --include="binaries/rdb2-spi-flash-dump.bin,binaries/fsl-image-flash-s32g274ardb2.flashimage"
```

After pulling, the files will be their actual size (typically 64 MB - 756 MB depending on the image).

### Network Configuration

The default network configuration for eMMC flashing assumes:
- Board IP: `192.168.55.3`
- Host/TFTP Server IP: `192.168.55.1`
- Netmask: `255.255.255.0`

Adjust these values based on your network setup when running `emmc_flash.py`.

### Reference Documentation

- **AN13185** - Flashing Binaries to S32G-VNP-RDB2
- **S32G-VNP-RDB2UG** - S32G-VNP-RDB2 User Guide
- **S32FTUG** - S32 Flash Tool User Guide