import struct
import lzss

import idaapi
import ida_idp
import ida_segment
import ida_entry
import ida_name
import ida_loader

SHOW_ZERO_LENGTH_ENTRIES = False

FLASH_MAGIC = 0xBAD2BFED
APPHDR_MAGIC = 0x3CA55A3C

flashSize = 0
firmwareFileOffset = 0
firmwareLoadAddress = 0

loaderInput = None


def toFileOffset(offset):
    return (offset - firmwareLoadAddress) + firmwareFileOffset


def getFirmwareUInt(offset):
    fileOffset = toFileOffset(offset)
    loaderInput.seek(fileOffset, idaapi.SEEK_SET)
    return struct.unpack(">I", loaderInput.read(4))[0]


def readCString(offset):
    s = bytearray()
    currentOffset = loaderInput.tell()

    fileOffset = toFileOffset(offset)
    loaderInput.seek(fileOffset, idaapi.SEEK_SET)

    while True:
        c = loaderInput.read(1)
        if c == b"\x00":
            break
        s.extend(c)

    loaderInput.seek(currentOffset, idaapi.SEEK_SET)
    return s.decode("utf-8")


class Header:
    def __init__(self, data):
        self.magic, self.unknown_1, self.size, self.unknown_2, self.pageSize_1, self.pageSize_2, self.unknown_3, \
        self.splashSize, self.unknown_4, self.unknown_5, self.unknown_6, self.unknown_7, self.loadAddress, \
        self.loadSize, self.unknown_10, self.startAddress, self.unknown_12, self.unknown_13, self.unknown_14, \
        self.unknown_15, self.unknown_16, self.unknown_17, self.unknown_18 \
            = struct.unpack(">" + ("I" * int(len(data) / 4)), data)


class AppHeader:
    def __init__(self, data):
        self.magic, self.size, self.moreMagic_1, self.moreMagic_2, self.unknown_1, self.splashPointer, self.unknown_2, \
        self.unknown_3, self.unknown_4, self.unknown_5, self.unknown_6, self.unknown_7, self.unknown_8, \
        self.entrypoint, self.protectedCountPtr, self.protectedRegionsPtr, self.segmentListPtr, self.unknown_9, self.memsetListStartPtr, \
        self.memsetListEndPtr, self.memcpyListStartPtr, self.memcpyListEndPtr, self.memcpyListBarrier, self.decompressListStartPtr, \
        self.decompressListEndPtr, self.decompressListBarrier, self.unknown_10 \
            = struct.unpack(">" + ("I" * int(len(data) / 4)), data)


class ProtectedRegion:
    def __init__(self, data):
        self.start, self.end = struct.unpack(">" + ("I" * int(len(data) / 4)), data)
        self.length = self.end - self.start


class Segment:
    def __init__(self, data):
        self.next, self.namePtr, self.startAddress, self.size, self.unknown_1, self.destSegment = struct.unpack(
            ">" + ("I" * int(len(data) / 4)), data)
        self.endAddress = self.startAddress + self.size


class MemsetEntry:
    def __init__(self, data):
        self.address, self.value, self.num = struct.unpack(">" + ("I" * int(len(data) / 4)), data)


class MemcpyEntry:
    def __init__(self, data):
        self.destination, self.source, self.num = struct.unpack(">" + ("I" * int(len(data) / 4)), data)


class DecompressEntry:
    def __init__(self, data):
        self.destination, self.source, self.compressedSize = struct.unpack(">" + ("I" * int(len(data) / 4)), data)


def accept_file(li, n):
    global flashSize
    li.seek(0, idaapi.SEEK_END)
    flashSize = li.tell()
    li.seek(0, idaapi.SEEK_SET)

    if flashSize < 4:
        return 0

    magic = struct.unpack(">I", li.read(4))[0]
    if magic != FLASH_MAGIC:
        return 0
    return "Sirius Flash"


