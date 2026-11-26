// Case parameters. Board geometry is NOT here: it comes from board.scad (generated from KiCad).
// All lengths in mm. Frame: board lower-left at origin, y up (radio edge), z = 0 on the front copper.

/* [Print] */
fit        = 0.25;   // clearance between printed parts that slide or nest
board_gap  = 0.35;   // board edge to inner wall
wall       = 2.0;    // side walls
corner_r   = 4.0;    // outer corner radius in plan
face_t     = 1.6;    // front face thickness
floor_t    = 1.4;    // tray floor
first_colour_t = 0.6; // first colour of the front face (printed face-down): inlays are this deep

/* [Display: Sharp LS027B7DH01] */
lcd_module    = [62.8, 42.82, 1.3];  // outline and glass stack (board README)
lcd_back_z    = 3.5;                 // glass back above F.Cu, on the spacer frame (board README)
lcd_active    = [58.8, 35.28];       // 400 x 240 dots at 0.147 mm
lcd_active_off = [0, -1.77];         // only used without the Dwgs.User drawing: 2.0 mm from the FPC-far edge
lcd_gasket    = 0.3;                 // foam between the glass and the face
window_margin = 0.8;                 // visible border around the active area
cover_t       = 1.0;                 // clear PC or PMMA cover, laser cut, sits flush in the face
cover_border  = 2.0;                 // cover overlap past the window on each side

/* [Keys: Kailh Choc PG1350] */
choc_cut      = 13.8;   // plate cut-out (Kailh)
choc_plate_t  = 1.2;    // plate thickness the clips expect
choc_plate_top = 2.2;   // plate top above the PCB
choc_cap_z    = 8.5;    // underside of the cap above the PCB, key at rest
choc_travel   = 3.0;
choc_stem_pitch = 5.7;  // the two stem slots, centre to centre
choc_peg      = [1.2, 3.0, 3.2];   // peg cross-section and length (slot is 1.2 x 3.0, see Kailh drawing)
cap_t         = 2.4;    // cap thickness (solid, printed face-down)
cap_clear     = 0.6;    // cap to well wall
cap_size      = [18, 15.2]; // cap envelope (w, h); 22 mm key pitch leaves 2.8 mm fences
fence_drop    = 2.0;    // fence tops sit this far below the resting cap tops
fence_w       = 1.8;

/* [Power] */
// The internal Li-ion pouch cell: [thickness, width, length]. Any 1S pouch that fits.
// Examples: 402030 = [4, 20, 30] (~200 mAh), 603450 = [6, 34, 50] (~1200 mAh), 805060 = [8, 50, 60] (~2000 mAh).
// [0, 0, 0] = no battery (USB power only); the tray gets shallower.
cell          = [6, 34, 50];
cell_foam     = 0.6;    // VHB foam tape under the cell (e.g. 3M 4930)
cell_gap      = 0.5;    // cell top to the board's back, where no part is under the board
cell_at       = [56, 34.6]; // cell centre in board coordinates: between the key sockets and the upper rail

/* [Barometer] */
baro_mode     = "cockpit";  // documentation only: the same sealed hood serves both; "static" = fit the 4 mm barb (needs approval)

/* [Antenna] */
sma           = true;   // SMA bulkhead for the external GNSS antenna (U.FL pigtail inside)
sma_wall      = "left"; // which short wall
sma_d         = 6.5;    // 1/4"-36 panel hole
sma_flat      = 5.9;    // D-flat across

/* [Fasteners] */
// Brass heat-set inserts and A4 or titanium screws: the magnetometer is on board.
insert_d      = 4.0;    // M3 x 5.7 heat-set insert, hole for it
insert_l      = 4.0;    // M3 x 4 short insert: the dovetail channel runs under the corner columns
screw_d       = 3.4;
screw_head_d  = 6.8;    // ISO 10642 countersunk
boss_d        = 6.6;    // stays inside the 7 mm keep-out around each board hole
nylon_holes   = ["H1"]; // next to the radio antenna: PA66 screw, no insert, no metal

/* [Mount] */
rail_w        = 6.0;    // dovetail at the mouth
rail_h        = 2.8;
rail_angle    = 30;     // flank angle from vertical
rail_inset    = 5.5;    // rail centre from the long outer edge
plate_t       = 3.0;
strap_w       = 26;     // for 25 mm webbing or hook-and-loop
strap_slot    = 3.6;
wing          = 13;     // plate overhang at each end for the strap slots
latch_wing    = 19;     // the right wing also carries the latch's release tab
stop_t        = 6;      // the stop block at the left end
latch_hook    = 1.2;    // how far the snap hook reaches into the notch in the tray
latch_arm     = [30, 10, 1.8];  // length, width, thickness of the spring arm in the plate
plate_screw   = 4.3;    // M4 / #8 countersunk
amps          = [30, 38];  // AMPS hole pattern (RAM and most cockpit mounts)
quarter_inch_nut = 11.2;   // 1/4"-20 hex nut across corners (+ fit)

/* [Text] */
font_bold     = "Inter:style=Bold";
font_reg      = "Inter:style=Medium";

$fn = 48;
