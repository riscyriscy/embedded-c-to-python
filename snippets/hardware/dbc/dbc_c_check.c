/* Uses the code that cantools generated from engine.dbc. */
#include <stdio.h>
#include <string.h>
#include "engine.h"

int main(void)
{
    struct engine_device_temp_t t = {0};
    uint8_t frame[3];

    t.temperature = engine_device_temp_temperature_encode(28.45);
    t.counter = 7;
    int n = engine_device_temp_pack(frame, &t, sizeof(frame));
    printf("pack   %d bytes: %02x %02x %02x\n", n, frame[0], frame[1], frame[2]);

    struct engine_device_temp_t u;
    uint8_t rx[3] = {0x1d, 0x0b, 0x07};
    int rc = engine_device_temp_unpack(&u, rx, sizeof(rx));
    printf("unpack rc %d  temperature %.2f C  counter %u\n", rc,
           engine_device_temp_temperature_decode(u.temperature), (unsigned)u.counter);
    printf("short  rc %d\n", engine_device_temp_unpack(&u, rx, 2));

    struct engine_pump_command_t p = {0};
    p.speed = engine_pump_command_speed_encode(1500.0);
    p.enable = 1;
    uint8_t pf[2];
    engine_pump_command_pack(pf, &p, sizeof(pf));
    printf("pump   %02x %02x\n", pf[0], pf[1]);
    printf("range  1500 rpm %d, 1800 rpm %d\n",
           engine_pump_command_speed_is_in_phys_range(1500.0),
           engine_pump_command_speed_is_in_phys_range(1800.0));
    return 0;
}
