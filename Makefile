export ANSIBLE_CONFIG=devops/ansible.cfg

app_version=$(shell git rev-parse --short HEAD 2> /dev/null | sed "s/\(.*\)/\1/")

venv:
	test -d venv || python -m venv venv
	. venv/bin/activate; pip install ansible~=3.2.0

deploy-prod: venv
	. venv/bin/activate; ansible-playbook devops/deploy-prod.yml -e version=$(app_version)
.PHONY: deploy-prod

deploy-staging: venv
	. venv/bin/activate; ansible-playbook devops/deploy-staging.yml -e version=$(app_version)
.PHONY: deploy-staging
