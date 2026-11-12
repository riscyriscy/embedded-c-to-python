/* Firmware-like globals for the probe scripting examples. */
#include <stdint.h>

typedef struct {
    uint8_t mode;
    uint16_t rate_hz;
    int32_t offset_mv;
} config_t;

volatile uint32_t g_counter = 41;
config_t g_config = {2, 250, -120};
uint16_t g_samples[8] = {100, 101, 103, 106, 110, 115, 121, 128};
volatile uint32_t g_errors; /* .bss: zero after reset */

void tick(void) { g_counter++; }

int main(void)
{
    for (;;) {
        tick();
    }
}
