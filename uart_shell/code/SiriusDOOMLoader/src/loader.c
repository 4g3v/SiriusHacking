#include "Bird.h"
#include "Sirius.h"
#include "ThreadX.h"
#include "Treck.h"
#include <stdarg.h>

typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;

#define MAIN "main"
#define LOADER "tDoomLoader"
#define DOOM "tDoom"

void log(const char *tag, const char *format, ...)
{
    char buf[128];
    va_list args;

    snprintf(buf, sizeof(buf), "[%s] %s\r\n", tag, format);

    va_start(args, format);
    vprintf(buf, args);
    va_end(args);
}

TX_THREAD** sm_ModuleTaskThreads = (TX_THREAD**)0xC3E17120;

#define STACK_SIZE 2048
#define DOOM_STACK_SIZE 8192
TX_THREAD loaderThread;
TX_THREAD doomThread;

typedef enum PacketType PacketType;
enum PacketType
{
    QUIT = 0,
    OK = 1,
    ADDRESS = 2,
    DATA = 3,
    COPY_JUMP_TEXT = 4
};

typedef struct Packet Packet;
struct Packet
{
    char Data[512];
    PacketType Type;
};

void sendPacket(int sock, PacketType type, char *data, unsigned int length)
{
    send(sock, &type, 1, 0);
    send(sock, &length, 4, 0);
    send(sock, data, length, 0);
}
#define sendOK() sendPacket(conSocket, OK, NULL, NULL)

unsigned int memAddress = 0;
unsigned int textAddress = 0;
unsigned int textLength = 0;

typedef struct InitStruct InitStruct;
struct InitStruct
{
    int poolHandle;
    int argc;
    char **argv;
};
#define DOOM_POOL_SIZE 3670016

void doomThreadEntry(u32 input)
{
    InitStruct initStruct;
    memset(&initStruct, 0, sizeof(InitStruct));
    // void *doomStack = malloc(8192);

    // void (*doom_start)(void *stack, InitStruct *initStruct) = (void*)textAddress;
    void (*doom_start)(InitStruct *initStruct) = (void*)textAddress;

    // Replace the code
    // memAddress points to the uploaded .text from the python script
    log(DOOM, "memcpy(0x%08x, 0x%08X, %d)", textAddress, memAddress, textLength);
    DisableCachesAndMPU();
    memcpy((void*)textAddress, (void*)memAddress, textLength);
    EnableMPUAndCaches();
    log(DOOM, "Copied .text!");

    // Create a new MemPool, only for DOOM
    // .bss comes after .data (so it starts at memAddress) and is around 300kb
    // Lets skip 500kb and allocate 3.5mb for doom
    memAddress += 500 * 1024;
    memset((void*)memAddress, 0x00, DOOM_POOL_SIZE);
    initStruct.poolHandle = mem_AddPool((void*)memAddress, DOOM_POOL_SIZE, 1, "loader.c", 0x37);
    log(DOOM, "Created MemPool with %d bytes at 0x%08X: %d", DOOM_POOL_SIZE, memAddress, initStruct.poolHandle);

    initStruct.argc = 0;
    initStruct.argv = NULL;

    log(DOOM, "Jumping to doom!");
    // doom_start(doomStack, &initStruct);
    doom_start(&initStruct);

    while(1) {}
}

