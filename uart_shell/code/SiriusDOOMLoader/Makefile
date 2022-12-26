PROJECTNAME = ${shell basename "$(CURDIR)"}

CC = arm-none-eabi-gcc
LINK = arm-none-eabi-ld
OBJCOPY = arm-none-eabi-objcopy

CFLAGS = -mcpu=cortex-r4 -mthumb -mbig-endian -ffreestanding -c
LDFLAGS = -EB -nostdlib --script=link.ld

OBJ = build/crt0.o build/Sirius.o build/loader.o

$(PROJECTNAME): buildDir build/$(PROJECTNAME).bin

buildDir:
	@mkdir -p build

build/$(PROJECTNAME).bin: build/$(PROJECTNAME).elf
	$(OBJCOPY) -j .text -j .rodata -O binary $< build/$(PROJECTNAME)_text_rodata.bin
	$(OBJCOPY) -j .data -O binary $< build/$(PROJECTNAME)_data.bin

build/$(PROJECTNAME).elf: $(OBJ)
	$(LINK) $(LDFLAGS) -o $@ $(filter-out build/crt0.o, $(OBJ))

build/%.o: src/%.c
	$(CC) $(CFLAGS) -o $@ $<

build/%.o: src/%.S
	$(CC) $(CFLAGS) -o $@ $<

clean:
	@rm -rf build/
	@echo "Cleaned up!"