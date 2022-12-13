MEMORY
{
    RAMRX (RX) : ORIGIN = {TEXT_ADDRESS}, LENGTH = {TEXT_SIZE}
    RAMRW (RW!X) : ORIGIN = {DATA_ADDRESS}, LENGTH = {DATA_SIZE}
}

SECTIONS
{
    .text : {
        build/crt0.o(.init)
        *(.text)
    }

    .rodata : {
        *(.rodata)
    }

    .bss : {
        _bss_start = .;
        *(.bss)
    }
    _bss_end = .;
}