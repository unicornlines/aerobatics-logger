// Unicornlines aerobatics logger: case, key bridge, keycaps and mount.
// Everything is derived from board.scad (generated from KiCad) and params.scad.
//
//   openscad -D 'part="front"' -o out/front.stl case.scad
//
// Parts: front, keybridge, lcd_frame, tray, plate, cap_up, cap_ok, cap_dn, all (= assembly)

include <params.scad>
include <board.scad>

part = "all";
explode = 0;     // 0 = assembled; ~1 = exploded view
show_board = true;
release = 0;      // 1 = the unit slid most of the way off its plate (render)
piece_name = "";  // with part = "piece": one assembly piece in place (used by tools/render)

// ---------------------------------------------------------------- board queries
function feats(role) = [for (f = board_features) if (f[1] == role) f];
function feat(role) = feats(role)[0];
function has(role) = len(feats(role)) > 0;
function fxy(f) = f[2];
function fbb(f) = f[5];
function fh(f) = f[6];
function in_list(x, l) = len([for (e = l) if (e == x) 1]) > 0;

holes = feats("hole");
// a column through the cell is impossible: such a hole is not used by the case
function in_cell(h) = cell[0] > 0 && fxy(h).x > cell_at.x - cell[2] / 2 - 4 && fxy(h).x < cell_at.x + cell[2] / 2 + 4
                                  && fxy(h).y > cell_at.y - cell[1] / 2 - 4 && fxy(h).y < cell_at.y + cell[1] / 2 + 4;
used_holes = [for (h = holes) if (!in_cell(h)) h];
keys  = [for (k = feats("key")) k];           // sorted by ref = left to right
key_kinds = ["up", "ok", "dn"];               // firmware decides, caps only say it

W = board_w; H = board_h;
// a hole is a "corner" hole if it is within 10 mm of two board edges
function is_corner(h) = (fxy(h).x < 10 || fxy(h).x > W - 10) && (fxy(h).y < 10 || fxy(h).y > H - 10);

// ---------------------------------------------------------------- levels (z)
lcd = has("lcd") ? feat("lcd") : undef;
lcd_top   = lcd_back_z + lcd_module.z;
z_face_in = lcd_top + lcd_gasket;            // underside of the face
z_face    = z_face_in + face_t;               // the front surface
z_split   = -board_t;                         // front shell meets tray at the board's back
back_clear = max(board_max_h_back + 0.8, 2.4);
cell_on   = cell[0] > 0;
cell_bb   = [cell_at.x - cell[2] / 2 - 0.5, cell_at.y - cell[1] / 2 - 0.5, cell_at.x + cell[2] / 2 + 0.5, cell_at.y + cell[1] / 2 + 0.5];
// back-side parts over the cell? then it has to clear them, otherwise it sits just under the board
cell_under_parts = len([for (q = board_parts) if (q[1] == "B" && q[2][2] > cell_bb[0] && q[2][0] < cell_bb[2] && q[2][3] > cell_bb[1] && q[2][1] < cell_bb[3]) 1]) > 0;
z_cell_top = z_split - (cell_under_parts ? back_clear : cell_gap);
z_floor_in = cell_on ? z_cell_top - cell[0] - cell_foam - 0.3 : z_split - back_clear;
rail_zone = rail_h + 1.2;                     // floor is this thick where the dovetails are
z_bot     = z_floor_in - floor_t;

cap_top_rest = choc_cap_z + cap_t;
z_fence   = cap_top_rest - fence_drop;

// ---------------------------------------------------------------- plan outlines
in0 = [-board_gap, -board_gap];
in1 = [W + board_gap, H + board_gap];
r_in = max(0.5, corner_r - wall);

module rrect(p0, p1, r) {
    translate([p0.x + r, p0.y + r]) offset(r = r) square([p1.x - p0.x - 2 * r, p1.y - p0.y - 2 * r]);
}
module plan_inner() rrect(in0, in1, r_in);
module plan_outer() offset(r = wall) plan_inner();
module tongue() difference() { offset(delta = -wall * 0.3) plan_outer(); offset(delta = wall * 0.3) plan_inner(); }
module bb2d(bb, grow = 0) translate([bb[0] - grow, bb[1] - grow]) square([bb[2] - bb[0] + 2 * grow, bb[3] - bb[1] + 2 * grow]);

// ---------------------------------------------------------------- key geometry
// Plan shapes say what a key does without looking: UP points up, DOWN points down, OK is round.
module cap_shape(kind, s = cap_size) {
    w = s.x; h = s.y;
    if (kind == "ok") scale([w / h, 1]) circle(d = h, $fn = 96);
    else {
        flip = kind == "dn" ? -1 : 1;
        scale([1, flip]) offset(r = 2.2) offset(delta = -2.2)
            polygon([[-w/2, -h/2], [w/2, -h/2], [w/2, h/2 - 4.2], [0, h/2 + 0.2], [-w/2, h/2 - 4.2]]);
    }
}
module key_at(i) translate([fxy(keys[i]).x, fxy(keys[i]).y]) children();
function key_kind(i) = key_kinds[min(i, len(key_kinds) - 1)];

// key bridge footprint: around the wells with room for the fences and a flange under the face
kb_margin = 3.2;
kb_lo = min([for (k = keys) fxy(k).y]) - cap_size.y/2 - cap_clear - 1.6;
// keys close to the bottom edge: the bridge runs out through the wall, so the wells open to the edge
kb_edge = kb_lo < 4;
kb0 = [min([for (k = keys) fxy(k).x]) - cap_size.x/2 - cap_clear - kb_margin, kb_edge ? -board_gap - wall - 2 : kb_lo];
kb_hi = max([for (k = keys) fxy(k).y]) + cap_size.y/2 + cap_clear + 1.6;
// the display sits right above the keys: the bridge stops short of the panel and has no flange there
kb_lcd = has("lcd") && kb_hi > fbb(feat("lcd"))[1] - 0.3;
kb1 = [max([for (k = keys) fxy(k).x]) + cap_size.x/2 + cap_clear + kb_margin, kb_lcd ? fbb(feat("lcd"))[1] - 0.3 : kb_hi];
kb_flange = 2.4;
module kb_open() rrect(kb0, kb1, 2.5);                      // hole in the face (and wall, at the edge)
module kb_body() intersection() { offset(delta = -fit/2) kb_open(); plan_outer(); }
module kb_flange_plan() difference() {
    offset(r = kb_flange) kb_open();
    if (kb_edge) translate([-500, -500]) square([1000, 500 - board_gap + 0.01]);  // no flange in the wall
    if (kb_lcd) translate([-500, kb1.y - 0.01]) square([1000, 500]);                // nor under the display
}
// at the edge, the tray carries a strip of wall up to the plate, the bridge sits on it
module kb_wall_strip() if (kb_edge) intersection() {
    translate([kb0.x + fit / 2, -50]) square([kb1.x - kb0.x - fit, 50 - board_gap]);
    plan_outer();
}

// ---------------------------------------------------------------- text and art
include <art/logo.scad>
module logo(h) scale(h / logo_size.y) logo_art();   // traced for print, see tools/mklogo_scad.py
module label(t, size, font = font_bold, halign = "center", valign = "center", spacing = 1)
    text(t, size = size, font = font, halign = halign, valign = valign, spacing = spacing);

module horn(h = 7) polygon([[-1.1, 0], [1.1, 0], [0.15, h], [-0.15, h]]);       // the charge LED: the horn glows
module star(r = 1.6) polygon([for (i = [0:9]) let(a = 90 + i * 36, rr = i % 2 ? r * 0.45 : r) [rr * cos(a), rr * sin(a)]]);

