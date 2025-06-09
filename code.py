# 8x8-neopixel-with-time-and-weather-pico.py
import board
import time
import neopixel
import wifi
import socketpool
import ssl
import adafruit_requests
import rtc
import os
import adafruit_ntp
from adafruit_pixel_framebuf import PixelFramebuffer

# === CONFIGURATION ===
LATITUDE = 42.3226
LONGITUDE = -71.1654
CITY_NAME = "Chestnut Hill"
UPDATE_INTERVAL = 900  # 15 minutes

# === HARDWARE SETUP ===
pixels = neopixel.NeoPixel(
    board.GP16,
    64,
    brightness=0.3,
    auto_write=False,
    pixel_order=neopixel.GRB  # <-- FIXED: GRB instead of RGB
)

pixel_framebuf = PixelFramebuffer(
    pixels,
    width=8,
    height=8,
    alternating=True,
    reverse_x=True
)

# === WIFI AND TIME SETUP ===
print("Connecting to WiFi...")
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
print(f"Connected! IP: {wifi.radio.ipv4_address}")

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

print("Syncing time...")
try:
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)
    rtc.RTC().datetime = ntp.datetime
    print("UTC time synced successfully!")
except Exception as e:
    print(f"Time sync failed: {e}")

# === UTILITIES ===
def get_eastern_time():
    utc_time = time.localtime()
    month = utc_time.tm_mon
    offset_hours = -4 if 3 <= month <= 10 else -5
    eastern_seconds = time.mktime(utc_time) + offset_hours * 3600
    return time.localtime(eastern_seconds)

def get_temp_color(temp):
    if temp >= 80: return 0xFF2200  # Bright red
    if temp >= 70: return 0xFFAA00  # Orange
    if temp >= 60: return 0xFFFF00  # Yellow
    if temp >= 50: return 0x00FF00  # Green
    if temp >= 40: return 0x00FFFF  # Cyan
    if temp >= 32: return 0x0088FF  # Light blue
    return 0x0044FF  # Deep blue

def simplify_weather_description(desc):
    desc = desc.lower()
    if 'clear' in desc or 'sun' in desc: return 'sunny'
    if 'cloud' in desc: return 'cloudy'
    if 'rain' in desc or 'drizzle' in desc: return 'rainy'
    if 'snow' in desc: return 'snowy'
    if 'thunder' in desc or 'storm' in desc: return 'stormy'
    if 'fog' in desc or 'mist' in desc: return 'foggy'
    return 'changing'

def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={LATITUDE}&lon={LONGITUDE}&appid={os.getenv('OPENWEATHER_TOKEN')}&units=imperial"
    try:
        print("Fetching weather data...")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return None

        data = response.json()
        temp = round(data['main']['temp'])
        description = data['weather'][0]['description']
        eastern_time = get_eastern_time()

        hour = eastern_time.tm_hour
        minute = eastern_time.tm_min
        am_pm = "am" if hour < 12 else "pm"
        hour = 12 if hour == 0 else (hour - 12 if hour > 12 else hour)
        time_str = f"{hour}:{minute:02d}{am_pm}"

        print(f"{time_str} - {temp}F - {description}")
        return {
            'temp': temp,
            'description': description,
            'time': time_str
        }

    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None

def create_weather_message(data):
    if not data:
        return "Weather data unavailable "
    time_str = data['time']
    temp = data['temp']
    simple = simplify_weather_description(data['description'])
    return f"{time_str}-It's {temp} & {simple} in {CITY_NAME} "

def scroll_text(text, color=0x00FF00, speed=0.12):
    print(f"Scrolling: {text} in color {hex(color)}")
    for scroll_pos in range(len(text) * 6 + 8):
        pixel_framebuf.fill(0x000000)
        pixel_framebuf.text(text, 8 - scroll_pos, 0, color)
        pixel_framebuf.display()
        time.sleep(speed)

def show_status(msg, color=0xFFFF00):
    pixel_framebuf.fill(0x000000)
    pixel_framebuf.text(msg, 1, 0, color)
    pixel_framebuf.display()
    time.sleep(2)

# === MAIN LOOP ===
def main():
    print("Weather Display Starting...")
    show_status("WIFI OK", 0x00FF00)

    weather_data = None
    last_update = 0

    while True:
        try:
            now = time.monotonic()
            if now - last_update > UPDATE_INTERVAL or weather_data is None:
                show_status("UPDATE", 0x0000FF)
                weather_data = get_weather()
                last_update = now

                if weather_data is None:
                    show_status("ERROR", 0xFF0000)
                    time.sleep(2)

            msg = create_weather_message(weather_data)
            color = get_temp_color(weather_data['temp']) if weather_data else 0xFFFFFF
            scroll_text(msg, color)
            time.sleep(1)

        except KeyboardInterrupt:
            print("Stopped by user.")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            show_status("ERROR", 0xFF0000)
            time.sleep(5)

    pixel_framebuf.fill(0x000000)
    pixel_framebuf.display()

if __name__ == "__main__":
    main()
