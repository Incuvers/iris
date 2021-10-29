
.PHONY: help
help: ## Print this help message and exit
	@echo Usage:
	@echo "  make [target]"
	@echo
	@echo Targets:
	@awk -F ':|##' \
		'/^[^\t].+?:.*?##/ {\
			printf "  %-30s %s\n", $$1, $$NF \
		 }' $(MAKEFILE_LIST)

.PHONY: coverage
coverage: ## run code coverage report on module via unittest
	@./scripts/coverage.sh ${case}

.PHONY: unit
unit: ## execute monitor unittest suite, for single case make unit case=<NAME>
	@rm -f monitor/logs/*.log*
	@./scripts/unittest.sh ${case}

.PHONY: lint
lint: ## lint codebase using a combination of yamllint, shellcheck and flake8
	@./scripts/lint.sh

.PHONY: config
config: ## send env delta to docker dev directory
	@./scripts/config.sh

.PHONY: dev
dev: config ## build development stack
	@./scripts/dev.sh

.PHONY: clean
clean: ## clean docker images and containers
	@./scripts/clean.sh

.PHONY: setup
setup: ## setup RPi dev environment from a fresh ubuntu 20.04 install
	@printf "${OKB}Installing iris apt package dependancies ...${NC}\n";
	@sudo apt update;
	@xargs -a apt-packages.txt sudo apt install -y;
	@printf "${OKB}Installing iris python package dependancies to root ...${NC}\n";
	@sudo -H python3 -m pip install -r --upgrade pre-requirements.txt --ignore-installed;
	@sudo -H python3 -m pip install -r requirements.txt;
	@printf "${OKB}Copying boot config files ...${NC}\n";
	@sudo cp ./dev/BOOT/firmware/*.* /boot/firmware/.
	@printf "${OKB}Reboot to apply boot config changes.${NC}\n"
	@printf "${OKG} ✓ ${NC} Complete\n";
