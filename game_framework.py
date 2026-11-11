import time
running = False
stack = []


def change_mode(mode):
    if stack:
        stack.pop().finish()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack.pop().finish()
    if stack:
        stack[-1].resume()
    else:
        quit()


def quit():
    global running
    running = False

frame_time = 0.0

def run(start_mode):
    global running, stack, frame_time
    running = True
    stack = [start_mode]
    frame_time = 0.0
    try:
        start_mode.init()
        current_time = time.perf_counter()
        while running:
            next_time = time.perf_counter()
            frame_time = next_time - current_time
            current_time = next_time
            stack[-1].handle_events()
            if not running:
                break
            stack[-1].update()
            stack[-1].render()

    finally:
        while stack:
            stack.pop().finish()
        running = False
