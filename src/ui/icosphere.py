import math
import pygame
import random
from .shape import Point, Point3D, Triangle


class AudioIcosphereVisualizer:

    def __init__(
        self,
        coordinates,
        sensitivity=2.0,
        rotation_speed=0.5,
        fps=60,
        subdivisions=2,
        base_scale=250,
    ):

        # Configuration / parameters
        self.coordinates = (base_scale, base_scale)
        self.sensitivity = sensitivity
        self.rotation_speed = rotation_speed
        self.fps = fps
        self.subdivisions = subdivisions
        self.base_scale = base_scale

        # Mesh and audio-related state (populated in _load_mesh)
        self.tris = None
        self.verts_unit = None
        self.clock = pygame.time.Clock()
        self.rot_angle = 0.0
        self.start_ticks = 0  # will be set on first draw()

        # Optimization caches
        self._cached_displaced_verts = None
        self._cached_rotated_verts = None
        self._cached_cos_sin = (0.0, 0.0)
        self._last_rot_angle = -1.0

        # MIDI-specific state
        self.midi_events = []  # list of (time_seconds, on_bool, note, vel_norm)
        self._midi_ptr = 0
        self._active_notes = {}  # note -> vel_norm

        # Vertex → midi mapping & randomness (initialized in _load_mesh)
        self._vertex_pref_pitch = None
        self._vertex_phase = None
        self._vertex_osc_freq = None

        # Build geometry
        self._load_mesh()


    def _normalize(self, v):
        norm = math.sqrt(v.x**2 + v.y**2 + v.z**2)
        if norm == 0:
            return Point3D(0, 0, 0)
        return Point3D(v.x / norm, v.y / norm, v.z / norm)

    def _create_icosahedron(self):
        t = (1.0 + math.sqrt(5.0)) / 2.0
        verts = [
            Point3D(-1, t, 0),
            Point3D(1, t, 0),
            Point3D(-1, -t, 0),
            Point3D(1, -t, 0),
            Point3D(0, -1, t),
            Point3D(0, 1, t),
            Point3D(0, -1, -t),
            Point3D(0, 1, -t),
            Point3D(t, 0, -1),
            Point3D(t, 0, 1),
            Point3D(-t, 0, -1),
            Point3D(-t, 0, 1),
        ]
        verts = [self._normalize(v) for v in verts]
        faces = [
            (0, 11, 5),
            (0, 5, 1),
            (0, 1, 7),
            (0, 7, 10),
            (0, 10, 11),
            (1, 5, 9),
            (5, 11, 4),
            (11, 10, 2),
            (10, 7, 6),
            (7, 1, 8),
            (3, 9, 4),
            (3, 4, 2),
            (3, 2, 6),
            (3, 6, 8),
            (3, 8, 9),
            (4, 9, 5),
            (2, 4, 11),
            (6, 2, 10),
            (8, 6, 7),
            (9, 8, 1),
        ]
        return verts, faces

    def _subdivide(self, verts, faces):
        new_faces = []
        midpoint_cache = {}

        def midpoint_key(a, b):
            return tuple(sorted((a, b)))

        def get_midpoint(i1, i2):
            key = midpoint_key(i1, i2)
            if key in midpoint_cache:
                return midpoint_cache[key]
            v1, v2 = verts[i1], verts[i2]
            vm = self._normalize(
                Point3D((v1.x + v2.x) / 2.0, (v1.y + v2.y) / 2.0, (v1.z + v2.z) / 2.0)
            )
            verts.append(vm)
            idx = len(verts) - 1
            midpoint_cache[key] = idx
            return idx

        for tri in faces:
            i0, i1, i2 = tri
            a = get_midpoint(i0, i1)
            b = get_midpoint(i1, i2)
            c = get_midpoint(i2, i0)
            new_faces += [(i0, a, c), (i1, b, a), (i2, c, b), (a, b, c)]
        return verts, new_faces

    def _create_icosphere(self, subdivisions):
        verts, faces = self._create_icosahedron()
        for _ in range(subdivisions):
            verts, faces = self._subdivide(verts, faces)
        return verts, faces

    def _project_vertex(self, v, width, height, scale, camera_z=3.0):
        zp = v.z + camera_z
        if zp <= 0.01:
            zp = 0.01
        f = scale / zp
        px = int(width / 2 + v.x * f)
        py = int(height / 2 - v.y * f)
        return Point(px, py), zp

    def _load_mesh(self):
        # Build the geometric mesh (verts on unit sphere and triangle faces)
        self.verts_unit, self.tris = self._create_icosphere(self.subdivisions)

        # Pre-allocate arrays for optimized processing
        self._num_verts = len(self.verts_unit)
        self._cached_displaced_verts = [None] * self._num_verts
        self._cached_rotated_verts = [None] * self._num_verts

        for i in range(self._num_verts):
            self._cached_displaced_verts[i] = Point3D(0, 0, 0)
            self._cached_rotated_verts[i] = Point3D(0, 0, 0)

        lo_pitch = 21
        hi_pitch = 108
        self._vertex_pref_pitch = [
            lo_pitch + (i * (hi_pitch - lo_pitch) / max(1, self._num_verts - 1))
            for i in range(self._num_verts)
        ]

        # Per-vertex randomness: phase and slow oscillator frequency
        rng = random.Random(4_8_15_16_23_42)  # small deterministic seed for stable look; change if you want more randomness
        self._vertex_phase = [rng.uniform(0, 2 * math.pi) for _ in range(self._num_verts)]
        self._vertex_osc_freq = [rng.uniform(0.4, 1.6) for _ in range(self._num_verts)]

    # ---------------- MIDI loading ----------------

    def update_by_note(self, notes):

        self._active_notes = {}

        if not notes:
            return


        for note in notes:
            vel_norm = float(note.velocity_on) / 127.0 if note.velocity_on > 0 else 0.0
            if vel_norm > 0:
                self._active_notes[note.pitch] = vel_norm

    # ---------------- main render ----------------

    def draw(self, screen):

        # dt: time elapsed since last frame in seconds (used to advance rotation)
        dt = self.clock.tick(self.fps) / 1000.0

        # Initialize start_ticks on first draw
        if self.start_ticks == 0:
            self.start_ticks = pygame.time.get_ticks()

        # current playback time in seconds since start
        current_time = (pygame.time.get_ticks() - self.start_ticks) / 1000.0

        # If we have MIDI, advance the events pointer and update active notes
        if self.midi_events:
            # consume events whose time <= current_time
            while self._midi_ptr < len(self.midi_events) and self.midi_events[self._midi_ptr][0] <= current_time:
                _, is_on, note, vel_norm = self.midi_events[self._midi_ptr]
                if is_on:
                    self._active_notes[note] = vel_norm
                else:
                    # note off
                    if note in self._active_notes:
                        del self._active_notes[note]
                self._midi_ptr += 1


        # Prepare some parameters for mapping
        sigma = 6.0  # semitone spread — how quickly influence decays with pitch distance
        two_sigma_sq = 2.0 * sigma * sigma

        # Optimize vertex displacement - reuse allocated objects
        for i, v in enumerate(self.verts_unit):
            # base displacement of 1.0, plus contributions from active MIDI notes
            influence = 0.0
            if self._active_notes:
                pref = self._vertex_pref_pitch[i]
                # sum contributions of each active note weighted by gaussian pitch distance
                for note, vel in self._active_notes.items():
                    d = (note - pref)
                    weight = math.exp(-(d * d) / two_sigma_sq)
                    influence += vel * weight

            # add per-vertex slow oscillation and per-frame random jitter
            phase = self._vertex_phase[i]
            osc = math.sin(phase + current_time * self._vertex_osc_freq[i])
            random_factor = 0.85 + random.random() * 0.3  # small per-frame randomness
            displacement = 1.0 + self.sensitivity * influence * (1.0 + 0.35 * osc) * random_factor

            # Reuse pre-allocated Point3D objects to avoid garbage collection
            displaced_v = self._cached_displaced_verts[i]
            displaced_v.x = v.x * displacement
            displaced_v.y = v.y * displacement
            displaced_v.z = v.z * displacement

        # Update rotation angle and cache cos/sin if needed
        self.rot_angle += self.rotation_speed * dt

        if abs(self.rot_angle - self._last_rot_angle) > 1e-6:
            self._cached_cos_sin = (math.cos(self.rot_angle), math.sin(self.rot_angle))
            self._last_rot_angle = self.rot_angle

        cos_a, sin_a = self._cached_cos_sin

        # Optimize vertex rotation - reuse allocated objects
        for i, v in enumerate(self._cached_displaced_verts):
            rotated_v = self._cached_rotated_verts[i]
            rotated_v.x = v.x * cos_a + v.z * sin_a
            rotated_v.y = v.y
            rotated_v.z = -v.x * sin_a + v.z * cos_a

        # Optimized depth sorting - compute and sort in single pass
        tri_depth_pairs = []
        rotated = self._cached_rotated_verts

        for i, tri in enumerate(self.tris):
            ia, ib, ic = tri
            z_avg = (rotated[ia].z + rotated[ib].z + rotated[ic].z) / 3.0
            tri_depth_pairs.append((z_avg, i))

        # Sort by depth (ascending) - farther triangles drawn first
        tri_depth_pairs.sort(key=lambda x: x[0])

        # Rendering parameters
        w, h = self.coordinates
        color = (255, 215, 0)  # gold-like wireframe color

        # Draw triangles in depth order as outlines (wireframe).
        for _, tri_idx in tri_depth_pairs:
            ia, ib, ic = self.tris[tri_idx]
            pa, _ = self._project_vertex(rotated[ia], w, h, self.base_scale)
            pb, _ = self._project_vertex(rotated[ib], w, h, self.base_scale)
            pc, _ = self._project_vertex(rotated[ic], w, h, self.base_scale)

            triangle = Triangle(pa, pb, pc, color)
            triangle.draw(screen, 1)

        return True