// ---------------------------------------------------------------- front shell
// the vent sits over the barometer unless the key bridge or the window is there; then it moves left
function vent_xy() = let(b = fxy(feat("baro"))) [min(b.x, kb0.x - 5.5), b.y + (b.x > kb0.x - 5.5 ? 0 : 0)];
lcd_bb = lcd ? fbb(lcd) : [30.6, 16.68, 93.4, 59.5];
lcd_c  = [(lcd_bb[0] + lcd_bb[2]) / 2, (lcd_bb[1] + lcd_bb[3]) / 2];
win    = [lcd_active.x + 2 * window_margin, lcd_active.y + 2 * window_margin];
win_c  = has("lcd_active") ? [(fbb(feat("lcd_active"))[0] + fbb(feat("lcd_active"))[2]) / 2, (fbb(feat("lcd_active"))[1] + fbb(feat("lcd_active"))[3]) / 2] : lcd_c + lcd_active_off;
cover  = [win.x + 2 * cover_border, win.y + 2 * cover_border];

// clear cover: overlaps the window by cover_border, less on the key side if the bridge is close
cover_lo = kb_lcd ? min(cover_border, win_c.y - win.y / 2 - kb1.y - 0.6) : cover_border;
module cover_plan(shrink = 0) translate([win_c.x - win.x / 2 - cover_border + shrink, win_c.y - win.y / 2 - cover_lo + shrink])
    offset(r = 1) offset(delta = -1) square([win.x + 2 * cover_border - 2 * shrink, win.y + cover_border + cover_lo - 2 * shrink]);

module front() {
    difference() {
        union() {
            // face + walls
            translate([0, 0, z_split]) linear_extrude(z_face - z_split) plan_outer();
        }
        // cavity
        translate([0, 0, z_split - 1]) linear_extrude(z_face_in - z_split + 1) plan_inner();
        // display window: chamfered so the reflective panel is not shaded, pocket for the clear cover
        // (no chamfer on the side that meets the key bridge)
        hull() {
            translate([win_c.x, win_c.y, z_face_in - 0.01]) linear_extrude(0.01) square(win, center = true);
            translate([win_c.x, win_c.y + (kb_lcd ? face_t / 2 : 0), z_face]) linear_extrude(0.02) square(win + [2 * face_t, kb_lcd ? face_t : 2 * face_t], center = true);
        }
        translate([0, 0, z_face - cover_t]) linear_extrude(cover_t + 1) cover_plan();
        // key bridge opening (through the wall too, when the keys sit at the edge)
        translate([0, 0, z_face_in - 1]) linear_extrude(face_t + 2) kb_open();
        if (kb_edge) translate([0, 0, z_split - 1]) linear_extrude(z_face - z_split + 2) intersection() { kb_open(); translate([-500, -500]) square([1000, 500 - board_gap + 0.01]); }
        // corner screws: countersunk from the front (honest fasteners, the face is the datum)
        for (h = holes) if (is_corner(h)) translate([fxy(h).x, fxy(h).y, 0]) {
            translate([0, 0, -5]) cylinder(d = screw_d, h = 20);
            translate([0, 0, z_face - (screw_head_d + 0.2 - screw_d) / 2]) cylinder(d1 = screw_d, d2 = screw_head_d + 0.2, h = (screw_head_d + 0.2 - screw_d) / 2 + 0.01);
            translate([0, 0, z_face - 0.4]) cylinder(d = screw_head_d + 0.2, h = 1);
        }
        // tall parts outside the panel: pockets in the underside of the face
        for (p = board_parts) if (p[1] == "F" && p[3] > z_face_in - 0.3 && !in_list(p[0], [for (k = keys) k[0]]))
            translate([0, 0, z_face_in - 1]) linear_extrude(p[3] + 0.4 - z_face_in + 1) bb2d(p[2], 0.5);
        // groove for the tray's tongue
        translate([0, 0, z_split - 0.01]) linear_extrude(1.2 + 0.3) offset(delta = fit / 2) tongue();
        // side openings
        usb_cut(); sd_cut(); flex_relief(); battery_lead_gully(); battery_plug_pocket(); knockouts();
        rh_vent(); baro_cut(); sma_cut();
        // LEDs: thin first-colour skin glows; the charge LED is a horn
        for (i = [0:len(feats("led")) - 1]) let(l = feats("led")[i], charge = fxy(l).x > W * 0.6)
            translate([fxy(l).x, fxy(l).y, z_face_in - 1]) {
                linear_extrude(1 + face_t - 0.45) if (charge) translate([0, -3.5]) offset(r = 0.6) horn(); else offset(r = 0.6) star(2);
            }
        // inlays on the face (debossed through the first colour)
        face_inlays();
        // hidden on the inside of the face, readable when opened
        translate([lcd_c.x, lcd_bb[1] - 0.2, z_face_in - 0.4]) mirror([1, 0, 0]) linear_extrude(1)
            label("PER PERFECTIONEM AD FELICITATEM", 2.2, font_reg, valign = "top");
    }
    // bosses: the board is clamped between these and the tray columns
    for (h = holes) if (is_corner(h)) translate([fxy(h).x, fxy(h).y, 0]) difference() {
        cylinder(d = boss_d, h = z_face_in + 0.01);
        translate([0, 0, -1]) cylinder(d = screw_d, h = 20);
    }
    if (lcd) carrier_lugs();
    difference() { union() { rh_baffles(rh_gap, z_face_in + 0.01); baro_solid(); } baro_cut(); }
    difference() { sma_boss(z_split, z_face); sma_cut(); }
    // tongue-and-groove: the front shell's groove is cut below; tray carries the tongue
}

module face_inlays() {
    zt = z_face - first_colour_t;
    // brand: logo in the free field right of the display, name level with the keys
    translate([(lcd_bb[2] + W + board_gap) / 2, (lcd_bb[1] + lcd_bb[3]) / 2 - 2, zt]) linear_extrude(1) logo(18);
    translate([(lcd_bb[2] + W + board_gap) / 2, (lcd_bb[1] + lcd_bb[3]) / 2 - 2 - 9 - 2.5, zt]) linear_extrude(1) label("UNICORNLINES®", 2.0);
    // left of the keys: the tagline
    // the tagline runs up the free strip left of the display, clear of the vent and the radio corner
    translate([has("patch") ? patch_bb[0] / 2 : (lcd_bb[0] - board_gap) / 2 + 4, (kb1.y + (has("radio") ? fbb(feat("radio"))[1] : H)) / 2 + 2, zt]) linear_extrude(1)
        rotate(90) label("NEVER STOP DREAMING", 2.2, font_reg);
    // over the GNSS patch: plastic only, and a constellation
    if (has("patch")) translate([(patch_bb[0] + patch_bb[2]) / 2, (patch_bb[1] + patch_bb[3]) / 2, zt]) linear_extrude(1) cassiopeia();
    // IMU origin and axes, exactly over the sensor, when the window does not cover it
    if (has("imu")) let(p = fxy(feat("imu"))) if (!(p.x > win_c.x - cover.x/2 - 6 && p.x < win_c.x + cover.x/2 + 6
              && p.y > win_c.y - cover.y/2 - 6 && p.y < win_c.y + cover.y/2 + 6))
        translate([p.x, p.y, zt]) linear_extrude(1) axes_mark();
}
module axes_mark() {
    difference() { circle(d = 3); circle(d = 1.8); } circle(d = 0.6);
    for (a = [[0, "X"], [90, "Y"]]) rotate(a[0]) { translate([2, -0.3]) square([6, 0.6]); translate([8, 0]) polygon([[0, -1], [2, 0], [0, 1]]);
        translate([11.2, 0]) rotate(-a[0]) label(a[1], 1.8); }
}

