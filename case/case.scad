// Unicornlines aerobatics logger: case, key bridge, keycaps and mount.
// Everything is derived from board.scad (generated from KiCad) and params.scad.
//
//   openscad -D 'part="front"' -o out/front.stl case.scad
//
// Parts: front, keybridge, lcd_frame, tray, plate, knob, cap_up, cap_ok, cap_dn, all (= assembly)

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
z_cell_top = z_split - back_clear;
cell_on   = cell[0] > 0;
z_floor_in = cell_on ? z_cell_top - cell[0] - cell_foam - 0.6 : z_cell_top;
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

// Aresti notation for a loop: a dot where the figure starts, the loop, a bar where it ends.
// Here it is the barometer vent: every stroke is an opening.
module aresti_loop(r = 3.2, w = 0.9) {
    difference() { circle(r = r + w/2, $fn = 64); circle(r = r - w/2, $fn = 64);
                   translate([-r * 0.42, -r - 2]) square([r * 0.84, 2.6]); }   // the loop does not close
    translate([-r * 0.42 - 1.6, -r]) circle(d = 1.5);                             // start: the dot
    translate([r * 0.42 + 0.9, -r]) square([w, 3.0], center = true);              // end: the bar
}
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
        usb_cut(); sd_cut(); flex_relief(); battery_lead_gully(); knockouts();
        // barometer
        if (has("baro")) translate([vent_xy().x, vent_xy().y, 0]) {
            if (baro_mode == "cockpit") translate([0, 0, z_face_in - 1]) linear_extrude(face_t + 2) aresti_loop();
            else translate([0, 0, z_face - first_colour_t]) linear_extrude(1) aresti_loop();  // the mark stays, as an inlay
        }
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
    // tongue-and-groove: the front shell's groove is cut below; tray carries the tongue
    if (baro_mode == "static") static_cup();
}

