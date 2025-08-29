from .shape import *
from ..utils.geometry import *
import math


class Cow(Shape):
    def __init__(
        self, center: Point, color=(0, 0, 0), scale_factor=1.0, facing_direction=1
    ):
        super().__init__(center, color)
        self.scale_factor = scale_factor
        self.facing_direction = facing_direction

        # Cache for optimization
        self._cached_parts = None
        self._cached_scale_factor = None
        self._cached_facing_direction = None
        self._pi = math.pi
        self._half_pi = math.pi / 2

        self._create_cow()

    def _create_cow(self):

        # Head configuration
        NECK_LENGTH = 20 * self.scale_factor
        HEAD_WIDTH = 30 * self.scale_factor
        NOSE_RADIUS = 5 * self.scale_factor
        FORHEAD_SIZE = 4 * self.scale_factor
        HORN_HEIGHT = 25 * self.scale_factor
        EYE_SIZE = 4 * self.scale_factor

        # Body configuration
        BODY_WIDTH = 140 * self.scale_factor
        BODY_HEIGHT = 90 * self.scale_factor

        # Legs configuration
        THIGH_LEG_WIDTH = 18 * self.scale_factor
        THIGH_LEG_HEIGHT = 30 * self.scale_factor
        CALF_LEG_WIDTH = 16 * self.scale_factor
        CALF_LEG_HEIGHT = 25 * self.scale_factor
        KNEE_RADIUS = 8 * self.scale_factor
        CLOG_SIZE = 14 * self.scale_factor
        HIP_RADIUS = 6 * self.scale_factor

        # Body
        self.body = Oval(
            Point(self.center.x, self.center.y),
            BODY_WIDTH / 2,
            BODY_HEIGHT / 2,
            self.color,
        )

        # Head - create for right direction first with unique Point instances
        # Store body points as unique instances
        p318 = Point(self.body.outerPoints[318].x, self.body.outerPoints[318].y)
        p18 = Point(self.body.outerPoints[18].x, self.body.outerPoints[18].y)
        p24 = Point(self.body.outerPoints[24].x, self.body.outerPoints[24].y)
        p312 = Point(self.body.outerPoints[312].x, self.body.outerPoints[312].y)
        p270 = Point(self.body.outerPoints[270].x, self.body.outerPoints[270].y)

        self.for_neck1 = Triangle(
            Point(p318.x, p318.y),
            Point(p18.x + NECK_LENGTH / 2, p18.y),
            Point(p24.x, p24.y),
            self.color,
        )

        for_neck2_b = Point(p312.x + 2 * NECK_LENGTH / 2, p312.y)
        self.for_neck2 = Triangle(
            Point(self.for_neck1.a.x, self.for_neck1.a.y),
            Point(for_neck2_b.x, for_neck2_b.y),
            Point(self.for_neck1.b.x, self.for_neck1.b.y),
            self.color,
        )

        dist_body_to_for_neck = for_neck2_b.x - p312.x
        self.for_neck_round = Oval(
            center=Point(p312.x + dist_body_to_for_neck / 2, p312.y),
            rx=dist_body_to_for_neck * 0.9,
            ry=self.for_neck1.a.y - for_neck2_b.y,
            color=self.color,
        )

        body_head_diff = for_neck2_b.y - p270.y
        neck1_a = Point(for_neck2_b.x + NECK_LENGTH / 2, for_neck2_b.y - body_head_diff)
        self.neck1 = Triangle(
            Point(neck1_a.x, neck1_a.y),
            Point(for_neck2_b.x, for_neck2_b.y),
            Point(self.for_neck2.c.x, self.for_neck2.c.y),
            self.color,
        )

        neck2_b = Point(
            self.for_neck2.c.x + NECK_LENGTH / 2, self.for_neck2.c.y - body_head_diff
        )
        self.neck2 = Triangle(
            Point(neck1_a.x, neck1_a.y),
            Point(neck2_b.x, neck2_b.y),
            Point(self.for_neck2.c.x, self.for_neck2.c.y),
            self.color,
        )

        head_c = Point(neck2_b.x + HEAD_WIDTH, neck2_b.y)
        self.head = Triangle(
            Point(neck1_a.x, neck1_a.y),  # en haut
            Point(neck2_b.x, neck2_b.y),
            Point(head_c.x, head_c.y),  # a droite
            self.color,
        )

        iris_center = Point(
            self.head.b.x,
            self.head.c.y - ((self.head.c.y - self.head.a.y) / 3 * 2),
        )
        self.iris = Circle(iris_center, EYE_SIZE / 4, (0, 0, 0))

        self.eye = Oval(
            Point(iris_center.x, iris_center.y),
            EYE_SIZE / 2,
            EYE_SIZE,
            (255, 255, 255),
        )
        self.eye.rotate(-math.pi / 4)

        nose_center = Point(head_c.x - NOSE_RADIUS, head_c.y - NOSE_RADIUS)
        self.nose = Circle(
            Point(nose_center.x, nose_center.y), NOSE_RADIUS * 2, self.color
        )

        snout_center = Point(
            nose_center.x + NOSE_RADIUS * 0.5, nose_center.y + NOSE_RADIUS * 0.5
        )
        self.snout = Oval(
            Point(snout_center.x, snout_center.y),
            NOSE_RADIUS * 2,
            NOSE_RADIUS * 1.4,
            (255, 192, 203),
        )
        self.snout.rotate(-math.pi / 4)

        nostril_center = Point(
            snout_center.x + NOSE_RADIUS * 0.6, snout_center.y - NOSE_RADIUS * 0.3
        )
        self.nostril = Oval(
            Point(nostril_center.x, nostril_center.y),
            NOSE_RADIUS * 0.6,
            NOSE_RADIUS * 0.3,
            (0, 0, 0),
        )
        self.nostril.rotate(math.pi / 4)

        chin_center = Point(neck2_b.x + HEAD_WIDTH / 2, neck2_b.y)
        self.chin = Oval(
            center=Point(chin_center.x, chin_center.y),
            ry=NOSE_RADIUS / 2,
            rx=HEAD_WIDTH / 2,
            color=self.color,
        )

        horns_center = Point(neck1_a.x + FORHEAD_SIZE, neck1_a.y + FORHEAD_SIZE)
        self.horns_circle = Circle(
            Point(horns_center.x, horns_center.y), FORHEAD_SIZE * 2, self.color
        )

        self.corn_neck = Triangle(
            Point(
                self.for_neck_round.outerPoints[0].x,
                self.for_neck_round.outerPoints[0].y,
            ),
            Point(
                self.for_neck_round.outerPoints[306].x,
                self.for_neck_round.outerPoints[306].y,
            ),
            Point(
                self.horns_circle.outerPoints[270].x,
                self.horns_circle.outerPoints[270].y,
            ),
            self.color,
        )

        self.forhead1 = Triangle(
            Point(
                self.horns_circle.outerPoints[0].x, self.horns_circle.outerPoints[0].y
            ),
            Point(self.nose.outerPoints[270].x, self.nose.outerPoints[270].y),
            Point(head_c.x, head_c.y),
            self.color,
        )

        self.forhead2 = Triangle(
            Point(neck1_a.x, neck1_a.y),
            Point(head_c.x, head_c.y),
            Point(
                self.horns_circle.outerPoints[0].x, self.horns_circle.outerPoints[0].y
            ),
            self.color,
        )

        horn_tip_angle = math.radians(48) - math.pi / 2
        horn_tip_x = self.horns_circle.center.x + HORN_HEIGHT * math.cos(horn_tip_angle)
        horn_tip_y = self.horns_circle.center.y + HORN_HEIGHT * math.sin(horn_tip_angle)
        self.horn1 = Triangle(
            Point(self.horns_circle.center.x, self.horns_circle.center.y),
            Point(
                self.horns_circle.outerPoints[48].x, self.horns_circle.outerPoints[48].y
            ),
            Point(horn_tip_x, horn_tip_y),
            (128, 128, 128),
        )

        horn2_tip_angle = math.radians(24) - math.pi / 2
        horn2_tip_x = self.horns_circle.center.x + HORN_HEIGHT * math.cos(
            horn2_tip_angle
        )
        horn2_tip_y = self.horns_circle.center.y + HORN_HEIGHT * math.sin(
            horn2_tip_angle
        )
        self.horn2 = Triangle(
            Point(self.horns_circle.center.x, self.horns_circle.center.y),
            Point(
                self.horns_circle.outerPoints[312].x,
                self.horns_circle.outerPoints[312].y,
            ),
            Point(horn2_tip_x, horn2_tip_y),
            (128, 128, 128),
        )

        # Create head_parts collection
        self.head_parts = [
            self.for_neck1,
            self.for_neck2,
            self.for_neck_round,
            self.neck1,
            self.neck2,
            self.head,
            self.chin,
            self.horn1,
            self.horn2,
            self.horns_circle,
            self.corn_neck,
            self.forhead1,
            self.forhead2,
            self.nose,
            self.snout,
            self.nostril,
            self.eye,
            self.iris,
        ]

        # Apply symmetry for left-facing direction
        if self.facing_direction == -1:
            for head_part in self.head_parts:
                head_part.symmetry(self.body.center.x)

        # Leg positions from body outer points (angles in multiples of 6)
        leg_positions = [
            self.body.outerPoints.get(150),
            self.body.outerPoints.get(54),
            self.body.outerPoints.get(120),
            self.body.outerPoints.get(48),
        ]

        # Building legs from body outer points
        self.thigh_1 = Oval(
            Point(leg_positions[0].x, leg_positions[0].y + THIGH_LEG_HEIGHT / 2),
            THIGH_LEG_WIDTH / 2,
            THIGH_LEG_HEIGHT / 2,
            self.color,
        )
        self.knee_1 = Circle(
            Point(
                self.thigh_1.center.x,
                self.thigh_1.center.y + THIGH_LEG_HEIGHT / 2 + KNEE_RADIUS,
            ),
            KNEE_RADIUS,
            (128, 128, 128),
        )
        self.calf_1 = Oval(
            Point(
                self.knee_1.center.x,
                self.knee_1.center.y + KNEE_RADIUS + CALF_LEG_HEIGHT / 2,
            ),
            CALF_LEG_WIDTH / 2,
            CALF_LEG_HEIGHT / 2,
            self.color,
        )
        self.clog_1 = Square(
            Point(
                self.calf_1.center.x,
                self.calf_1.center.y + CALF_LEG_HEIGHT / 2 + CLOG_SIZE / 2,
            ),
            CLOG_SIZE,
            (128, 128, 128),
        )
        self.hip_1 = Circle(
            Point(leg_positions[0].x, leg_positions[0].y),
            HIP_RADIUS,
            self.color,
        )

        # Leg 2
        self.thigh_2 = Oval(
            Point(leg_positions[1].x, leg_positions[1].y + THIGH_LEG_HEIGHT / 2),
            THIGH_LEG_WIDTH / 2,
            THIGH_LEG_HEIGHT / 2,
            self.color,
        )
        self.knee_2 = Circle(
            Point(
                self.thigh_2.center.x,
                self.thigh_2.center.y + THIGH_LEG_HEIGHT / 2 + KNEE_RADIUS,
            ),
            KNEE_RADIUS,
            (128, 128, 128),
        )
        self.calf_2 = Oval(
            Point(
                self.knee_2.center.x,
                self.knee_2.center.y + KNEE_RADIUS + CALF_LEG_HEIGHT / 2,
            ),
            CALF_LEG_WIDTH / 2,
            CALF_LEG_HEIGHT / 2,
            self.color,
        )
        self.clog_2 = Square(
            Point(
                self.calf_2.center.x,
                self.calf_2.center.y + CALF_LEG_HEIGHT / 2 + CLOG_SIZE / 2,
            ),
            CLOG_SIZE,
            (128, 128, 128),
        )
        self.hip_2 = Circle(
            Point(leg_positions[1].x, leg_positions[1].y),
            HIP_RADIUS,
            self.color,
        )

        # Leg 3
        self.thigh_3 = Oval(
            Point(
                leg_positions[2].x - 8 * self.scale_factor,
                leg_positions[2].y + THIGH_LEG_HEIGHT / 2,
            ),
            THIGH_LEG_WIDTH / 2,
            THIGH_LEG_HEIGHT / 2,
            self.color,
        )
        self.knee_3 = Circle(
            Point(
                self.thigh_3.center.x,
                self.thigh_3.center.y + THIGH_LEG_HEIGHT / 2 + KNEE_RADIUS,
            ),
            KNEE_RADIUS,
            (128, 128, 128),
        )
        self.calf_3 = Oval(
            Point(
                self.knee_3.center.x,
                self.knee_3.center.y + KNEE_RADIUS + CALF_LEG_HEIGHT / 2,
            ),
            CALF_LEG_WIDTH / 2,
            CALF_LEG_HEIGHT / 2,
            self.color,
        )
        self.clog_3 = Square(
            Point(
                self.calf_3.center.x,
                self.calf_3.center.y + CALF_LEG_HEIGHT / 2 + CLOG_SIZE / 2,
            ),
            CLOG_SIZE,
            (128, 128, 128),
        )
        self.hip_3 = Circle(
            Point(leg_positions[2].x - 8 * self.scale_factor, leg_positions[2].y),
            HIP_RADIUS,
            self.color,
        )

        # Leg 4
        self.thigh_4 = Oval(
            Point(
                leg_positions[3].x + 8 * self.scale_factor,
                leg_positions[3].y + THIGH_LEG_HEIGHT / 2,
            ),
            THIGH_LEG_WIDTH / 2,
            THIGH_LEG_HEIGHT / 2,
            self.color,
        )
        self.knee_4 = Circle(
            Point(
                self.thigh_4.center.x,
                self.thigh_4.center.y + THIGH_LEG_HEIGHT / 2 + KNEE_RADIUS,
            ),
            KNEE_RADIUS,
            (128, 128, 128),
        )
        self.calf_4 = Oval(
            Point(
                self.knee_4.center.x,
                self.knee_4.center.y + KNEE_RADIUS + CALF_LEG_HEIGHT / 2,
            ),
            CALF_LEG_WIDTH / 2,
            CALF_LEG_HEIGHT / 2,
            self.color,
        )
        self.clog_4 = Square(
            Point(
                self.calf_4.center.x,
                self.calf_4.center.y + CALF_LEG_HEIGHT / 2 + CLOG_SIZE / 2,
            ),
            CLOG_SIZE,
            (128, 128, 128),
        )
        self.hip_4 = Circle(
            Point(leg_positions[3].x + 8 * self.scale_factor, leg_positions[3].y),
            HIP_RADIUS,
            self.color,
        )

        self.parts = [
            self.body,
            *self.head_parts,
            self.hip_1,
            self.thigh_1,
            self.calf_1,
            self.knee_1,
            self.clog_1,
            self.hip_2,
            self.thigh_2,
            self.calf_2,
            self.knee_2,
            self.clog_2,
            self.hip_3,
            self.thigh_3,
            self.calf_3,
            self.knee_3,
            self.clog_3,
            self.hip_4,
            self.thigh_4,
            self.calf_4,
            self.knee_4,
            self.clog_4,
        ]

        # Store original clog positions for walking animation
        self.clog_1_original_y = self.clog_1.center.y
        self.clog_2_original_y = self.clog_2.center.y
        self.clog_3_original_y = self.clog_3.center.y
        self.clog_4_original_y = self.clog_4.center.y

        # Pre-cache frequently accessed points for walk animation optimization
        self._cache_walk_points()

        # Store some values that can be usefull
        self.global_height = abs(
            self.clog_1.outerPoints["bottom_middle"].y - self.body.outerPoints[270].y
        )
        self.global_width = abs(
            self.snout.outerPoints[0].x - self.body.outerPoints[180].x
        )

    def set_scale_factor(self, new_scale_factor):
        """Update the scale factor and recreate the cow with new dimensions"""
        if self.scale_factor == new_scale_factor:
            return  # No change needed

        self.scale_factor = new_scale_factor
        self._cache_reinstanciation()
        self._create_cow()

    def set_facing_direction(self, new_direction):
        """Update the facing direction (1 for right, -1 for left)"""
        if self.facing_direction == new_direction:
            return

        self.facing_direction = new_direction
        self._cache_reinstanciation()
        self._create_cow()

    def _cache_reinstanciation(self):
        """Resintanciation parts when cow needs to be recreated"""
        self._cached_parts = None
        self._cached_scale_factor = None
        self._cached_facing_direction = None

    def _cache_walk_points(self):
        # Cache leg component references for faster access
        self._leg_components = [
            {
                "thigh": self.thigh_1,
                "knee": self.knee_1,
                "calf": self.calf_1,
                "clog": self.clog_1,
                "original_y": self.clog_1_original_y,
                "calf_point_90": self.calf_1.outerPoints.get(90),
                "thigh_point_270": self.thigh_1.outerPoints.get(270),
            },
            {
                "thigh": self.thigh_2,
                "knee": self.knee_2,
                "calf": self.calf_2,
                "clog": self.clog_2,
                "original_y": self.clog_2_original_y,
                "calf_point_90": self.calf_2.outerPoints.get(90),
                "thigh_point_270": self.thigh_2.outerPoints.get(270),
            },
            {
                "thigh": self.thigh_3,
                "knee": self.knee_3,
                "calf": self.calf_3,
                "clog": self.clog_3,
                "original_y": self.clog_3_original_y,
                "calf_point_90": self.calf_3.outerPoints.get(90),
                "thigh_point_270": self.thigh_3.outerPoints.get(270),
            },
            {
                "thigh": self.thigh_4,
                "knee": self.knee_4,
                "calf": self.calf_4,
                "clog": self.clog_4,
                "original_y": self.clog_4_original_y,
                "calf_point_90": self.calf_4.outerPoints.get(90),
                "thigh_point_270": self.thigh_4.outerPoints.get(270),
            },
        ]

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)

    def walk(self, angle):
        # Create a walking animation using procedural movement.

        leg_angles = [
            angle * self.facing_direction,
            (angle + self._pi) * self.facing_direction,
            (angle + self._pi) * self.facing_direction,
            angle * self.facing_direction,
        ]

        for i, leg_angle in enumerate(leg_angles):
            # Access to cached leg components
            leg_comp = self._leg_components[i]
            thigh = leg_comp["thigh"]
            knee = leg_comp["knee"]
            calf = leg_comp["calf"]
            clog = leg_comp["clog"]

            # Access to cached points
            original_y = leg_comp["original_y"]
            calf_point_90 = leg_comp["calf_point_90"]
            thigh_point_270 = leg_comp["thigh_point_270"]

            # Calculate new clog position
            lift_height = 2 / 3 * calf.ry
            lift_factor = math.cos(leg_angle)
            lift_offset = -lift_height * (lift_factor + 1) / 2

            new_clog_y = original_y + lift_offset
            dy = new_clog_y - clog.center.y

            if abs(dy) > 0.1:
                clog.translate(0, dy)

                # Use cached point reference
                calf_dx = clog.outerPoints["top_middle"].x - calf_point_90.x
                calf_dy = clog.outerPoints["top_middle"].y - calf_point_90.y
                calf.translate(calf_dx, calf_dy)

            # Circle 1 based by clog top position
            clog_x = clog.outerPoints["top_middle"].x
            clog_y = clog.outerPoints["top_middle"].y
            rad1 = calf.ry * 2 + knee.radius

            A1 = -2 * clog_x
            B1 = -2 * clog_y
            C1 = clog_x**2 + clog_y**2 - rad1**2

            # Circle 2 based by hip position and thigh ry + knee radius
            hip_x = thigh_point_270.x
            hip_y = thigh_point_270.y

            rad2 = thigh.ry * 2 + knee.radius

            A2 = -2 * hip_x
            B2 = -2 * hip_y
            C2 = hip_x**2 + hip_y**2 - rad2**2

            try:
                intersections = get_intersection_between_two_circles(
                    A1, B1, C1, A2, B2, C2
                )

                if len(intersections) >= 1:
                    knee_x, knee_y = intersections[0]
                    if len(intersections) == 2:
                        x1, y1 = intersections[0]
                        x2, y2 = intersections[1]

                        if self.facing_direction == 1:
                            if x2 > x1:  # Choose rightward knee position
                                knee_x, knee_y = x2, y2
                        else:  # Facing left
                            if x2 < x1:  # Choose leftward knee position
                                knee_x, knee_y = x2, y2

                    # Update knee position
                    knee_dx = knee_x - knee.center.x
                    knee_dy = knee_y - knee.center.y
                    if abs(knee_dx) > 0.1 or abs(knee_dy) > 0.1:
                        knee.translate(knee_dx, knee_dy)

            except (ValueError, IndexError, ZeroDivisionError):
                pass

            # Update clog, calf angle and position
            clog_angle = math.atan2(
                knee.center.y - clog.center.y, knee.center.x - clog.center.x
            )
            clog.rotate(clog_angle)

            calf_angle = math.atan2(
                knee.center.y - calf_point_90.y,
                knee.center.x - calf_point_90.x,
            )
            if self.facing_direction == 1:  # Facing right
                calf.rotate(calf_angle + self._half_pi, calf_point_90)
            else:  # Facing left
                calf.rotate(calf_angle - self._half_pi + self._pi, calf_point_90)

            thigh_angle = math.atan2(
                knee.center.y - thigh_point_270.y,
                knee.center.x - thigh_point_270.x,
            )
            if self.facing_direction == 1:  # Facing right
                thigh.rotate(thigh_angle - self._half_pi, thigh_point_270)
            else:  # Facing left
                thigh.rotate(thigh_angle + self._half_pi + self._pi, thigh_point_270)
