    .section .text.bl_c64_actor_ram_hash,"ax"
    .globl bl_c64_actor_ram_hash
bl_c64_actor_ram_hash:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_actor_ram_hash_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_actor_registers,"ax"
    .globl bl_c64_actor_registers
bl_c64_actor_registers:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_actor_registers_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_actor_test_call,"ax"
    .globl bl_c64_actor_test_call
bl_c64_actor_test_call:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_actor_test_call_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_attribute,"ax"
    .globl bl_c64_attribute
bl_c64_attribute:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_attribute_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_audio_frame,"ax"
    .globl bl_c64_audio_frame
bl_c64_audio_frame:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_audio_frame_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_audio_request,"ax"
    .globl bl_c64_audio_request
bl_c64_audio_request:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_audio_request_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_audio_reset,"ax"
    .globl bl_c64_audio_reset
bl_c64_audio_reset:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_audio_reset_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_build_animation_cache,"ax"
    .globl bl_c64_build_animation_cache
bl_c64_build_animation_cache:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_build_animation_cache_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_cell_dirty,"ax"
    .globl bl_c64_cell_dirty
bl_c64_cell_dirty:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_cell_dirty_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_charset_row,"ax"
    .globl bl_c64_charset_row
bl_c64_charset_row:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_charset_row_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_check_interleaved,"ax"
    .globl bl_c64_check_interleaved
bl_c64_check_interleaved:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_check_interleaved_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_clear_death,"ax"
    .globl bl_c64_clear_death
bl_c64_clear_death:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_clear_death_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_clear_dirty,"ax"
    .globl bl_c64_clear_dirty
bl_c64_clear_dirty:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_clear_dirty_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_collect,"ax"
    .globl bl_c64_collect
bl_c64_collect:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_collect_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_collected,"ax"
    .globl bl_c64_collected
bl_c64_collected:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_collected_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_collected_all,"ax"
    .globl bl_c64_collected_all
bl_c64_collected_all:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_collected_all_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_contact,"ax"
    .globl bl_c64_contact
