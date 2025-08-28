import math
import pygame
import random
from .shape import *


class AudioIcosphereVisualizer:
    """
    Audio-driven icosphere visualizer.

    - Builds an icosphere mesh (subdivided icosahedron) represented by 3D vertices and triangle faces.

    Parameters mirror the original variables:
    - coordinates: (width, height) of the pygame rendering surface.
    - sensitivity: multiplier for how strongly the audio amplitude displaces the vertices.
    - rotation_speed: angular speed (radians per second) for the rotation applied each frame.
    - fps: target frames per second for the rendering loop.
    - subdivisions: number of recursive subdivisions applied to the base icosahedron (controls mesh density).
    - base_scale: base projection scale (bigger values make the sphere appear larger on-screen).
    """

    def __init__(self, coordinates=(1920, 1080),
                 sensitivity=2.0, rotation_speed=0.5,
                 fps=60, subdivisions=2, base_scale=250):

        # Configuration / parameters
        self.coordinates = coordinates
        self.sensitivity = sensitivity
        self.rotation_speed = rotation_speed
        self.fps = fps
        self.subdivisions = subdivisions
        self.base_scale = base_scale

        # Mesh and audio-related state (populated in _load_audio_and_mesh)
        self.tris = None  # list of triangle indices (tuples of vertex indices)
        self.verts_unit = None  # list of Point3D unit-length vertices on the sphere
        self.frames_per_second = None  # audio-derived frames per second for spectrogram frames
        self.clock = pygame.time.Clock()  # pygame clock for frame timing
        self.rot_angle = 0.0  # cumulative rotation angle (radians)
        self.start_ticks = 0  # pygame time when audio started (milliseconds)
        
        # Optimization caches
        self._cached_displaced_verts = None
        self._cached_rotated_verts = None
        self._cached_cos_sin = (0.0, 0.0)  # Cached cos/sin values
        self._last_rot_angle = -1.0  # Track rotation changes

        self._load_mesh()

    # ---------------- helper utilities ----------------

    def _normalize(self, v):
        """
        Normalize a 3D vector-like object to unit length and return a Point3D.
        Used to keep all vertices on the unit sphere after subdivision/interpolation.

        Input 'v' must have attributes x, y, z.
        """
        norm = math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)
        if norm == 0:
            return Point3D(0, 0, 0)
        return Point3D(v.x / norm, v.y / norm, v.z / norm)

    def _create_icosahedron(self):
        """
        Create the base icosahedron: 12 vertices and 20 triangular faces.

        Returns:
            verts: list of Point3D unit vertices
            faces: list of index triples referencing verts
        """
        t = (1.0 + math.sqrt(5.0)) / 2.0
        verts = [
            Point3D(-1, t, 0), Point3D(1, t, 0), Point3D(-1, -t, 0), Point3D(1, -t, 0),
            Point3D(0, -1, t), Point3D(0, 1, t), Point3D(0, -1, -t), Point3D(0, 1, -t),
            Point3D(t, 0, -1), Point3D(t, 0, 1), Point3D(-t, 0, -1), Point3D(-t, 0, 1),
        ]
        # Normalize base vertices so they sit on the unit sphere
        verts = [self._normalize(v) for v in verts]
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
        ]
        return verts, faces

    def _subdivide(self, verts, faces):
        """
        Subdivide each triangular face into 4 smaller triangles by creating midpoints
        on each edge and projecting them back to the unit sphere.

        This uses a midpoint cache (midpoint_cache) keyed by sorted endpoint indices
        to avoid duplicating vertices for shared edges.

        Returns updated verts (list of Point3D) and new_faces (list of index triples).
        """
        new_faces = []
        midpoint_cache = {}

        def midpoint_key(a, b):
            # ensure key ordering is stable for undirected edge
            return tuple(sorted((a, b)))

        def get_midpoint(i1, i2):
            """
            Return index of midpoint vertex between verts[i1] and verts[i2].
            If midpoint already computed, return cached index; otherwise compute,
            normalize, append to verts, cache index, and return it.
            """
            key = midpoint_key(i1, i2)
            if key in midpoint_cache:
                return midpoint_cache[key]
            v1, v2 = verts[i1], verts[i2]
            vm = self._normalize(Point3D(
                (v1.x + v2.x) / 2.0,
                (v1.y + v2.y) / 2.0,
                (v1.z + v2.z) / 2.0
            ))
            verts.append(vm)
            idx = len(verts) - 1
            midpoint_cache[key] = idx
            return idx

        # For each original triangle, build four smaller triangles using midpoints
        for tri in faces:
            i0, i1, i2 = tri
            a = get_midpoint(i0, i1)
            b = get_midpoint(i1, i2)
            c = get_midpoint(i2, i0)
            new_faces += [(i0, a, c), (i1, b, a), (i2, c, b), (a, b, c)]
        return verts, new_faces

    def _create_icosphere(self, subdivisions):
        """
        Build an icosphere by repeatedly subdividing the base icosahedron.
        subdivisions=0 returns a simple icosahedron, higher values increase mesh density.

        Returns verts (list of Point3D) and faces (list of index triples).
        """
        verts, faces = self._create_icosahedron()
        for _ in range(subdivisions):
            verts, faces = self._subdivide(verts, faces)
        return verts, faces

    def _project_vertex(self, v, width, height, scale, camera_z=3.0):
        """
        Project a 3D vertex to 2D screen coordinates using a simple perspective projection.

        Parameters:
            v: Point3D (assumed rotated/displaced already)
            width, height: screen size in pixels
            scale: base scale that affects field of view / zoom
            camera_z: camera offset along z-axis. This shifts vertices forward.

        Returns:
            (Point(px, py), zp) where Point is a 2D point from shape.Point and zp is the
            depth used for depth sorting or other effects.
        """
        zp = v.z + camera_z
        # Avoid division by small numbers; clamp zp to a small positive value
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
        
        # Initialize arrays with Point3D objects to avoid allocation during animation
        for i in range(self._num_verts):
            self._cached_displaced_verts[i] = Point3D(0, 0, 0)
            self._cached_rotated_verts[i] = Point3D(0, 0, 0)

    # ---------------- main render routine ----------------

    def draw(self, screen):

        # dt: time elapsed since last frame in seconds (used to advance rotation)
        dt = self.clock.tick(self.fps) / 1000.0

        # Optimize vertex displacement - reuse allocated objects
        for i, v in enumerate(self.verts_unit):
            # TODO Part to make animation. Sound data needs to be extracted
            #random_factor = random.uniform(0.8, 1.2)
            #displacement = 1.0 + self.sensitivity * random_factor

            displacement = 1.0

            # Reuse pre-allocated Point3D objects to avoid garbage collection
            displaced_v = self._cached_displaced_verts[i]
            displaced_v.x = v.x * displacement
            displaced_v.y = v.y * displacement
            displaced_v.z = v.z * displacement

        # Update rotation angle and cache cos/sin if needed
        self.rot_angle += self.rotation_speed * dt
        
        # Only recalculate cos/sin if rotation changed significantly
        if abs(self.rot_angle - self._last_rot_angle) > 1e-6:
            self._cached_cos_sin = (math.cos(self.rot_angle), math.sin(self.rot_angle))
            self._last_rot_angle = self.rot_angle
            
        cos_a, sin_a = self._cached_cos_sin
        
        # Optimize vertex rotation - reuse allocated objects
        for i, v in enumerate(self._cached_displaced_verts):
            # Apply rotation matrix around Y axis, reusing pre-allocated objects
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

            # Create Triangle object (provided by shape.Triangle) and draw its outline.
            # Points are converted to tuples for pygame.draw.polygon.
            triangle = Triangle(pa, pb, pc, color)
            triangle.draw(screen, 1)

        return True