// USB-C: receptacle opening, with the wall thinned outside so slim overmoulds reach full depth
usb_z = 1.63;   // receptacle centre above F.Cu (GCT USB4105)
module usb_cut() if (has("usb_c")) let(f = feat("usb_c"), y = fxy(f).y) {
    translate([W + board_gap - 0.5, y, usb_z]) rotate([0, 90, 0]) linear_extrude(wall + 2)
        offset(r = 1.6) square([3.6 - 3.2, 9.4 - 3.2], center = true);
    translate([W + board_gap + 0.8, y, usb_z]) rotate([0, 90, 0]) linear_extrude(wall + 2)
        offset(r = 2.6) square([6.4 - 5.2, 12.4 - 5.2], center = true);
}
// microSD: a slot at card height and a thumb scoop; an inserted card stands ~1 mm proud of the wall
sd_z = 0.95;
module sd_cut() if (has("microsd")) let(f = feat("microsd"), y = fxy(f).y) {
    translate([W, y, sd_z]) cube([10, 12.2, 1.5], center = true);
    translate([W + board_gap + wall + 3.2, y, sd_z]) scale([1, 1, 0.55]) rotate([90, 0, 0]) cylinder(r = 4.6, h = 15, center = true, $fn = 64);
}
// Qwiic and camera sockets are for leads inside the case; a lead to the outside breaks out a
// 0.6 mm skin in the wall next to the socket (cut it with a knife, no drilling near the board)
module knockouts() for (r = ["qwiic", "camera"]) if (has(r)) let(f = feat(r), bb = fbb(f), top = fxy(f).y > H / 2)
    translate([fxy(f).x, top ? H + board_gap - 0.01 : -board_gap - wall + 0.6, 0.4])
        rotate([-90, 0, 0]) linear_extrude(wall - 0.6 + 0.01) translate([0, -1.6]) offset(r = 1.4) square([4, 0.4], center = true);
module flex_relief() if (has("lcd_flex")) let(bb = fbb(feat("lcd_flex")))
    translate([bb[0] - 0.5, H + board_gap - 0.01, 0]) cube([bb[2] - bb[0] + 1, 1.2, z_face_in - 0.01]);   // the fold may stand 1 mm past the edge
// Battery: the JST PH plug enters J2 from the right; its lead turns down past the board edge in a gully in the
// right (or left) wall of both shells and runs under the board to the cell. A bridge clip in the tray holds it.
bat_gully = [1.2, 6.0];                       // depth into the wall, width
function bat_side() = fxy(feat("battery")).x > W / 2;
module battery_lead_gully(z0 = z_split - 1, z1 = z_face_in) if (cell_on && has("battery")) let(f = feat("battery"), r = bat_side())
    translate([r ? W + board_gap - 0.01 : -board_gap - bat_gully.x, fxy(f).y - bat_gully.y / 2, z0]) cube([bat_gully.x + 0.01, bat_gully.y, z1 - z0]);
// the plug past the socket opening: 4.85 mm tall leaves 0.25 mm under the face, so pocket it
module battery_plug_pocket() if (has("battery")) let(b = fbb(feat("battery")), r = bat_side())
    translate([r ? b[2] - 0.5 : -board_gap, fxy(feat("battery")).y - 3.4, z_face_in - 1]) cube([r ? W + board_gap - b[2] + 0.5 : b[0] + board_gap + 0.5, 6.8, 1 + 0.6]);
module battery_clip() if (cell_on && has("battery")) let(f = feat("battery"), r = bat_side(), x = r ? W - 9 : 9, y = fxy(f).y)
    translate([x, y, z_floor_in - 0.01]) {
        for (sy = [-1, 1]) translate([-1, sy * 2.6 - 0.8, 0]) cube([2, 1.6, 3.2]);
        translate([-1, -3.4, 2.2]) cube([2, 6.8, 1.0]);
    }


// ---------------------------------------------------------------- display spacer frame
// Free spots on the board: where a post or a foot of radius r touches no front-side part.
function hits(p, r) = [for (q = board_parts) if (q[1] == "F" && q[3] > 0.05 && p.x + r > q[2][0] - 0.3 && p.x - r < q[2][2] + 0.3
                                                 && p.y + r > q[2][1] - 0.3 && p.y - r < q[2][3] + 0.3) q[0]];
function nearest_free(t, r, cands) = let(f = [for (c = cands) if (len(hits(c, r)) == 0) c], d = [for (c = f) norm(c - t)])
    len(f) == 0 ? undef : f[search(min(d), d)[0]];

// The display rests on a thin ring just above the parts under it (they are 2.9 mm at most),
// carried by posts that stand on the board wherever it is free. Printed ring-side down.
lcd_back = lcd_back_z;
ring_t = 0.4;
lcd_post_r = 1.2;
function lcd_post_targets() = let(o = lcd_bb, m = 2.5)
    [[o[0] + m, o[1] + m], [o[2] - m, o[1] + m], [o[0] + m, o[3] - m], [o[2] - m, o[3] - m],
     [(o[0] + o[2]) / 2 - 14, o[1] + m], [(o[0] + o[2]) / 2 + 14, o[1] + m], [o[0] + m, (o[1] + o[3]) / 2], [o[2] - m, (o[1] + o[3]) / 2]];
function lcd_post_cands() = let(o = lcd_bb) [for (x = [o[0] + 1.5 : 0.5 : o[2] - 1.5], y = [o[1] + 1.5 : 0.5 : o[3] - 1.5])
    if (x < o[0] + 9 || x > o[2] - 9 || y < o[1] + 9 || y > o[3] - 9) [x, y]];
lcd_posts = lcd ? [for (t = lcd_post_targets()) let(p = nearest_free(t, lcd_post_r, lcd_post_cands())) if (p != undef) p] : [];

// Display carrier: boxes the panel on the left, right and top (the key bridge is the fourth side),
// carries it on a lip under the glass border, stands on posts on the board, and is clamped by the face.
carrier_wall = 1.0;
carrier_fit  = 0.15;
module lcd_frame() {
    o = lcd_bb; c = carrier_fit; w = carrier_wall;
    // walls, from the lip up to just under the face
    translate([0, 0, lcd_back - ring_t]) linear_extrude(z_face_in - 0.1 - (lcd_back - ring_t)) difference() {
        translate([o[0] - c - w, kb_lcd ? o[1] - c : o[1] - c - w]) offset(r = 0.6) offset(delta = -0.6)
            square([o[2] - o[0] + 2 * (c + w), o[3] - o[1] + c + w + (kb_lcd ? 0 : c + w)]);
        translate([o[0] - c, o[1] - c - 2]) square([o[2] - o[0] + 2 * c, o[3] - o[1] + 2 * c + 2]);
        // the flex leaves the top edge: an opening for its fold
        if (has("lcd_flex")) let(fb = fbb(feat("lcd_flex"))) translate([fb[0] - 1, o[3] - 1]) square([fb[2] - fb[0] + 2, 4]);
    }
    // lip under the glass border (the flex side stays open for the fold)
    translate([0, 0, lcd_back - ring_t]) linear_extrude(ring_t) difference() {
        bb2d(lcd_bb, carrier_fit + carrier_wall - 0.01);
        bb2d(lcd_bb, -2.0);
        if (kb_lcd) translate([0, lcd_bb[1] - carrier_fit - 10]) square([500, 10]);   // the bridge side
        if (has("lcd_flex")) let(fb = fbb(feat("lcd_flex"))) translate([fb[0] - 1, lcd_bb[3] - 4]) square([fb[2] - fb[0] + 2, 6]);
    }
    // posts from the board to the ring, with a web to the ring where they stand inside it
    for (p = lcd_posts) {
        translate([p.x, p.y, 0]) cylinder(r = lcd_post_r, h = lcd_back, $fn = 24);
        translate([0, 0, lcd_back - ring_t]) linear_extrude(ring_t) hull() {
            translate(p) circle(r = lcd_post_r, $fn = 24);
            translate(ring_pt(p)) circle(r = 0.8, $fn = 12);
        }
    }
}
// Locating lugs: hang from the face just outside the carrier walls, so the carrier (and the panel in it)
// is held in the plane by the case itself, not by friction on the board. The key bridge locates the fourth side.
carrier_lug = [6, 1.2];                      // length along the wall, thickness
carrier_lug_z = lcd_back + 0.3;              // lug tips, well clear of the parts under the panel border (2.9 mm)
function carrier_lug_rects() = let(o = lcd_bb, g = carrier_fit + carrier_wall + fit / 2, l = carrier_lug.x, t = carrier_lug.y, h = o[3] - o[1])
    concat([for (y = [o[1] + h * 0.25, o[1] + h * 0.75]) each [[o[0] - g - t, y - l / 2, o[0] - g, y + l / 2], [o[2] + g, y - l / 2, o[2] + g + t, y + l / 2]]],
           [for (x = [lcd_c.x - 20, lcd_c.x + 20]) [x - l / 2, o[3] + g, x + l / 2, o[3] + g + t]]);