module face_inlays() {
    zt = z_face - first_colour_t;
    // brand: logo in the free field right of the display, name level with the keys
    translate([(lcd_bb[2] + W + board_gap) / 2, (lcd_bb[1] + lcd_bb[3]) / 2 - 2, zt]) linear_extrude(1) logo(18);
    translate([(kb1.x + W + board_gap) / 2, fxy(keys[0]).y, zt]) linear_extrude(1) label("UNICORNLINES®", 2.3);
    // left of the keys: the tagline
    // the tagline runs up the free strip left of the display, clear of the vent and the radio corner
    translate([(lcd_bb[0] - board_gap) / 2 + 4, (kb1.y + (has("radio") ? fbb(feat("radio"))[1] : H)) / 2 + 2, zt]) linear_extrude(1)
        rotate(90) label("NEVER STOP DREAMING", 2.2, font_reg);
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
module battery_lead_gully() if (cell_on && has("battery")) let(f = feat("battery"))
    let(right = fxy(f).x > W / 2) translate([right ? W + board_gap - 0.01 : -board_gap - 1.8, fxy(f).y - 3.5, z_split - 1]) cube([1.81, 7, 20]);

module static_cup() let(b = feat("baro")) translate([fxy(b).x, fxy(b).y, 0]) difference() {
    // a cup over the sensor, foam ring underneath, fed from a 4 mm barb in the wall
    translate([0, 0, 0.9]) cylinder(d = 8, h = z_face_in - 0.9);
    translate([0, 0, -0.1]) cylinder(d = 5, h = z_face_in - 0.4);
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

module lcd_frame() {
    // ring under the glass border (the flex side stays open for the fold)
    translate([0, 0, lcd_back - ring_t]) linear_extrude(ring_t) difference() {
        bb2d(lcd_bb, -0.2);
        bb2d(lcd_bb, -2.2);
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
// nearest point on the ring's centre line
function ring_pt(p) = let(o = lcd_bb, c = 1.2, d = [p.x - o[0], o[2] - p.x, p.y - o[1], o[3] - p.y], m = min(d))
    m == d[0] ? [o[0] + c, p.y] : m == d[1] ? [o[2] - c, p.y] : m == d[2] ? [p.x, o[1] + c] : [p.x, o[3] - c];

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
module tray() {
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
        // thumbscrew insert, left end
        translate([-board_gap - wall - 1, thumb_y, z_bot + thumb_z]) rotate([0, 90, 0]) cylinder(d = insert_d, h = insert_l + wall + 1.5);
        // under the board: nothing of the tongue where the openings are
        if (has("usb_c")) translate([W, fxy(feat("usb_c")).y - 7, z_split - 0.5]) cube([10, 14, 3]);
        if (has("microsd")) translate([W, fxy(feat("microsd")).y - 7, z_split - 0.5]) cube([10, 14, 3]);
        if (has("lcd_flex")) translate([0, 0, z_split - 0.5]) linear_extrude(3) bb2d(fbb(feat("lcd_flex")), 0.6);
        for (h = holes) if (!is_corner(h)) translate([fxy(h).x, fxy(h).y, z_bot]) {
            translate([0, 0, -1]) cylinder(d = screw_d, h = 30);
            translate([0, 0, -0.01]) cylinder(d1 = screw_head_d + 0.2, d2 = screw_d, h = (screw_head_d + 0.2 - screw_d) / 2);
        }
        // inside the floor, readable when the board is out
        translate([W / 2, 6, z_floor_in - 0.4]) linear_extrude(1) label("PER PERFECTIONEM AD FELICITATEM", 2.6, font_reg);
    }
    // columns: floor to the board's back, brass inserts for the front screws
    for (h = holes) translate([fxy(h).x, fxy(h).y, z_floor_in - 0.01]) difference() {
        cylinder(d = boss_d, h = z_split - z_floor_in + 0.01);
        nyl = in_list(h[0], nylon_holes);
        if (is_corner(h)) translate([0, 0, z_split - z_floor_in - (nyl ? 9 : insert_l + 0.3)]) cylinder(d = nyl ? 2.7 : insert_d, h = 20);
        else translate([0, 0, -10]) cylinder(d = screw_d, h = 40);  // inner hole: screw from the back, thin nut on the front
    }
    // (inner holes are countersunk into the bottom, see below)
    // wall strip under the key bridge
    translate([0, 0, z_split - 0.01]) linear_extrude(plate_bot - z_split + 0.01 - fit) kb_wall_strip();
    // the cell: a rib frame and four snap fingers over its long edges
    if (cell_on) cell_bay();
    // block behind the thumbscrew insert
    translate([-board_gap - 0.01, thumb_y - 4.5, z_floor_in - 0.01]) cube([insert_l + 1.2, 9, max(0.01, z_bot + thumb_z + 3.5 - z_floor_in)]);
}
module rail_strips() for (y = rail_ys()) translate([-500, y - (rail_w + 2 * rail_h * tan(rail_angle) + 3.2) / 2]) square([1000, rail_w + 2 * rail_h * tan(rail_angle) + 3.2]);
thumb_y = H / 2 + ((sma && has("gnss_rf") && sma_wall == "left" && fxy(feat("gnss_rf")).y >= H / 2) ? -thumb_dy : thumb_dy) * ((sma && has("gnss_rf") && abs(fxy(feat("gnss_rf")).y - H / 2) < thumb_dy) ? 1 : 0);
function rail_ys() = [-board_gap - wall + rail_inset, H + board_gap + wall - rail_inset];

module dovetail(len, grow = 0) {
    // trapezoid: narrow at z = 0 (the tray bottom), wide at the top; flanks lean 30 deg
    w0 = rail_w + 2 * grow; w1 = w0 + 2 * rail_h * tan(rail_angle);
    translate([-len / 2, 0, -0.01]) rotate([90, 0, 90]) linear_extrude(len)
        polygon([[-w0/2, 0], [w0/2, 0], [w1/2, rail_h + grow], [-w1/2, rail_h + grow]]);
}

module cell_bay() {
    c = cell_at; l = cell[2] + 1.0; w = cell[1] + 1.0; t = cell[0] + cell_foam;
    rib = 1.2;
    translate([c.x, c.y, z_floor_in - 0.01]) {
        difference() {
            linear_extrude(t * 0.6) difference() { square([l + 2 * rib, w + 2 * rib], center = true); square([l, w], center = true); }
            for (sx = [-1, 1]) translate([sx * l / 2, 0, -1]) cube([rib * 3, w * 0.4, t + 2], center = true);   // finger notches to lift it out
        }
        for (sx = [-0.25, 0.25], sy = [-1, 1]) translate([sx * l, sy * (w / 2 + rib / 2), 0]) snap_finger(t, sy);
        // fuel gauge joke: the cell sizes that fit, drawn on the floor
        translate([0, 0, -0.4]) linear_extrude(0.41) { label("1S LiPo", 3.2); translate([0, -4.5]) label(str(cell[0], cell[1], cell[2]), 2.4, font_reg); }
    }
}
module snap_finger(t, side) {
    // a cantilever on the frame: the cell pushes it out, it snaps back over the edge
    translate([-2.5, -0.6, 0]) cube([5, 1.2, t + 0.4]);
    translate([0, 0, t + 0.2]) rotate([0, 90, 0]) linear_extrude(5, center = true)
        polygon([[0, 0.6 * -side], [0, (0.6 + 1.0) * -side], [-1.2, 0.6 * -side]]);
}

module tray_openings() {
    // SMA bulkhead for the external GNSS antenna, low in the wall so its nut is inside the tray
    if (sma && has("gnss_rf")) let(y = fxy(feat("gnss_rf")).y, z = (z_floor_in + z_split) / 2)
        translate([sma_wall == "left" ? -board_gap - wall - 1 : W + board_gap - 1, y, z]) rotate([0, 90, 0])
            intersection() { cylinder(d = sma_d, h = wall + 2); translate([-sma_flat/2 - 5, -5, 0]) cube([sma_flat / 2 + 5 + sma_flat / 2, 10, wall + 2]); }
    battery_lead_gully();
    if (baro_mode == "static" && has("baro")) let(b = feat("baro"))
        translate([-board_gap - wall - 1, fxy(b).y, z_split - 2.5]) rotate([0, 90, 0]) cylinder(d = 2.2, h = wall + 2);
}

// ---------------------------------------------------------------- mount plate
plate_x0 = -board_gap - wall - stop_t - fit;
plate_x1 = W + board_gap + wall;
module plate() {
    L = plate_x1 - plate_x0 + 2 * wing;
    x0 = plate_x0 - wing; y0 = -board_gap - wall; y1 = H + board_gap + wall;
    difference() {
        union() {
            translate([0, 0, -plate_t]) linear_extrude(plate_t) rrect([x0, y0], [x0 + L, y1], corner_r);
            // male rails
            for (y = rail_ys()) translate([(plate_x0 + stop_t + plate_x1) / 2, y, 0]) dovetail(len = plate_x1 - plate_x0 - stop_t - 0.01);
            // the stop at the left end, with the thumbscrew
            translate([plate_x0, y0, -0.01]) cube([stop_t, y1 - y0, thumb_z + 4]);
        }
        // strap slots at both wings
        for (x = [x0 + wing / 2, x0 + L - wing / 2]) translate([x, (y0 + y1) / 2, -plate_t - 1]) linear_extrude(plate_t + 2)
            offset(r = strap_slot / 2) square([0.01, strap_w - strap_slot], center = true);
        // screw it down: four corner holes inside the wings, countersunk from the top
        for (x = [x0 + wing / 2, x0 + L - wing / 2], y = [y0 + 6, y1 - 6]) translate([x, y, 0]) csk(plate_screw);
        // AMPS pattern + 1/4"-20 nut, centred under the unit
        translate([W / 2, H / 2, 0]) {
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * amps.y / 2, sy * amps.x / 2, 0]) csk(plate_screw);
            translate([0, 0, -plate_t - 1]) cylinder(d = 6.6, h = plate_t + 2);
            translate([0, 0, -plate_t + 1.2]) cylinder(d = quarter_inch_nut, h = plate_t, $fn = 6);
        }
        // thumbscrew through the stop
        translate([plate_x0 - 1, thumb_y, thumb_z]) rotate([0, 90, 0]) cylinder(d = screw_d, h = stop_t + 2);
        // lighter: pockets from below between the rails (keeps the rails and the edges solid)
        // (a grid of pockets, 1.2 mm skin on top, ribs between; the screw bosses stay solid)
        translate([0, 0, -plate_t - 0.01]) linear_extrude(plate_t - 1.2) difference() {
            intersection() {
                translate([plate_x0 + stop_t + 3, rail_ys()[0] + rail_w]) square([plate_x1 - plate_x0 - stop_t - 6, rail_ys()[1] - rail_ys()[0] - 2 * rail_w]);
                union() for (i = [0:7], j = [0:2]) translate([plate_x0 + stop_t + 4 + i * 16.5, rail_ys()[0] + rail_w + 1 + j * 13.5]) offset(r = 1.5) square([12.5, 10]);
            }
            translate([W / 2, H / 2]) { circle(d = 18); for (sx = [-1, 1], sy = [-1, 1]) translate([sx * amps.y / 2, sy * amps.x / 2]) circle(d = 10); }
        }
        // easter egg: hidden where only the unit covers it
        translate([W / 2 - 4, H / 2 + 9, -0.4]) linear_extrude(1) label("YOU FOUND IT. NOW FLY IT.", 2.0, font_reg);
        translate([W / 2 + 36, H / 2, -0.4]) linear_extrude(1) logo(16);
    }
}
module csk(d) {
    translate([0, 0, -plate_t - 1]) cylinder(d = d, h = plate_t + 2);
    translate([0, 0, -d / 2 - 0.2]) cylinder(d1 = d, d2 = 2 * d + 0.4, h = d / 2 + 0.2 + 0.01);
}

// a knob for the M3 thumbscrew (press an M3 x 12 socket-head screw into it)
module knob() difference() {
    union() {
        cylinder(d = 14, h = 5, $fn = 18);    // 18 flats: gloves grip it
        cylinder(d = 7.5, h = 7);
    }
    translate([0, 0, 2]) cylinder(d = 5.7, h = 10, $fn = 6);   // screw head
    translate([0, 0, -1]) cylinder(d = screw_d, h = 10);
    translate([0, 0, 5 - 0.4]) linear_extrude(1) star(3.5);
}

// ---------------------------------------------------------------- board stand-in (renders)
// sel picks one material group, so the renderer can colour it; "" = all, with OpenSCAD colours
module board_model(sel = "") {
    module g(n, c) if (sel == "" || sel == n) color(c) children();
    g("pcb", "#1d3d2a") translate([0, 0, -board_t]) linear_extrude(board_t) difference() {
        polygon(board_outline);
        for (h = holes) translate(fxy(h)) circle(d = 3.2);
    }
    g("parts", "#2a2a2a") for (p = board_parts) if (p[3] > 0) translate([0, 0, p[1] == "F" ? 0 : -board_t - p[3]]) linear_extrude(p[3]) bb2d(p[2], -0.2);
    for (f = board_features) {
        r = f[1];
        if (r == "usb_c") g("metal", "silver") translate([fxy(f).x - 3.7, fxy(f).y - 4.47, 0]) cube([7.35 + 0.2, 8.94, 3.26]);
        if (r == "microsd") g("metal", "silver") linear_extrude(1.7) bb2d(fbb(f), -1.2);
        if (r == "radio") g("metal", "#555") linear_extrude(fh(f)) bb2d(fbb(f), -0.3);
        if (r == "battery" || r == "qwiic" || r == "camera") g("white", "#eee") linear_extrude(fh(f)) bb2d(fbb(f), -0.4);
        if (r == "baro" || r == "imu" || r == "mag") g("metal", "#888") linear_extrude(0.9) bb2d(fbb(f));
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
c_accent = "#c2185b";   // key bridge, knob (magenta PETG)
c_plate  = "#3b3f46";

module front_split(first) intersection() { front(); translate([-50, -50, first ? z_face - first_colour_t : -50]) cube([500, 500, first ? 10 : 50 + z_face - first_colour_t]); }
module cap_split(kind, first) intersection() { keycap(kind); translate([-50, -50, first ? cap_t - first_colour_t : -50]) cube([100, 100, first ? 10 : 50 + cap_t - first_colour_t]); }

// ---------------------------------------------------------------- assembly
// Each piece in its place; e > 0 explodes it along z in build order (the plate also slides off its rails).
pieces = [  // name, colour, alpha
    ["plate", c_plate, 1], ["knob", c_accent, 1], ["tray", c_body, 1], ["cell", "#3a6ea5", 1],
    ["pcb", "#1d3d2a", 1], ["parts", "#2a2a2a", 1], ["metal", "#b8bcc2", 1], ["white", "#efefea", 1], ["led", "#ffb300", 1],
    ["switch", "#303236", 1], ["stem", "#8b5a2b", 1], ["lcd_frame", "#4a4d55", 1], ["lcd", "#c9ccd0", 1], ["lcd_active", "#a9b5a0", 1],
    ["keybridge", c_accent, 1], ["caps_body", c_accent, 1], ["caps_first", c_first, 1],
    ["front_body", c_body, 1], ["front_first", c_first, 1], ["cover", "#d6ecff", 0.3],
];
module piece(n, e = explode) {
    function dz(k) = k * 13 * e;
    if (n == "plate") translate([-45 * e - 75 * release, 0, z_bot + dz(-2.2)]) plate();
    if (n == "knob") translate([plate_x0 - 9 - 70 * e - 75 * release - 14 * release, thumb_y, z_bot + thumb_z + dz(-2.2)]) rotate([0, 90, 0]) knob();
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
else if (part == "knob") knob();
else if (part == "cap_up") translate([0, 0, cap_t]) rotate([0, 180, 0]) keycap("up");    // face down
else if (part == "cap_ok") translate([0, 0, cap_t]) rotate([0, 180, 0]) keycap("ok");
else if (part == "cap_dn") translate([0, 0, cap_t]) rotate([0, 180, 0]) keycap("dn");

// ---------------------------------------------------------------- checks (echoed on every run)
echo(str("CASE: display posts ", lcd_posts, ", bridge feet ", kb_feet()));
echo(str("CASE: outer ", W + 2 * (board_gap + wall), " x ", H + 2 * (board_gap + wall), " x ", z_face - z_bot,
         " mm (face ", z_face, ", bottom ", z_bot, "), key bridge ", kb1 - kb0));
for (p = board_parts) if (p[1] == "F" && p[3] + 0.4 > z_face - 0.8) echo(str("CHECK: ", p[0], " is ", p[3], " mm tall, too close to the face"));
for (q = board_parts) if (lcd && q[1] == "F" && q[3] > lcd_back - ring_t - 0.15) let(o = lcd_bb, b = q[2])
    if (b[2] > o[0] && b[0] < o[2] && b[3] > o[1] && b[1] < o[3]) echo(str("CHECK: ", q[0], " (", q[3], " mm) under the display ring"));
if (lcd && len(lcd_posts) < 4) echo("CHECK: fewer than 4 free spots for display posts");
for (p = kb_feet()) for (q = board_parts) if (q[1] == "F" && p.x > q[2][0] - 1.2 && p.x < q[2][2] + 1.2 && p.y > q[2][1] - 1.2 && p.y < q[2][3] + 1.2)
    echo(str("CHECK: key bridge foot at ", p, " lands on ", q[0]));
