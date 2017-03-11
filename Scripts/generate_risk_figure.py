#!/usr/bin/python
from __future__ import division
from colorsys import hls_to_rgb
from PIL import Image, ImageDraw, ImageFont

# Generate a chart of the bivariate risk colouring scheme for the dissertation.
RISK_LEVELS = [(0.167, 0.720), (0.125, 0.450), (0.083, 0.500), (0.0, 0.500), (0.0, 0.250)]
RISK_TEXTS = ["Low", "Moderate", "Considerable", "High", "Very High"]
BLOCK_HEIGHT = 40
SATURATION_LEVELS = 256

base_image = Image.open("./base.png")
chart_image = Image.new("RGB", (SATURATION_LEVELS, BLOCK_HEIGHT * len(RISK_LEVELS)))
chart_image_pixels = chart_image.load()
for j in range(len(RISK_LEVELS)):
    for i in range(SATURATION_LEVELS):
        x = i
        y = j * BLOCK_HEIGHT
        for h in range(BLOCK_HEIGHT):
            chart_image_pixels[x, y + h] = tuple(map(lambda x: int(round(x * 255)), hls_to_rgb(RISK_LEVELS[j][0], RISK_LEVELS[j][1], i / 255)))

text_draw = ImageDraw.Draw(chart_image)
text_font = ImageFont.truetype("./helvetica-normal.ttf", 13)
height = BLOCK_HEIGHT / 4 * 2.7
for j in range(len(RISK_LEVELS)):
    text_draw.text((10, height), RISK_TEXTS[j], (0, 255, 42), font=text_font)
    height += BLOCK_HEIGHT

text_draw.text((10, 2), "Low Static Risk              High Static Risk", (0, 0, 0), font=text_font)

chart_image = Image.blend(base_image, chart_image, 0.9)
chart_image.save('../Dissertation/images/final-colour-scheme.png')
