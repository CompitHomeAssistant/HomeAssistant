# Home assistant Compit integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
[![Community Forum][forum-shield]][forum]

This integration is created by Compit https://compit.pl/ to integrate air conditioning, ventilation and heating controllers with HomeAssistant. This integration needs Compit iNext account setup https://inext.compit.pl.

**This component supports the following Compit devices.**

| Device        | Description                                                                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nano Color 2  | https://compit.pl/produkty/termostaty-pokojowe/88-termostat-pokojowy-nano-color-2.html?ic=1                                                                   |
| Nano Color    |
| Nano One      | https://compit.pl/produkty/termostaty-pokojowe/24-termostat-pokojowy-nano-one.html?ic=1                                                                       |
| R900          | https://compit.pl/produkty/sterowniki-pomp-ciepla/89-r900.html?ic=1                                                                                           |
| R810          | https://compit.pl/produkty/sterowniki-instalacji/43-pogodowy-regulator-temperatury-obiegu-grzewczego-r810.html?ic=1                                           |
| R490          | https://compit.pl/produkty/sterowniki-pomp-ciepla/12-sterownik-pompy-ciepla-r490-one.html?ic=1                                                                |
| R480          |
| R470          | https://compit.pl/produkty/sterowniki-pomp-ciepla/10-sterownik-pompy-ciepla-r470-one.html?ic=1                                                                |
| R770RS R771RS | https://compit.pl/produkty/sterowniki-do-kotlow/83-pogodowy-regulator-kotla-retortowego-i-instalacji-grzewczej-r771-2.html?ic=1                               |
| BWC310        |
| BioMax775     |
| BioMax772     |
| BioMax742     |
| SHC           | https://compit.pl/produkty/osprzet/67-czujnik-stezenia-dwutlenku-wegla-wilgotnosci-i-temperatury-w-pomieszczeniach-shc.html?ic=1                              |
| SPM           | https://compit.pl/produkty/osprzet/87-czujnik-jakosci-powietrza-spm.html?ic=1                                                                                 |
| L2            | https://compit.pl/produkty/sterowniki-ogrzewania-podlogowego/40-sterownik-ogrzewania-podlogowego-l2.html?ic=1                                                 |
| COMBO         | https://compit.pl/produkty/osprzet/92-combo.html?ic=1                                                                                                         |
| EL750         | https://compit.pl/produkty/sterowniki-do-kotlow/73-sterownik-kotla-elektrycznego-el750-1.html?ic=1
| R350.M        | https://compit.pl/produkty/sterowniki-uniwerslane/85-pogodowy-regulator-temperatury-obiegu-grzewczego-z-mieszaczem-r350m.html?ic=1                            |
| R350 T3       | https://compit.pl/produkty/sterowniki-instalacji/42-dwustopniowy-sterownik-temperatury-regulator-pi-regulator-krokowy-sterowanie-3-punktowe-r350-07.html?ic=1 |
| R350.CWU      | https://compit.pl/produkty/sterowniki-uniwerslane/78-sterownik-do-podgrzewania-wody-r350-cwu.html?ic=1                                                        |
| AF-1          | https://compit.pl/produkty/osprzet/91-af-1.html?ic=1

## Installation

HACS (recommended)

1. Open HACS
2. Search for Compit (use integrations tab) and download it
3. Restart HomeAssistant
4. In the HA UI go to "Configuration" -> "Integrations" and search for "Compit"
5. Pass your iNext login and password https://inext.compit.pl
6. See created integration entities

## Configuration is done in the UI

| Parameter  | Description                            |
| ---------- | -------------------------------------- |
| `Email`    | User email for https://inext.compit.pl |
| `Password` | Password for the account               |

---

[CompitHomeAssistant]: https://github.com/CompitHomeAssistant/HomeAssistant
[maintainer]: hhttps://github.com/CompitHomeAssistant
[maintainer-shield]: https://img.shields.io/badge/maintainer-%40CompitHomeAssistant-blue.svg?style=for-the-badge
[commits]: https://github.com/CompitHomeAssistant/HomeAssistant/commits/master
[commits-shield]: https://img.shields.io/github/commit-activity/y/CompitHomeAssistant/HomeAssistant.svg?style=for-the-badge
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[releases]: https://github.com/CompitHomeAssistant/HomeAssistant/releases
[releases-shield]: https://img.shields.io/github/release/CompitHomeAssistant/HomeAssistant.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/CompitHomeAssistant/HomeAssistant.svg?style=for-the-badge