void loaderThreadEntry(u32 input)
{
    Packet packet;
    sockaddr_in destAddr;
    sockaddr_in sourceAddr;
    int addrLen = sizeof(sourceAddr);
    int listenSocket;
    int conSocket;
    int res;

    // log(LOADER, "start");

    memset(&destAddr, 0, sizeof(destAddr));
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = input;

    listenSocket = socket(AF_INET, SOCK_STREAM, IP_PROTOTCP);
    // log(LOADER, "socket(): %d", listenSocket);
    res = bind(listenSocket, &destAddr, sizeof(destAddr));
    // log(LOADER, "bind(): %d", res);
    res = listen(listenSocket, 10);
    // log(LOADER, "listen(): %d", res);

    log(LOADER, "Waiting for connection");
    while (1)
    {
        conSocket = accept(listenSocket, &sourceAddr, &addrLen);
        log(LOADER, "addr: %08X | port: %d", sourceAddr.sin_addr, sourceAddr.sin_port);
        // sendOK();

        while(1)
        {
            unsigned char typeByte = 0x00;
            unsigned int dataLen = 0;
            memset(&packet, 0x00, sizeof(packet));

            res = recv(conSocket, &typeByte, 1, 0);
            if (res == 0)
                break;
            packet.Type = typeByte;

            res = recv(conSocket, &dataLen, 4, 0);
            if (res == 0)
                break;

            res = recv(conSocket, packet.Data, dataLen, 0);
            if (res == 0)
                break;
            
            switch (packet.Type)
            {
                case QUIT:
                {
                    log(LOADER, "QUIT");
                    tfClose(conSocket);
                    tfClose(listenSocket);
                    return;
                }
                case ADDRESS:
                {
                    memAddress = *(unsigned int*)packet.Data;
                    log(LOADER, "addr: 0x%08X", memAddress);
                    sendOK();
                    break;
                }
                case DATA:
                {
                    // log(LOADER, "Writing %d bytes to 0x%08X", dataLen, memAddress);

                    memcpy((void*)memAddress, packet.Data, dataLen);
                    memAddress += dataLen;

                    // log(LOADER, "Wrote bytes!", dataLen, memAddress);

                    sendOK();

                    // log(LOADER, "Sent ok!", dataLen, memAddress);
                    break;
                }
                case COPY_JUMP_TEXT:
                {
                    textAddress = *(unsigned int*)packet.Data;
                    textLength = *(((unsigned int*)packet.Data) + 1);
                    
                    sendOK();
                    tfClose(conSocket);
                    tfClose(listenSocket);

                    void *stack = malloc(DOOM_STACK_SIZE);
                    txe_thread_create(&doomThread, DOOM, doomThreadEntry, 1337, stack, STACK_SIZE, 0, 0, 4, 1, sizeof(TX_THREAD));
                    log(MAIN, "Created tDoom thread!");
                    break;
                }
                default:
                {
                    log(LOADER, "Unknown PacketType: %02X", packet.Type);
                    break;
                }
            }
        }

        tfClose(conSocket);
        log(LOADER, "Closed!");
    }
}

void main(void)
{
    /*
            Kill:   Name: tUI | Entry: 0x40C257E3
                    Name: tui_main | Entry: 0x40C74D75
            .text addr: 0x40C257E4 (tUI thread, there's more than enough space here)

            Pool handle = 63,   pool_entry = 0xc3fc9648,   pool_tag = 0x0031cd51
            Total RAM size : 5199968 bytes
            Total RAM allocated : 2151080 bytes
            Peak RAM usage : 2152992 bytes
            Total free space: 3048888 bytes
            Total # of free blocks: 13
            Largest free block: 2922336 bytes
            Smallest free block: 16 bytes
    */
    
    // Kill UI threads
    for (int i = 0; i < 256; i++)
    {
        TX_THREAD *thread = sm_ModuleTaskThreads[i];
        if (thread == NULL)
            continue;
        
        if (!strcmp(thread->tx_thread_name, "tUI") || !strcmp(thread->tx_thread_name, "tui_main"))
        {
            log(MAIN, "Terminating: %s", thread->tx_thread_name, thread->tx_thread_entry);
            txe_thread_terminate(thread);
        }
    }
    // Remove the UI MemPool so we have ~5mb ram for ourselves
    mem_RemovePool(63);
    log(MAIN, "Deleted ui_main MemPool!");

    void *stack = malloc(STACK_SIZE);
    txe_thread_create(&loaderThread, LOADER, loaderThreadEntry, 1337, stack, STACK_SIZE, 200, 200, 4, 1, sizeof(TX_THREAD));
    log(MAIN, "Created tDoomLoader thread!");
}