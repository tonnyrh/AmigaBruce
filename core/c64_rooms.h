#ifndef BRUCE_C64_ROOMS_H
#define BRUCE_C64_ROOMS_H
#include "game.h"
/* Scalar API arguments use32-bit long, including with the room-only -mshort build. */
/* Source coordinates: X=sprite left, Y=bottom+1 of the21-row source mask. */
void bl_c64_reset(void);
void bl_c64_load(long room);
void bl_c64_load_at(long room,long x,long y);
void bl_c64_tick(long x,long y);
void bl_c64_field(void);
/* Optional cooperative I/O checkpoint. Must not call room/actor routines. */
void bl_c64_set_service(void (*service)(void));
void bl_c64_set_load_service(void (*service)(long loading));
void bl_c64_audio_reset(void);
void bl_c64_audio_request(long effect);
void bl_c64_audio_frame(unsigned char *registers); /*25SID bytes + gate-rise mask*/
unsigned short bl_c64_audio_faults(void);
unsigned short bl_c64_audio_requests(void);
unsigned char bl_c64_room(void);
unsigned char bl_c64_pixel(long x,long y);
unsigned char bl_c64_contact(long x,long y,long pose,long body_only);
/* Source idle/punch/prone, kick, jump/fall, net and wall-recovery masks.
 * Walk/reaction pose sequencing remains an explicit actor adapter. */
unsigned char bl_c64_object_pose(const BlGame *game);
unsigned char bl_c64_recovery_pose(long previous_pose);
unsigned char bl_c64_tile(long column,long row);
unsigned char bl_c64_attribute(long column,long row);
unsigned char bl_c64_charset_row(long tile,long row);
void bl_c64_colors(long y,unsigned char *colors);
unsigned long bl_c64_planar(long bits,long color,long y);
unsigned char bl_c64_changed_rows(long cell);
unsigned char bl_c64_flash_color(void);
const unsigned short *bl_c64_offsets(void);
const unsigned char *bl_c64_cell_y(void);
void bl_c64_paint_room(unsigned char *planes,long scene_top);
unsigned char bl_c64_needs_full_paint(void);
typedef struct {unsigned char *bitmap;const unsigned char *planes;unsigned long cell,slot,changed,scene_top;} BlC64Paint;
typedef void (*BlC64Painter)(const BlC64Paint *request);
void bl_c64_set_painter(BlC64Painter painter);
typedef struct {unsigned char *bitmap;const unsigned char *pixels;unsigned long left,top,width,height,first_mask,last_mask;} BlC64Block;
typedef void (*BlC64BlockPainter)(const BlC64Block *request);
void bl_c64_set_block_painter(BlC64BlockPainter painter);
long bl_c64_build_animation_cache(unsigned char *cache,long capacity);
void bl_c64_prepare_paint(void);
void bl_c64_test_execute(long entry);
long bl_c64_check_interleaved(const unsigned char *bitmap,long scene_top);
const unsigned short *bl_c64_paint_changes(unsigned char *planes,long scene_top,unsigned short *count);
const unsigned short *bl_c64_paint_part(unsigned char *planes,long scene_top,long limit,unsigned short *count);
unsigned char bl_c64_paint_done(void);
const unsigned long *bl_c64_part_words(void);
const unsigned char *bl_c64_part_rows(void);
unsigned char bl_c64_screen(long cell);
unsigned char bl_c64_screen_color(long cell);
unsigned char bl_c64_glyph(long code,long row);
unsigned char bl_c64_has_dirty(void);
unsigned char bl_c64_cell_dirty(long cell);
void bl_c64_clear_dirty(void);
unsigned short bl_c64_revision(void);
unsigned short bl_c64_fault(void);
long bl_c64_collect(long column,long row);
long bl_c64_door(long tile,long x,long y,long falling);
void bl_c64_motion(const BlGame *game);
void bl_c64_reenter(void); /* $24DB-$24EA, source default entry in current room */
long bl_c64_transition(long *x,long *y,unsigned char *room);
unsigned short bl_c64_collected(long room);
unsigned char bl_c64_remaining(long room);
void bl_c64_object(long tile,long column,long row);
unsigned char bl_c64_dead(void);
typedef struct {signed short x,y;unsigned char active,color,width;unsigned char bits[63];} BlC64Projectile;
void bl_c64_projectile(long index,BlC64Projectile *sprite);
void bl_c64_player_sprite_contact(long x,long y,long pose);
/* Read-only diagnostic access, used to compare native room state with source. */
unsigned char bl_c64_read(long address);
void bl_c64_test_write(long address,long value);
void bl_c64_profile_reset(void);
unsigned short bl_c64_profile(long item);
void bl_c64_profile_add(long item,long lines);
#endif
