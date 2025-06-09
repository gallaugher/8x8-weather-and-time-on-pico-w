# 8x8-weather-and-time-on-pico-w
Shows time &amp; weather scrolling using open weather API and an 8x8 neopixel display.

Color of text will change depending on temperature:

    if temp >= 80: return 0xFF2200  # Bright red
    if temp >= 70: return 0xFFAA00  # Orange
    if temp >= 60: return 0xFFFF00  # Yellow
    if temp >= 50: return 0x00FF00  # Green
    if temp >= 40: return 0x00FFFF  # Cyan
    if temp >= 32: return 0x0088FF  # Light blue
    return 0x0044FF  # Deep blue