module carrier_lugs() translate([0, 0, carrier_lug_z]) linear_extrude(z_face_in - carrier_lug_z + 0.01)
    for (r = carrier_lug_rects()) translate([r[0], r[1]]) square([r[2] - r[0], r[3] - r[1]]);
// nearest point on the ring's centre line
function ring_pt(p) = let(o = lcd_bb, c = 1.2, d = [p.x - o[0], o[2] - p.x, p.y - o[1], o[3] - p.y], m = min(d))
    m == d[0] ? [o[0] + c, p.y] : m == d[1] ? [o[2] - c, p.y] : m == d[2] ? [p.x, o[1] + c] : [p.x, o[3] - c];

// ---------------------------------------------------------------- humidity sensor and microphone
// SHT40 on a tongue cut free by an L-shaped notch: a vent in the left wall right in front of it, and a small
// chamber (baffles on both sides of the board, stopping short of it) so it reads cockpit air, not the warm case.
// Nothing touches the tongue: no rib, foam or clamp.
rh_gap = 0.4;                                 // baffles stop this far from the board
rh_baffle = 1.2;
function env_bb() = let(bs = [for (r = ["rh", "mic"]) if (has(r)) fbb(feat(r))])
    [min([for (b = bs) b[0]]), min([for (b = bs) b[1]]), max([for (b = bs) b[2]]), max([for (b = bs) b[3]])];
// [x0, y0, x1, y1] inside the baffles: the board keeps a 1.2 mm part-free strip round this box
function rh_box() = let(b = env_bb()) [-board_gap, b[1] - 0.9, b[2] + 1.9, b[3] + 1.45];
module rh_baffles(z0, z1) if (has("rh")) let(r = rh_box(), t = rh_baffle)
    translate([0, 0, z0]) linear_extrude(z1 - z0) difference() {
        translate([-board_gap - 0.5, r[1] - t]) square([r[2] + t + board_gap + 0.5, r[3] - r[1] + 2 * t]);
        translate([-board_gap - 1, r[1]]) square([r[2] + board_gap + 1, r[3] - r[1]]);
    }
module rh_vent() if (has("rh")) let(r = rh_box(), yc = (r[1] + r[3]) / 2, l = r[3] - r[1] - 3.5)
    for (z = [1.1, 3.1]) translate([-board_gap - wall - 1, yc, z]) rotate([0, 90, 0]) linear_extrude(wall + 1.5)
        hull() for (dy = [-l / 2, l / 2]) translate([0, dy]) circle(d = 1.1, $fn = 16);

// Microphone: a top-port part inside the humidity chamber, so it hears the cockpit through the same left-wall vent.
mic_duct_z = 2.7;                             // barometer duct underside: clears the parts it crosses (2.4 mm at most)
mic_duct_d = 2.6;
function mic_bore_z() = (mic_duct_z + z_face_in) / 2;

// Barometer: one sealed hood for both modes. A foam ring seals it onto the free ring the board keeps round the
// sensor; a duct runs out through the bottom wall. Left open (ePTFE sticker) it breathes cockpit air; with a
// push-in 4 mm hose barb in the outlet it reads the aircraft's static port (that mode needs approval).
baro_ring = 1.6;                              // seal land width round the cavity
baro_seal = [1.0, 0.7];                       // foam ring: free and squeezed thickness
baro_barb = [4.2, 3.4];                       // outlet counterbore for the barb: diameter, depth
function baro_cav() = let(b = fbb(feat("baro"))) [b[0] - 0.2, b[1] - 0.2, b[2] + 0.2, b[3] + 0.2];
function baro_out() = let(c = baro_cav()) [c[0] - baro_ring, c[1] - baro_ring, c[2] + baro_ring, c[3] + baro_ring];
module baro_solid() if (has("baro")) let(o = baro_out(), c = fxy(feat("baro")), zr = baro_seal[1] - 0.3) {
    translate([o[0], o[1], zr]) cube([o[2] - o[0], o[3] - o[1], z_face_in - zr + 0.01]);
    hull() for (y = [o[1], -board_gap - 0.5]) translate([c.x, y, mic_duct_z]) cylinder(d = mic_duct_d, h = z_face_in - mic_duct_z + 0.01, $fn = 20);
    translate([c.x - 3.5, -board_gap - 0.5, 1.4]) cube([7, 2.4, z_face_in - 1.4 + 0.01]);      // boss behind the barb
}
module baro_cut() if (has("baro")) let(v = baro_cav(), o = baro_out(), c = fxy(feat("baro")), zr = baro_seal[1] - 0.3) {
    translate([v[0], v[1], -1]) cube([v[2] - v[0], v[3] - v[1], 1 + z_face_in - 0.8]);
    translate([o[0] + 0.2, o[1] + 0.2, zr - 0.01]) difference() { cube([o[2] - o[0] - 0.4, o[3] - o[1] - 0.4, 0.3]); }   // recess locating the foam ring
    hull() for (y = [v[1] + 1, -board_gap - wall - 1]) translate([c.x, y, mic_bore_z()]) rotate([90, 0, 0]) cylinder(d = 1.4, h = 0.01, $fn = 16);
    translate([c.x, -board_gap - wall - 0.01, mic_bore_z()]) rotate([-90, 0, 0]) cylinder(d = baro_barb[0], h = baro_barb[1], $fn = 32);
}

// ---------------------------------------------------------------- key bridge (also the switch plate)
plate_bot = choc_plate_top - choc_plate_t;
module keybridge() {
    difference() {
        union() {
            // switch plate + flange, sits under the face
            translate([0, 0, plate_bot]) linear_extrude(z_face_in - plate_bot - fit) kb_flange_plan();
            // body up to the face
            translate([0, 0, plate_bot]) linear_extrude(z_face - plate_bot) kb_body();
            // fences between and beside the keys: a gloved finger falls into the right well
            for (i = [0:len(keys)]) let(x = i == 0 ? kb0.x + fence_w/2 + 0.6
                                       : i == len(keys) ? kb1.x - fence_w/2 - 0.6
                                       : (fxy(keys[i-1]).x + fxy(keys[i]).x) / 2)
                translate([x, (kb0.y + kb1.y) / 2, z_face - 0.01]) fence(kb1.y - kb0.y - 1.2, z_fence - z_face);
        }
        for (i = [0:len(keys) - 1]) key_at(i) {
            translate([0, 0, plate_bot - 1]) linear_extrude(10) square(choc_cut, center = true);          // switch clips
            translate([0, 0, choc_plate_top]) linear_extrude(20) offset(r = cap_clear) cap_shape(key_kind(i));
            translate([0, 0, choc_plate_top]) linear_extrude(20) square(choc_cut + 1.2, center = true);  // housing top flange
        }
        // an LED under the bridge glows through a thin skin
        for (l = feats("led")) if (fxy(l).x > kb0.x && fxy(l).x < kb1.x && fxy(l).y > kb0.y && fxy(l).y < kb1.y)
            translate([fxy(l).x, fxy(l).y, plate_bot - 1]) linear_extrude(1 + z_face - plate_bot - 0.6) offset(r = 0.6) star(2);
        // relief under the flange so the clips can open
        for (i = [0:len(keys) - 1]) key_at(i) translate([0, 0, plate_bot - 1]) linear_extrude(1 + 0.01) square([choc_cut + 1.2, 6], center = true);
    }
    // feet onto the board at the four corners of the bridge (keep these spots free of parts)
    for (p = kb_feet()) translate([p.x, p.y, 0]) cylinder(d = 2.2, h = plate_bot + 0.01, $fn = 24);
}
// feet at free spots near the bridge corners, outside the switch cut-outs and on the board
function kb_feet_cands() = [for (x = [max(kb0.x, 0) + 1.5 : 0.5 : kb1.x - 1.5], y = [max(kb0.y, 0) + 1.5 : 0.5 : kb1.y - 1.5])
    if (len([for (k = keys) if (abs(x - fxy(k).x) < choc_cut / 2 + 2.6 && abs(y - fxy(k).y) < choc_cut / 2 + 2.6) 1]) == 0) [x, y]];
