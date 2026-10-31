/* Public Amiga ABI: preserve all32 caller D7 bits and long args. */
    .section .text.bl_c64_actor_registers,"ax"
    .globl bl_c64_actor_registers
bl_c64_actor_registers:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_actor_registers_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_actor_test_call,"ax"
    .globl bl_c64_actor_test_call
bl_c64_actor_test_call:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_actor_test_call_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_audio_request,"ax"
    .globl bl_c64_audio_request
bl_c64_audio_request:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_audio_request_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_collect,"ax"
    .globl bl_c64_collect
bl_c64_collect:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_collect_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_contact,"ax"
    .globl bl_c64_contact
bl_c64_contact:
    move.l %d7,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_contact_d7
    lea 16(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_contact_kernel_selftest,"ax"
    .globl bl_c64_contact_kernel_selftest
bl_c64_contact_kernel_selftest:
    move.l %d7,-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_contact_kernel_selftest_d7
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_door,"ax"
    .globl bl_c64_door
bl_c64_door:
    move.l %d7,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_door_d7
    lea 16(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_enemy_door,"ax"
    .globl bl_c64_enemy_door
bl_c64_enemy_door:
    move.l %d7,-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_enemy_door_d7
    lea 32(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_enemy_entry,"ax"
    .globl bl_c64_enemy_entry
bl_c64_enemy_entry:
    move.l %d7,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_enemy_entry_d7
    lea 16(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_enemy_hazard,"ax"
    .globl bl_c64_enemy_hazard
bl_c64_enemy_hazard:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_enemy_hazard_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_enemy_remove,"ax"
    .globl bl_c64_enemy_remove
bl_c64_enemy_remove:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_enemy_remove_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_field,"ax"
    .globl bl_c64_field
bl_c64_field:
    move.l %d7,-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_field_d7
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_load,"ax"
    .globl bl_c64_load
bl_c64_load:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_load_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_load_at,"ax"
    .globl bl_c64_load_at
bl_c64_load_at:
    move.l %d7,-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_load_at_d7
    lea 12(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_object,"ax"
    .globl bl_c64_object
bl_c64_object:
    move.l %d7,-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_object_d7
    lea 12(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_object_pose,"ax"
    .globl bl_c64_object_pose
bl_c64_object_pose:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_object_pose_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_paint_animation_frame,"ax"
    .globl bl_c64_paint_animation_frame
bl_c64_paint_animation_frame:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_paint_animation_frame_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_paint_changes,"ax"
    .globl bl_c64_paint_changes
bl_c64_paint_changes:
    move.l %d7,-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_paint_changes_d7
    lea 12(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_paint_part,"ax"
    .globl bl_c64_paint_part
bl_c64_paint_part:
    move.l %d7,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_paint_part_d7
    lea 16(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_paint_room,"ax"
    .globl bl_c64_paint_room
bl_c64_paint_room:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_paint_room_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_reset,"ax"
    .globl bl_c64_reset
bl_c64_reset:
    move.l %d7,-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_reset_d7
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_restore_progress,"ax"
    .globl bl_c64_restore_progress
bl_c64_restore_progress:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_restore_progress_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_spawn_services,"ax"
    .globl bl_c64_spawn_services
bl_c64_spawn_services:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_spawn_services_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_test_execute,"ax"
    .globl bl_c64_test_execute
bl_c64_test_execute:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_test_execute_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_tick,"ax"
    .globl bl_c64_tick
bl_c64_tick:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_tick_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_tick_begin,"ax"
    .globl bl_c64_tick_begin
bl_c64_tick_begin:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_tick_begin_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_tick_room,"ax"
    .globl bl_c64_tick_room
bl_c64_tick_room:
    move.l %d7,-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_tick_room_d7
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_world_jump,"ax"
    .globl bl_c64_world_jump
bl_c64_world_jump:
    move.l %d7,-(%sp)
    move.l 8(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_world_jump_d7
    lea 4(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_world_start,"ax"
    .globl bl_c64_world_start
bl_c64_world_start:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_world_start_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_c64_world_step,"ax"
    .globl bl_c64_world_step
bl_c64_world_step:
    move.l %d7,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_c64_world_step_d7
    lea 8(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
    .section .text.bl_d7_probe_abi,"ax"
    .globl bl_d7_probe_abi
bl_d7_probe_abi:
    move.l %d7,-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.b bruce_a_mirror,%d7
    jsr bl_d7_probe_abi_d7
    lea 32(%sp),%sp
    move.b %d7,bruce_a_mirror
    move.l (%sp)+,%d7
    rts
