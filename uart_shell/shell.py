import struct
from structures import TX_THREAD

import serial
from hexdump import hexdump

PORT = "COM3"
PAGE_SIZE = 2048
BLOCK_SIZE = 64
PLANE_SIZE = 1024
sm_ModuleTaskThreads = 0xC3E17120

ser = serial.Serial(PORT, 115200)
tasks = {}


def runShellCommand(s):
    ser.write(bytes(s + "\n", "utf-8"))
    ser.readline()  # ignore command echo
    return ser.read_until(b"->").decode("utf-8")[:-5]


def runUnderware(s):
    return runShellCommand(f"udws \"{s}\"")


def runPieUnderware(s):
    return runShellCommand(f"udws_rpc \"{s}\"")


def udw_help():
    print("udw d [s] - Decrypts an underware string")
    print("udw e [s] - Encrypts an underware string")
    print("udw iter - Prints all underware commands, including pie underware")


def getUdwCryptOutput(s):
    firstline = s.split("\n")[0]
    if "ERROR" not in firstline:
        return firstline.split(" => ")[1]
    else:
        return firstline


def udw_command(args):
    if len(args) == 0:
        udw_help()
        return

    if len(args) > 1:
        udw_s = " ".join(args[1:])
        if args[0] == "d":
            udwOutput = runUnderware(f"udw.decr {udw_s}")
        elif args[0] == "e":
            udwOutput = runUnderware(f"udw.encr {udw_s}")
        else:
            udw_help()
            return
        print(getUdwCryptOutput(udwOutput))
    elif args[0] == "iter":
        runPieUnderware("udw.iter_reset")
        runUnderware("udw.iter_reset")

        print("pie underware commands:")
        while True:
            udwCommand = runPieUnderware("udw.iter_get_next")
            if udwCommand.startswith("iter_done"):
                break
            print(udwCommand.split(';')[0])

        print("\nARM underware commands:")
        while True:
            udwCommand = runUnderware("udw.iter_get_next")
            if udwCommand.startswith("iter_done"):
                break
            print(udwCommand.split(';')[0])

        pass
    else:
        udw_help()


def nand_read(block, page, size, offset):
    dataStr = runUnderware(f"test_nos_nand.read_blocking {block} {page} {size} {offset} {size}").split("\n")[0]
    dataBytes = bytearray()

    data = " ".join(dataStr.split())
    for dword in data.split(' ')[:-1]:
        dataBytes.extend(bytearray.fromhex(dword.zfill(8)))
    return dataBytes


def nand_help():
    print("nand dump [file] - Dumps the nand (Takes around 8 hours with a 128mb nand)")
    print("nand read [block] [page] - Hexdumps the specified page at the specified block")


def nand_command(args):
    if len(args) == 0:
        nand_help()
        return

    if len(args) > 1:
        if args[0] == "dump":
            path = args[1]
            nand_dump = open(path, "wb")

            for block in range(PLANE_SIZE):
                for page in range(BLOCK_SIZE):
                    read = nand_read(block, page, 512, 0)
                    hexdump(read)
                    nand_dump.write(read)
                    print(f"Dumped block {block} page {page}")

            nand_dump.close()
            print(f"Finished dumping nand to {path}!")
        elif args[0] == "read" and len(args) == 3:
            block = int(args[1])
            page = int(args[2])
            hexdump(nand_read(block, page, 512, 0))
        else:
            nand_help()
    else:
        nand_help()


def mem_help():
    print("mem r [address] [size] - Hexdumps memory, size has to be >= 4")
    print("mem rb [address] - Reads a single byte")
    print("mem rs [address] - Reads a string")


def mem_read_dword(addr):
    output = runUnderware(f"photo_hw.read {addr} 4").split('\n')[0]
    return int(output.strip().split(": ")[1]).to_bytes(4, "big", signed=True)


def mem_read_byte(addr):
    output = runUnderware(f"photo_hw.read {addr} 1").split('\n')[0]
    return int(output.strip().split(": ")[1]).to_bytes(1, "big")


def mem_read_string(addr):
    strBytes = bytearray()
    while True:
        byte = mem_read_byte(addr)
        if byte == b"\x00":
            break

        strBytes.extend(byte)
        addr = addr + 1

    return strBytes.decode("utf-8")


