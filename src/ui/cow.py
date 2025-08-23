from .shape import *
from ..utils.geometry import *
import math


class Cow(Shape):
    def __init__(self, center: Point, color=(139, 69, 19)):
        super().__init__(center, color)
        self._create_cow()

    def _create_cow(self):

        # Legs configuration
        THIGH_LEG_WIDTH = 20
        THIGH_LEG_HEIGHT = 70
        CALF_LEG_WIDTH = THIGH_LEG_WIDTH
        CALF_LEG_HEIGHT = 60
        KNEE_RADIUS = THIGH_LEG_WIDTH / 2
        CLOG_SIZE = CALF_LEG_WIDTH

        # Building legs
        self.thigh_1 = Oval(
            Point(self.center.x, self.center.y - THIGH_LEG_HEIGHT),
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

        # Build legs 2, 3, and 4
        leg_spacing = 40
        
        # Leg 2
        self.thigh_2 = Oval(
            Point(self.center.x + leg_spacing, self.center.y - THIGH_LEG_HEIGHT),
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
        
        # Leg 3
        self.thigh_3 = Oval(
            Point(self.center.x - leg_spacing, self.center.y - THIGH_LEG_HEIGHT),
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
        
        # Leg 4
        self.thigh_4 = Oval(
            Point(self.center.x + 2*leg_spacing, self.center.y - THIGH_LEG_HEIGHT),
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

        self.parts = [
            self.thigh_1, self.calf_1, self.knee_1, self.clog_1,
            self.thigh_2, self.calf_2, self.knee_2, self.clog_2,
            self.thigh_3, self.calf_3, self.knee_3, self.clog_3,
            self.thigh_4, self.calf_4, self.knee_4, self.clog_4
        ]

        # Store original clog positions for walking animation
        self.clog_1_original_y = self.clog_1.center.y
        self.clog_2_original_y = self.clog_2.center.y
        self.clog_3_original_y = self.clog_3.center.y
        self.clog_4_original_y = self.clog_4.center.y

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)

    def walk(self, angle):
        # Create a walking animation that lifts the clogs upward using cos
        # Different legs have different phase offsets for realistic walking
        legs = [
            (self.thigh_1, self.knee_1, self.calf_1, self.clog_1, self.clog_1_original_y, angle),
            (self.thigh_2, self.knee_2, self.calf_2, self.clog_2, self.clog_2_original_y, angle + math.pi/2),
            (self.thigh_3, self.knee_3, self.calf_3, self.clog_3, self.clog_3_original_y, angle),
            (self.thigh_4, self.knee_4, self.calf_4, self.clog_4, self.clog_4_original_y, angle + math.pi/2)
        ]
        
        for thigh, knee, calf, clog, original_y, leg_angle in legs:
            # Calculate new clog position
            lift_height = 2 / 3 * 2 * calf.ry
            lift_factor = math.cos(leg_angle)
            lift_offset = -lift_height * (lift_factor + 1) / 2

            new_clog_y = original_y + lift_offset
            dy = new_clog_y - clog.center.y

            if abs(dy) > 0.1:
                clog.translate(0, dy)

            # Find knee position
            clog_x = clog.center.x
            clog_y = clog.center.y
            rad1 = calf.ry * 2 + knee.radius + clog.size / 2

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
                        if y2 < y1:
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
            
            calf_dx = clog.outerPoints["right_middle"].x - calf.outerPoints.get(90).x
            calf_dy = clog.outerPoints["right_middle"].y - calf.outerPoints.get(90).y
            calf_angle = math.atan2(knee.center.y - calf.outerPoints[90].y, knee.center.x - calf.outerPoints[90].x)
            calf.translate(calf_dx, calf_dy)
            calf.rotate(calf_angle + math.pi/2, calf.outerPoints[90])

            thigh_angle = math.atan2(knee.center.y - thigh.outerPoints[270].y, knee.center.x - thigh.outerPoints[270].x)
            thigh.rotate(thigh_angle - math.pi/2, thigh.outerPoints[270])