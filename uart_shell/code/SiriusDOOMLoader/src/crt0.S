.section ".init"
.arm
.align 4
.global _start
.global _exit

_start:
    # Setup stack pointer, received from RopChain 
    mov sp, r0
    add sp, #{STACK_SIZE}
    
    # memset(_bss_start, 0x00, _bss_end - _bss_start)
    ldr r0, =(_bss_start)
    ldr r2, =(_bss_end)
    sub r2, r2, r0
    mov r1, #0x00
    blx 0x00000678

    blx main
    b _exit

_exit:
    ldr r0, =(endStr)
    ldr r1, =(0x4008696F) @ BOOT_console_put_string
    blx r1

    # Cleanup like in the RopChains
    ldr r0, =(0xc4eca118+0x24)
    mov sp, r0
    mov r0, #0
    pop {r4-r6, pc}

endStr:
    .asciz "\r\nEND\r\n"