"""Tiny drawing helpers shared by all characters."""


def ellipse(d, cx, cy, rx, ry, fill, outline=None, width=0):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=fill, outline=outline, width=width)
