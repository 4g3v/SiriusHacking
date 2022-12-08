import struct


class TX_SEMAPHORE:
    SIZE = 0x20

    def __init__(self, data):
        self.id, self.name, self.count, self.suspension_list, self.suspended_count, self.created_next, \
            self.created_previous, self.field_1C = struct.unpack(">" + ("I" * int(len(data) / 4)), data)

    def dump(self):
        print(f"id: {hex(self.id)}")
        print(f"name: {hex(self.name)}")
        print(f"count: {hex(self.count)}")
        print(f"suspension_list: {hex(self.suspension_list)}")
        print(f"suspended_count: {hex(self.suspended_count)}")
        print(f"created_next: {hex(self.created_next)}")
        print(f"created_previous: {hex(self.created_previous)}")
        print(f"field_1C: {hex(self.field_1C)}")