kb_feet_list = [for (t = [[kb0.x, kb0.y], [kb1.x, kb0.y], [kb0.x, kb1.y], [kb1.x, kb1.y]]) let(p = nearest_free(t, 1.1, kb_feet_cands())) if (p != undef) p];
function kb_feet() = kb_feet_list;
module fence(len, h) {
    // a rounded rail, highest in the middle, so it guides rather than snags
    rotate([90, 0, 0]) linear_extrude(len, center = true) hull() {
        translate([-fence_w/2, 0]) square([fence_w, 0.01]);
        translate([0, h - fence_w/2]) circle(d = fence_w, $fn = 24);
    }
}

// ---------------------------------------------------------------- keycaps
// Printed face-down. First 0.6 mm in colour 1, the rest in colour 2: the debossed mark shows colour 2.
module keycap(kind) {
    difference() {
        union() {
            // body, rounded top edge
            hull() {
                linear_extrude(cap_t - 0.8) cap_shape(kind);
                translate([0, 0, cap_t - 0.8]) linear_extrude(0.8) offset(r = -0.8) cap_shape(kind);
            }
        }
        // the mark
        translate([0, 0, cap_t - first_colour_t]) linear_extrude(1) {
            if (kind == "ok") star(3.2);
            else scale([1, kind == "dn" ? -1 : 1]) translate([0, -1.5]) for (dy = [0, 3]) translate([0, dy])
                polygon([[-3.6, -1.1], [0, 1.9], [3.6, -1.1], [3.6, -2.5], [0, 0.5], [-3.6, -2.5]]);
        }
        // underside relief over the switch housing top
        translate([0, 0, -0.01]) linear_extrude(0.4) square([12.8, 13], center = true);
    }
    // stem pegs (Choc: two 1.2 x 3.0 legs, 5.7 apart), slightly crushed ribs for a press fit
    for (sx = [-1, 1]) translate([sx * choc_stem_pitch / 2, 0, -choc_peg.z + 0.01]) {
        translate([-choc_peg.x/2 + 0.05, -choc_peg.y/2, 0]) cube([choc_peg.x - 0.1, choc_peg.y, choc_peg.z + 0.5]);  // roots into the cap above the relief
        for (sy = [-1, 1]) translate([0, sy * 0.6, choc_peg.z / 2 + 0.3]) cube([choc_peg.x + 0.08, 0.4, choc_peg.z - 0.6], center = true);
    }
}

// ---------------------------------------------------------------- tray
// The dovetail channels are cut from everything the tray carries: columns, ribs and clips must not reach into them.
module tray() difference() {
    tray_body();
    for (y = rail_ys()) translate([0, y, z_bot]) dovetail(len = 400, grow = fit);
}
module tray_body() {
    difference() {
        union() {
            translate([0, 0, z_bot]) linear_extrude(z_split - z_bot) plan_outer();
            // tongue into the front shell's groove
            translate([0, 0, z_split - 0.01]) linear_extrude(1.2) tongue();
        }
        // the cavity, minus the thicker floor over the dovetail channels
        difference() {
            translate([0, 0, z_floor_in]) linear_extrude(50) plan_inner();
            translate([0, 0, z_bot]) linear_extrude(rail_h + 1.4) rail_strips();
        }
        // dovetail channels, open at the right end so the unit slides onto the plate from there
        for (y = rail_ys()) translate([0, y, z_bot]) dovetail(len = 400, grow = fit);
        // side openings continue below the split
        tray_openings();
        // no tongue under the antenna ferrule
        sma_cut();
        // the notch the plate's snap hook falls into
        translate([latch_x - 2, H / 2 - latch_arm.y / 2 - 0.4, z_bot - 0.01]) cube([4, latch_arm.y + 0.8, latch_hook + 0.3]);
        // under the board: nothing of the tongue where the openings are
        if (has("usb_c")) translate([W, fxy(feat("usb_c")).y - 7, z_split - 0.5]) cube([10, 14, 3]);
        if (has("microsd")) translate([W, fxy(feat("microsd")).y - 7, z_split - 0.5]) cube([10, 14, 3]);
        if (has("lcd_flex")) translate([0, 0, z_split - 0.5]) linear_extrude(3) bb2d(fbb(feat("lcd_flex")), 0.6);
        for (h = used_holes) if (!is_corner(h)) translate([fxy(h).x, fxy(h).y, z_bot]) {
            translate([0, 0, -1]) cylinder(d = screw_d, h = 30);
            translate([0, 0, -0.01]) cylinder(d1 = screw_head_d + 0.2, d2 = screw_d, h = (screw_head_d + 0.2 - screw_d) / 2);
        }
        // inside the floor, readable when the board is out
        translate([W / 2, 6, z_floor_in - 0.4]) linear_extrude(1) label("PER PERFECTIONEM AD FELICITATEM", 2.6, font_reg);
    }
    // columns: floor to the board's back, brass inserts for the front screws
    for (h = used_holes) translate([fxy(h).x, fxy(h).y, z_floor_in - 0.01]) difference() {
        cylinder(d = boss_d, h = z_split - z_floor_in + 0.01);
        nyl = in_list(h[0], nylon_holes);
        if (is_corner(h)) translate([0, 0, z_split - z_floor_in - (nyl ? 4.6 : insert_l + 0.3)]) cylinder(d = nyl ? 2.7 : insert_d, h = 20);
        else translate([0, 0, -10]) cylinder(d = screw_d, h = 40);  // inner hole: screw from the back, thin nut on the front
    }
    // (inner holes are countersunk into the bottom, see below)
    // wall strip under the key bridge
    translate([0, 0, z_split - 0.01]) linear_extrude(plate_bot - z_split + 0.01 - fit) kb_wall_strip();
    // the cell: a rib frame and four snap fingers over its long edges
    if (cell_on) cell_bay();
    rh_baffles(z_floor_in - 0.01, z_split - rh_gap);
    difference() { sma_boss(-50, z_split); sma_cut(); }
    battery_clip();   // the chamber's back half: still air under the tongue
    // the floor is thicker over the latch notch
    difference() {
        translate([latch_x - 5, H / 2 - latch_arm.y / 2 - 3, z_floor_in - 0.01]) cube([10, latch_arm.y + 6, latch_hook + 1.6 - floor_t]);
        translate([latch_x - 2, H / 2 - latch_arm.y / 2 - 0.4, z_bot - 0.01]) cube([4, latch_arm.y + 0.8, latch_hook + 0.3]);
    }
}
function rail_strip_w() = rail_w + 2 * rail_h * tan(rail_angle) + 2.4;
module rail_strips() for (y = rail_ys()) translate([-500, y - rail_strip_w() / 2]) square([1000, rail_strip_w()]);
// snap latch: a hook on a spring arm in the plate, a notch near the tray's right end
latch_x = W + board_gap + wall - 7;
function rail_ys() = [-board_gap - wall + rail_inset, H + board_gap + wall - rail_inset];

