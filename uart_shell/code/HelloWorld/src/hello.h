void (*BOOT_console_put_string)(const char *s) = (void*)0x4008696F;
void (*BOOT_console_put_int_hex)(unsigned int i) = (void*)0x40086A85;
void (*BOOT_console_put_short_hex)(unsigned int i) = (void*)0x40086A27;
int (*GetTouchScreen)(short *x, short *y) = (void*)0x40095329;