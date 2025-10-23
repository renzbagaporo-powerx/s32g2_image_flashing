#!/usr/bin/env python3
"""
U-Boot eMMC Flash Tool
Sends commands to U-Boot over serial to flash an image to eMMC via TFTP
"""

import argparse
import os
import sys
import time
import serial


def calculate_blocks(file_path, block_size=512):
    """Calculate number of blocks needed for a file."""
    file_size = os.path.getsize(file_path)
    blocks = (file_size + block_size - 1) // block_size  # Ceiling division
    return blocks, file_size


def send_command(ser, command, wait_time=1.0):
    """Send a command to U-Boot and wait for prompt."""
    print(f"Sending: {command}")
    ser.write(f"{command}\n".encode('utf-8'))
    ser.flush()

    output = ""

    while True:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='replace')
            output += chunk
            print(chunk, end='', flush=True)

            # Check for U-Boot prompt
            if "=>" in chunk:
                time.sleep(wait_time)
                return output

        time.sleep(0.1)


def flash_emmc(serial_device, ip_address, netmask, server_ip, file_path, start_address):
    """Execute U-Boot commands to flash image to eMMC."""

    # Calculate blocks
    blocks, file_size = calculate_blocks(file_path)
    blocks_hex = f"{blocks:X}"

    print(f"File: {file_path}")
    print(f"File size: {file_size} bytes")
    print(f"Blocks needed: {blocks} (0x{blocks_hex})")
    print(f"Start address: 0x{start_address}")
    print()

    # Get just the filename from the path
    filename = os.path.basename(file_path)

    try:
        # Open serial connection
        print(f"Opening serial connection to {serial_device}...")
        ser = serial.Serial(
            port=serial_device,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )

        print("Connected. Waiting for U-Boot prompt...")
        time.sleep(2)

        # Send initial newline to get prompt
        ser.write(b"\n")
        time.sleep(1)

        # Read and display any existing output
        if ser.in_waiting > 0:
            print(ser.read(ser.in_waiting).decode('utf-8', errors='replace'))

        # Execute U-Boot commands
        commands = [
            "setenv ethact eth_eqos",
            f"setenv ipaddr {ip_address}",
            f"setenv serverip {server_ip}",
            f"setenv netmask {netmask}",
            f"tftp {start_address} {filename}",
            "mmc rescan",
            f"mmc write {start_address} 0 {blocks_hex}",
        ]

        for cmd in commands:
            send_command(ser, cmd)

        print("\nFlashing complete!")

    except serial.SerialException as e:
        print(f"Serial error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed.")


def main():
    parser = argparse.ArgumentParser(
        description='Flash image to eMMC via U-Boot over serial',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s -d /dev/ttyUSB0 -i 192.168.55.3 -n 255.255.255.0 \\
           -s 192.168.55.1 -f fsl-image-auto-s32g274ardb2.sdcard -a A0000000
        """
    )

    parser.add_argument('-d', '--device', required=True,
                        help='Serial device (e.g., /dev/ttyUSB0)')
    parser.add_argument('-i', '--ip', required=True,
                        help='IP address for the device running U-Boot')
    parser.add_argument('-n', '--netmask', required=True,
                        help='Network mask (e.g., 255.255.255.0)')
    parser.add_argument('-s', '--server', required=True,
                        help='TFTP server IP address')
    parser.add_argument('-f', '--file', required=True,
                        help='Image file to flash (must be accessible via TFTP server)')
    parser.add_argument('-a', '--address', required=True,
                        help='Start address for TFTP load (e.g., A0000000)')

    args = parser.parse_args()

    # Validate serial device
    if not os.path.exists(args.device):
        print(f"Error: Serial device {args.device} does not exist", file=sys.stderr)
        sys.exit(1)

    # Validate file exists (for block calculation)
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} does not exist", file=sys.stderr)
        sys.exit(1)

    flash_emmc(
        serial_device=args.device,
        ip_address=args.ip,
        netmask=args.netmask,
        server_ip=args.server,
        file_path=args.file,
        start_address=args.address
    )


if __name__ == '__main__':
    main()
