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
FRAMES_PER_FLAP = 14
TIME_PER_FLAP = 1.0
FLAPS_PER_SECOND = 1 / TIME_PER_FLAP
FLY_FRAMES_PER_SECOND = FRAMES_PER_FLAP * FLAPS_PER_SECOND
BOB_HEIGHT_METER = 0.15  # 최저점부터 최고점까지의 높이 차이
BOB_HEIGHT_PIXEL = BOB_HEIGHT_METER * PIXEL_PER_METER
RISE_START_FRAME = 4.0  # 사람이 세는 5번째 프레임
FALL_START_FRAME = 10.0  # 사람이 세는 11번째 프레임
SPRITE_SCALE = 0.5
# 모든 날갯짓의 범위를 감싸는 공통 사각형. 경계 계산에 사용한다.
DRAW_WIDTH = 200 * SPRITE_SCALE
DRAW_HEIGHT = 200 * SPRITE_SCALE


# 원본의 위쪽 행부터 왼쪽→오른쪽. 빈 마지막 칸은 제외한다.
# Pico2D의 잘림 y는 이미지 아래쪽에서 센다.
# 원본의 불투명 픽셀 영역. 균등 격자는 인접 날개·꼬리를 섞는다.
FRAME_BOUNDS = (
    (34, 1, 179, 143), (216, 2, 361, 142), (398, 12, 543, 141),
    (555, 17, 725, 138), (728, 48, 909, 135),
    (34, 217, 179, 334), (216, 216, 361, 339), (398, 216, 543, 335),
    (580, 217, 725, 325), (762, 219, 907, 328),
    (34, 392, 179, 499), (216, 394, 361, 499), (376, 395, 543, 482),
    (546, 370, 725, 483),
)
FRAME_RECTS = tuple((left, 506 - bottom - 1, right - left + 1, bottom - top + 1)
                    for left, top, right, bottom in FRAME_BOUNDS)
# 부리와 몸통의 기준점은 자른 이미지의 중심과 별도로 유지한다.
FRAME_ANCHORS = tuple((100 + 182 * (i % 5), 90 + 166 * (i // 5))
                      for i in range(FRAMES_PER_FLAP))


def height_offset(frame):
    """5번째부터 상승, 11번째부터 하강하는 연속적인 높이."""
    phase = (frame - RISE_START_FRAME) % FRAMES_PER_FLAP
    rise_frames = FALL_START_FRAME - RISE_START_FRAME
    if phase < rise_frames:
        return BOB_HEIGHT_PIXEL * phase / rise_frames
    fall_frames = FRAMES_PER_FLAP - rise_frames
    return BOB_HEIGHT_PIXEL * (FRAMES_PER_FLAP - phase) / fall_frames


class Bird:
    image = None

    def __init__(self, x=400, y=300, direction=1, frame=0,
                 canvas_width=1600, canvas_height=600):
        self.x = float(x)
        self.base_y = float(y)
        self.y = self.base_y
        self.direction = direction
        self.frame = float(frame) % FRAMES_PER_FLAP
        if not isfinite(self.frame):
            raise ValueError('초기 프레임은 유한해야 한다.')
        if not DRAW_HEIGHT / 2 <= self.base_y <= canvas_height - DRAW_HEIGHT / 2 - BOB_HEIGHT_PIXEL:
            raise ValueError('상하 이동을 포함한 초기 높이를 확인해야 한다.')
        self.y = self.base_y + height_offset(self.frame)
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

        self.frame = (self.frame + FLY_FRAMES_PER_SECOND * dt) % FRAMES_PER_FLAP
        nearest_frame = round(self.frame)
        if isclose(self.frame, nearest_frame, rel_tol=0, abs_tol=1e-10):
            self.frame = float(nearest_frame % FRAMES_PER_FLAP)
        self.y = self.base_y + height_offset(self.frame)

    def draw(self):
        image = self.load_shared_image()
        index = int(self.frame)
        rect = FRAME_RECTS[index]
        left, top, right, bottom = FRAME_BOUNDS[index]
        anchor_x, anchor_y = FRAME_ANCHORS[index]
        offset_x = ((left + right + 1) / 2 - anchor_x) * SPRITE_SCALE
        offset_y = (anchor_y - (top + bottom + 1) / 2) * SPRITE_SCALE
        flip = '' if self.direction == 1 else 'h'
        draw_x = self.x + self.direction * offset_x
        image.clip_composite_draw(
            *rect, 0, flip, draw_x, self.y + offset_y,
            rect[2] * SPRITE_SCALE, rect[3] * SPRITE_SCALE)
