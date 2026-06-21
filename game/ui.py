import pygame

pygame.init()
from json_reader import JSONReader

# all the keys that can't work with chr() or ord() function but we still want to be able to bind them
special_keys = {
    pygame.K_RIGHT: "right arrow",
    pygame.K_LEFT: "left arrow",
    pygame.K_UP: "up arrow",
    pygame.K_DOWN: "down arrow"
}

assets = {
        "logo": pygame.image.load("assets/logo.png"),
        "play": pygame.image.load("assets/play_button.png"),
        "settings": pygame.image.load("assets/settings_button.png"),
        "back": pygame.image.load("assets/back_button.png"),
        "victory": pygame.image.load("assets/victory.png"),
        "connection": pygame.image.load("assets/connection_button.png"),
        "rank1": pygame.image.load("assets/gold_rank.png"),
        "rank2": pygame.image.load("assets/silver_rank.png"),
        "rank3": pygame.image.load("assets/bronze_rank.png"),
        "no_rank": pygame.image.load("assets/no_rank.png"),
        "add": pygame.image.load("assets/plus_button.png"),
        "delete": pygame.image.load("assets/delete_button.png"),
        "modify": pygame.image.load("assets/modify_button.png"),
        "choose": pygame.image.load("assets/choose_button.png"),
}


class Shape:

    def __init__(self, screen: pygame.surface.Surface, json_reader: JSONReader, shape: str, size: tuple, pos: tuple, color: str, side: str, radius : int):
        self.screen = screen
        self.json_reader = json_reader
        self.shape = shape
        self.rect = pygame.Rect(pos, size)
        self.color = self.json_reader.config["colors"][color]
        self.side = side

        self.font = pygame.font.SysFont(self.json_reader.config["font_name"], self.json_reader.config["font_size"])

        self.all_shapes = {
            "rect": lambda: pygame.draw.rect(self.screen, self.color, self.rect),
            "circle": lambda: pygame.draw.circle(self.screen, self.color, (self.rect.x, self.rect.y), radius),
            "line": lambda: pygame.draw.line(self.screen, self.color, self.rect,
                                             (self.rect.x + size[0], self.rect.y + self.rect.h)),
            "rounded_rect": lambda: self.draw_rounded_rectangle(self.screen, self.color, self.rect, radius),
            "none": lambda: self.draw_nothing()
        }

        setattr(self.rect, self.side, pos)


    def draw_rounded_rectangle(self, screen: pygame.Surface, color: tuple, rect: pygame.Rect, radius: int):
        x, y, width, height = rect

        pygame.draw.rect(screen, color, (x + radius, y, width - 2 * radius, height))
        pygame.draw.rect(screen, color, (x, y + radius, width, height - 2 * radius))

        pygame.draw.circle(screen, color, (x + radius, y + radius,), radius)
        pygame.draw.circle(screen, color, (x + width - radius, y + radius,), radius)
        pygame.draw.circle(screen, color, (x + radius, y + height - radius), radius)
        pygame.draw.circle(screen, color, (x + width - radius, y + height - radius,), radius)


    def draw_rectange(self, screen: pygame.Surface, color: tuple, rect: pygame.Rect):
        pygame.draw.rect(screen, color, rect)

    def draw_circle(self, screen: pygame.Surface, color: tuple, rect: pygame.Rect, radius: int):
        pygame.draw.circle(screen, color, rect, radius)

    def draw_line(self, screen: pygame.Surface, color: tuple, start_pos: tuple, end_pos: tuple, width: int =1):
        pygame.draw.line(screen, color, start_pos, end_pos, width)

    def draw_nothing(self):
        pass

    def render(self):
        self.all_shapes[self.shape]()