def mem_read(addr, size):
    data = bytearray()

    size = int(size / 4)
    for i in range(size):
        data.extend(mem_read_dword(addr + (i * 4)))

    return data


def mem_command(args):
    if len(args) == 0:
        mem_help()
        return

    if len(args) > 1:
        if args[0] == "r" and len(args) == 3:
            hexdump(mem_read(int(args[1], 16), int(args[2], 16)))
        elif args[0] == "rb" and len(args) == 2:
            hexdump(mem_read_byte(int(args[1], 16)))
        elif args[0] == "rs" and len(args) == 2:
            print(mem_read_string(int(args[1], 16)))
        else:
            mem_help()
    else:
        mem_help()


def task_help():
    print("task parse - Parses the threads of all tasks in memory")
    print("task save [fileName] - Saves the parsed threads to a file")
    print("task load [fileName] - Loads the parsed threads from a file")
    print("task dump [taskName] - Dumps all fields of the specified task")
    print("task stackdump [taskName] - Dumps the stack of the specified task")
    print("task stackdump [taskName] [size] - Dumps [size] bytes from the stack of the specified task")


def task_command(args):
    global tasks
    if len(args) == 0:
        task_help()
        return

    if len(args) == 1 and args[0] == "parse":
        tasks = {}
        print("Reading sm_ModuleTaskThreads...")

        taskThreadList = struct.unpack(">" + ("I" * 256), mem_read(sm_ModuleTaskThreads, 0x400))
        for thread in taskThreadList:
            if thread == 0:
                continue

            namePtr = struct.unpack(">I", mem_read(thread + 0x34, 4))[0]
            taskName = mem_read_string(namePtr)

            tasks[taskName] = thread
            print(f"Found {taskName} at {hex(thread)}")
        print("Finished parsing tasks!")
    elif len(args) >= 2:
        if args[0] == "save":
            with open(args[1], "w") as f:
                for taskName in tasks:
                    f.write(f"{taskName}:{tasks[taskName]}\n")
            print(f"Saved to: {args[1]}")
            return
        elif args[0] == "load":
            with open(args[1], "r") as f:
                lines = f.readlines()
                lineCount = len(lines)
                for line in lines:
                    split = line.split(':')
                    tasks[split[0]] = int(split[1])
            print(f"Loaded {lineCount} tasks from: {args[1]}")
            return

        taskName = args[1]

        if taskName not in tasks:
            print(f"{taskName} does not exist or the tasks haven't been parsed!")
            return

        threadPtr = tasks[taskName]
        print(f"Reading thread at {hex(threadPtr)}...")
        thread = TX_THREAD.TX_THREAD(mem_read(threadPtr, TX_THREAD.SIZE))
        taskName = mem_read_string(thread.name)

        if args[0] == "dump":
            print(f"Dumping fields of {taskName}:")
            thread.dumpFields()
        elif args[0] == "stackdump":
            if len(args) == 3:
                size = int(args[2], 16)
                start = (thread.stack_start + thread.stack_size) - size

                print(f"Dumping the stack of {taskName} ({size} bytes)...")
                hexdump(mem_read(start, size))
            else:
                print(f"Dumping the stack of {taskName} ({thread.stack_size} bytes)...")
                hexdump(mem_read(thread.stack_start, thread.stack_size))
        else:
            task_help()
    else:
        task_help()


def print_help():
    print("Available commands:")
    print("! [s] - Run shell command")
    print("!! [s] - Run underware command")
    print("!!! [s] - Run pie underware command")
    udw_help()
    nand_help()
    mem_help()
    task_help()


commands = {
    "udw": udw_command,
    "nand": nand_command,
    "mem": mem_command,
    "task": task_command
}
print_help()
while True:
    inp = input()
    if inp.startswith("!"):
        if inp.startswith("!!"):
            if inp.startswith("!!!"):
                print(runPieUnderware(inp[3:]))
                continue
            print(runUnderware(inp[2:]))
            continue
        print(runShellCommand(inp[1:]))
        continue

    args = inp.split()
    if len(args) == 0:
        print_help()
        continue

    cmd = args[0]
    if cmd in commands:
        commands[args[0]](args[1:])
    else:
        print_help()
