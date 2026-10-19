# ui.py
# Drawing helpers shared by main.py and report.py:
# the gradient background, rounded boxes (panels), pills and text.

import pygame
from settings import SCREEN, BACKGROUND, BACKGROUND_BOTTOM, PANEL, PANEL_EDGE


def make_background():
    # Build the gradient once, before the game loop, then copy it each frame.
    # Each row of pixels gets a colour between the top and bottom colours.
    surface = pygame.Surface(SCREEN)
    height = SCREEN[1]
    for y in range(height):
        colour = blend(BACKGROUND, BACKGROUND_BOTTOM, y / float(height))
        pygame.draw.line(surface, colour, (0, y), (SCREEN[0], y))
    return surface


def blend(first, second, t):
    # Mix two colours. t = 0 gives first, t = 1 gives second.
    red = int(first[0] + (second[0] - first[0]) * t)
    green = int(first[1] + (second[1] - first[1]) * t)
    blue = int(first[2] + (second[2] - first[2]) * t)
    return (red, green, blue)


def draw_panel(screen, rect, colour=PANEL, edge=PANEL_EDGE):
    # A box with rounded corners and a thin border
    pygame.draw.rect(screen, colour, rect, border_radius=14)
    pygame.draw.rect(screen, edge, rect, 2, border_radius=14)


def draw_pill(screen, font, text, text_colour, fill, centre):
    # A rounded label, centred on a point. Returns its rectangle.
    surface = font.render(text, True, text_colour)
    rect = surface.get_rect(center=centre).inflate(36, 16)
    pygame.draw.rect(screen, fill, rect, border_radius=18)
    screen.blit(surface, surface.get_rect(center=rect.center))
    return rect


def draw_text(screen, font, text, colour, centre):
    # Text centred on a point
    surface = font.render(text, True, colour)
    screen.blit(surface, surface.get_rect(center=centre))


def draw_text_left(screen, font, text, colour, topleft):
    # Text with its top-left corner at a point
    surface = font.render(text, True, colour)
    screen.blit(surface, topleft)


def draw_text_right(screen, font, text, colour, topright):
    # Text with its top-right corner at a point
    surface = font.render(text, True, colour)
    screen.blit(surface, surface.get_rect(topright=topright))
