#ifndef _SIRIUS_H
#define _SIRIUS_H

#include <stdarg.h>

#define NULL 0
typedef int FILE;

static void (*DisableCachesAndMPU)() = (void*)0x4009D2D8;
static void (*EnableMPUAndCaches)() = (void*)0x4009D424;

static void (*BOOT_console_put_byte)(unsigned short b) = (void*)0x40086953;
static void (*BOOT_console_put_string)(const char *s) = (void*)0x4008696F;
static void (*BOOT_console_put_int_hex)(unsigned int i) = (void*)0x40086A85;
static void (*BOOT_console_put_short_hex)(unsigned int i) = (void*)0x40086A27;
static void (*BOOT_console_put_byte_hex)(unsigned int i) = (void*)0x400869CB;

static void (*nos_ui_SetHWLed)(unsigned int hwLED, int value) = (void*)0x400948D3;
static int (*uart_driver_DoRead)(int field4, void *buf, int size, int zero) = (void*)0x40598B7F;
static int (*GetTouchScreen)(short *x, short *y) = (void*)0x40095329;

static unsigned int (*free)(void* ptr) = (void*)0x413B0498;
static void *(*malloc)(unsigned int size) = (void*)0x40BD0BA3;
static void *(*malloc_ED)(unsigned int size) = (void*)0x40BD0C51;
static void *(*memset)(void *s, int c, unsigned int n) = (void*)0x00000678;
static void *(*memcpy)(void *dest, const void *src, unsigned int n) = (void*)0x000003C0;

static int (*mem_AddPool)(void *pool_entry, unsigned int size, int a3, const char *fileName, int tag) = (void*)0x4098C027;
static void (*mem_RemovePool)(int poolHandle) = (void*)0x4098C15F;
static void *(*mem_alloc)(int poolHandle, unsigned int size, const char *fileName, int line_num, int a5) = (void*)0x4098BCDF;
static void (*mem_free)(int poolHandle, void *ptr) = (void*)0x4098BD7B;

static int (*atoi)(const char *str) = (void*)0x403229B5;
static int (*strlen)(const char *s) = (void*)0x4009FA5F;
static char *(*strncat)(char *dest, const char *src, unsigned int n) = (void*)0x413AE785;
static int (*strcmp)(const char *s1, const char *s2) = (void*)0x4031455D;
static int (*strncmp)(const char *s1, const char *s2, unsigned int n) = (void*)0x414028A3;
static char *(*strtok)(char *str, const char *delim) = (void*)0x403216C5;
static char *(*strncpy)(char *dest, const char *src, unsigned int n) = (void*)0x41402813;
static int (*snprintf)(char *str, unsigned int size, const char *format, ...) = (void*)0x40314575;
static int (*vsnprintf)(char *str, unsigned int size, const char *format, va_list arg) = (void*)0x41402D07;

typedef struct UartDataStruct UartDataStruct;
struct UartDataStruct
{
  int field_0;
  int field_4;
  int field_8;
  int field_C;
  int TotalRead;
  int field_14;
  int field_18;
  unsigned short *UartBase;
  int WriteBuffer;
  int ReadBuffer;
  int ReadBufferStart;
  int ReadBufferPos;
  int field_30;
  int ReadBufferLeft;
  int ReadBufferSize;
  int WriteBufferStart;
  int WriteBufferPos;
  int field_44;
  int WriteBufferLeft;
  int WriteBufferSize;
  int field_50;
  int field_54;
};

int vprintf(const char *format, va_list arg);
int printf(const char *format, ...);
int sprintf(char *str, const char *format, ...);

#define fprintf(x, ...) printf(__VA_ARGS__)
#define vfprintf(x, y, z) vprintf(y, z)
#define strcpy(dest,src) strncpy(dest,src,128)
#define strcat(dest,src) strncpy(dest,src,128)

#endif