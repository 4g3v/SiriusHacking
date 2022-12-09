import importlib
import inspect
import struct
import pkgutil
import serial
from hexdump import hexdump

PORT = "COM3"
PAGE_SIZE = 2048
BLOCK_SIZE = 64
PLANE_SIZE = 1024
sm_ModuleTaskThreads = 0xC3E17120

ser = serial.Serial(PORT, 115200)
tasks = {}
structs = {}


def getClassFromModule(m):
    return inspect.getmembers(mod, inspect.isclass)[0][1]


for _, name, _ in pkgutil.iter_modules(["structures"]):
    mod = importlib.import_module("structures." + name)
    structs[name] = getClassFromModule(mod)


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
    print("mem w [filePath] [address] - Writes a file to the specified address, file size has to be a multiple of 4")
    print("mem wd [address] [dword] - Writes a dword to the specified address")
    print("mem wb [address] [byte] - Writes a byte to the specified address")


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


def mem_write_dword(addr, dword):
    runUnderware(f"photo_hw.write {hex(addr)} 4 {hex(dword)}")


def mem_write_byte(addr, byte):
    runUnderware(f"photo_hw.write {hex(addr)} 1 {hex(byte)}")


def mem_write(addr, data):
    offset = 0
    while True:
        if offset == len(data):
            break
        dword = struct.unpack(">I", data[offset:offset+4])[0]
        mem_write_dword(addr+offset, dword)
        offset += 4


def mem_command(args):
    if len(args) == 0:
        mem_help()
        return

    if len(args) > 1:
        if len(args) == 3:
            if args[0] == "r":
                hexdump(mem_read(int(args[1], 16), int(args[2], 16)))
            elif args[0] == "w":
                filePath = args[1]
                addr = int(args[2], 16)

                with open(filePath, "rb") as f:
                    fileData = f.read()

                mem_write(addr, fileData)
                print(f"Wrote {filePath} ({len(fileData)} bytes) to {hex(addr)}")
            elif args[0] == "wd":
                addr = int(args[1], 16)
                dword = int(args[2], 16)
                mem_write_dword(addr, dword)

                print(f"Wrote {hex(dword)} to {hex(addr)}")
            elif args[0] == "wb":
                addr = int(args[1], 16)
                dword = int(args[2], 16)
                mem_write_byte(addr, dword)

                print(f"Wrote {hex(dword)} to {hex(addr)}")
            else:
                mem_help()
        elif args[0] == "rb" and len(args) == 2:
            hexdump(mem_read_byte(int(args[1], 16)))
        elif args[0] == "rs" and len(args) == 2:
            print(mem_read_string(int(args[1], 16)))
        else:
            mem_help()
    else:
        mem_help()


def struct_read(name, address):
    structType = structs[name]
    structData = mem_read(address, structType.SIZE)
    return structType(structData)


def task_help():
    print("task parse - Parses the threads of all tasks in memory")
    print("task list - Lists parsed tasks")
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

    if len(args) == 1:
        if args[0] == "parse":
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
        elif args[0] == "list":
            for taskName in tasks:
                print(f"{taskName} at {hex(tasks[taskName])}")
        else:
            task_help()
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

        thread = struct_read("TX_THREAD", threadPtr)
        taskName = mem_read_string(thread.name)

        if args[0] == "dump":
            print(f"Dumping fields of {taskName}:")
            thread.dump()
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


def struct_help():
    print("struct dump [structName] [address] - Reads a struct at the specified address and dumps its fields")
    print(
        "struct stackdump [structName] [taskName] [offset] - Reads a struct from the stack of the specified task and dumps its fields")
    print("struct list - Lists all available structs")


def struct_command(args):
    if len(args) == 0:
        struct_help()
        return

    if len(args) > 1:
        if len(args) == 3 and args[0] == "dump":
            structName = args[1]
            structAddress = int(args[2], 16)
            if structName not in structs:
                print(f"{structName} doesn't exist!")
                return

            print(f"Reading {structName} at {hex(structAddress)}")
            struct_ = struct_read(structName, structAddress)
            struct_.dump()
        elif len(args) == 4 and args[0] == "stackdump":
            structName = args[1]
            taskName = args[2]
            offset = int(args[3], 16)

            if taskName not in tasks:
                print(f"{taskName} does not exist or the tasks haven't been parsed!")
                return
            if structName not in structs:
                print(f"{structName} doesn't exist!")
                return

            threadPtr = tasks[taskName]
            print(f"Reading thread at {hex(threadPtr)}...")

            thread = struct_read("TX_THREAD", threadPtr)
            taskName = mem_read_string(thread.name)

            start = (thread.stack_start + thread.stack_size) - offset
            print(f"Reading {structName} from the stack of {taskName} at {hex(start)}")
            struct_ = struct_read(structName, start)
            struct_.dump()
        else:
            struct_help()
    elif args[0] == "list":
        print("Available structs:")
        for structName in structs:
            print(f"{structName} ({hex(structs[structName].SIZE)} bytes)")
    else:
        struct_help()


def eval_help():
    print("eval [expression] - Evaluates the expression")


def eval_command(args):
    if len(args) == 0:
        eval_help()
        return

    try:
        expression = " ".join(args)
        print(f"Evaluating {expression}")
        res = eval(expression)
        print(f"Result: {res}")
    except Exception as exc:
        print(f"Exception: {exc}")


def print_help():
    print("Available commands:")
    print("! [s] - Run shell command")
    print("!! [s] - Run underware command")
    print("!!! [s] - Run pie underware command")
    udw_help()
    nand_help()
    mem_help()
    task_help()
    struct_help()
    eval_help()


commands = {
    "udw": udw_command,
    "nand": nand_command,
    "mem": mem_command,
    "task": task_command,
    "struct": struct_command,
    "eval": eval_command
}
print_help()
while True:
    inp = input()
    print()
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