module dovetail(len, grow = 0) {
    // trapezoid: narrow at z = 0 (the tray bottom), wide at the top; flanks lean 30 deg
    w0 = rail_w + 2 * grow; w1 = w0 + 2 * rail_h * tan(rail_angle);
    translate([-len / 2, 0, -0.01]) rotate([90, 0, 90]) linear_extrude(len)
        polygon([[-w0/2, 0], [w0/2, 0], [w1/2, rail_h + grow], [-w1/2, rail_h + grow]]);
}

module cell_bay() {
    // The cell is taped down (VHB foam) and boxed in: end ribs in x, the rail strips (or side ribs) in y,
    // and the board 0.5 mm above it. Nothing presses on the pouch.
    c = cell_at; l = cell[2] + 1.0; w = cell[1] + 1.0; t = cell[0] + cell_foam;
    rib = 1.2;
    lo = rail_ys()[0] + rail_strip_w() / 2; hi = rail_ys()[1] - rail_strip_w() / 2;
    translate([c.x, c.y, z_floor_in - 0.01]) {
        for (sx = [-1, 1]) translate([sx * (l / 2 + rib / 2), 0, 0]) difference() {
            translate([-rib / 2, -w / 2, 0]) cube([rib, w, t * 0.6]);
            translate([-rib, -w * 0.2, t * 0.3]) cube([rib * 2, w * 0.4, t]);       // finger notch to lift it out
        }
        // side ribs only where a rail strip does not already hold that side
        for (sy = [-1, 1]) if ((sy < 0 && c.y - w / 2 > lo + 1.5) || (sy > 0 && c.y + w / 2 < hi - 1.5))
            translate([-l / 2, sy * (w / 2 + rib / 2) - rib / 2, 0]) cube([l, rib, t * 0.6]);
        // the floor names the cell it was built for
        translate([0, 0, -0.4]) linear_extrude(0.41) { label("1S LiPo", 3.2); translate([0, -4.5]) label(str(cell[0], cell[1], cell[2]), 2.4, font_reg); }
    }
}
module tray_openings() {
    battery_lead_gully(z_floor_in, z_split + 1.3);
    battery_lead_gully();
}

// ---------------------------------------------------------------- GNSS: edge-mount SMA and the patch
// The jack's square flange sits in a square pocket split between the front shell and the tray, so cable torque
// and pull go into the case, not the solder joints. The thread passes a hole in a small boss on the left wall.
sma_on = has("sma");
sma_y  = sma_on ? let(b = fbb(feat("sma"))) (b[1] + b[3]) / 2 : 0;
sma_x_wall = -board_gap - wall;
function sma_boss_z() = [sma_z - 5.5, sma_z + 5.5];
module sma_cut() if (sma_on) {
    f = sma_flange.x + 2 * 0.15;
    translate([-sma_flange.y - 0.15, sma_y - f / 2, sma_z - f / 2]) cube([sma_flange.y + 0.15 + 0.5, f, f]);
    translate([-sma_reach - 2, sma_y, sma_z]) rotate([0, 90, 0]) cylinder(d = sma_thread_d + 0.2, h = sma_reach + 2);
}
module sma_boss(lo, hi) if (sma_on) intersection() {
    translate([sma_x_wall - sma_boss, sma_y, 0]) rotate([0, 90, 0]) linear_extrude(sma_boss + 0.5)
        offset(r = 1.5) offset(delta = -1.5) translate([-sma_boss_z()[1], -5.5]) square([sma_boss_z()[1] - sma_boss_z()[0], 11]);
    translate([-50, -50, lo]) cube([100, 200, hi - lo]);
}
patch_bb = has("patch") ? fbb(feat("patch")) : undef;
// Cassiopeia's W over the patch: the antenna looks at the sky, the face says so
module cassiopeia(s = 1) {
    st = [[-6, 2.2], [-3, -1.4], [0, 0.6], [3, -2.2], [6, 1.4]] * s;
    for (q = st) translate(q) star(1.3);
    for (i = [0:3]) hull() { translate(st[i]) circle(d = 0.35, $fn = 8); translate(st[i + 1]) circle(d = 0.35, $fn = 8); }
}
// Dust cap for the SMA when no external antenna is fitted: a PETG thimble with three crush ribs that grip the
// thread crests, and a lanyard eye so it can be tied to the mount.
module sma_cap() {
    id = sma_thread_d + 0.1; od = id + 2.4; h = 6.5;
    difference() {
        union() {
            cylinder(d = od, h = h, $fn = 48);
            translate([0, 0, 0]) hull() { cylinder(d = od, h = 1.6, $fn = 48); translate([od / 2 + 2.5, 0, 0]) cylinder(d = 5, h = 1.6, $fn = 32); }
        }
        translate([0, 0, 1.2]) cylinder(d = id, h = h, $fn = 48);
        translate([od / 2 + 2.5, 0, -1]) cylinder(d = 2.2, h = 5, $fn = 24);
    }
    for (a = [0, 120, 240]) rotate(a) translate([id / 2 - 0.25, -0.4, 1.2]) cube([0.5, 0.8, h - 1.2]);
}
if (sma_on) {
    if (sma_boss_z()[0] < z_bot + 5 + 0.3) echo("CHECK: SMA boss sits on the plate's stop block");
    if (sma_x_wall - sma_boss < -sma_reach + 4.5) echo("CHECK: less than 4.5 mm of SMA thread outside the case");
    echo(str("CASE: SMA at y ", sma_y, ", axis z ", sma_z, ", thread outside ", sma_reach + sma_x_wall - sma_boss, " mm"));
}
if (has("patch")) {
    if (z_face_in - feat("patch")[6] < patch_air) echo("CHECK: less than ", patch_air, " mm air over the patch");
    let(near = [for (h = holes) if (fxy(h).x > patch_bb[0] - patch_keepout && fxy(h).x < patch_bb[2] + patch_keepout
                                    && fxy(h).y > patch_bb[1] - patch_keepout && fxy(h).y < patch_bb[3] + patch_keepout) h[0]])
        if (len(near) > 0) echo("CHECK: screw or insert within the patch keep-out", near);
    echo(str("CASE: patch ", patch_bb, ", air over it ", z_face_in - feat("patch")[6]));
}

