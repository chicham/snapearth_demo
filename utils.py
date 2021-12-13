import rasterio
import environ
import asyncio
import warnings
from collections import OrderedDict
from datetime import date, datetime
from typing import Iterable, List

import folium
import numpy as np
import pandas as pd
from google.protobuf import timestamp_pb2
from grpclib.client import Channel
from grpclib.config import Configuration
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from shapely import wkt
from shapely.geometry import mapping

from snapearth.api.v1.database_grpc import DatabaseProductServiceStub
from snapearth.api.v1.database_pb2 import ListSegmentationRequest, SegmentationResponse

# Europe bounding box
EUROPE_COORDINATES = wkt.loads(
    "POLYGON((-10.61 71.16, 44.85 71.16, 44.85 35.97, -10.61 35.97, -10.61 71.16))",
)
MAP_CENTER = mapping(EUROPE_COORDINATES.centroid)

CATEGORY_TO_RGB = OrderedDict(
    {
        0: (255, 255, 255),
        111: (230, 0, 77),
        112: (255, 0, 0),
        121: (204, 77, 242),
        122: (204, 0, 0),
        123: (230, 204, 204),
        124: (230, 204, 230),
        131: (166, 0, 204),
        132: (166, 77, 0),
        133: (255, 77, 255),
        141: (255, 166, 255),
        142: (255, 230, 255),
        211: (255, 255, 168),
        212: (255, 255, 0),
        213: (230, 230, 0),
        221: (230, 128, 0),
        222: (242, 166, 77),
        223: (230, 166, 0),
        231: (230, 230, 77),
        241: (255, 230, 166),
        242: (255, 230, 77),
        243: (230, 204, 77),
        244: (242, 204, 166),
        311: (128, 255, 0),
        312: (0, 166, 0),
        313: (77, 255, 0),
        321: (204, 242, 77),
        322: (166, 255, 128),
        323: (166, 230, 77),
        324: (166, 242, 0),
        331: (230, 230, 230),
        332: (204, 204, 204),
        333: (204, 255, 204),
        334: (0, 0, 0),
        335: (166, 230, 204),  # Not used for classification
        411: (166, 166, 255),
        412: (77, 77, 255),
        421: (204, 204, 255),
        422: (230, 230, 255),
        423: (166, 166, 230),
        511: (0, 204, 242),
        512: (128, 242, 230),
        521: (0, 255, 166),
        522: (166, 255, 230),
        523: (230, 242, 255),
    },
)


@environ.config(prefix="SNAPEARTH")
class DemoConfig:
    @environ.config
    class GRPC:
        host: str = environ.var()
        port: int = environ.var(converter=int)
        max_receive_message_length: int = environ.var(converter=int)
        max_send_message_length: int = environ.var(converter=int)
        keepalive_timeout_ms: int = environ.var(converter=int)
        use_ssl: bool = environ.bool_var()
        max_results: int = environ.var(default=1, converter=int)

    grpc: GRPC = environ.group(GRPC)


async def request_earthsignature(
    host: str,
    port: int,
    use_ssl: bool,
    geom: str,
    start_date: date,
    end_date: date,
    product_ids: List[str],
    categories: List[str],
    n_results: int,
) -> Iterable[SegmentationResponse]:
    min_time = datetime.min.time()
    config = Configuration(
        http2_connection_window_size=2000000000,
        http2_stream_window_size=2000000000,
    )
    async with Channel(
        host=host,
        port=port,
        ssl=use_ssl,
        config=config,
    ) as channel:
        stub = DatabaseProductServiceStub(channel)
        geom = geom if not geom == "" else geom
        request = ListSegmentationRequest(
            wkt=geom,
            start_date=timestamp_pb2.Timestamp().FromDatetime(
                datetime.combine(start_date, min_time),
            ),
            end_date=timestamp_pb2.Timestamp().FromDatetime(
                datetime.combine(end_date, min_time),
            ),
            product_ids=product_ids,
            categories=categories,
            n_results=n_results,
        )
        return await stub.ListSegmentation(request)


def read_inmemory(segmentation, width=None, height=None, resampling=None, dtype=None):

    with MemoryFile(segmentation) as memfile:
        with memfile.open(
            mode="r",
            count=1,
            width=width,
            height=height,
            resampling=resampling,
            dtype=dtype,
        ) as dataset:
            return dataset.read()


def segmentation_to_image(segmentation, cloud_mask, out_dtype=np.ubyte):
    array = read_inmemory(segmentation, dtype=rasterio.uint16).squeeze()
    # cloud_array = read_inmemory(
    #     cloud_mask,
    #     height=array.shape[0],
    #     width=array.shape[1],
    #     resampling=Resampling.nearest,
    #     dtype=rasterio.ubyte,
    # ).squeeze()
    categories = np.unique(array)
    image = np.empty((array.shape[0], array.shape[1], 3), dtype=out_dtype)

    for category in categories:
        mask = array == category
        try:
            image[mask] = CATEGORY_TO_RGB[category]
        except KeyError:
            warnings.warn(f"Category {category} not found")
            image[mask] = (255, 255, 255)
    # image[cloud_array] = (255, 255, 255)  # Remove cloud areas
    return image


def plot_responses(
    host, port, use_ssl, geom, start_date, end_date, product_ids, categories, n_results
):
    product_ids = product_ids.value.split(",") if product_ids.value else None
    categories = categories.value.split(",") if categories.value else None
    responses = asyncio.run(
        request_earthsignature(
            host,
            port,
            use_ssl,
            geom.value,
            start_date.value,
            end_date.value,
            product_ids,
            categories,
            n_results.value,
        )
    )

    map_ = folium.Map(
        location=MAP_CENTER["coordinates"][::-1],
        zoom_start=3,
        crs="EPSG3857",
    )
    data = []
    for response in responses:
        geom = wkt.loads(response.wkt)
        folium.GeoJson(geom).add_to(map_)
        centroid = mapping(geom.centroid)
        folium.Marker(
            location=centroid["coordinates"][::-1],
            tooltip=f"{response.product_id}",
        ).add_to(map_)
        bounds = geom.bounds
        bounds = (
            (bounds[1], bounds[0]),
            (bounds[3], bounds[2]),
        )
        image = segmentation_to_image(response.segmentation, response.cloud_mask)
        folium.raster_layers.ImageOverlay(
            image,
            bounds=bounds,
            name=response.product_id,
            overlay=True,
            control=False,
            opacity=0.8,
        ).add_to(map_)
        data.append(
            {
                # "geometry": geom,
                "creation_date": datetime.fromtimestamp(
                    response.creation_date.seconds,
                ),
                "publication_date": datetime.fromtimestamp(
                    response.creation_date.seconds,
                ),
                "product_id": response.product_id,
                "quicklook_url": response.quicklook,
                "cloud_cover": response.cloud_cover,
                "browse_url": response.browse_url,
                "download_url": response.download_url,
            },
        )

    return pd.DataFrame(data), map_
