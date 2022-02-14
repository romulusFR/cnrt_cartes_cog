METADATA=meta.yaml 
PANDOC=pandoc --metadata-file=$(METADATA)

projet-tuteure-2022.pdf: projet-tuteure-2022.md $(METADATA)
	$(PANDOC) --to=pdf --number-sections --pdf-engine=pdflatex -o $@ $<
