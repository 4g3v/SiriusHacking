import struct
import threading
import time
import sys
from hexdump import hexdump
from struct import unpack
from enum import Enum

skipFirstStage = False
PAGE_SIZE = 2048
OOB_SIZE = 0x40


class CompressionMethod(Enum):
    UNENCODED = 0
    RLE = 1
    TIFF = 2
    DELTA_ROW = 3
    RESERVED = 4
    ADAPTIVE = 5


class SRecordType(Enum):
    HEADER = 0
    DATA = 3
    TERMINATION = 7


def read(data, end, includeEnd=False, skipFirst=False):
    readData = data.split(end)[0 if not skipFirst else 1]
    if includeEnd:
        readData += end

    return readData, len(readData) if not skipFirst else len(readData) + len(end)


firstStageRunning = True


def firstStagePercentage():
    global offset
    global totalDataLen
    while firstStageRunning:
        percentage = 0 if offset == 0 or offset == totalDataLen else (offset / totalDataLen) * 100
        print(f"FirstStage: {'{:.2f}'.format(percentage)}%")
        time.sleep(2)


percentageThread = threading.Thread(target=firstStagePercentage)


def exceptionHook(excType, value, traceback):
    global firstStageRunning
    if excType == KeyboardInterrupt:
        firstStageRunning = False
    else:
        sys.__excepthook__(excType, value, traceback)


sys.excepthook = exceptionHook

path = sys.argv[1]

with open(path, "rb") as f:
    firmware = f.read()

if not firmware.startswith(b"\x1B%-12345X"):
    print("Invalid ful file!")
    exit(-1)

pjlHeader, pjlHeaderLength = read(firmware, b"FWUPDATE!\x0d\x0a", True)

data = firmware[pjlHeaderLength:]

COMPRESSION_METHOD = 0
RASTER_WIDTH = 0

print(f"Starting to unpack {path}")
firstStageBuffer = bytearray()
if not skipFirstStage:
    totalDataLen = len(data)
    offset = 0

    percentageThread.start()
    while True:
        cmdData, cmdLength = read(data[offset:], b"\x1B", skipFirst=True)

        if cmdData.startswith(b"*rt"):  # *rt16384sA
            RASTER_WIDTH = int(cmdData[3:-2])
            # print(f"RASTER_WIDTH: {RASTER_WIDTH}")

            offset += cmdLength
            continue
        elif cmdData.startswith(b"*b"):
            if cmdLength < 10 and cmdData.endswith(b"Y"):
                # print("Ignoring: " + str(cmdData))
                offset += cmdLength
                continue

            # *b2m16362V{DATA}
            # *b16179V{DATA}
            cmdWithCompression = False
            if chr(cmdData[3]) == 'm':
                COMPRESSION_METHOD = CompressionMethod(int(chr(cmdData[2])))
                cmdWithCompression = True

            plane = True
            cmdWithoutData, cmdWithoutData_length = read(cmdData, b"V", includeEnd=True)

            try:
                compSize = int(cmdWithoutData[4 if cmdWithCompression else 2:-1])
            except:
                plane = False
                cmdWithoutData, cmdWithoutData_length = read(cmdData, b"W", includeEnd=True)
                try:
                    compSize = int(cmdWithoutData[4 if cmdWithCompression else 2:-1])
                except:
                    break

            compDataOffset = cmdWithoutData_length + 1  # +1 because of the \x1B byte

            compressedData = data[offset + compDataOffset:offset + compDataOffset + compSize]
            # print(f"Read {compSize} {COMPRESSION_METHOD.name} {'plane' if plane else 'row'} bytes")

            decompressedData = bytearray()

            if COMPRESSION_METHOD == CompressionMethod.UNENCODED:
                decompressedData.extend(compressedData)
            elif COMPRESSION_METHOD == CompressionMethod.TIFF:
                while True:
                    if len(compressedData) == 0:
                        break

                    control = unpack("b", compressedData[:1])[0]
                    if control >= 0:
                        decompressedData.extend(compressedData[1:control + 2])
                        compressedData = compressedData[control + 2:]
                        continue
                    elif control < 0:
                        if control == -128:
                            print("NOP")
                            exit(-1)
                            raise KeyboardInterrupt

                        repeat = abs(control)
                        decompressedData.extend(compressedData[1:2] * (repeat + 1))
                        compressedData = compressedData[2:]
            elif COMPRESSION_METHOD == CompressionMethod.DELTA_ROW:
                while True:
                    if len(compressedData) == 0:
                        break

                    command = unpack("B", compressedData[:1])[0]
                    bytesToReplace = ((command & 0b11100000) >> 5) + 1
                    deltaOffset = (command & 0b00011111)

                    if deltaOffset == 31:
                        print("Unhandled 31 offset")
                        exit(-1)
                        raise KeyboardInterrupt

                    deltaBytes = compressedData[1:1 + bytesToReplace]

                    # print(f"command: {hex(command)}")
                    # print(f"bytesToReplace: {bytesToReplace}")
                    # print(f"offset: {offset}")
                    # hexdump(deltaBytes)
                    decompressedData.extend(deltaOffset * b"\x00" + deltaBytes)

                    compressedData = compressedData[1 + bytesToReplace:]
            else:
                print(f"Unimplemented compression: {COMPRESSION_METHOD}")
                exit(-1)
                raise KeyboardInterrupt

            decompressedLength = len(decompressedData)
            if plane and decompressedLength < RASTER_WIDTH:
                count = (RASTER_WIDTH - decompressedLength)
                # print(f"Zero filling {count} bytes")
                decompressedData.extend(count * b"\x00")

            offset += compDataOffset + compSize
            firstStageBuffer.extend(decompressedData)
            continue
        else:
            print("Unhandled command!")
            hexdump(cmdData)
            exit(-1)
            raise KeyboardInterrupt

    print("Finished first stage!")
    firstStageRunning = False

    with open("firstStage.bin", "wb") as firstStage:
        firstStage.write(firstStageBuffer)
