/* What C does with sizes, integer division and wrap-around.
   Build and run: cc -O0 -o c_facts c_facts.c && ./c_facts */
#include <stdint.h>
#include <stdio.h>

int main(void) {
    printf("sizeof: char %zu, short %zu, int %zu, long %zu, long long %zu, void* %zu, double %zu\n",
           sizeof(char), sizeof(short), sizeof(int), sizeof(long), sizeof(long long),
           sizeof(void *), sizeof(double));
    int a = -7, b = 2;
    printf("-7 / 2 = %d, -7 %% 2 = %d, 7 / 2 = %d, 1 / 2 = %d\n", a / b, a % b, 7 / b, 1 / b);
    uint8_t u8 = 250;
    u8 += 10;                       /* unsigned arithmetic wraps modulo 256 */
    uint16_t u16 = (uint16_t)0x10000;
    printf("uint8_t 250 + 10 = %u, (uint16_t)0x10000 = %u\n", u8, u16);
    uint32_t big = 4000000000u;
    printf("uint32_t 4000000000 * 3 = %u\n", big * 3);
    int x = 1, y = 2, t;
    t = x; x = y; y = t;            /* swap through a temporary */
    printf("swapped: x = %d, y = %d\n", x, y);
    return 0;
}
