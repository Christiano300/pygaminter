from time import time
from typing import overload, Callable, Union
import pygame
pygame.font.init()


def lerp(a, b, t): return a * (1 - t) + b * t


def lighter(color: int, amount: float) -> pygame:
    r, g, b = color.r, color.g, color.b
    return pygame.Color(int(lerp(r, 255, amount)), int(lerp(g, 255, amount)), int(lerp(b, 255, amount)))


def darker(color: int, amount: float) -> pygame:
    r, g, b = color.r, color.g, color.b
    return pygame.Color(int(lerp(0, r, amount)), int(lerp(0, g, amount)), int(lerp(0, b, amount)))


def get_color(color: pygame.Color | int | str, default: int) -> int:
    if isinstance(color, (list, tuple)) and len(color) == 3:
        return pygame.Color(*color)
    elif isinstance(color, int):
        try:
            return pygame.Color(color << 8 | 255)
        except ValueError:
            return pygame.Color(color)
    elif isinstance(color, str):
        try:
            return pygame.Color(color)
        except ValueError or UnicodeEncodeError:
            return pygame.Color(default)
    elif isinstance(color, pygame.Color):
        return color
    else:
        return pygame.Color(default)


def get_font(font: pygame.font.Font | str):
    if isinstance(font, pygame.font.Font):
        return font
    elif isinstance(font, str) and "_" in font and font.count("_") == 1:
        name, rest = font.split("_")
        for i, l in enumerate(rest):
            if not l.isdecimal():
                break
        size = rest[:i+1]
        bold = True if "b" in rest else False
        italic = True if "i" in rest else False
        return pygame.font.SysFont(name, size, bold, italic)
    else:
        return None


class Widget(pygame.sprite.Sprite):
    group = pygame.sprite.Group()

    def __init__(self, rect: pygame.Rect, text: str):
        pygame.sprite.Sprite.__init__(self)
        if isinstance(rect, pygame.Rect):
            self.rect = rect
        else:
            self.rect = pygame.Rect(rect)
        self.text = text
        self.image = pygame.Surface(self.rect.size)
        Widget.group.add(self)

    def draw(self, surface_dest: pygame.Surface):
        surface_dest.blit(self.image, self.rect)

    def render(self):
        pass

    @overload
    def config(self, rect: pygame.Rect, text: str, color: pygame.Color, command: Callable[[], None], active: bool, textcolor: pygame.Color, font: pygame.font.Font) -> Union[dict, None]:
        ...

    def config(self, **kwargs):
        if kwargs:
            for k, v in kwargs.items():
                if k in "color":
                    self.__setattr__(k, get_color(v, 0xf0f0f0))
                elif k == "textcolor":
                    self.__setattr__(k, get_color(v, 0x000000))
                else:
                    self.__setattr__(k, v)
            self.render()
        else:
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class Button(Widget):
    group = pygame.sprite.Group()

    def __init__(self, rect: pygame.Rect, text: str = "", color: pygame.Color = 0xf0f0f0,
                 command: Callable[[], None] = None, active: bool = True,
                 textcolor: pygame.Color = 0x000000, font: pygame.font.Font = None):
        super().__init__(rect, text)
        Button.group.add(self)
        self.command = command
        self.color = get_color(color, 0xf0f0f0)
        self.textcolor = get_color(textcolor, 0x000000)
        self.active = active
        self.pressed = False
        self.font = get_font(font)
        self.render()

    def render(self):
        if not self.font:
            self.font = pygame.font.Font(None, self.rect.height)
        if self.pressed:
            self.image.fill(lighter(self.color, .6))
            pygame.draw.rect(self.image, darker(self.color, .7),
                             (0, 0, self.rect.width - 1, self.rect.height - 1))
            pygame.draw.rect(self.image, darker(self.color, .9),
                             (1, 1, self.rect.width - 2, self.rect.height - 2))
            pygame.draw.rect(self.image, darker(self.color, .6),
                             (1, 1, self.rect.width - 3, self.rect.height - 3))
            pygame.draw.rect(self.image, self.color,
                             (2, 2, self.rect.width - 4, self.rect.height - 4))
            self.image.blit(self.font.render(self.text, True,
                            self.textcolor), (4, self.rect.height // 6 + 1))
        else:
            self.image.fill(darker(self.color, .6))
            pygame.draw.rect(self.image, lighter(self.color, .6),
                             (0, 0, self.rect.width - 1, self.rect.height - 1))
            pygame.draw.rect(self.image, darker(self.color, .7),
                             (1, 1, self.rect.width - 2, self.rect.height - 2))
            pygame.draw.rect(self.image, darker(self.color, .9),
                             (1, 1, self.rect.width - 3, self.rect.height - 3))
            pygame.draw.rect(self.image, self.color,
                             (2, 2, self.rect.width - 4, self.rect.height - 4))
            color = self.textcolor if self.active else 0x6d6d6dff
            self.image.blit(self.font.render(self.text, True,
                            color), (3, self.rect.height // 6))

    def update(self, mousepos: tuple, pressed: bool):
        if pressed:
            if self.active and pygame.Rect.collidepoint(self.rect, mousepos):
                self.pressed = True
                self.render()
                self.command() if self.command else 0
        elif self.pressed:
            self.pressed = False
            self.render()


class EntryGroup(pygame.sprite.Group):
    def __init__(self, *sprites):
        super().__init__(self, *sprites)
        self.focus_entry = None

    def focused(self):
        return bool(self.focus_entry)

    def key_action(self, event):
        if event.key == pygame.K_BACKSLASH:
            # delete last character
            self.focus_entry.text = self.focus_entry.text[:-1]
            self.focus_entry.render(True)
        elif event.key == pygame.K_ESCAPE:
            # unfocus entries
            self.focus_entry.focused = False
            self.focus_entry.render(False)
            self.focus_entry = None
        else:
            # add event.unicode to focused entry
            self.focus_entry.text += event.unicode
            self.focus_entry.render(False)

    def mouse_pressed(self, mousepos):
        for i in self.sprites():
            if pygame.Rect.collidepoint(i.rect, mousepos):
                self.focus_entry = i
                i.focused = True
                i.timerstart = time()
                break
            else:
                i.focused = False


class Entry(Widget):
    group = EntryGroup()

    def __init__(self, rect: pygame.Rect, prompt: str = "", allow_empty: bool = True,
                 color: pygame.Color = 0xffffff, textcolor: pygame.Color = 0x000000,
                 active: bool = True, font: pygame.font.Font = None):
        Entry.group.add(self)
        super().__init__(rect, "")
        self.prompt = prompt
        self.allow_empty = allow_empty
        self.color = get_color(color, 0xffffff)
        self.textcolor = get_color(textcolor, 0x000000)
        self.active = active
        self.focused = False
        self.render()

    def render(self, full: bool = True):
        if not self.font:
            self.font = pygame.font.Font(None, self.rect.height)
        w = self.font.size(self.text)[0]
        x = min(self.rect.width - x - 10, 0)
        

    def draw(self, surface_dest: pygame.Surface):
        super().draw(surface_dest)

    def get(self): return self.text
