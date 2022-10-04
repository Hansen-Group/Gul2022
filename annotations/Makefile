TAG := v1

all:
	echo "VERSION = '$(shell git log -1 --format="%h (%ai)")'" > pipeline/_version.py
	podman build -t annovep:${TAG} .
