#include "Sirius.h"

int vprintf(const char *format, va_list arg)
{
    int res;

    char buf[128];
    res = vsnprintf(buf, sizeof(buf), format, arg);
    BOOT_console_put_string(buf);

    return res;
}

int printf(const char *format, ...)
{
    int res;
    va_list args;

    va_start(args, format);
    res = vprintf(format, args);
    va_end(args);

    return res;
}

int sprintf(char *str, const char *format, ...)
{
    int res;
    va_list args;

    va_start(args, format);
    res = vsnprintf(str, sizeof(str), format, args);
    va_end(args);

    return res;
}