void (*BOOT_console_put_string)(const char *s) = (void*)0x4008696F;
void (*BOOT_console_put_int_hex)(unsigned int i) = (void*)0x40086A85;
void (*BOOT_console_put_short_hex)(unsigned int i) = (void*)0x40086A27;

int (*GetTouchScreen)(short *x, short *y) = (void*)0x40095329;

void *(*malloc)(unsigned int size) = (void*)0x40BD0BA3;
void *(*malloc_ED)(unsigned int size) = (void*)0x40BD0C51;
void *(*memset)(void *s, int c, unsigned int n) = (void*)0x00000678;
void *(*memcpy)(void *dest, const void *src, unsigned int n) = (void*)0x000003C0;

int (*strlen)(const char *s) = (void*)0x4009FA5F;
char *(*strncat)(char *dest, const char *src, unsigned int n) = (void*)0x413AE785;
int (*strcmp)(const char *s1, const char *s2) = (void*)0x4031455D;
char *(*strtok)(char *str, const char *delim) = (void*)0x403216C5;
int (*snprintf)(char *str, unsigned int size, const char *format, ...) = (void*)0x40314575;
int (*printf)(const char *format, ...) = (void*)0x40B3C499;