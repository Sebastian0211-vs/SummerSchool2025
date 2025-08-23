from .shape import *
from ..utils.geometry import *
import math


class Cow(Shape):
    def __init__(self, center: Point, color=(139, 69, 19)):
        super().__init__(center, color)
        self._create_cow()

    def _create_cow(self):

        THIGH_LEG1_WIDTH = 20
        THIGH_LEG1_HEIGHT = 70

        CALF_LEG1_WIDTH = THIGH_LEG1_WIDTH
        CALF_LEG1_HEIGHT = 60

        KNEE_RADIUS = THIGH_LEG1_WIDTH / 2

        CLOG_SIZE = CALF_LEG1_WIDTH

        self.thigh_1 = Oval(
            Point(self.center.x, self.center.y - THIGH_LEG1_HEIGHT),
            THIGH_LEG1_WIDTH / 2,
            THIGH_LEG1_HEIGHT / 2,
            self.color,
        )

        self.knee_1 = Circle(
            Point(
                self.thigh_1.center.x,
                self.thigh_1.center.y + THIGH_LEG1_HEIGHT / 2 + KNEE_RADIUS,
            ),
            KNEE_RADIUS,
            (0, 255, 0),
        )

        self.calf_1 = Oval(
            Point(
                self.knee_1.center.x,
                self.knee_1.center.y + KNEE_RADIUS + CALF_LEG1_HEIGHT / 2,
            ),
            CALF_LEG1_WIDTH / 2,
            CALF_LEG1_HEIGHT / 2,
            self.color,
        )

        self.clog_1 = Square(
            Point(
                self.calf_1.center.x,
                self.calf_1.center.y + CALF_LEG1_HEIGHT / 2 + CLOG_SIZE / 2,
            ),
            CLOG_SIZE,
            (0, 255, 0),
        )

        self.parts = [self.thigh_1, self.calf_1, self.knee_1, self.clog_1]

        # Store original clog position for walking animation
        self.clog_1_original_y = self.clog_1.center.y

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)

    def walk(self, angle):
        # Create a walking animation that lifts the clog upward using cos
        lift_height = 2 / 3 * 2 * self.calf_1.ry
        lift_factor = math.cos(angle)
        lift_offset = -lift_height * (lift_factor + 1) / 2

        # Calculate new clog position
        new_clog_y = self.clog_1_original_y + lift_offset
        dy = new_clog_y - self.clog_1.center.y

        # Apply translation only if dy is significant
        if abs(dy) > 0.1:
            self.clog_1.translate(0, dy)

        # Find knee position

        # Circle 1 based by clog.center position and clog + calf + knee radius
        clog_x = self.clog_1.center.x
        clog_y = self.clog_1.center.y
        rad1 = self.calf_1.ry * 2 + self.knee_1.radius + self.clog_1.size / 2

        A1 = -2 * clog_x
        B1 = -2 * clog_y
        C1 = clog_x**2 + clog_y**2 - rad1**2

        hip_point = self.thigh_1.outerPoints.get(270)
        hip_x = hip_point.x
        hip_y = hip_point.y

        rad2 = self.thigh_1.ry * 2 + self.knee_1.radius

        A2 = -2 * hip_x
        B2 = -2 * hip_y
        C2 = hip_x**2 + hip_y**2 - rad2**2

        try:
            intersections = get_intersection_between_two_circles(A1, B1, C1, A2, B2, C2)

            if len(intersections) >= 1:
                # Choose intersection that keeps knee in reasonable position
                knee_x, knee_y = intersections[0]
                if len(intersections) == 2:
                    x1, y1 = intersections[0]
                    x2, y2 = intersections[1]
                    # Choose the forward-facing knee (higher position, lower y)
                    if y2 < y1:
                        knee_x, knee_y = x2, y2

                # Update knee position
                knee_dx = knee_x - self.knee_1.center.x
                knee_dy = knee_y - self.knee_1.center.y

                if abs(knee_dx) > 0.1 or abs(knee_dy) > 0.1:
                    self.knee_1.translate(knee_dx, knee_dy)

        except (ValueError, IndexError, ZeroDivisionError):
            # Keep current position if intersection fails
            pass
