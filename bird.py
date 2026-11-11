"""Boy.Run.do() 방식의 시간 기반 비행."""
from math import isclose, isfinite
from pathlib import Path

from pico2d import load_image

import game_framework

BIRD_COUNT = 10
PIXEL_PER_METER = 10 / 0.3
FLY_SPEED_KMPH = 45.0
FLY_SPEED_MPM = FLY_SPEED_KMPH * 1000 / 60
FLY_SPEED_MPS = FLY_SPEED_MPM / 60
FLY_SPEED_PPS = FLY_SPEED_MPS * PIXEL_PER_METER
DRAW_WIDTH = 90
DRAW_HEIGHT = DRAW_WIDTH * 169 / 184


# 원본의 위쪽 행부터 왼쪽→오른쪽. 빈 마지막 칸은 제외한다.
# Pico2D의 잘림 y는 이미지 아래쪽에서 센다.
COLUMN_EDGES = (0, 183, 366, 549, 732, 918)
ROW_EDGES = (0, 168, 337, 506)
FRAME_RECTS = tuple(
    (COLUMN_EDGES[column], 506 - ROW_EDGES[row + 1],
     COLUMN_EDGES[column + 1] - COLUMN_EDGES[column],
     ROW_EDGES[row + 1] - ROW_EDGES[row])
    for row in range(3)
    for column in range(5 if row < 2 else 4)
)


class Bird:
    image = None

    def __init__(self, x=400, y=300, direction=1, frame=0,
                 canvas_width=1600, canvas_height=600):
        self.x = float(x)
        self.base_y = float(y)
        self.y = self.base_y
        self.direction = direction
        self.frame = float(frame)
        self.left = DRAW_WIDTH / 2
        self.right = canvas_width - DRAW_WIDTH / 2

    @classmethod
    def load_shared_image(cls):
        if cls.image is None:
            cls.image = load_image(str(Path(__file__).with_name('bird_animation.png')))
        return cls.image
