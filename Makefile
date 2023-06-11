run_first:
	docker compose up proto_server proto_client_1 proto_client_2 proto_client_3 proto_client_4

## build_image_for_custom_client: build image for custom client container
build_image_for_custom_client:
	docker build . -f ./proto_client.Dockerfile -t custom_client


## add_custom_client: add client with custom name
add_custom_client:
	@read -p "Enter client name: " client_name; \
 	docker run --env GRPC_CLIENT_HOST=client_name --env GRPC_CLIENT_PORT=50057 --env USERNAME=client_name --network soa-2_SOA-2_default_additional --name client_name custom_client

down:
	docker compose down --remove-orphans

## pip-compile: compile all requirements
pip-compile:
	docker compose run app pip-compile requirements.in

## pip-upgrade: upgrade all requirements
pip-upgrade:
	docker compose run app pip-compile -U requirements.in

## pip-sync: sync requirements in local environment
pip-sync:
	pip-sync requirements.txt
