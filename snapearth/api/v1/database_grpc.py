# Generated by the Protocol Buffers compiler. DO NOT EDIT!
# source: snapearth/api/v1/database.proto
# plugin: grpclib.plugin.main
import abc
import typing

import grpclib.client
import grpclib.const

if typing.TYPE_CHECKING:
    import grpclib.server

import google.protobuf.descriptor_pb2
import google.protobuf.empty_pb2
import google.protobuf.timestamp_pb2

import geobufproto.geobuf_pb2
import google.api.annotations_pb2
import snapearth.api.v1.database_pb2


class DatabaseProductServiceBase(abc.ABC):
    @abc.abstractmethod
    async def ListSegmentation(
        self,
        stream: "grpclib.server.Stream[snapearth.api.v1.database_pb2.ListSegmentationRequest, snapearth.api.v1.database_pb2.SegmentationResponse]",
    ) -> None:
        pass

    @abc.abstractmethod
    async def CreateProduct(
        self,
        stream: "grpclib.server.Stream[snapearth.api.v1.database_pb2.CreateProductRequest, snapearth.api.v1.database_pb2.CreateProductResponse]",
    ) -> None:
        pass

    @abc.abstractmethod
    async def SearchSegmentation(
        self,
        stream: "grpclib.server.Stream[snapearth.api.v1.database_pb2.SearchSegmentationRequest, snapearth.api.v1.database_pb2.SegmentationResponse]",
    ) -> None:
        pass

    def __mapping__(self) -> typing.Dict[str, grpclib.const.Handler]:
        return {
            "/snapearth.api.v1.database.DatabaseProductService/ListSegmentation": grpclib.const.Handler(
                self.ListSegmentation,
                grpclib.const.Cardinality.UNARY_STREAM,
                snapearth.api.v1.database_pb2.ListSegmentationRequest,
                snapearth.api.v1.database_pb2.SegmentationResponse,
            ),
            "/snapearth.api.v1.database.DatabaseProductService/CreateProduct": grpclib.const.Handler(
                self.CreateProduct,
                grpclib.const.Cardinality.UNARY_UNARY,
                snapearth.api.v1.database_pb2.CreateProductRequest,
                snapearth.api.v1.database_pb2.CreateProductResponse,
            ),
            "/snapearth.api.v1.database.DatabaseProductService/SearchSegmentation": grpclib.const.Handler(
                self.SearchSegmentation,
                grpclib.const.Cardinality.UNARY_STREAM,
                snapearth.api.v1.database_pb2.SearchSegmentationRequest,
                snapearth.api.v1.database_pb2.SegmentationResponse,
            ),
        }


class DatabaseProductServiceStub:
    def __init__(self, channel: grpclib.client.Channel) -> None:
        self.ListSegmentation = grpclib.client.UnaryStreamMethod(
            channel,
            "/snapearth.api.v1.database.DatabaseProductService/ListSegmentation",
            snapearth.api.v1.database_pb2.ListSegmentationRequest,
            snapearth.api.v1.database_pb2.SegmentationResponse,
        )
        self.CreateProduct = grpclib.client.UnaryUnaryMethod(
            channel,
            "/snapearth.api.v1.database.DatabaseProductService/CreateProduct",
            snapearth.api.v1.database_pb2.CreateProductRequest,
            snapearth.api.v1.database_pb2.CreateProductResponse,
        )
        self.SearchSegmentation = grpclib.client.UnaryStreamMethod(
            channel,
            "/snapearth.api.v1.database.DatabaseProductService/SearchSegmentation",
            snapearth.api.v1.database_pb2.SearchSegmentationRequest,
            snapearth.api.v1.database_pb2.SegmentationResponse,
        )
