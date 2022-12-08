import struct

SIZE = 0xD8


class TX_THREAD:
    def __init__(self, data):
        self.id, self.run_count, self.stack_ptr, self.stack_start, self.stack_end, self.stack_size, self.time_slice, \
            self.new_time_slice, self.ready_next, self.ready_previous, self.field_28, self.field_2C, self.field_30, \
            self.name, self.priority, self.state, self.delayed_suspend, self.suspending, self.preempt_threshold, \
            self.schedule_hook, self.entry, self.entry_parameter, self.timer, self.suspend_cleanup, \
            self.suspend_control_block, self.suspended_next, self.suspended_previous, self.suspend_info, \
            self.additional_suspend_info, self.suspend_option, self.suspend_status, self.field_7C, self.field_80, \
            self.field_84, self.field_88, self.field_8C, self.field_90, self.field_94, self.field_98, self.field_9C, \
            self.field_A0, self.field_A4, self.field_A8, self.field_AC, self.field_B0, self.field_B4, self.field_B8, \
            self.maybe_filex_ptr, self.user_priority, self.user_preempt_threshold, self.inherit_priority, \
            self.owned_mutex_count, self.owned_mutex_list, self.entry_exit_notify \
            = struct.unpack(">" + ("I" * int(len(data) / 4)), data)

    def dumpFields(self):
        print(f"id: {hex(self.id)}")
        print(f"run_count: {hex(self.run_count)}")
        print(f"stack_ptr: {hex(self.stack_ptr)}")
        print(f"stack_start: {hex(self.stack_start)}")
        print(f"stack_end: {hex(self.stack_end)}")
        print(f"stack_size: {hex(self.stack_size)}")
        print(f"time_slice: {hex(self.time_slice)}")
        print(f"new_time_slice: {hex(self.new_time_slice)}")
        print(f"ready_next: {hex(self.ready_next)}")
        print(f"ready_previous: {hex(self.ready_previous)}")
        print(f"field_28: {hex(self.field_28)}")
        print(f"field_2C: {hex(self.field_2C)}")
        print(f"field_30: {hex(self.field_30)}")
        print(f"name: {hex(self.name)}")
        print(f"priority: {hex(self.priority)}")
        print(f"state: {hex(self.state)}")
        print(f"delayed_suspend: {hex(self.delayed_suspend)}")
        print(f"suspending: {hex(self.suspending)}")
        print(f"preempt_threshold: {hex(self.preempt_threshold)}")
        print(f"schedule_hook: {hex(self.schedule_hook)}")
        print(f"entry: {hex(self.entry)}")
        print(f"entry_parameter: {hex(self.entry_parameter)}")
        print(f"timer: {hex(self.timer)}")
        print(f"suspend_cleanup: {hex(self.suspend_cleanup)}")
        print(f"suspend_control_block: {hex(self.suspend_control_block)}")
        print(f"suspended_next: {hex(self.suspended_next)}")
        print(f"suspended_previous: {hex(self.suspended_previous)}")
        print(f"suspend_info: {hex(self.suspend_info)}")
        print(f"additional_suspend_info: {hex(self.additional_suspend_info)}")
        print(f"suspend_option: {hex(self.suspend_option)}")
        print(f"suspend_status: {hex(self.suspend_status)}")
        print(f"field_7C: {hex(self.field_7C)}")
        print(f"field_80: {hex(self.field_80)}")
        print(f"field_84: {hex(self.field_84)}")
        print(f"field_88: {hex(self.field_88)}")
        print(f"field_8C: {hex(self.field_8C)}")
        print(f"field_90: {hex(self.field_90)}")
        print(f"field_94: {hex(self.field_94)}")
        print(f"field_98: {hex(self.field_98)}")
        print(f"field_9C: {hex(self.field_9C)}")
        print(f"field_A0: {hex(self.field_A0)}")
        print(f"field_A4: {hex(self.field_A4)}")
        print(f"field_A8: {hex(self.field_A8)}")
        print(f"field_AC: {hex(self.field_AC)}")
        print(f"field_B0: {hex(self.field_B0)}")
        print(f"field_B4: {hex(self.field_B4)}")
        print(f"field_B8: {hex(self.field_B8)}")
        print(f"maybe_filex_ptr: {hex(self.maybe_filex_ptr)}")
        print(f"user_priority: {hex(self.user_priority)}")
        print(f"user_preempt_threshold: {hex(self.user_preempt_threshold)}")
        print(f"inherit_priority: {hex(self.inherit_priority)}")
        print(f"owned_mutex_count: {hex(self.owned_mutex_count)}")
        print(f"owned_mutex_list: {hex(self.owned_mutex_list)}")
        print(f"entry_exit_notify: {hex(self.entry_exit_notify)}")
