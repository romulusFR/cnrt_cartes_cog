# Notes vrac visualisation

## Format heatmap

Format daily weather <https://vega.github.io/vega/data/seattle-weather.csv>

```tsv
date        precipitation   temp_max    temp_min    wind   weather
2012-01-01  0               12.8        5           4.7    drizzle
2012-01-02  10.9            10.6        2.8         4.5    rain
2012-01-03  0.8             11.7        7.2         2.3    rain
```

## Edge bundling

<https://stackoverflow.com/questions/64874024/vega-edge-bundling-directed-vary-thickness-of-each-edge-to-show-strength-of>

```json

{ "type": "filter", "expr": "datum.level == 'mother'" },

"url": "https://vega.github.io/vega/data/flare.json",

 "url": "https://vega.github.io/vega/data/flare-dependencies.json",

 "strokeWidth": { "value": 1.5 }
```
