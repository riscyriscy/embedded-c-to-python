#!/bin/sh
# Build fw_probe.elf: Arm cross compiler if it is installed, else the host gcc.
if command -v arm-none-eabi-gcc >/dev/null; then
    arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -g -O0 -nostdlib -Wl,-T,fw.ld \
        -o fw_probe.elf fw_probe.c
else
    gcc -g -O0 -no-pie -nostdlib -static -Wl,-e,main -o fw_probe.elf fw_probe.c
fi
