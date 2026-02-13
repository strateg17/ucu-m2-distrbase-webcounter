CASS_CONTAINER=cass1
CQLSH=docker exec -i $(CASS_CONTAINER) cqlsh
LOG=run.log

.PHONY: cql all tail

cql:
	@echo "== Running: $(FILE) =="
	@$(CQLSH) < $(FILE) 2>&1 | tee -a $(LOG)

all:
	@echo "== Running all CQL files =="
	@for f in cql/*.cql; do \
		echo "\n== $$f =="; \
		$(CQLSH) < $$f 2>&1 | tee -a $(LOG); \
	done

tail:
	@tail -n 200 -f $(LOG)
