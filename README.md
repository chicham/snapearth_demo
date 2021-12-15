# README

## Online demo

Click on the [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/chicham/snapearth_demo/HEAD?urlpath=%2Fvoila%2Frender%2Fdemo.ipynb) button to open the online demo.

## Documentation

- An online version of api documentation available [here](https://buf.build/qwant/snapearth/docs/main/snapearth.api.v1.database)
- The documentation can also be generated using `buf` (see below)

## Try Using grpcurl

Example of query:
- Download the `grpcurl` https://github.com/fullstorydev/grpcurl
- start_date and stop_date are formatted as "YYYY-MM-DDTHH:MM:SSZ"
- Fields for `grpcurl` should be passed as a json payload like in the example
- name of the fields are the same as the ones in `ListSegmentationRequest` in the `api.html` files
- Repeated and optional arguments are not mandatory
- The returns of the `ListSegmentation` method is a list of `SegmentationResponse`
- When using `grpcurl` the response message is a concatenated JSON where each element is the JSON representation of a `SegmentationResponse`
- Note the `wkt` field is the geometry of area where you want to search for the segmentation

 ```bash
 grpcurl url -d '{"n_results": 5, "start_date": "2021-01-01T00:00:00Z", "end_date": "2022-01-01T00:00:00Z", "wkt": "MULTIPOLYGON (((1.6415459999999999 48.6570210000000003, 2.5066069999999998 48.6616240000000033, 2.5143049999999998 48.6782680000000028, 2.5817120000000000 48.8229529999999983, 2.6498390000000001 48.9676520000000011, 2.7181340000000001 49.1124610000000033, 2.7869250000000001 49.2572189999999992, 2.8559869999999998 49.4018480000000011, 2.9250820000000002 49.5464559999999992, 2.9757820000000001 49.6517830000000018, 1.6142719999999999 49.6444299999999998, 1.6415459999999999 48.6570210000000003)))" }' earthsignature.snapearth.eu:443 snapearth.api.v1.database.DatabaseProductService.ListSegmentation > res.pbtxt
 ```

## Alternative Implementing a client

## Prerequisite
- Read the documentation that describes the messages exchanged between earthsignature and its clients
- Having the `protobuf` compiler for your programming language of choice (documentation of protobuf: https://developers.google.com/protocol-buffers )
- Having the `grpc` plugin for your programming language of choice (documentation of gRPC: https://grpc.io/)
- The officially supported languages for gRPC are C#, C++, Dart, Go, Java, Kotlin, Python, NodeJS, Objective-C, PHP, Python, Ruby. (https://grpc.io/docs/languages/)
- Optional: For generating document install the following plugin https://github.com/pseudomuto/protoc-gen-doc

### Generate messages and stubs

- Create a directory which will be the root of your client implementation
- Download and install https://github.com/bufbuild/buf . Buf is a tool that facilitates the usage of protocol buffer based services creation.
- Create a `buf.gen.yaml` at the root of the directory (see documentation at https://docs.buf.build/configuration/v1/buf-gen-yaml/)
- Here is an example of a `buf.gen.yaml` file:
```{yaml}
version: v1
# https://docs.buf.build/configuration/v1/buf-gen-yaml/#managed
managed:
  enabled: true
plugins:
    # The name of the plugin.
    # Required.
    # By default, buf generate will look for a binary named protoc-gen-NAME on your $PATH.
  - name: go
    # The the relative output directory.
    # Required.
    out: gen/go
    # Any options to provide to the plugin.
    # Optional.
    # This can be either a single string or a list of strings.
    opt: paths=source_relative
    # The custom path to the plugin binary, if not protoc-gen-NAME on your $PATH.
    path: custom-gen-go  # optional
    # The generation strategy to use. There are two options:
    #
    # 1. "directory"
    #
    #   This will result in buf splitting the input files by directory, and making separate plugin
    #   invocations in parallel. This is roughly the concurrent equivalent of:
    #
    #     for dir in $(find . -name '*.proto' -print0 | xargs -0 -n1 dirname | sort | uniq); do
    #       protoc -I . $(find "${dir}" -name '*.proto')
    #     done
    #
    #   Almost every Protobuf plugin either requires this, or works with this,
    #   and this is the recommended and default value.
    #
    # 2. "all"
    #
    #   This will result in buf making a single plugin invocation with all input files.
    #   This is roughly the equivalent of:
    #
    #     protoc -I . $(find . -name '*.proto')
    #
    #   This is needed for certain plugins that expect all files to be given at once.
    #
    # Optional. If omitted, "directory" is used. Most users should not need to set this option.
    strategy: directory
  - name: java
    out: gen/java
```

- For example for a golang client:
```{yaml}
version: v1
managed:
  enabled: true
  optimize_for: SPEED

plugins:
  - name: go
    out: gen/go/
  - name: go-grpc
    out: gen/go/
  # OPTIONAL
  #- name: doc
  #  out: docs/source/
  #  opt: html,api.html
```

- Use `buf generate buf.build/qwant/snapearth --include-imports` to generate the messages and stubs for your client.

### Implement the client in the language of your choice

- The client must use the generated file in order to communicate with the EarthSignature service.
- The EarthSignature endpoint is locate at the adress [earthsignature.snapearth.eu:443]
- The connection is secured using the TLS protocol
- The products can be queried using the service `snapearth.api.v1.DatabaseProductService` and the method `ListSegmenation`
