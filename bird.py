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
        if self.right <= self.left:
            raise ValueError('캔버스 폭이 새의 출력 폭보다 커야 한다.')
        if not self.left <= self.x <= self.right or direction not in (-1, 1):
            raise ValueError('초기 수평 위치와 방향을 확인해야 한다.')

    @classmethod
    def load_shared_image(cls):
        if cls.image is None:
            cls.image = load_image(str(Path(__file__).with_name('bird_animation.png')))
        return cls.image

    def update(self):
        dt = game_framework.frame_time
        if not isfinite(dt) or dt < 0:
            raise ValueError('frame_time은 유한한 0 이상의 초 단위 값이어야 한다.')
        if dt == 0:
            return
        # 왕복 경로를 펼쳐 계산하면 큰 dt의 다중 반사도 한 번에 처리된다.
        span = self.right - self.left
        offset = self.x - self.left
        unfolded = offset if self.direction == 1 else 2 * span - offset
        position = (unfolded + FLY_SPEED_PPS * dt) % (2 * span)
        if isclose(position, 0, rel_tol=0, abs_tol=1e-9) or isclose(
                position, 2 * span, rel_tol=0, abs_tol=1e-9):
            position = 0.0
        elif isclose(position, span, rel_tol=0, abs_tol=1e-9):
            position = span
        if position < span:
            self.x = self.left + position
            self.direction = 1
        else:
            self.x = self.right - (position - span)
            self.direction = -1

    def draw(self):
        image = self.load_shared_image()
        rect = FRAME_RECTS[int(self.frame)]
        flip = '' if self.direction == 1 else 'h'
        image.clip_composite_draw(
            *rect, 0, flip, self.x, self.y, DRAW_WIDTH, DRAW_HEIGHT)
