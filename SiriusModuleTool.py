import ctypes

import idaapi
import idc
import idc_bc695
import struct
import ctypes
from enum import Enum

try:
    from base import database
    from base import segment
    from base import structure
    from base import function
    from base import instruction
except:
    pass


def swap32(i):
    return struct.unpack("<I", struct.pack(">I", i))[0]


def swap16(i):
    return struct.unpack("<H", struct.pack(">H", i))[0]


class StructToClass:
    def __init__(self, dict):
        for k in dict:
            val = dict[k]

            ctype = type(val)

            if ctype == ctypes.c_ulong:
                val = swap32(val.value)
            elif ctype == ctypes.c_ushort:
                val = swap16(val.value)
            else:
                val = val.value

            setattr(self, k, val)


class ModuleType(Enum):
    Library = 0
    Component = 1
    Hybrid = 2


def log(s):
    with open("SiriusModuleTool.log", "a") as f:
        f.write(s + "\n")


def unknownAndString(ea):
    database.set.unknown(ea)
    database.set.string(ea)
    return database.get.string(ea)


def rename(ea, s):
    if s.startswith("sub"):
        s = f"_{s}"
    try:
        database.name(ea, s)
    except:
        print(f"Failed to create {s} label, it probably exists already.")


def renameFunc(ea, s):
    if s.startswith("sub"):
        s = f"_{s}"
    function.name(ea, s)
    # print(f"Failed to rename function at 0x{hex(ea)} to {s}")


def createFuncAndRename(ea, s):
    isThumb = ea % 2
    ea -= isThumb
    idaapi.split_sreg_range(ea, idaapi.str2reg("T"), isThumb, idaapi.SR_user)

    database.set.unknown(ea)
    database.set.code(ea)
    try:
        function.new(ea)
        renameFunc(ea, s)
    except:
        print(f"Failed creating func at 0x{hex(ea)}:{s}, trying to create a label instead")
        rename(ea, s)