// ---------------------------------------------------------------- mount plate
plate_x0 = -board_gap - wall - stop_t - fit;
plate_x1 = W + board_gap + wall;
module plate() {
    L = plate_x1 - plate_x0 + wing + latch_wing;
    x0 = plate_x0 - wing; y0 = -board_gap - wall; y1 = H + board_gap + wall;
    ax0 = latch_x - latch_arm.x + 4;              // arm root (left), free end runs out past the unit as the tab
    ax1 = plate_x1 + 8;
    difference() {
        union() {
            translate([0, 0, -plate_t]) linear_extrude(plate_t) rrect([x0, y0], [x0 + L, y1], corner_r);
            // male rails
            for (y = rail_ys()) translate([(plate_x0 + stop_t + plate_x1) / 2, y, 0]) dovetail(len = plate_x1 - plate_x0 - stop_t - 0.01);
            // the stop at the left end
            translate([plate_x0, y0, -0.01]) cube([stop_t, y1 - y0, 5]);
        }
        // the spring arm: free on three sides, thinner from below
        translate([0, 0, -plate_t - 1]) linear_extrude(plate_t + 2) difference() {
            translate([ax0, H / 2 - latch_arm.y / 2 - 1.2]) square([ax1 - ax0 + 1.2, latch_arm.y + 2.4]);
            translate([ax0 - 1, H / 2 - latch_arm.y / 2]) square([ax1 - ax0 + 1, latch_arm.y]);
        }
        translate([ax0 + 2, H / 2 - latch_arm.y / 2 - 1, -plate_t - 0.01]) cube([ax1 - ax0, latch_arm.y + 2, plate_t - latch_arm.z]);
        // strap slots at both wings (the right one beyond the release tab)
        for (x = [x0 + wing / 2, x0 + L - wing / 2 + 1.5]) translate([x, (y0 + y1) / 2, -plate_t - 1]) linear_extrude(plate_t + 2)
            offset(r = strap_slot / 2) square([0.01, strap_w - strap_slot], center = true);
        // screw it down: four corner holes inside the wings, countersunk from the top
        for (x = [x0 + wing / 2, x0 + L - wing / 2 + 1.5], y = [y0 + 6, y1 - 6]) translate([x, y, 0]) csk(plate_screw);
        // AMPS pattern + 1/4"-20 nut, centred under the unit
        translate([W / 2, H / 2, 0]) {
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * amps.y / 2, sy * amps.x / 2, 0]) csk(plate_screw);
            translate([0, 0, -plate_t - 1]) cylinder(d = 6.6, h = plate_t + 2);
            translate([0, 0, -plate_t + 1.0]) cylinder(d = quarter_inch_nut, h = plate_t, $fn = 6);
        }
        // lighter: pockets from below between the rails, clear of the arm, the AMPS bosses and the nut
        translate([0, 0, -plate_t - 0.01]) linear_extrude(plate_t - 1.2) difference() {
            intersection() {
                translate([plate_x0 + stop_t + 3, rail_ys()[0] + rail_w]) square([ax0 - 3 - plate_x0 - stop_t - 3, rail_ys()[1] - rail_ys()[0] - 2 * rail_w]);
                union() for (i = [0:7], j = [0:2]) translate([plate_x0 + stop_t + 4 + i * 16.5, rail_ys()[0] + rail_w + 1 + j * 13.5]) offset(r = 1.5) square([12.5, 10]);
            }
            translate([W / 2, H / 2]) { circle(d = 18); for (sx = [-1, 1], sy = [-1, 1]) translate([sx * amps.y / 2, sy * amps.x / 2]) circle(d = 10); }
        }
        // easter egg: hidden where only the unit covers it
        translate([W / 2 - 4, H / 2 + 9, -0.4]) linear_extrude(1) label("YOU FOUND IT. NOW FLY IT.", 2.0, font_reg);
        translate([W / 2 - 38, H / 2, -0.4]) linear_extrude(1) logo(16);
    }
    // the hook: ramp on the right (the unit slides in from the right), square face on the left
    translate([latch_x - 2 + fit, H / 2, 0]) rotate([90, 0, 0]) linear_extrude(latch_arm.y - 1, center = true)
        polygon([[0, -0.01], [3.6 - fit, -0.01], [1.8, latch_hook], [0, latch_hook]]);
    // release tab: ribs to find it with a glove, push down and slide the unit off to the right
    for (dx = [0 : 1.6 : 4.8]) translate([plate_x1 + 2 + dx, H / 2 - latch_arm.y / 2 + 1, -0.01]) cube([0.8, latch_arm.y - 2, 1.0]);
}
module csk(d) {
    translate([0, 0, -plate_t - 1]) cylinder(d = d, h = plate_t + 2);
    translate([0, 0, -d / 2 - 0.2]) cylinder(d1 = d, d2 = 2 * d + 0.4, h = d / 2 + 0.2 + 0.01);
}


// ---------------------------------------------------------------- board stand-in (renders)
// sel picks one material group, so the renderer can colour it; "" = all, with OpenSCAD colours
module board_model(sel = "") {
    module g(n, c) if (sel == "" || sel == n) color(c) children();
    g("pcb", "#1d3d2a") translate([0, 0, -board_t]) linear_extrude(board_t) difference() {
        polygon(board_outline);
        for (h = holes) translate(fxy(h)) circle(d = 3.2);
    }
    g("parts", "#2a2a2a") for (p = board_parts) if (p[3] > 0 && !(has("sma") && p[0] == feat("sma")[0])) translate([0, 0, p[1] == "F" ? 0 : -board_t - p[3]]) linear_extrude(p[3]) bb2d(p[2], -0.2);
    for (f = board_features) {
        r = f[1];
        if (r == "usb_c") g("metal", "silver") translate([fxy(f).x - 3.7, fxy(f).y - 4.47, 0]) cube([7.35 + 0.2, 8.94, 3.26]);
        if (r == "microsd") g("metal", "silver") linear_extrude(1.7) bb2d(fbb(f), -1.2);
        if (r == "radio") g("metal", "#555") linear_extrude(fh(f)) bb2d(fbb(f), -0.3);
        if (r == "battery" || r == "qwiic" || r == "camera") g("white", "#eee") linear_extrude(fh(f)) bb2d(fbb(f), -0.4);
        if (r == "baro" || r == "imu" || r == "mag") g("metal", "#888") linear_extrude(0.9) bb2d(fbb(f));
        if (r == "sma") g("metal", "gold") translate([0, sma_y, sma_z]) {
            translate([-sma_flange.y, -sma_flange.x / 2, -sma_flange.x / 2]) cube([sma_flange.y + 2.0, sma_flange.x, sma_flange.x]);
            rotate([0, -90, 0]) cylinder(d = sma_thread_d - 0.3, h = sma_reach, $fn = 6 * 6);
            rotate([0, -90, 0]) translate([0, 0, sma_reach - 0.5]) difference() { cylinder(d = 4.6, h = 0.5); cylinder(d = 3.6, h = 2, center = true); }
        }
        if (r == "patch") g("white", "#d9d4c4") linear_extrude(fh(f)) bb2d(fbb(f), 0.2);
        if (r == "led") g("led", fxy(f).x > W * 0.6 ? "orange" : "lime") linear_extrude(0.8) bb2d(fbb(f));
    }
    g("switch", "#333") for (i = [0:len(keys) - 1]) key_at(i) choc_switch(false);
    g("stem", "#8b5a2b") for (i = [0:len(keys) - 1]) key_at(i) choc_switch(true);
}
module lcd_model(sel = "") if (lcd) {
    if (sel == "" || sel == "lcd") color("#bbb") difference() {
        translate([0, 0, lcd_top - lcd_module.z]) linear_extrude(lcd_module.z) bb2d(lcd_bb);
        translate([win_c.x, win_c.y, lcd_top - 0.05]) linear_extrude(1) square(lcd_active, center = true);
    }
    if (sel == "" || sel == "lcd_active") color("#9aa88f") translate([win_c.x, win_c.y, lcd_top - 0.3]) linear_extrude(0.3) square(lcd_active, center = true);
}
module choc_switch(stem = false) {
    if (!stem) { linear_extrude(2.2) square(13.6, center = true); translate([0, 0, 2.2]) linear_extrude(0.8) square(15, center = true);
                 translate([0, 0, 3.0]) linear_extrude(2.5, scale = 0.92) square(12.4, center = true); }
    else translate([0, 0, 5.5]) linear_extrude(choc_cap_z - 5.5) square([10.2, 4.5], center = true);
}

// ---------------------------------------------------------------- cell stand-in
module cell_model() if (cell_on) color("#3a6ea5")
    translate([cell_at.x, cell_at.y, z_floor_in + cell_foam]) linear_extrude(cell[0]) offset(r = 1) square([cell[2] - 2, cell[1] - 2], center = true);

// ---------------------------------------------------------------- colours
c_body   = "#24262b";   // colour 2 of the shells (graphite PETG)
c_first  = "#e9e6df";   // colour 1: the face skin (natural PETG, lets the LEDs glow)
c_accent = "#c2185b";   // key bridge (magenta PETG)
c_plate  = "#3b3f46";

