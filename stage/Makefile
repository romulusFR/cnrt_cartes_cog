METADATA=meta.yaml 
PANDOC=pandoc --metadata-file=$(METADATA)

stage-miage-2022.pdf: stage-miage-2022.md $(METADATA)
	$(PANDOC) --to=pdf --number-sections --pdf-engine=pdflatex -o $@ $<
