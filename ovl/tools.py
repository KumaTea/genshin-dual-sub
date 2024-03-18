from ovl.init import pygame
from ovl.session import rect, font, ruby_font


def rebuild_ruby(orig_text: str, rubies: list[tuple[float, str]]) -> list[tuple[str, str]]:
    # '私は会社員です。', [(0.0, 'わたし'), (3.0, 'かいしゃいん')]

    # int
    rubies = [(int(index), content) for index, content in rubies]
    ruby_dict = {index: content for index, content in rubies}

    split_text = []
    temp_text = ''
    for i in range(len(orig_text)):
        ruby = ruby_dict.get(i, '')
        if ruby:
            if temp_text:
                split_text.append((temp_text, ''))
            split_text.append((orig_text[i], ruby))
            temp_text = ''
        else:
            temp_text += orig_text[i]
    if temp_text:
        split_text.append((temp_text, ''))

    return split_text


def render_ruby(split_text: list[list[str, str]]) -> list[tuple[pygame.Surface, pygame.Rect]]:
    x, _ = rect.topleft
    _, y = rect.center
    text_boxes = []

    # render text and ruby
    for text, ruby in split_text:
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(topleft=(x, y))
        x += text_rect.width
        if ruby:
            ruby_surface = ruby_font.render(ruby, True, (255, 255, 255))
            # centered at x of text_rect
            ruby_rect = ruby_surface.get_rect(centerx=text_rect.centerx, bottom=text_rect.top)
            text_boxes.append((ruby_surface, ruby_rect))
        text_boxes.append((text_surface, text_rect))

    # now text_boxes elements are aligned left
    # make it center
    offset = (rect.width - x) / 2
    for text_surface, text_rect in text_boxes:
        text_rect.move_ip(offset, 0)

    return text_boxes


def draw(screen: pygame.Surface, ruby_text: list[list[str, str]]) -> pygame.Surface:
    text_boxes = render_ruby(ruby_text)

    # draw text and ruby
    for text_surface, text_rect in text_boxes:
        screen.blit(text_surface, text_rect)

    return screen
