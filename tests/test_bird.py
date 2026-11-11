"""창을 열지 않는 비행 수치·통합 검증."""
import math
import ctypes
import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import bird
from bird import Bird
import game_framework
import game_world
import play_mode


def advance(subject, times):
    for dt in times:
        game_framework.frame_time = dt
        subject.update()
    return subject


class FlightTests(unittest.TestCase):
    def tearDown(self):
        game_framework.frame_time = 0
        Bird.image = None
        game_world.clear()

    def assertSame(self, a, b):
        self.assertAlmostEqual(a.x, b.x, delta=1e-6)
        self.assertEqual(a.direction, b.direction)
        phase_error = abs(a.frame - b.frame)
        self.assertLessEqual(min(phase_error, 14 - phase_error), 1e-6)
        self.assertAlmostEqual(a.y, b.y, delta=1e-6)

    def test_physical_units(self):
        self.assertEqual(bird.FLY_SPEED_KMPH, 45)
        self.assertEqual(bird.FLY_SPEED_MPS, 12.5)
        self.assertAlmostEqual(bird.FLY_SPEED_PPS, 416.6666666667)
        self.assertEqual(bird.BOB_HEIGHT_PIXEL, 5)

    def test_three_second_free_flight(self):
        subject = advance(Bird(x=100, canvas_width=10000), [3])
        self.assertAlmostEqual(subject.x, 1350)

    def test_fps_independence_for_all_birds(self):
        for i in range(10):
            initial = dict(x=100 + i * 140, direction=(-1) ** i, frame=i * 1.4)
            expected = advance(Bird(**initial), [10])
            for fps in (30, 60, 144):
                with self.subTest(bird=i, fps=fps):
                    actual = advance(Bird(**initial), [1 / fps] * (10 * fps))
                    self.assertSame(expected, actual)

    def test_irregular_frames(self):
        rng = random.Random(14)
        times = [rng.uniform(0.001, 0.08) for _ in range(300)]
        for direction in (-1, 1):
            self.assertSame(
                advance(Bird(direction=direction, frame=6.3), [sum(times)]),
                advance(Bird(direction=direction, frame=6.3), times))

    def test_right_overshoot_preserved(self):
        subject = Bird(x=1545)
        advance(subject, [15 / bird.FLY_SPEED_PPS])
        self.assertAlmostEqual(subject.x, 1540)
        self.assertEqual(subject.direction, -1)

    def test_left_overshoot_preserved(self):
        subject = Bird(x=55, direction=-1)
        advance(subject, [15 / bird.FLY_SPEED_PPS])
        self.assertAlmostEqual(subject.x, 60)
        self.assertEqual(subject.direction, 1)

    def test_exact_boundary_points_inward(self):
        for start, direction, expected in ((400, 1, 1550), (400, -1, 50)):
            subject = Bird(x=start, direction=direction)
            advance(subject, [abs(expected - start) / bird.FLY_SPEED_PPS])
            self.assertAlmostEqual(subject.x, expected)
            self.assertEqual(subject.direction, -direction)

    def test_multiple_reflections(self):
        span = 1500
        subject = Bird(x=50)
        advance(subject, [(8 * span + 200) / bird.FLY_SPEED_PPS])
        self.assertAlmostEqual(subject.x, 250)
        self.assertEqual(subject.direction, 1)

    def test_single_large_step_equals_many(self):
        self.assertSame(advance(Bird(frame=3.7), [1000]),
                        advance(Bird(frame=3.7), [0.1] * 10000))

    def test_zero_time_changes_nothing(self):
        subject = Bird(x=50, direction=-1, frame=8.2)
        before = vars(subject).copy()
        advance(subject, [0])
        self.assertEqual(before, vars(subject))

    def test_invalid_delta_rejected(self):
        for dt in (-1, math.inf, math.nan):
            with self.subTest(dt=dt), self.assertRaises(ValueError):
                advance(Bird(), [dt])

    def test_bob_keyframes(self):
        self.assertEqual(bird.height_offset(4), 0)
        self.assertEqual(bird.height_offset(10), 5)
        self.assertEqual(bird.height_offset(18), 0)
        self.assertAlmostEqual(bird.height_offset(7), 2.5)
        self.assertAlmostEqual(bird.height_offset(0), 2.5)

    def test_bob_continuity_at_cycle_and_turns(self):
        for frame in (0, 4, 10, 14):
            self.assertAlmostEqual(bird.height_offset(frame - 1e-8),
                                   bird.height_offset(frame + 1e-8), delta=1e-6)

    def test_bob_has_no_drift(self):
        subject = Bird(frame=4)
        for _ in range(300):
            advance(subject, [1])
            self.assertAlmostEqual(subject.y, subject.base_y)

    def test_frame_skips_still_update_height(self):
        subject = advance(Bird(frame=4), [6 / 14 + 50])
        self.assertAlmostEqual(subject.frame, 10)
        self.assertAlmostEqual(subject.y, subject.base_y + 5)

    def test_exact_animation_frame_at_different_fps(self):
        for target_frame in (4, 10):
            total = target_frame / 14
            for fps in (30, 60, 144):
                count = int(total * fps)
                times = [1 / fps] * count + [total - count / fps]
                subject = advance(Bird(frame=0), times)
                with self.subTest(target=target_frame, fps=fps):
                    self.assertEqual(int(subject.frame), target_frame)

    def test_output_rects_inside_image(self):
        self.assertEqual(len(bird.FRAME_RECTS), 14)
        for x, y, w, h in bird.FRAME_RECTS:
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + w, 918)
            self.assertLessEqual(y + h, 506)

    def test_source_alpha_is_preserved_by_frame_rects(self):
        # SDL 이미지만 디코딩한다. 캔버스·창·렌더러를 만들지 않는다.
        from sdl2 import SDL_ConvertSurfaceFormat, SDL_FreeSurface, SDL_PIXELFORMAT_RGBA32
        from sdl2.sdlimage import IMG_Load
        source = IMG_Load(str(bird.Path(bird.__file__).with_name('bird_animation.png')).encode())
        self.assertTrue(source)
        converted = None
        try:
            converted = SDL_ConvertSurfaceFormat(source, SDL_PIXELFORMAT_RGBA32, 0)
            self.assertTrue(converted)
            surface = converted.contents
            pixels = ctypes.string_at(surface.pixels, surface.pitch * surface.h)
            total = sum(pixels[y * surface.pitch + x * 4 + 3] > 0
                        for y in range(surface.h) for x in range(surface.w))
            covered = 0
            for x, bottom, w, h in bird.FRAME_RECTS:
                top = surface.h - bottom - h
                count = sum(pixels[y * surface.pitch + column * 4 + 3] > 0
                            for y in range(top, top + h) for column in range(x, x + w))
                self.assertGreater(count, 0)
                covered += count
            self.assertEqual(covered, total)
        finally:
            if converted:
                SDL_FreeSurface(converted)
            SDL_FreeSurface(source)

    def test_draw_shares_image_and_flips_with_direction(self):
        image = Mock()
        with patch('bird.load_image', return_value=image) as load:
            Bird(direction=1).draw()
            Bird(direction=-1).draw()
            self.assertEqual(load.call_count, 1)
            self.assertTrue(load.call_args.args[0].endswith('bird_animation.png'))
            self.assertEqual(image.clip_composite_draw.call_args_list[0].args[5], '')
            self.assertEqual(image.clip_composite_draw.call_args_list[1].args[5], 'h')

    def test_all_drawings_preserve_ratio_and_fit_boundary_box(self):
        Bird.image = Mock()
        for frame in range(14):
            for direction in (-1, 1):
                subject = Bird(frame=frame, direction=direction)
                subject.draw()
                args = Bird.image.clip_composite_draw.call_args.args
                x, y, width, height = args[6:]
                self.assertAlmostEqual(width / height, args[2] / args[3])
                self.assertGreaterEqual(x - width / 2, subject.x - bird.DRAW_WIDTH / 2)
                self.assertLessEqual(x + width / 2, subject.x + bird.DRAW_WIDTH / 2)
                self.assertGreaterEqual(y - height / 2, subject.y - bird.DRAW_HEIGHT / 2)
                self.assertLessEqual(y + height / 2, subject.y + bird.DRAW_HEIGHT / 2)