def load_file(li, neflags, format):
    global firmwareFileOffset
    global firmwareLoadAddress
    global loaderInput

    loaderInput = li
    idaapi.set_processor_type("armb", ida_idp.SETPROC_LOADER_NON_FATAL)
    print()

    # Parse Header
    li.seek(8, idaapi.SEEK_SET)
    headerSize = struct.unpack(">I", li.read(4))[0]
    li.seek(0, idaapi.SEEK_SET)

    headerData = li.read(headerSize)
    header = Header(headerData)
    print(f"header.pageSize_1:                      {header.pageSize_1}")
    print(f"header.splashSize:                      {header.splashSize}")
    print(f"header.loadAddress:                     {hex(header.loadAddress)}")
    print(f"header.loadSize:                        {header.loadSize}")
    print(f"header.startAddress:                    {hex(header.startAddress)}")

    # Find firmware by going to the page after the splashscreen
    splashEnd = header.pageSize_1 + header.splashSize
    firmwareFileOffset = (splashEnd - (splashEnd % header.pageSize_1)) + header.pageSize_1
    firmwareLoadAddress = header.loadAddress

    print(f"firmwareFileOffset:                     {hex(firmwareFileOffset)}")

    # Find AppHeader
    li.seek(0, idaapi.SEEK_END)
    while True:
        li.seek(-4, idaapi.SEEK_CUR)
        magic = struct.unpack(">I", li.read(4))[0]
        li.seek(-4, idaapi.SEEK_CUR)

        if magic == APPHDR_MAGIC:
            break

    # Parse AppHeader
    appheaderFileOffset = li.tell()
    print(f"appheaderFileOffset:                    {hex(appheaderFileOffset)}")

    li.seek(4, idaapi.SEEK_CUR)
    appheaderSize = struct.unpack(">I", li.read(4))[0]
    print(f"appheaderSize:                          {appheaderSize}")

    li.seek(appheaderFileOffset, idaapi.SEEK_SET)
    appHeader = AppHeader(li.read(appheaderSize))
    print(f"appHeader.entrypoint:                   {hex(appHeader.entrypoint)}")

    # Parse protected regions
    protectedRegions = []
    protectedCount = getFirmwareUInt(appHeader.protectedCountPtr)
    protectedRegionsFileOffset = toFileOffset(appHeader.protectedRegionsPtr)
    li.seek(protectedRegionsFileOffset, idaapi.SEEK_SET)
    for i in range(protectedCount):
        region = ProtectedRegion(li.read(2 * 4))
        protectedRegions.append(region)

    # Parse segments
    segments = []
    segmentsByStart = {}
    segmentListFileOffset = toFileOffset(appHeader.segmentListPtr)
    li.seek(segmentListFileOffset, idaapi.SEEK_SET)
    while True:
        segment = Segment(li.read(6 * 4))
        segment.name = readCString(segment.namePtr)
        li.seek(toFileOffset(segment.next), idaapi.SEEK_SET)

        segments.append(segment)
        segmentsByStart[segment.startAddress] = segment
        if segment.next == 0:
            break

    # Parse memset list
    memsetList = []
    memsetListSize = appHeader.memsetListEndPtr - appHeader.memsetListStartPtr
    memsetListFileOffset = toFileOffset(appHeader.memsetListStartPtr)
    li.seek(memsetListFileOffset, idaapi.SEEK_SET)
    for i in range(int((memsetListSize / 4) / 3)):
        memset = MemsetEntry(li.read(3 * 4))
        memsetList.append(memset)

    # Parse memcpy list
    memcpyList = []
    memcpyListSize = appHeader.memcpyListEndPtr - appHeader.memcpyListStartPtr
    memcpyListFileOffset = toFileOffset(appHeader.memcpyListStartPtr)
    li.seek(memcpyListFileOffset, idaapi.SEEK_SET)
    for i in range(int((memcpyListSize / 4) / 3)):
        memcpy = MemcpyEntry(li.read(3 * 4))
        memcpyList.append(memcpy)

    # Parse decompress list
    decompressList = []
    decompressListSize = appHeader.decompressListEndPtr - appHeader.decompressListStartPtr
    decompressListFileOffset = toFileOffset(appHeader.decompressListStartPtr)
    li.seek(decompressListFileOffset, idaapi.SEEK_SET)
    for i in range(int((decompressListSize / 4) / 3)):
        decompress = DecompressEntry(li.read(3 * 4))
        decompressList.append(decompress)

    # Dump parsed entries
    print()
    for i in range(len(protectedRegions)):
        region = protectedRegions[i]
        if not SHOW_ZERO_LENGTH_ENTRIES and region.length == 0:
            continue

        print(
            f"protectedRegions[{i}]: start: {segmentsByStart[region.start].name} | end: {hex(region.end)} | length: {hex(region.length)}")
    print()
    for i in range(len(segments)):
        segment = segments[i]
        if not SHOW_ZERO_LENGTH_ENTRIES and segment.size == 0:
            continue

        print(
            f"segments[{i}]: name: {segment.name} | startAddress: {hex(segment.startAddress)} | endAddress: {hex(segment.endAddress)} | size: {hex(segment.size)}")
    print()
    for i in range(len(memsetList)):
        memset = memsetList[i]

        if not SHOW_ZERO_LENGTH_ENTRIES and memset.num == 0:
            continue

        print(
            f"memsetList[{i}]: address: {segmentsByStart[memset.address].name} | value: {hex(memset.value)} | num: {hex(memset.num)}")
    print()
    for i in range(len(memcpyList)):
        memcpy = memcpyList[i]

        if not SHOW_ZERO_LENGTH_ENTRIES and memcpy.num == 0:
            continue

        print(
            f"memcpyList[{i}]: destination: {segmentsByStart[memcpy.destination].name} | source: {segmentsByStart[memcpy.source].name} | num: {hex(memcpy.num)}")
    print()
    for i in range(len(decompressList)):
        decompress = decompressList[i]

        if not SHOW_ZERO_LENGTH_ENTRIES and decompress.compressedSize == 0:
            continue

        print(
            f"decompressList[{i}]: destination: {hex(decompress.destination)} | source: {hex(decompress.source)} | compressedSize: {hex(decompress.compressedSize)}")
    print()

    # Start loading firmware
    li.file2base(firmwareFileOffset, header.loadAddress, header.loadAddress + header.loadSize, 1)

    # Handle memcpy list
    for memcpy in memcpyList:
        if memcpy.num == 0:
            continue

        print(f"Copying {segmentsByStart[memcpy.source].name} to {segmentsByStart[memcpy.destination].name}")
        fileOffset = toFileOffset(memcpy.source)
        li.file2base(fileOffset, memcpy.destination, memcpy.destination + memcpy.num, 1)
    print()

    # Decompress segments and put them into the right location
    for decompress in decompressList:
        if decompress.compressedSize == 0:
            continue

        sourceName = segmentsByStart[decompress.source].name
        if decompress.destination not in segmentsByStart:
            print(f"[Error] Tried to decompress {sourceName} into an invalid segment: {hex(decompress.destination)}, trying to fix.")
            decompress.destination |= 0x80000
            if decompress.destination not in segmentsByStart:
                print(f"[Warning] Still not a valid segment: {hex(decompress.destination)} continuing anyways!")
            else:
                print(f"Managed to fix it apparently?")
        print(f"Decompressing {sourceName} to {segmentsByStart[decompress.destination].name}")

        li.seek(toFileOffset(decompress.source), idaapi.SEEK_SET)
        compressedBuffer = li.read(decompress.compressedSize)
        decompressedBuffer = lzss.decompress(compressedBuffer)
        ida_loader.mem2base(decompressedBuffer, decompress.destination, 0)
    print()

    # Add segments
    for segment in segments:
        if segment.size == 0:
            continue

        segmentName = segment.name.lower()
        if segmentName.startswith(".c") or "dat" in segmentName:
            ida_segment.add_segm(0, segment.startAddress, segment.endAddress, segment.name, "DATA")
            ida_name.set_name(segment.startAddress, segment.name[1:])
        elif "bss" in segmentName:
            ida_segment.add_segm(0, segment.startAddress, segment.endAddress, segment.name, "BSS")
            ida_name.set_name(segment.startAddress, segment.name[1:])
        elif "text" in segmentName or segmentName == ".reset":
            ida_segment.add_segm(0, segment.startAddress, segment.endAddress, segment.name, "CODE")
        else:
            ida_segment.add_segm(0, segment.startAddress, segment.endAddress, segment.name, "UNK")

    # Add entrypoints
    ida_entry.add_entry(header.startAddress, header.startAddress, "_start", 1)
    ida_entry.add_entry(appHeader.entrypoint, appHeader.entrypoint, "entrypoint", 1)
    return 1
