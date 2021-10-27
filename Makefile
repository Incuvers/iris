
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

.PHONY: env
env: ## build docker monitor environment and mount
	@./scripts/ci.sh build

.PHONY: clean
clean: ## clean docker images and containers
	@./scripts/clean.sh

.PHONY: cache
cache: ## clean cache
	@printf "${OKB}Deleting cached objects ...${NC}\n";
	@sudo rm /etc/iris/SNAP_COMMON/cache/*.json
	@printf "${OKG} ✓ ${NC} Complete\n";

.PHONY: setup
setup: ## setup RPi dev environment from a fresh ubuntu 20.04 install
	@printf "${OKB}Installing iris apt package dependancies ...${NC}\n";
	@sudo apt update;
	@xargs -a apt-packages.txt sudo apt install -y;
	@printf "${OKB}Building TIS dependancies from source${NC}\n";
	@./scripts/tis-install.sh;
	@printf "${OKB}Installing iris python package dependancies to root ...${NC}\n";
	@sudo -H python3 -m pip install -r --upgrade pre-requirements.txt --ignore-installed;
	@sudo -H python3 -m pip install -r requirements.txt;
	@printf "${OKB}Copying boot config files ...${NC}\n";
	@sudo cp ./dev/BOOT/firmware/*.* /boot/firmware/.
	@printf "${OKB}Reboot to apply boot config changes.${NC}\n"
	@printf "${OKG} ✓ ${NC} Complete\n";

.PHONY: monitor
monitor: ## Purge logs and run monitor app outside of package context.
	@rm -f monitor/logs/*.log*
	@sudo ./bin/monitor -d

.PHONY: service
service: ## Purge logs and run monitor app in service mode outside of package context.
	@rm -f monitor/logs/*.log*
	@sudo ./bin/monitor -d -m service

.PHONY: dev
dev: dist ## build iris python package, save certs for dev environment to /etc run monitor outside of /monitor scope
	@printf "${OKB}Starting development environment${NC}"
	@sudo daemon-dev
	@sudo runwebserver-dev &
	@sudo monitor -d

.PHONY: dist
dist: ## build iris python distribution
	@python3 -m pip uninstall -y iris;
	@printf "${OKB}Installing iris ...\n${NC}"
	@python3 -m pip install --upgrade pip
	@python3 -m pip install . --ignore-installed
	@printf "${OKG} ✓ ${NC} iris installed\n";