bl_c64_contact:
    move.l %a4,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_contact_a4
    lea 16(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_contact_kernel_selftest,"ax"
    .globl bl_c64_contact_kernel_selftest
bl_c64_contact_kernel_selftest:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_contact_kernel_selftest_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_dead,"ax"
    .globl bl_c64_dead
bl_c64_dead:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_dead_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_debug_complete_before,"ax"
    .globl bl_c64_debug_complete_before
bl_c64_debug_complete_before:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_debug_complete_before_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_door,"ax"
    .globl bl_c64_door
bl_c64_door:
    move.l %a4,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_door_a4
    lea 16(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_enemy_door,"ax"
    .globl bl_c64_enemy_door
bl_c64_enemy_door:
    move.l %a4,-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_enemy_door_a4
    lea 32(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_enemy_entries_clear,"ax"
    .globl bl_c64_enemy_entries_clear
bl_c64_enemy_entries_clear:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_enemy_entries_clear_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_enemy_entry,"ax"
    .globl bl_c64_enemy_entry
bl_c64_enemy_entry:
    move.l %a4,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_enemy_entry_a4
    lea 16(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_enemy_follow,"ax"
    .globl bl_c64_enemy_follow
bl_c64_enemy_follow:
    move.l %a4,-(%sp)
    move.l 24(%sp),-(%sp)
    move.l 24(%sp),-(%sp)
    move.l 24(%sp),-(%sp)
    move.l 24(%sp),-(%sp)
    move.l 24(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_enemy_follow_a4
    lea 20(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_enemy_hazard,"ax"
    .globl bl_c64_enemy_hazard
bl_c64_enemy_hazard:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_enemy_hazard_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_enemy_remove,"ax"
    .globl bl_c64_enemy_remove
bl_c64_enemy_remove:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_enemy_remove_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_field,"ax"
    .globl bl_c64_field
bl_c64_field:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_field_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_flash_color,"ax"
    .globl bl_c64_flash_color
bl_c64_flash_color:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_flash_color_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_glyph,"ax"
    .globl bl_c64_glyph
bl_c64_glyph:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_glyph_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_has_dirty,"ax"
    .globl bl_c64_has_dirty
bl_c64_has_dirty:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_has_dirty_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_load,"ax"
    .globl bl_c64_load
bl_c64_load:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_load_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_load_at,"ax"
    .globl bl_c64_load_at
bl_c64_load_at:
    move.l %a4,-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_load_at_a4
    lea 12(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_motion,"ax"
    .globl bl_c64_motion
bl_c64_motion:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_motion_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_needs_full_paint,"ax"
    .globl bl_c64_needs_full_paint
bl_c64_needs_full_paint:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_needs_full_paint_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_object,"ax"
    .globl bl_c64_object
bl_c64_object:
    move.l %a4,-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_object_a4
    lea 12(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_object_pose,"ax"
    .globl bl_c64_object_pose
bl_c64_object_pose:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_object_pose_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_paint_animation_frame,"ax"
    .globl bl_c64_paint_animation_frame
bl_c64_paint_animation_frame:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_paint_animation_frame_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_paint_changes,"ax"
    .globl bl_c64_paint_changes
bl_c64_paint_changes:
    move.l %a4,-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_paint_changes_a4
    lea 12(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_paint_part,"ax"
    .globl bl_c64_paint_part
bl_c64_paint_part:
    move.l %a4,-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    move.l 20(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_paint_part_a4
    lea 16(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_paint_room,"ax"
    .globl bl_c64_paint_room
bl_c64_paint_room:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_paint_room_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_pixel,"ax"
    .globl bl_c64_pixel
bl_c64_pixel:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_pixel_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_player_sprite_contact,"ax"
    .globl bl_c64_player_sprite_contact
bl_c64_player_sprite_contact:
    move.l %a4,-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    move.l 16(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_player_sprite_contact_a4
    lea 12(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_prepare_paint,"ax"
    .globl bl_c64_prepare_paint
bl_c64_prepare_paint:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_prepare_paint_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_projectile,"ax"
    .globl bl_c64_projectile
bl_c64_projectile:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_projectile_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_read,"ax"
    .globl bl_c64_read
bl_c64_read:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_read_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_recovery_pose,"ax"
    .globl bl_c64_recovery_pose
bl_c64_recovery_pose:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_recovery_pose_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_reenter,"ax"
    .globl bl_c64_reenter
bl_c64_reenter:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_reenter_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_remaining,"ax"
    .globl bl_c64_remaining
bl_c64_remaining:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_remaining_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_reset,"ax"
    .globl bl_c64_reset
bl_c64_reset:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_reset_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_restore_progress,"ax"
    .globl bl_c64_restore_progress
bl_c64_restore_progress:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_restore_progress_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_save_progress,"ax"
    .globl bl_c64_save_progress
bl_c64_save_progress:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_save_progress_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_screen,"ax"
    .globl bl_c64_screen
bl_c64_screen:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_screen_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_screen_color,"ax"
    .globl bl_c64_screen_color
bl_c64_screen_color:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_screen_color_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_set_lives,"ax"
    .globl bl_c64_set_lives
bl_c64_set_lives:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_set_lives_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_set_opponent_mode,"ax"
    .globl bl_c64_set_opponent_mode
bl_c64_set_opponent_mode:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_set_opponent_mode_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_spawn_counter,"ax"
    .globl bl_c64_spawn_counter
bl_c64_spawn_counter:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_spawn_counter_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_spawn_result,"ax"
    .globl bl_c64_spawn_result
bl_c64_spawn_result:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_spawn_result_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_spawn_services,"ax"
    .globl bl_c64_spawn_services
bl_c64_spawn_services:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_spawn_services_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_spawn_sync,"ax"
    .globl bl_c64_spawn_sync
bl_c64_spawn_sync:
    move.l %a4,-(%sp)
    move.l 28(%sp),-(%sp)
    move.l 28(%sp),-(%sp)
    move.l 28(%sp),-(%sp)
    move.l 28(%sp),-(%sp)
    move.l 28(%sp),-(%sp)
    move.l 28(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_spawn_sync_a4
    lea 24(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_test_execute,"ax"
    .globl bl_c64_test_execute
bl_c64_test_execute:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_test_execute_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_test_write,"ax"
    .globl bl_c64_test_write
bl_c64_test_write:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_test_write_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_tick,"ax"
    .globl bl_c64_tick
bl_c64_tick:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_tick_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_tick_begin,"ax"
    .globl bl_c64_tick_begin
bl_c64_tick_begin:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_tick_begin_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_tick_room,"ax"
    .globl bl_c64_tick_room
bl_c64_tick_room:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_tick_room_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_tile,"ax"
    .globl bl_c64_tile
bl_c64_tile:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_tile_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_vic_compare_selftest,"ax"
    .globl bl_c64_vic_compare_selftest
bl_c64_vic_compare_selftest:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_vic_compare_selftest_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_world_actor,"ax"
    .globl bl_c64_world_actor
bl_c64_world_actor:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_world_actor_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_world_jump,"ax"
    .globl bl_c64_world_jump
bl_c64_world_jump:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_world_jump_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_world_ready,"ax"
    .globl bl_c64_world_ready
bl_c64_world_ready:
    move.l %a4,-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_world_ready_a4
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_world_start,"ax"
    .globl bl_c64_world_start
bl_c64_world_start:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_world_start_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_world_stat,"ax"
    .globl bl_c64_world_stat
bl_c64_world_stat:
    move.l %a4,-(%sp)
    move.l 8(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_world_stat_a4
    lea 4(%sp),%sp
    move.l (%sp)+,%a4
    rts
    .section .text.bl_c64_world_step,"ax"
    .globl bl_c64_world_step
bl_c64_world_step:
    move.l %a4,-(%sp)
    move.l 12(%sp),-(%sp)
    move.l 12(%sp),-(%sp)
    lea bruce_m_storage,%a4
    jsr bl_c64_world_step_a4
    lea 8(%sp),%sp
    move.l (%sp)+,%a4
    rts
