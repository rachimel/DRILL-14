from pico2d import *
import game_world
import game_framework
from boy import Boy
from grass import Grass
from bird import Bird, BIRD_COUNT, DRAW_WIDTH, FRAMES_PER_FLAP

boy = None
birds = []


def handle_events():


    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        else:
            boy.handle_event(event)


def init():
    global boy, birds

    boy = Boy()
    game_world.add_oject(boy)

    canvas_width = get_canvas_width()
    canvas_height = get_canvas_height()
    birds = [
        Bird(x=DRAW_WIDTH / 2 + (canvas_width - DRAW_WIDTH) * (i + 0.5) / BIRD_COUNT,
             y=canvas_height * (0.38 + 0.12 * (i % 4)),
             direction=1 if i % 2 == 0 else -1,
             frame=FRAMES_PER_FLAP * i / BIRD_COUNT,
             canvas_width=canvas_width, canvas_height=canvas_height)
        for i in range(BIRD_COUNT)
    ]
    for bird in birds:
        game_world.add_oject(bird)

    grass = Grass()
    game_world.add_oject(grass, 0)


def pause():
    boy.pause()


def resume():
    pass


def finish():
    global boy, birds
    game_world.clear()
    boy = None
birds = []


def update():
    game_world.update()

def render():
    clear_canvas()
    game_world.render()
    update_canvas()