def main():
    if not structure.has("Module"):
        log("No Module structure found in idb!")
        return

    moduleStart, moduleEnd = segment.bounds(segment.by_name(".module"))

    log(f"Module segment at start: {hex(moduleStart)} end: {hex(moduleEnd)}")
    modulesCount = int((moduleEnd - moduleStart) / 4)
    log(f"There are {modulesCount} modules")

    currentOffset = moduleStart
    while currentOffset != moduleEnd:
        database.set.unknown(currentOffset)
        moduleOffset = database.get.unsigned(currentOffset, 4)
        database.set.unknown(moduleOffset)

        database.set(currentOffset, "Module*")
        database.set(moduleOffset, "Module")
        moduleIDAStruct = database.get.structure(moduleOffset, "Module")
        moduleStruct = StructToClass(moduleIDAStruct)
        log(f"ModulePtr: 0x{hex(currentOffset)} Module: 0x{hex(moduleOffset)}")

        if moduleStruct.field_2 == 0x20:
            currentOffset += 4
            log(f"Skipping 0x{hex(moduleStruct.ID)} because of abnormal values.")
            continue

        try:
            moduleName = unknownAndString(moduleStruct.Name)
        except:
            currentOffset += 4
            log(f"Skipping 0x{hex(moduleStruct.ID)}, this module has no name?")
            continue

        try:
            moduleType = ModuleType(moduleStruct.Type)
        except:
            currentOffset += 4
            log(f"Skipping 0x{hex(moduleStruct.ID)}, this module has an invalid type.")
            continue

        if moduleStruct.TaskCount > 500 or moduleStruct.ExportsCount > 500 or moduleStruct.ImportsCount > 500:
            currentOffset += 4
            log(f"Skipping 0x{hex(moduleStruct.ID)}, this module has abnormal list counts.")
            continue

        isARMCode = moduleStruct.GetFunctionTable % 2 == 0
        log(f"\tID: 0x{hex(moduleStruct.ID)}")
        log(f"\tName: {moduleName}")
        log(f"\tType: {str(moduleType)}")
        log(f"\tTaskCount: {moduleStruct.TaskCount}")
        log(f"\tExportsCount: {moduleStruct.ExportsCount}")
        log(f"\tImportsCount: {moduleStruct.ImportsCount}")

        log(f"\tGetFunctionTable code is ARM: {isARMCode}")
        getFunctionTableInstr = database.instruction(moduleStruct.GetFunctionTable)

        getFuncTable = moduleStruct.GetFunctionTable - 1 if not isARMCode else moduleStruct.GetFunctionTable
        try:
            if "MOV" not in getFunctionTableInstr:
                log(f"\tGetFunctionTable instruction before fixing: {getFunctionTableInstr}")

                database.set.unknown(getFuncTable, 8)
                # database.set.unknown(getFuncTable + 4)

                if isARMCode:
                    idaapi.split_sreg_range(getFuncTable, idaapi.str2reg("T"), 0, idaapi.SR_user)
                else:
                    idaapi.split_sreg_range(getFuncTable, idaapi.str2reg("T"), 1, idaapi.SR_user)

                database.set.code(getFuncTable)
                # database.set.code(getFuncTable + 4)

                getFunctionTableInstr = database.instruction(moduleStruct.GetFunctionTable)
                log(f"\tGetFunctionTable instruction after fixing: {getFunctionTableInstr}")
                if "MOV" not in getFunctionTableInstr:
                    log("\tStill invalid! Try running the script again.")
                    return
            function.new(getFuncTable)
        except:
            pass
        rename(getFuncTable, f"{moduleName}_GetFunctionTable")

        if "MOVW" in getFunctionTableInstr:
            funcTablePtr = instruction.op_reference(getFuncTable + 4, 1)
        else:
            funcTablePtr = instruction.op_reference(getFuncTable, 1)
        funcTable = database.get.unsigned(funcTablePtr, 4)
        log(f"\tfuncTablePtr: 0x{hex(funcTablePtr)}")
        log(f"\tfuncTable: 0x{hex(funcTable)}")

        database.set.unknown(funcTablePtr)
        database.set.unknown(funcTable)
        database.set(funcTablePtr, "FuncTable*")
        database.set(funcTable, "FuncTable")

        funcTableStruct = database.get.structure(funcTable, "FuncTable")
        for func in funcTableStruct:
            ea = swap32(funcTableStruct[func].value)
            if ea != 0:
                createFuncAndRename(ea, f"{moduleName}_{func}")

        if moduleStruct.TaskCount > 0:
            database.set.unknown(moduleStruct.Tasks)
            database.set(moduleStruct.Tasks, f"Task[{moduleStruct.TaskCount}]")
            rename(moduleStruct.Tasks, f"{moduleName}_Tasks")
            log("\tTasks:")
            for taskStruct in database.get.array(moduleStruct.Tasks):
                tid = swap32(taskStruct["TID"].value)
                taskName = unknownAndString(swap32(taskStruct["TaskName"].value))
                stackSize = swap32(taskStruct["StackSize"].value)
                entry = swap32(taskStruct["Entry"].value)

                log(f"\t\t{taskName}:")
                log(f"\t\t\tTID: 0x{hex(tid)}")
                log(f"\t\t\tStackSize: 0x{hex(stackSize)}")
                log(f"\t\t\tEntry: 0x{hex(entry)}")

                createFuncAndRename(entry, f"{moduleName}_{taskName}")

        if moduleStruct.ExportsCount > 0:
            database.set.unknown(moduleStruct.Exports)
            database.set(moduleStruct.Exports, f"Export[{moduleStruct.ExportsCount}]")
            rename(moduleStruct.Exports, f"{moduleName}_Exports")
        if moduleStruct.ImportsCount > 0:
            database.set.unknown(moduleStruct.Imports)
            database.set(moduleStruct.Imports, f"Import[{moduleStruct.ImportsCount}]")
            rename(moduleStruct.Imports, f"{moduleName}_Imports")

        rename(moduleOffset, f"{moduleName}_Module")
        rename(funcTablePtr, f"{moduleName}_FuncTablePtr")
        rename(funcTable, f"{moduleName}_FuncTable")

        currentOffset += 4


if __name__ == "__main__":
    main()
