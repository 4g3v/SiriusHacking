#include "hello.h"

static int dataVar = 0xFF;
static int bssVar;

void testFunc()
{
    dataVar = 0x1337;
}

void main(void)
{
    short x;
    short y;

    testFunc();

    BOOT_console_put_string("Hello world from C!\r\n");
    for (int i = 0; i < 10; i++)
    {
        BOOT_console_put_int_hex(i);
        BOOT_console_put_string("\r\n");
    }

    while(1)
    {
        bssVar++;
        if (bssVar == 500)
            break;

        GetTouchScreen(&x, &y);

        BOOT_console_put_string("X: ");
        BOOT_console_put_short_hex(x);
        BOOT_console_put_string(" | Y: ");
        BOOT_console_put_short_hex(y);
        BOOT_console_put_string("\r\n");
    }

    BOOT_console_put_string("main finished!\r\n");
}