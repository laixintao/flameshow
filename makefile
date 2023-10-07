.PHONY: proto run-test

proto:
	docker run --rm -v${PWD}:${PWD} -w${PWD} namely/protoc-all --proto_path=${PWD}/proto \
		    --python_out=${PWD}/flameshow/pprof_parser/ ${PWD}/proto/profile.proto
bump_patch:
	bumpversion patch

bump_minor:
	bumpversion minor

patch: bump_patch
	rm -rf dist
	poetry build
	poetry publish

_perf_startup:
	sudo py-spy record python _perf_main.py

run-test:
	rm -rf htmlcov && pytest --cov-report html --cov=flameshow -vv --disable-warnings
	flake8 .
	black .
	open htmlcov/index.html
