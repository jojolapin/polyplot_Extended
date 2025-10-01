# polyplot_Extended

PolyPlot is an interactive desktop tool for analysing land enclosures from coordinate lists. Paste latitude/longitude or UTM coordinates, validate the geometry and instantly generate a richly annotated Folium map.

## Highlights

- Modern Tk interface with contextual menus and progress feedback
- Automatic UTM → WGS84 conversion with configurable zones and hemisphere presets
- Interactive summary panel that reports area, perimeter, post counts and fencing costs
- Dedicated **Calculate Costs** action that compiles enclosure totals into a share-ready report
- One-click clipboard export for sharing enclosure reports
- CSV export of calculations and Folium map generation with optional markers and popups

## Getting Started

```bash
python polyplot.py
```

Use the **Coordinate Settings** panel on the right-hand side to pick a country preset or manually select the UTM zone used for conversions. The **Enclosure Summary** panel updates whenever you validate input, load data or build a map, and the **Copy Summary** button makes it easy to share tabulated metrics. Tap **Calculate Costs** at the bottom of the window to open a detailed cost breakdown for every enclosure alongside project-wide totals.
