from homeassistant.const import Platform

MANURFACER_NAME = "Compit"
DOMAIN = "compit"
API_HOST = "inext.compit.pl"
API_URL = f"https://{API_HOST}/mobile/v2/compit"
FULL_API_URL = f"https://{API_HOST}"

PLATFORMS = [
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]