class ProfileWidget(Shape):

    def __init__(self, screen: pygame.surface.Surface, json_reader: JSONReader, shape: str, size: tuple, pos: tuple, color: str, profile_name, profile_key, side: str = "topleft", radius : int = 1):
        super().__init__(screen, json_reader, shape, size, pos, color, side, radius)

        self.profile_name = profile_name
        self.profile_key = profile_key

        self.delete_rect = assets["delete"].get_rect()
        self.delete_rect.x, self.delete_rect.y = (self.rect.x + self.rect.w - self.json_reader.config["offset_delete_button"] - self.delete_rect.w , self.rect.y + self.rect.h // 2 - self.delete_rect.h // 2)

        self.modify_rect = assets["modify"].get_rect()
        self.modify_rect.x, self.modify_rect.y = (self.rect.x + self.rect.w - self.modify_rect.w - self.json_reader.config["offset_delete_button"] - self.delete_rect.w - self.json_reader.config["space_delete_button_modify_button"], self.rect.y + self.rect.h // 2 - self.modify_rect.h // 2)

        self.choose_rect = assets["choose"].get_rect()
        self.choose_rect.x, self.choose_rect.y = (self.rect.x + self.rect.w - self.json_reader.config["offset_delete_button"] - self.delete_rect.w - self.json_reader.config["space_delete_button_modify_button"] - self.modify_rect.w - self.json_reader.config["space_modify_button_choose_button"] - self.choose_rect.w, self.rect.y + self.rect.h // 2 - self.choose_rect.h // 2)

    def render(self):
        super().render()

        profile_name_text = self.font.render(self.profile_name, 1, self.json_reader.config["colors"]["black"])
        self.screen.blit(profile_name_text, (self.rect.x + self.json_reader.config["offset_profile_name"], self.rect.y + self.rect.h // 2 - profile_name_text.get_height() // 2))

        self.screen.blit(assets["delete"], self.delete_rect)

        self.screen.blit(assets["modify"], self.modify_rect)

        self.screen.blit(assets["choose"], self.choose_rect)

    def handle_events(self,event: pygame.event.Event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.delete_rect.collidepoint(event.pos):
                return {"DELETE" : self.profile_key}

            elif self.modify_rect.collidepoint(event.pos):
                return {"MODIFY" : self.profile_key}

            elif self.choose_rect.collidepoint(event.pos):
                return {"CHOOSE" : self.profile_key}

        return None


class Entry(Shape):

    def __init__(self, screen: pygame.surface.Surface, json_reader: JSONReader, shape: str, size: tuple, pos: tuple, color: str, side: str = "topleft", radius : int = 1, str: str = ""):
        super().__init__(screen, json_reader, shape, size, pos, color, side, radius)

        self.selected = False

        self.str = str
        self.font = pygame.font.SysFont(self.json_reader.config["font_name"], self.json_reader.config["font_size"])

    def render(self):
        super().render()

        text = self.font.render(self.str, 1, self.json_reader.config["colors"]["white"])
        self.screen.blit(text, (self.rect.x + self.rect.w // 2 - text.get_width() // 2, self.rect.y + self.rect.h // 2 - text.get_height() // 2))

    def handle_events(self,event: pygame.event.Event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.selected = True

        elif event.type == pygame.KEYDOWN and self.selected:
            new_str = None
            keys = pygame.key.get_pressed()
            # formulas to know if the shift key or the capslock key are on.
            maj_pressed = (pygame.key.get_mods() & pygame.KMOD_SHIFT) or (pygame.key.get_mods() & pygame.KMOD_CAPS)

            if event.key in range(self.json_reader.config["first_accepted_letter"], self.json_reader.config["last_accepted_letter"] + 1):
                if maj_pressed:
                    new_str = self.str + chr(event.key - self.json_reader.config["nb_lowercase_to_uppercase"])
                else:
                    new_str = self.str + chr(event.key)

            elif event.key == pygame.K_BACKSPACE:
                new_str = self.str[:-1]

            elif event.key == pygame.K_SPACE:
                new_str =  self.str + " "

            if new_str is not None:
                # check if the text isn't too big
                new_text = self.font.render(new_str, 1, self.json_reader.config["colors"]["black"])
                if new_text.get_width() < self.rect.w:
                    self.str = new_str



class RankDisplay(Shape):

    def __init__(self, screen: pygame.surface.Surface, json_reader: JSONReader, pos: tuple, rank: int, nickname: str, score: int, side: str = "topleft", radius : int = 1):
        super().__init__(screen, json_reader, "none", (0, 0), pos, "white", side, radius) # as the rank display is an image, it doesn't need a shape nor a color nor a size (we use the image's size)

        self.x_offset = self.json_reader.config["offset_rank_nickname"]

        self.rank = rank
        self.nickname = nickname
        self.score = score

        # if the player is on the podium
        if self.rank in range(1, 4):
            key = "rank" + str(self.rank)

        else:
            key = "no_rank"

        self.image = assets[key]
        self.rect = self.image.get_rect()
        setattr(self.rect, side, pos)

    def render(self):
        self.screen.blit(self.image, self.rect)

        rank_text = self.font.render(str(self.rank), 1, self.json_reader.config["colors"]["black"])
        self.screen.blit(rank_text, (self.rect.x + self.x_offset, self.rect.y + self.rect.h // 2 - rank_text.get_height() // 2))

        nickname_text = self.font.render(str(self.nickname), 1, self.json_reader.config["colors"]["black"])
        self.screen.blit(nickname_text, (self.rect.x + self.x_offset + rank_text.get_width() + 10, self.rect.y + self.rect.h // 2 - nickname_text.get_height() // 2))

        score_text = self.font.render(str(self.score), 1, self.json_reader.config["colors"]["black"])
        self.screen.blit(score_text, (self.rect.x + self.rect.w - self.x_offset - score_text.get_width(), self.rect.y + self.rect.h // 2 - score_text.get_height() // 2))


class Selector(Shape):

    def __init__(self, screen: pygame.surface.Surface, json_reader: JSONReader, shape, size: tuple, pos: tuple, color: str, iter: list, side: str = "topleft", radius : int = 1):
        super().__init__(screen, json_reader, shape, size, pos, color, side, radius)

        self.list = iter
        self.counter = 0

    def next_text(self):
        self.counter += 1
        if self.counter >= len(self.list):
            self.counter = 0

    def get_selected_text(self) -> str:
        return self.list[self.counter]

    def render(self):
        super().render()

        text = self.font.render(self.list[self.counter], 1, self.json_reader.config["colors"]["white"])
        self.screen.blit(text, (self.rect.x + self.rect.w // 2 - text.get_width() // 2,
                                    self.rect.y + self.rect.h // 2 - text.get_height() // 2))

    def handle_events(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:

            if self.rect.collidepoint(event.pos):
                self.next_text()

class KeySelector(Shape):

    def __init__(self, screen: pygame.surface.Surface, json_reader: JSONReader, shape, size: tuple, pos: tuple, color: str, nkey: int, side: str = "topleft", radius : int = 1):
        super().__init__(screen, json_reader, shape, size, pos, color, side, radius)

        # the key that it is displaying
        self.nkey = nkey
        self.selected = False
        self.size = (200, 50)

    def render(self):
        """""
        displays the key_selector at its position
        """""

        super().render()

        key_text = self.font.render(self.get_key(self.nkey), 1, self.json_reader.config["colors"]["white"])
        self.screen.blit(key_text, (self.rect.x + self.rect.w // 2 - key_text.get_width() // 2,
                                    self.rect.y + self.rect.h // 2 - key_text.get_height() // 2))

    def change_key(self, nkey: int):
        """""
        changes the nkey by n if possible
        """""
        # if the key isn't valid
        if self.get_key(nkey) is None:
            print("You can't use that key, please enter another one")
        else:
            self.nkey = nkey

    def get_key(self, nkey: int) -> str | None:
        """""
        returns the key name corresponding to the nkey
        """""
        if nkey in special_keys:
            return special_keys[nkey]
        elif nkey in range(self.json_reader.config["first_accepted_letter"], self.json_reader.config["last_accepted_letter"] + 1):
            return chr(nkey)

        return None
