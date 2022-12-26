typedef struct TX_THREAD TX_THREAD;
struct TX_THREAD
{
    int tx_thread_id;
    int tx_thread_run_count;
    void *tx_thread_stack_ptr;
    void *tx_thread_stack_start;
    void *tx_thread_stack_end;
    int tx_thread_stack_size;
    int tx_thread_time_slice;
    int tx_thread_new_time_slice;
    TX_THREAD *tx_thread_ready_next;
    TX_THREAD *tx_thread_ready_previous;
    int field_28;
    int field_2C;
    int field_30;
    char *tx_thread_name;
    int tx_thread_priority;
    int tx_thread_state;
    int tx_thread_delayed_suspend;
    int tx_thread_suspending;
    int tx_thread_preempt_threshold;
    int tx_thread_schedule_hook;
    void (*tx_thread_entry)(unsigned int id);
    int tx_thread_entry_parameter;
    int tx_thread_timer;
    int tx_thread_suspend_cleanup;
    int tx_thread_suspend_control_block;
    TX_THREAD *tx_thread_suspended_next;
    TX_THREAD *tx_thread_suspended_previous;
    int tx_thread_suspend_info;
    void *tx_thread_additional_suspend_info;
    int tx_thread_suspend_option;
    int tx_thread_suspend_status;
    int field_7C;
    int field_80;
    int field_84;
    int field_88;
    int field_8C;
    int field_90;
    int field_94;
    int field_98;
    int field_9C;
    int field_A0;
    int field_A4;
    int field_A8;
    int field_AC;
    int field_B0;
    int field_B4;
    int field_B8;
    int maybe_tx_thread_filex_ptr;
    int tx_thread_user_priority;
    int tx_thread_user_preempt_threshold;
    int tx_thread_inherit_priority;
    int tx_thread_owned_mutex_count;
    int tx_thread_owned_mutex_list;
    void (*tx_thread_entry_exit_notify)(TX_THREAD *thread_ptr, unsigned int type);
};

#define TICKS_PER_SECOND 60

TX_THREAD **_tx_thread_current_ptr = (TX_THREAD**)0x80000CD0;
unsigned int (*txe_thread_create)(TX_THREAD *thread_ptr, char *name_ptr, void (*entry_function)(unsigned int),
        int entry_input, void *stack_start, unsigned int stack_size, unsigned int priority, 
        unsigned int preempt_threshold, int time_slice, unsigned int auto_start, 
        int thread_control_block_size) = (void*)0x413B0F68;
unsigned int (*tx_thread_sleep)(unsigned int timer_ticks) = (void*)0x413AF5D8;