from homeassistant.const import Platform

MANURFACER_NAME = "Compit"
DOMAIN = "compit"
API_URL = "https://inext.compit.pl/mobile/v2/compit"

PLATFORMS = [
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]
