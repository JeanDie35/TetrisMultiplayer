import pygame
from json_reader import JSONReader
from ui import RankDisplay, Entry, Selector, KeySelector, assets, ProfileWidget

pygame.init()

# parent class for all the different frames there's
class Frame:

    def __init__(self, screen: pygame.surface.Surface,json_reader):
        self.screen = screen
        self.json_reader =json_reader
        self.font = pygame.font.SysFont(json_reader.config["font_name"],json_reader.config["font_size"])

    def update(self):
        return None

    def handle_events(self, event):
        return None



# thr frame that will be displayed when you launch the app
class Welcome(Frame):

    def __init__(self, screen: pygame.surface.Surface, json_reader, client):
        super().__init__(screen, json_reader)

        self.client = client

        # creating grid var for the buttons' rect because it'll be needed when cheking if the mouse is on the button
        self.play_rect = assets["play"].get_rect()
        self.play_rect.x, self.play_rect.y = (self.screen.get_width() // 2 - assets["play"].get_width() // 2,
                                              3 * self.screen.get_height() // 4 - assets["play"].get_width() // 2)

        self.settings_rect = assets["settings"].get_rect()
        self.settings_rect.x, self.settings_rect.y = (0, 0)

        self.mode_selector = Selector(self.screen, self.json_reader, (200, 50), self.json_reader.config['game_modes'],
                                      (self.screen.get_width() // 2, 5 * self.screen.get_height() // 6), "center")

    def update(self):
        self.screen.blit(assets["logo"], (self.screen.get_width() // 2 - assets["logo"].get_width() // 2,
                                               self.screen.get_height() // 4 - assets["logo"].get_width() // 2))

        self.screen.blit(assets["play"], self.play_rect)

        self.screen.blit(assets["settings"], self.settings_rect)

        self.mode_selector.render()

        # when the client has reveived the message from the server that the game is starting, we start the game
        if "GAME_STARTED" in self.client.responses and self.client.responses["GAME_STARTED"] is not None:
            return "game"

    def handle_events(self, event: pygame.event.Event) -> str | None:
        self.mode_selector.handle_events(event)

        if event.type == pygame.MOUSEBUTTONDOWN:

            if self.settings_rect.collidepoint(event.pos):
                return "settings"

            elif self.play_rect.collidepoint(event.pos):
                # if the user tries to start the game, we don't change the active frame, but we send a request to the server
                self.client.send_request({"type": "EVENT", "name": "START", "args": self.mode_selector.get_selected_text()})

        return None


# the frame where you can change the key binds
class Settings(Frame):

    def __init__(self, screen: pygame.surface.Surface, json_reader, client):
        super().__init__(screen, json_reader)
        self.client = client

        # gets the profiles
        self.profiles = self.client.get_profiles()
        self.profile_widgets = []

        # by default, the active_profile is the first one
        self.active_profile_key = list(self.profiles.keys())[0]
        self.active_profile = self.profiles[self.active_profile_key]

        # creating a var for the buttons' rect because it'll be needed when cheking if the mouse is on the button
        self.back_rect = assets["back"].get_rect()
        self.back_rect.x, self.back_rect.y = (0, 0)

        self.add_rect = assets["add"].get_rect()
        self.add_rect.x, self.add_rect.y = (self.screen.get_width() - self.json_reader.config["offset_add_profile_button"] - self.add_rect.w , 60)

        self.profile_entry = Entry(screen, json_reader, (350, 50), (self.json_reader.config["offset_profile_entry"], 60))


    def update(self):
        # updates the profiles if there was a change
        if "PROFILES" in self.client.responses:
            self.profiles = self.client.responses["PROFILES"]
            # by default, the active_profile is the first one
            self.active_profile_key = list(self.profiles.keys())[0]
            self.active_profile = self.profiles[self.active_profile_key]

        self.screen.fill(self.json_reader.config["bg_color"])

        # updates all the profile widgets
        for i in range(len(self.profiles)):
            profile_widget = ProfileWidget(self.screen, self.json_reader, list(self.profiles.values())[i]["name"],
                                           list(self.profiles.keys())[i], (400, 60), (self.screen.get_width() // 2, self.json_reader.config["offset_first_profile_widget"] + i * (self.json_reader.config["space_profile_widgets"] + 60)), side="center")
            profile_widget.render()
            self.profile_widgets.append(profile_widget)

        self.screen.blit(assets["back"], self.back_rect)

        active_profile_text = self.font.render("Active profile: " + str(self.active_profile["name"]), 1, self.json_reader.config["colors"]["white"])
        self.screen.blit(active_profile_text, (self.screen.get_width() // 2 - active_profile_text.get_width() // 2, 20))

        self.profile_entry.render()
        self.screen.blit(assets["add"], self.add_rect)

        profile_text = self.font.render("Profiles: ", 1, self.json_reader.config["colors"]["white"])
        self.screen.blit(profile_text, (self.json_reader.config["offset_profile_text"], 125))


    def get_key_binds(self) -> dict:
        """""
        returns the chosen key binds
        """""
        return self.active_profile["key_binds"]

    def change_active_profile(self, key):
        self.active_profile_key = key
        self.active_profile = self.profiles[key]

    def add_profile(self, name: str):
        self.client.send_request({"type": "TRANSFER", "name": "ADD_PROFILE", "receivers" : "all", "args": name})

    def delete_profile(self, key):
        self.client.send_request({"type": "TRANSFER", "name": "DELETE_PROFILE", "receivers" : "all", "args": key})


    def handle_events(self, event: pygame.event.Event) -> str | None:
        self.profile_entry.handle_events(event)

        if event.type == pygame.MOUSEBUTTONDOWN:

            if self.back_rect.collidepoint(event.pos):
                return "welcome"

            if self.add_rect.collidepoint(event.pos):
                if self.profile_entry != "" and self.profile_entry.str not in self.profiles:
                    # we add a profile with the text in the entry
                    self.add_profile(self.profile_entry.str)
                    # clears the entry
                    self.profile_entry.str = ""

        for profile_widgets in self.profile_widgets:
            result = profile_widgets.handle_events(event)

            if result is not None:
                if "MODIFY" in result:
                    pass

                elif "DELETE" in result:
                    self.delete_profile(result["DELETE"])

                elif "CHOOSE" in result:
                    self.change_active_profile(result["CHOOSE"])

        return None



class Profile(Frame):

    def __init__(self, screen: pygame.surface.Surface, json_reader: JSONReader, client, profile: dict, profile_key):
        super().__init__(screen, json_reader)
        self.client = client

        self.profile = profile
        self.profile_key = profile_key

        # creating a var for the buttons' rect because it'll be needed when cheking if the mouse is on the button
        self.back_rect = assets["back"].get_rect()
        self.back_rect.x, self.back_rect.y = (0, 0)

        self.key_selectors = self.update_key_selectors()

    def update(self):

        self.key_selectors = self.update_key_selectors()

        # for each key selector
        for i in range(len(list(self.key_selectors.keys()))):
            # we display grid text saying what movement is the key selector bound to
            key_text = self.font.render(list(self.key_selectors.keys())[i], 1,
                                        self.json_reader.config["colors"]["white"])
            self.screen.blit(key_text, (self.screen.get_width() // 2 - key_text.get_width() // 2,
                                        self.json_reader.config["offset_first_key_selector"] + i *
                                        self.json_reader.config["offset_key_selector"]))

            # displays the key selector
            self.key_selectors[list(self.key_selectors.keys())[i]].render()

        self.screen.blit(assets["back"], self.back_rect)

    def send_changes(self):
        """""
        after the user modified the profile's data we send it to the server
        """""

        self.client.send_request(self.client.send_request({"type": "POST", "name": "CHANGE_PROFILE", "args": {
            "data": {"key": self.profile_key, "profile": self.profile}, "receiver": "all"}}))

    def update_key_selectors(self) -> dict:
        # creating a dict to store all the key selectors depending on what key are they bound to
        key_selectors = {}
        for i in range(len(self.profile["key_binds"])):
            movement = list(self.profile["key_binds"].keys())[i]
            key_selectors[movement] = KeySelector(self.screen, self.profile["key_binds"][movement],
                                                       self.json_reader.config["offset_first_key_selector"] + i * self.json_reader.config["offset_key_selector"] + self.json_reader.config["space_text_key_selector"], self.json_reader)
        return key_selectors

    def handle_events(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            for k_selector in self.key_selectors.items():
                # if grid key selector is selected, its key will be the pressed one
                if k_selector[1].selected:
                    k_selector[1].change_key(event.key)


        elif event.type == pygame.MOUSEBUTTONDOWN:

            # if the user clicks on grid key selector, it becomes selected
            for k_selector in self.key_selectors.items():
                if k_selector[1].rect.collidepoint(event.pos):
                    k_selector[1].selected = True
                else:
                    k_selector[1].selected = False

            if self.back_rect.collidepoint(event.pos):
                return "settings"

        return None


# frame when the game is over
class GameOver(Frame):

    def __init__(self, screen: pygame.surface.Surface, json_reader, client):
        super().__init__(screen, json_reader)
        self.client = client

        # creating a var for the buttons' rect because it'll be needed when cheking if the mouse is on the button
        self.back_rect = assets["back"].get_rect()
        self.back_rect.x, self.back_rect.y = (0, 0)

        self.rank_displays = []

    def update(self):
        for i in range(len(self.rank_displays)):
            self.rank_displays[i].render()

        self.screen.blit(assets["back"], self.back_rect)

        self.screen.blit(assets["victory"],
                         (self.screen.get_width() // 2 - assets["victory"].get_width() // 2, 20))

    def handle_events(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_rect.collidepoint(event.pos):
                return "welcome"

        return None

    def create_rank_displays(self, results: list):
        rank_displays = []
        for i in range(len(results)):
            if i + 1 <= self.json_reader.config["max_rank_display"]:
                rank_display = RankDisplay(self.screen, self.json_reader, i + 1, list(results[i].keys())[0], list(results[i].values())[0],
                                           (self.screen.get_width() // 2, self.json_reader.config["offset_first_rank_display"] + self.json_reader.config["space_rank_displays"] * i), "center")
                self.rank_displays.append(rank_display)

