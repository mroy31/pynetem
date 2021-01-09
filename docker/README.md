
# Docker images

This folder contains source for docker images used for pynetem:

- mroy31/pynetem-host
- mroy31/pynetem-server
- mroy31/pynetem-frr

## Build

To build an image, you just need to go in the right folder and use the following commands:

```bash
# exemple for host
cd host
docker build -t mroy31/pynetem-host:<version> .
```

## Cross-build with buildx

If you need to build an image for several platform, you can use the new [buildx extension](https://github.com/docker/buildx).

First, install supported compilation platform with
```bash
docker run --privileged --rm tonistiigi/binfmt --install all
```

Then create an new builder with
```bash
docker buildx create --use --name mybuild
```

Finally to build an image
```bash
# exemple for host
cd host
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t mroy31/pynetem-host:<version> .
```
