#include "Bird.h"
#include "Sirius.h"
#include "ThreadX.h"
#include "Treck.h"

#include <stdarg.h>

typedef unsigned int u32;
typedef unsigned short u16;

u32 read32(void *p)
{
    return *(u32*)p;
}

u32 GetTime()
{
    return read32(BIRD_TIME);
}

u32 sleep(u32 ms)
{
    u32 startTime = GetTime();

    while (1)
    {
        u32 currentTime = GetTime();
        if ((currentTime - startTime) >= ms * 1000)
            return currentTime;
    }
}

#define STACK_SIZE 2048
TX_THREAD testServerThread;
TX_THREAD testServerThread2;

void testServerThreadEntry(u32 input)
{
    char buf[128];
    sockaddr_in destAddr;
    sockaddr_in sourceAddr;
    int addrLen;
    int listenSocket;
    int conSocket;
    int res;

    snprintf(buf, sizeof(buf), "testServerThreadEntry(%d)\r\n", input);
    BOOT_console_put_string(buf);

    memset(&destAddr, 0, sizeof(destAddr));
    destAddr.sin_family = AF_INET;
    destAddr.sin_port = input;

    listenSocket = socket(AF_INET, SOCK_STREAM, IP_PROTOTCP);
    snprintf(buf, sizeof(buf), "socket(): %d\r\n", listenSocket);
    BOOT_console_put_string(buf);

    res = bind(listenSocket, &destAddr, sizeof(destAddr));
    snprintf(buf, sizeof(buf), "bind(): %d\r\n", res);
    BOOT_console_put_string(buf);

    res = listen(listenSocket, 10);
    snprintf(buf, sizeof(buf), "listen(): %d\r\n", res);
    BOOT_console_put_string(buf);

    while(1)
    {
        addrLen = sizeof(sourceAddr);
        conSocket = accept(listenSocket, &sourceAddr, &addrLen);

        snprintf(buf, sizeof(buf), "accept(): conSocket: %d | addr: %08X | port: %d\r\n", conSocket, sourceAddr.sin_addr, sourceAddr.sin_port);
        BOOT_console_put_string(buf);

        snprintf(buf, sizeof(buf), "Hello %08X! Your port: %d\r\n", sourceAddr.sin_addr, sourceAddr.sin_port);
        send(conSocket, buf, strlen(buf), 0);

        while(1)
        {
            memset(buf, 0, sizeof(buf));

            res = recv(conSocket, buf, sizeof(buf), 0);
            if (res == 0)
            {
                res = tfClose(conSocket);
                snprintf(buf, sizeof(buf), "tfClose(): %d\r\n", res);
                BOOT_console_put_string(buf);
                break;
            }

            if(!strcmp(buf, "QUIT\n"))
            {
                BOOT_console_put_string("Closing sockets and terminating thread!\r\n");

                tfClose(conSocket);
                tfClose(listenSocket);
                return;
            }

            BOOT_console_put_string(buf);
            send(conSocket, buf, strlen(buf), 0);
        }
    }
}

void main(void)
{
    void *stack = malloc(STACK_SIZE);
    void *stack2 = malloc(STACK_SIZE);
    BOOT_console_put_string("Allocated stacks\r\n");

    txe_thread_create(&testServerThread, "tAyylmao", testServerThreadEntry, 1337, stack, STACK_SIZE, 200, 200, 4, 1, sizeof(TX_THREAD));
    txe_thread_create(&testServerThread2, "tAyylmao2", testServerThreadEntry, 1338, stack2, STACK_SIZE, 200, 200, 4, 1, sizeof(TX_THREAD));

    BOOT_console_put_string("Created threads!\r\n");
}