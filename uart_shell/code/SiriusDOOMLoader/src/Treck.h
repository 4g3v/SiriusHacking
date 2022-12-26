typedef struct sockaddr_in sockaddr_in;
struct sockaddr_in
{
    unsigned char sin_len;
    unsigned char sin_family;
    unsigned short sin_port;
    unsigned int sin_addr;
    char sin_zero[16];
};

int (*tfSocket)(int addrressFamily, int socketType, int protocol) = (void*)0x4044DD11;
int (*tfBind)(int socketDescriptor, const struct sockaddr_in *localAddressPtr, int localAddressLength) = (void*)0x40415B1F;
int (*tfListen)(int socketDescriptor, int backLog) = (void*)0x40419161;
int (*tfAccept)(int socketDescriptor, struct sockaddr_in *peerAddressPtr, int *addressLengthPtr) = (void*)0x4041558B;
int (*tfRecv)(int socketDescriptor, const char *bufferPtr, int bufferLength, int flags) = (void*)0x40420689;
int (*tfSend)(int socketDescriptor, const char *bufferPtr, int bufferLength, int flags) = (void*)0x404201E1;
int (*tfSendto)(int socketDescriptor, const char *bufferPtr, int bufferLength, int flags, const struct sockaddr_in *toAddressPtr, int addressLength) = (void*)0x4041EC29;
int (*tfClose)(int socketDescriptor) = (void*)0x40415EC5;

#define AF_UNSPEC 0
#define AF_INET 2
#define AF_INET6 28

#define SOCK_STREAM 1
#define SOCK_DGRAM 2
#define SOCK_RAW 3
#define SOCK_RDM 4
#define SOCK_SEQPACKET 5

#define IP_PROTOIP 0
#define IP_PROTOICMP 1
#define IP_PROTOIGMP 2
#define IP_PROTOIPV4 4
#define IP_PROTOTCP 6
#define IP_PROTOUDP 17
#define IP_PROTORDP 46
#define IP_PROTOOSPF 89
#define IP_PROTOTPACKET 127
#define IPPROTO_HOPOPTS 0
#define IPPROTO_IPV6 41
#define IPPROTO_ROUTING 43
#define IPPROTO_FRAGMENT 44
#define IPPROTO_ESP 50
#define IPPROTO_AH 51
#define IPPROTO_ICMPV6 58
#define IPPROTO_NONE 59
#define IPPROTO_DSTOPTS 60

#define socket tfSocket
#define bind tfBind
#define listen tfListen
#define accept tfAccept
#define recv tfRecv
#define send tfSend
#define sendto tfSendto