# Pinvyn v0.1 parts list

Prices are what turned up in a web search on 2026-11-15 and will move. "Not checked" means the shop's stock was not confirmed.

| Part | Qty | Where | Price seen | Notes |
|---|---|---|---|---|
| nRF52840 controller, "SuperMini nRF52840" (nice!nano v2 clone) | 2, buy 3 | AliExpress | A few dollars each | Builds in ZMK as `nice_nano_v2`. Reliability can vary, hence the spare. The original nice!nano v2 costs about ten times more. |
| Display, nice!view type (36 × 14 mm memory LCD) | 1 | splitkb.com (NL) | About €24 | Left half, battery status |
| Trackball, 34 mm, Perixx PERIPRO-303 | 1 | perixx.com or Amazon.de | €11.99 on perixx.com | Sold as a replacement ball for trackball mice |
| PMW3610 sensor board with LM18-LSI lens | 1 | AliExpress, or Randware on Tindie | Tindie: $25, ships from the US | Sits under the ball. Prefer a badjeff or siderakb design, which the reference mount is drawn for |
| Ceramic balls, 2.5 mm (ZrO2 or Si3N4) | 3, buy a bag | AliExpress | Cents each | Static supports for the trackball |
| Mouse-wheel encoder | 2, buy 4 | AliExpress | Cents to a couple of dollars | For the two scrollers; wheels get printed |
| MX switches | 73, buy 80 | AliExpress, or splitkb / KEYGEM in the EU | Depends on the switch | |
| Keycaps, with three 2u caps | 1 set | Same shops | Depends on the set | Two Space keys and Enter are 2u |
| 2u stabilizers, plate-mount | 3 | Same shops | | No PCB in v0.1, so they must mount in the plate |
| 1N4148 diodes, through-hole (DO-35) | 80 | Local electronics shop (Oomipood, not checked), Farnell Estonia | Cents each | One per switch |
| TRRS jacks | 2 | Local electronics shop or splitkb | | 4-pole |
| TRRS cable | 1 | Any | | 4-pole |
| LiPo battery, 3.7 V | 1 | Not chosen | | Size gets fixed with the case |
| Slide power switch | 1 | Local electronics shop | | |
| Wire, screws, threaded inserts | | Local | | |

## Ordering notes

- AliExpress deliveries usually take a couple of weeks, so that order goes first.
- splitkb.com ships from the Netherlands within two business days and advertises free European shipping above €100.
- Farnell's Estonian site lists the 1N4148 family with 1–2 working-day delivery. The listing found was the surface-mount version; hand-wiring needs the through-hole one.

## Sources

- SuperMini nRF52840 and ZMK board name: <https://github.com/joric/nrfmicro/wiki/ALternatives>
- nice!view specifications: <https://kbd.news/nice-view-1674.html>
- Low-power display advice for battery builds: <https://docs.splitkb.com/product-guides/nice-nano/frequently-asked-questions>
- PMW3610 breakout: <https://www.tindie.com/products/randware/pmw3610-breakout-board/>
- PMW3610 driver for ZMK, usable on the peripheral half: <https://github.com/badjeff/zmk-pmw3610-driver>
- Parts list of a comparable trackball build: <https://docs.bastardkb.com/help/bluetooth.html>
- EVQWGD001 availability and the mouse-encoder replacement: <https://ergomech.store/blog/ergomech-blog-1/the-roller-encoder-is-dead-long-live-the-roller-encoder-13>
- ZMK split transports: <https://zmk.dev/docs/features/split-keyboards>
- ZMK dongle: <https://zmk.dev/docs/hardware-integration/dongle>
- splitkb.com shipping: <https://splitkb.com/>
- Farnell Estonia, 1N4148WS: <https://ee.farnell.com/diodes-inc/1n4148ws-7-f/small-signal-sw-diode-75v-sod/dp/1843678>
