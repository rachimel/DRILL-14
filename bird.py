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
