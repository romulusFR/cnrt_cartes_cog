# Notes VIZ

all: ../dist/thesaurus-sunburst.pdf ../dist/thesaurus-tree.pdf ../dist/thesaurus-radial.pdf ../dist/thesaurus-treemap.pdf

../dist/thesaurus-sunburst.pdf: specs/vega-sunburst.json
	vg2pdf  -b . $< $@

../dist/thesaurus-tree.pdf: specs/vega-tree.json
	vg2pdf  -b . $< $@

../dist/thesaurus-radial.pdf: specs/vega-radial.json
	vg2pdf  -b . $< $@

../dist/thesaurus-treemap.pdf: specs/vega-treemap.json
	vg2pdf  -b . $< $@
