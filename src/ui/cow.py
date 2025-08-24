from .shape import *
from ..utils.geometry import *
import math


class Cow(Shape):
    def __init__(self, center: Point, color=(139, 69, 19), scale_factor=1.0, facing_direction=1):
        super().__init__(center, color)
        self.scale_factor = scale_factor
        self.facing_direction = facing_direction
        self._create_cow()

    def _create_cow(self):

        # Neck length
        NECK_LENGTH = 20 * self.scale_factor
        HEAD_WIDTH = 30 * self.scale_factor
        NOSE_RADIUS = 5 * self.scale_factor
        FORHEAD_SIZE = 4 * self.scale_factor

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

        # Head
        self.for_neck1 = Triangle(
            self.body.outerPoints[318],
            Point(self.body.outerPoints[18].x + NECK_LENGTH / 2, self.body.outerPoints[18].y),
            self.body.outerPoints[24],
            self.color
        )
        self.for_neck2 = Triangle(
            self.for_neck1.a,
            Point(self.body.outerPoints[312].x + 2 * NECK_LENGTH / 2,  self.body.outerPoints[312].y),
            self.for_neck1.b,
            self.color
        )
        dist_body_to_for_neck = self.for_neck2.b.x - self.body.outerPoints[312].x
        self.for_neck_round = Oval(
            center= Point(self.body.outerPoints[312].x + dist_body_to_for_neck / 2, self.body.outerPoints[312].y),
            rx=dist_body_to_for_neck / 2,
            ry=self.for_neck1.a.y - self.for_neck2.b.y,
            color=self.color
        )

        body_head_diff = self.for_neck2.b.y - self.body.outerPoints[270].y
        self.neck1 = Triangle(
            Point(self.for_neck2.b.x + NECK_LENGTH / 2, self.for_neck2.b.y - body_head_diff),
            self.for_neck2.b,
            self.for_neck2.c,
            self.color,
        )
        self.neck2 = Triangle(
            self.neck1.a,
            Point(self.for_neck2.c.x + NECK_LENGTH / 2, self.for_neck2.c.y - body_head_diff),
            self.for_neck2.c,
            self.color,
        )

        self.head = Triangle(
            self.neck1.a,
            self.neck2.b,
            Point(self.neck2.b.x + HEAD_WIDTH, self.neck2.b.y),
            self.color
        )

        self.nose = Circle(
            Point(self.head.c.x - NOSE_RADIUS, self.head.c.y - NOSE_RADIUS),
            NOSE_RADIUS * 2,
            self.color
        )

        self.snout = Oval(
            Point(self.nose.center.x + NOSE_RADIUS * 0.5, self.nose.center.y + NOSE_RADIUS * 0.5),
            NOSE_RADIUS * 2,
            NOSE_RADIUS,
            (255, 192, 203) 
        )
        self.snout.rotate(- math.pi/4)
        
        # Add nostrils (narine) inside the snout
        self.nostril = Oval(
            Point(self.snout.center.x + NOSE_RADIUS * 0.6, self.snout.center.y - NOSE_RADIUS * 0.3),
            NOSE_RADIUS * 0.6,
            NOSE_RADIUS * 0.3,
            (0, 0, 0)
        )
        self.nostril.rotate(math.pi/4)

        self.chin = Oval(
            center=Point(self.head.b.x + HEAD_WIDTH / 2, self.head.b.y),
            ry=NOSE_RADIUS/2,
            rx=HEAD_WIDTH/2,
            color=self.color
        )

        self.horns_circle = Circle(
            Point(self.head.a.x + FORHEAD_SIZE, self.head.a.y + FORHEAD_SIZE),
            FORHEAD_SIZE * 2,
            self.color
        )

        self.forhead1 = Triangle(
            self.horns_circle.outerPoints[0],
            self.nose.outerPoints[270],
            self.head.c,
            self.color
        )

        self.forhead2 = Triangle(
            self.head.a,
            self.head.c,
            self.horns_circle.outerPoints[0],
            self.color
        )

        # Leg positions from body outer points (angles in multiples of 6)
        leg_positions = [
            self.body.outerPoints.get(150),
            self.body.outerPoints.get(30),
            self.body.outerPoints.get(120),
            self.body.outerPoints.get(60),
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
            (0, 255, 0),
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
            (0, 255, 0),
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
            (0, 255, 0),
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
            (0, 255, 0),
        )
        self.hip_2 = Circle(
            Point(leg_positions[1].x, leg_positions[1].y),
            HIP_RADIUS,
            self.color,
        )
        
        # Leg 3
        self.thigh_3 = Oval(
            Point(leg_positions[2].x - 8*self.scale_factor, leg_positions[2].y + THIGH_LEG_HEIGHT / 2),
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
            (0, 255, 0),
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
            (0, 255, 0),
        )
        self.hip_3 = Circle(
            Point(leg_positions[2].x - 8*self.scale_factor, leg_positions[2].y),
            HIP_RADIUS,
            self.color,
        )
        
        # Leg 4
        self.thigh_4 = Oval(
            Point(leg_positions[3].x + 8*self.scale_factor, leg_positions[3].y + THIGH_LEG_HEIGHT / 2),
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
            (0, 255, 0),
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
            (0, 255, 0),
        )
        self.hip_4 = Circle(
            Point(leg_positions[3].x + 8*self.scale_factor, leg_positions[3].y),
            HIP_RADIUS,
            self.color,
        )

        self.parts = [
            self.body,
            self.for_neck1, self.for_neck2, self.for_neck_round, self.neck1, self.neck2,
            self.head, self.chin, self.nose, self.horns_circle, self.forhead1, self.forhead2, self.snout, self.nostril,
            self.hip_1, self.thigh_1, self.calf_1, self.knee_1, self.clog_1,
            self.hip_2, self.thigh_2, self.calf_2, self.knee_2, self.clog_2,
            self.hip_3, self.thigh_3, self.calf_3, self.knee_3, self.clog_3,
            self.hip_4, self.thigh_4, self.calf_4, self.knee_4, self.clog_4
        ]

        # Store original clog positions for walking animation
        self.clog_1_original_y = self.clog_1.center.y
        self.clog_2_original_y = self.clog_2.center.y
        self.clog_3_original_y = self.clog_3.center.y
        self.clog_4_original_y = self.clog_4.center.y

    def set_scale_factor(self, new_scale_factor):
        """Update the scale factor and recreate the cow with new dimensions"""
        self.scale_factor = new_scale_factor
        self._create_cow()
    
    def set_facing_direction(self, new_direction):
        """Update the facing direction (1 for right, -1 for left)"""
        self.facing_direction = new_direction
        self._create_cow()

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)

    def walk(self, angle):
        # Create a walking animation that lifts the clogs upward using cos
        # Different legs have different phase offsets for realistic walking
        legs = [
            (self.thigh_1, self.knee_1, self.calf_1, self.clog_1, self.clog_1_original_y, angle * self.facing_direction),
            (self.thigh_2, self.knee_2, self.calf_2, self.clog_2, self.clog_2_original_y, (angle + math.pi) * self.facing_direction),
            (self.thigh_3, self.knee_3, self.calf_3, self.clog_3, self.clog_3_original_y, (angle + math.pi) * self.facing_direction),
            (self.thigh_4, self.knee_4, self.calf_4, self.clog_4, self.clog_4_original_y, angle * self.facing_direction)
        ]
        
        for thigh, knee, calf, clog, original_y, leg_angle in legs:
            # Calculate new clog position
            lift_height = 1 / 3 * calf.ry
            lift_factor = math.cos(leg_angle)
            lift_offset = -lift_height * (lift_factor + 1) / 2

            new_clog_y = original_y + lift_offset
            dy = new_clog_y - clog.center.y

            if abs(dy) > 0.1:
                clog.translate(0, dy)

                # Move calf too
                calf_dx = clog.outerPoints["top_middle"].x - calf.outerPoints.get(90).x
                calf_dy = clog.outerPoints["top_middle"].y - calf.outerPoints.get(90).y
                calf.translate(calf_dx, calf_dy)

            # Circle 1 based by clog top position
            clog_x = clog.outerPoints["top_middle"].x
            clog_y = clog.outerPoints["top_middle"].y
            rad1 = calf.ry * 2 + knee.radius

            A1 = -2 * clog_x
            B1 = -2 * clog_y
            C1 = clog_x**2 + clog_y**2 - rad1**2

            # Circle 2 based by hip position and thigh ry + knee radius
            hip_point = thigh.outerPoints.get(270)
            hip_x = hip_point.x
            hip_y = hip_point.y

            rad2 = thigh.ry * 2 + knee.radius

            A2 = -2 * hip_x
            B2 = -2 * hip_y
            C2 = hip_x**2 + hip_y**2 - rad2**2

            try:
                intersections = get_intersection_between_two_circles(A1, B1, C1, A2, B2, C2)

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
                knee.center.y - clog.center.y,
                knee.center.x - clog.center.x
            )
            clog.rotate(clog_angle)
            
            calf_angle = math.atan2(knee.center.y - calf.outerPoints[90].y, knee.center.x - calf.outerPoints[90].x)
            if self.facing_direction == 1:  # Facing right
                calf.rotate(calf_angle + math.pi/2, calf.outerPoints[90])
            else:  # Facing left
                calf.rotate(calf_angle - math.pi/2 + math.pi, calf.outerPoints[90])

            thigh_angle = math.atan2(knee.center.y - thigh.outerPoints[270].y, knee.center.x - thigh.outerPoints[270].x)
            if self.facing_direction == 1:  # Facing right
                thigh.rotate(thigh_angle - math.pi/2, thigh.outerPoints[270])
            else:  # Facing left
                thigh.rotate(thigh_angle + math.pi/2 + math.pi, thigh.outerPoints[270])