class IntegrationTests(unittest.TestCase):
    def tearDown(self):
        play_mode.finish()

    @patch('play_mode.get_canvas_height', return_value=600)
    @patch('play_mode.get_canvas_width', return_value=1600)
    @patch('play_mode.Grass')
    @patch('play_mode.Boy')
    def test_reinitialization_keeps_exactly_ten(self, *_):
        for _ in range(3):
            play_mode.init()
            actual = [o for layer in game_world.world for o in layer if isinstance(o, Bird)]
            self.assertEqual(len(actual), 10)
            self.assertEqual(len(play_mode.birds), 10)
            self.assertEqual(len({id(o) for o in actual}), 10)
            self.assertGreater(len({o.y for o in actual}), 1)
            self.assertEqual({o.direction for o in actual}, {-1, 1})
            for o in actual:
                for dt in (1 / 30, 1 / 144, 10):
                    advance(o, [dt])
                    self.assertGreaterEqual(o.x - bird.DRAW_WIDTH / 2, -1e-6)
                    self.assertLessEqual(o.x + bird.DRAW_WIDTH / 2, 1600 + 1e-6)
                    self.assertGreaterEqual(o.y - bird.DRAW_HEIGHT / 2, 0)
                    self.assertLessEqual(o.y + bird.DRAW_HEIGHT / 2, 600)

    def test_finish_clears_birds_and_resources(self):
        subject = Bird()
        game_world.add_oject(subject)
        play_mode.birds.append(subject)
        Bird.image = Mock()
        play_mode.finish()
        self.assertFalse(play_mode.birds)
        self.assertTrue(all(not layer for layer in game_world.world))
        self.assertIsNone(Bird.image)

    def test_escape_and_close_request_quit(self):
        for event in (SimpleNamespace(type=play_mode.SDL_QUIT),
                      SimpleNamespace(type=play_mode.SDL_KEYDOWN, key=play_mode.SDLK_ESCAPE)):
            with patch('play_mode.get_events', return_value=[event]), patch('game_framework.quit') as quit_:
                play_mode.handle_events()
                quit_.assert_called_once()

    def test_framework_uses_current_monotonic_delta(self):
        seen = []
        mode = Mock()
        def update():
            seen.append(game_framework.frame_time)
            if len(seen) == 3:
                game_framework.quit()
        mode.update.side_effect = update
        with patch('game_framework.time.perf_counter', side_effect=[100, 100.01, 100.03, 100.06]):
            game_framework.run(mode)
        for actual, expected in zip(seen, (0.01, 0.02, 0.03)):
            self.assertAlmostEqual(actual, expected)
        mode.finish.assert_called_once()


if __name__ == '__main__':
    unittest.main()