module front_split(first) intersection() { front(); translate([-50, -50, first ? z_face - first_colour_t : -50]) cube([500, 500, first ? 10 : 50 + z_face - first_colour_t]); }
module cap_split(kind, first) intersection() { keycap(kind); translate([-50, -50, first ? cap_t - first_colour_t : -50]) cube([100, 100, first ? 10 : 50 + cap_t - first_colour_t]); }

// ---------------------------------------------------------------- assembly
// Each piece in its place; e > 0 explodes it along z in build order (the plate also slides off its rails).
pieces = [  // name, colour, alpha
    ["plate", c_plate, 1], ["tray", c_body, 1], ["cell", "#3a6ea5", 1],
    ["pcb", "#1d3d2a", 1], ["parts", "#2a2a2a", 1], ["metal", "#b8bcc2", 1], ["white", "#efefea", 1], ["led", "#ffb300", 1],
    ["switch", "#303236", 1], ["stem", "#8b5a2b", 1], ["lcd_frame", "#4a4d55", 1], ["lcd", "#c9ccd0", 1], ["lcd_active", "#a9b5a0", 1],
    ["keybridge", c_accent, 1], ["caps_body", c_accent, 1], ["caps_first", c_first, 1],
    ["front_body", c_body, 1], ["front_first", c_first, 1], ["cover", "#d6ecff", 0.3],
];
module piece(n, e = explode) {
    function dz(k) = k * 13 * e;
    if (n == "plate") translate([-45 * e - 75 * release, 0, z_bot + dz(-2.2)]) plate();
    if (n == "tray") tray();
    if (n == "cell") translate([0, 0, dz(1)]) cell_model();
    if (in_list(n, ["pcb", "parts", "metal", "white", "led", "switch", "stem"])) translate([0, 0, dz(2.2)]) board_model(n);
    if (n == "lcd_frame") translate([0, 0, dz(3.0)]) lcd_frame();
    if (n == "lcd" || n == "lcd_active") translate([0, 0, dz(3.8)]) lcd_model(n);
    if (n == "keybridge") translate([0, 0, dz(4.8)]) keybridge();
    if (n == "caps_body" || n == "caps_first") for (i = [0:len(keys) - 1]) key_at(i) translate([0, 0, choc_cap_z + dz(5.8)]) cap_split(key_kind(i), n == "caps_first");
    if (n == "front_body" || n == "front_first") translate([0, 0, dz(7.0)]) front_split(n == "front_first");
    if (n == "cover" && has("lcd")) translate([0, 0, z_face - cover_t + dz(8.0)])
        linear_extrude(cover_t) cover_plan(0.15);
}
module assembly(e = explode) for (p = pieces) if (show_board || !in_list(p[0], ["pcb", "parts", "metal", "white", "led", "switch", "stem", "lcd", "lcd_active"]))
    color(p[1], p[2]) piece(p[0], e);

// ---------------------------------------------------------------- part selector (print orientation)
if (part == "all") assembly();
else if (part == "piece") piece(piece_name);
else if (part == "front") translate([0, 0, z_face]) rotate([0, 180, 0]) front();        // face down
else if (part == "keybridge") translate([0, 0, -plate_bot]) keybridge();               // plate down
else if (part == "lcd_frame") lcd_frame();
else if (part == "tray") translate([0, 0, -z_bot]) tray();
else if (part == "plate") translate([0, 0, plate_t]) plate();
else if (part == "sma_cap") sma_cap();                                                  // closed end down
else if (part == "cap_up") translate([0, 0, cap_t]) rotate([0, 180, 0]) keycap("up");    // face down
else if (part == "cap_ok") translate([0, 0, cap_t]) rotate([0, 180, 0]) keycap("ok");
else if (part == "cap_dn") translate([0, 0, cap_t]) rotate([0, 180, 0]) keycap("dn");

// ---------------------------------------------------------------- checks (echoed on every run)
if (cell_on) let(lo = rail_ys()[0] + rail_strip_w() / 2, hi = rail_ys()[1] - rail_strip_w() / 2)
    if (cell_at.y - cell[1] / 2 - 0.5 < lo || cell_at.y + cell[1] / 2 + 0.5 > hi) echo(str("CHECK: cell (", cell[1], " mm wide) overlaps a rail strip: room is ", lo, " to ", hi));
for (h = holes) if (in_cell(h)) echo(str("NOTE: hole ", h[0], " is over the cell and is not used by the case"));
echo(str("CASE: cell ", cell_under_parts ? "below the key sockets" : "right under the board", ", total height with plate ", z_face - z_bot + plate_t, " mm"));
echo(str("CASE: display posts ", lcd_posts, ", bridge feet ", kb_feet()));
echo(str("CASE: outer ", W + 2 * (board_gap + wall), " x ", H + 2 * (board_gap + wall), " x ", z_face - z_bot,
         " mm (face ", z_face, ", bottom ", z_bot, "), key bridge ", kb1 - kb0));
for (p = board_parts) if (p[1] == "F" && p[3] + 0.4 > z_face - 0.8) echo(str("CHECK: ", p[0], " is ", p[3], " mm tall, too close to the face"));
for (q = board_parts) if (lcd && q[1] == "F" && q[3] > lcd_back - ring_t - 0.15) let(o = lcd_bb, b = q[2])
    if (b[2] > o[0] && b[0] < o[2] && b[3] > o[1] && b[1] < o[3]) echo(str("CHECK: ", q[0], " (", q[3], " mm) under the display ring"));
for (q = board_parts, r = lcd ? carrier_lug_rects() : []) let(b = q[2]) if (q[1] == "F" && q[3] > carrier_lug_z - 0.3 && b[2] > r[0] && b[0] < r[2] && b[3] > r[1] && b[1] < r[3])
    echo(str("CHECK: display carrier lug lands on ", q[0]));
if (has("rh")) let(r = rh_box()) for (q = board_parts) let(b = q[2]) if (q[0] != feat("rh")[0] && b[2] > r[0] - rh_baffle && b[0] < r[2] + rh_baffle && b[3] > r[1] - rh_baffle && b[1] < r[3] + rh_baffle && !(b[0] >= r[0] && b[2] <= r[2] && b[1] >= r[1] && b[3] <= r[3]))
    echo(str("CHECK: humidity chamber baffle crosses ", q[0]));
if (has("baro")) let(o = baro_out()) if (o[2] > kb0.x - 0.2) echo("CHECK: barometer hood touches the key bridge");
if (has("baro")) let(o = baro_out()) for (q = board_parts) let(b = q[2]) if (q[1] == "F" && q[0] != feat("baro")[0] && b[2] > o[0] && b[0] < o[2] && b[3] > o[1] && b[1] < o[3])
    echo(str("CHECK: barometer seal ring lands on ", q[0]));
if (has("battery")) let(b = fbb(feat("battery")), r = bat_side(), y = fxy(feat("battery")).y) for (q = board_parts) let(c = q[2]) if (q[1] == "F" && q[0] != feat("battery")[0] && q[3] > z_face_in - 1.3 && (r ? c[2] > b[2] - 0.5 : c[0] < b[0] + 0.5) && c[3] > y - 3.4 && c[1] < y + 3.4)
    echo(str("CHECK: battery plug pocket meets ", q[0]));
if (lcd && len(lcd_posts) < 4) echo("CHECK: fewer than 4 free spots for display posts");
for (p = kb_feet()) for (q = board_parts) if (q[1] == "F" && p.x > q[2][0] - 1.2 && p.x < q[2][2] + 1.2 && p.y > q[2][1] - 1.2 && p.y < q[2][3] + 1.2)
    echo(str("CHECK: key bridge foot at ", p, " lands on ", q[0]));
