from .shape import Point, Shape


class Cow(Shape):
    def __init__(self, center: Point, color=(139, 69, 19)):
        super().__init__(center, color)
        self._create_cow()

    def _create_cow(self):

        pass

    def walk(self):
        pass
