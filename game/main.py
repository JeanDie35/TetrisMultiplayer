from game import Game
from frames import Welcome, Settings, GameOver, Frame
from json_reader import JSONReader
from client import Client
import pygame
pygame.init()
pygame.font.init()

json_reader = JSONReader()

FPS = json_reader.config["FPS"]
BG_COLOR = json_reader.config["bg_color"]

clock = pygame.time.Clock()


"""""
Careful:
 I used numpy to store the position of every block. Although, axis 1 in numpy arrays is the y axis, axis 2 is the x axis
 The numpy array that stores the position of the blocks is called grid, there can be 3 different values:
    0 is when there's no block
    1 is for the blocks that you can move
    2-8 is for the bdlocks that you can't move anymore, the number depends on the color
"""""


running = True

pygame.display.set_caption(json_reader.config["title"])
screen_size = (json_reader.config["game_screen_width"], json_reader.config["game_screen_height"])
screen = pygame.display.set_mode(screen_size)

client = Client(json_reader)

# we try to connect to the server
client_key = client.connect()
# if the client is not already connected we stop the program
if client_key is None:
    running = False
    pygame.quit()

else:
    # creating the frames
    welcome = Welcome(screen, json_reader, client)
    game = Game(screen, json_reader)
    settings = Settings(screen, json_reader, client)
    game_over = GameOver(screen, json_reader, client)

    active_frame = welcome
    next_frame = None

    frames = {
        "game": game,
        "welcome": welcome,
        "settings": settings,
        "game_over": game_over
    }

    while running:

        # hiding the old widgets
        screen.fill(BG_COLOR)

        # handles all the transitions that are triggered by the code
        internal_result = active_frame.update()

        # when the client has reveived the message from the server that the game is starting, we start the game
        if "GAME_STARTED" in client.responses and client.responses["GAME_STARTED"] is not None:
            internal_result = "game"

        if internal_result is not None:
            next_frame = frames[internal_result]

            if next_frame == game_over and active_frame == game:

                # when the game is over and the server needs the score and the name
                client.send_request({"type": "POST", "name": "GAME_OVER_DATA", "args": {"score": game.score, "name": settings.active_profile["name"]}})

                if game.status is not None:
                    # sends a request to the server saying that the game is over
                    client.send_request({"type": "EVENT", "name": "GAME_OVER", "args": game.status})

                # saving the score
                settings.active_profile["best_score"] = max(game.score, settings.active_profile["best_score"])
                client.send_request({"type": "TRANSFER", "name": "CHANGE_PROFILE", "args": {
                    "data": {"key": settings.active_profile_key, "profile": settings.active_profile}, "receivers": "all"}})

                game_over.game_time = game.chrono.get_time()
                game.reset()

                # waits for the server to send the results
                while "RESULTS" not in client.responses or client.responses["RESULTS"] is None:
                    pass

                # when the server sent the result, the game isn't over anymore
                client.responses["GAME_OVER"] = None
                # creating the rank displays with the results
                game_over.create_rank_displays(client.responses["RESULTS"])
                client.responses["RESULTS"] = None

            elif next_frame == game:
                game.start_game(client, settings.active_profile)

            active_frame = next_frame

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                # sending a request to the server saying that we want to close the conn
                client.send_request({"type": "EVENT", "name": "CLOSE", "args": None})
                pygame.quit()
                running = False

            # handles the transitions that are triggered by the user
            external_result = active_frame.handle_events(event)

            if external_result is not None:

                if isinstance(external_result, str):
                    next_frame = frames[external_result]

                # if the result is directly a Frame
                elif isinstance(external_result, Frame):
                    next_frame = external_result


                active_frame = next_frame

        clock.tick(FPS)
