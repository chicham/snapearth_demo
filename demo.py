# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.4
# ---

import asyncio
import warnings
from datetime import date, datetime, timedelta
from typing import Iterable, List

import environ
import folium
import ipywidgets as widgets
import nest_asyncio
import numpy as np
import pandas as pd
from google.protobuf import timestamp_pb2
from grpclib.client import Channel
from grpclib.config import Configuration

# +
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from shapely import wkt
from shapely.geometry import mapping

from snapearth.api.v1.database_grpc import DatabaseProductServiceStub
from snapearth.api.v1.database_pb2 import ListSegmentationRequest, SegmentationResponse
from utils import CATEGORY_TO_RGB

nest_asyncio.apply()

# Europe bounding box
EUROPE_COORDINATES = wkt.loads(
    "POLYGON((-10.61 71.16, 44.85 71.16, 44.85 35.97, -10.61 35.97, -10.61 71.16))",
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
            # product_ids=product_ids if product_ids != "" else None,
            # categories=categories if categories != "" else None,
            n_results=n_results,
        )
        return await stub.ListSegmentation(request)


def read_inmemory(segmentation, width=None, height=None, resampling=None):

    with MemoryFile(segmentation) as memfile:
        with memfile.open(
            mode="r",
            count=1,
            width=width,
            height=height,
            resampling=resampling,
        ) as dataset:
            return dataset.read()


def segmentation_to_image(segmentation, cloud_mask, out_dtype=np.ubyte):
    array = read_inmemory(segmentation).squeeze()
    cloud_array = read_inmemory(
        cloud_mask,
        height=array.shape[0],
        width=array.shape[1],
        resampling=Resampling.nearest,
    ).squeeze()
    categories = np.unique(array)
    image = np.empty((array.shape[0], array.shape[1], 3), dtype=out_dtype)

    for category in categories:
        mask = array == category
        try:
            image[mask] = CATEGORY_TO_RGB[category]
        except KeyError:
            warnings.warn(f"Category {category} not found")
            image[mask] = (255, 255, 255)
    image[cloud_array] = (255, 255, 255)  # Remove cloud areas
    return image


def plot_responses(geom, start_date, end_date, product_ids, categories, n_results):
    responses = asyncio.run(
        request_earthsignature(
            cfg.grpc.host,
            cfg.grpc.port,
            cfg.grpc.use_ssl,
            geom.value,
            start_date.value,
            end_date.value,
            product_ids.value.split(","),
            categories.value.split(","),
            n_results.value,
        ),
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


cfg = DemoConfig.from_environ(
    {
        "SNAPEARTH_GRPC_HOST": "earthsignature.snapearth.eu",
        "SNAPEARTH_GRPC_PORT": 443,
        "SNAPEARTH_GRPC_USE_SSL": True,
        "SNAPEARTH_GRPC_KEEPALIVE_TIMEOUT_MS": 60000,
        "SNAPEARTH_GRPC_MAX_RECEIVE_MESSAGE_LENGTH": 10 ** 20,
        "SNAPEARTH_GRPC_MAX_SEND_MESSAGE_LENGTH": 10 ** 20,
    },
)
MAP_CENTER = mapping(EUROPE_COORDINATES.centroid)

geom = widgets.Text(
    value=str(EUROPE_COORDINATES),
    placeholder="",
    description="WKT polygon of the area of interest",
    disabled=False,
)

start_date = widgets.DatePicker(
    value=datetime.now() - timedelta(1),
    description="Start date",
    disabled=False,
)

end_date = widgets.DatePicker(
    value=datetime.now() - timedelta(1),
    description="Stop date",
    disabled=False,
)

product_ids = widgets.Text(
    value="",
    placeholder="",
    description="Product IDs (comma separated)",
    disabled=False,
)

categories = widgets.Text(
    value="",
    description="Categories (comma separated)",
    disabled=False,
)

n_results = widgets.IntSlider(
    value=cfg.grpc.max_results,
    min=1,
    max=20,
    step=1,
    description="Max results",
    disabled=False,
)
# -

widgets.VBox([geom, start_date, end_date, product_ids, categories, n_results])

df, map_ = plot_responses(geom, start_date, end_date, product_ids, categories, n_results)
map_
