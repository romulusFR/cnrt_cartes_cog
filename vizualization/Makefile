# Notes VIZ
dist := ../dist/
spec := specs/
vega := vg2pdf
specs := $(wildcard specs/*.json)
# pdfs := $(patsubst specs/%.json,../dist/%.pdf, $(specs))
pdfs := $(specs:$(spec)%.json=$(dist)%.pdf)

all : $(pdfs)

$(pdfs): $(dist)%.pdf : $(spec)%.json
	vg2pdf -b . $< $@