else:
    with open("firstStage.bin", "rb") as firstStage:
        firstStageBuffer.extend(firstStage.read())

asciiSrecEnd = b"P02628000"
# asciiSrecEnd = b"F0047ACE9"
# asciiSrecEnd = b"F0041CCE9"

bootloaderSrec, data = firstStageBuffer.split(asciiSrecEnd)
bootloaderSrec += asciiSrecEnd
with open("bootloader.srec", "wb") as bootloader:
    bootloader.write(bootloaderSrec)

print("Wrote bootloader.srec!")
print()

rawFlashBuffer = bytearray()

totalDataLen = len(data)
offset = 0

while True:
    srecStart = data[offset:offset + 3]
    if len(srecStart) == 1:
        break

    checksum, recTypeByte, recLength = struct.unpack("BBB", srecStart)
    if (recTypeByte & 0xF0) != 0x30:
        print("Invalid binary SRecord type!")
        exit(-1)

    recordType = SRecordType(recTypeByte & 0xF)
    recLength -= 1

    if recordType == SRecordType.HEADER:
        address = data[offset + 3:offset + 5]
        recLength -= 2

        totalLength = 5 + recLength
        text = data[offset + 5:offset + totalLength]

        print("Binary SRecord header:")
        print(f"Address: {address.hex()}")
        print(f"Text: {text.decode()}")
        print()

        offset += totalLength
        continue
    elif recordType == SRecordType.DATA:
        address = data[offset + 3:offset + 7]
        recLength -= 4

        totalLength = 7 + recLength
        srecData = data[offset + 7:offset + totalLength]

        offset += totalLength
        rawFlashBuffer.extend(srecData)
        continue
    elif recordType == SRecordType.TERMINATION:
        startAddress = data[offset + 3:offset + 7]
        recLength -= 4

        print("Binary SRecord termination:")
        print(f"StartAddress: {startAddress.hex()}")
        print()

        offset += 7

print("Finished extracting raw flash image!")

with open("rawFlash.bin", "wb") as flash:
    flash.write(rawFlashBuffer)

print("Removing OOB data...")

flashBuffer = bytearray()

totalDataLen = len(rawFlashBuffer)
offset = 0

while True:
    print(f"Page at: {hex(offset)}")
    if offset >= totalDataLen:
        print(f"End offset: {hex(offset)}")
        break
    page = rawFlashBuffer[offset:offset + PAGE_SIZE]
    flashBuffer.extend(page)
    offset += PAGE_SIZE + OOB_SIZE

with open("flash.bin", "wb") as flash:
    flash.write(flashBuffer)

print("Finished extracting flash image!")
