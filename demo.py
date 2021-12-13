import asyncio
import warnings
from base64 import b64decode
from collections import ChainMap
from datetime import date, datetime, timedelta
from enum import Enum
from time import perf_counter
from typing import ChainMap, List

import environ
import folium
import numpy as np
import pandas as pd
import rasterio
import streamlit as st
from google.protobuf import timestamp_pb2
from grpclib.client import Channel
from grpclib.config import Configuration
from numpy.lib.type_check import imag
from rasterio.io import MemoryFile
from rasterio.plot import reshape_as_image
from shapely import wkt
from shapely.geometry import mapping
from snapearth.api.v1.database_grpc import DatabaseProductServiceStub
from snapearth.api.v1.database_pb2 import ListSegmentationRequest
from streamlit_folium import folium_static
from utils import CATEGORY_TO_RGB
from vespa.application import Vespa
from vespa.query import QueryModel, RankProfile, WeakAnd

# EPSG3857 format
EUROPE_COORDINATES = wkt.loads(
    "POLYGON((-10.61 71.16, 44.85 71.16, 44.85 35.97, -10.61 35.97, -10.61 71.16))",
)


class Application(Enum):
    EARTHSIGNATURE = "earthsignature"
    EARTHSEARCH = "earthsearch"


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

    @environ.config
    class VESPA:
        host: str = environ.var()
        port: int = environ.var(converter=int)
        max_results: int = environ.var(default=10, converter=int)

    grpc: GRPC = environ.group(GRPC)
    vespa: VESPA = environ.group(VESPA)


async def call_service(
    host: str,
    port: int,
    use_ssl: bool,
    geom: str,
    start_date: date,
    end_date: date,
    product_ids: List[str],
    categories: List[str],
    n_results: int,
):
    min_time = datetime.min.time()
    config = Configuration(
        http2_connection_window_size=2000000000,
        http2_stream_window_size=2000000000,
    )
    async with Channel(
        host=host,
        port=int(port),
        ssl=bool(use_ssl),
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
            n_results=int(n_results),
        )
        return await stub.ListSegmentation(request)


def read_inmemory(segmentation):

    with MemoryFile(segmentation) as memfile:
        with memfile.open(mode="r", count=1) as dataset:
            return dataset.read()


def segmentation_to_image(segmentation, out_dtype=np.ubyte):
    array = read_inmemory(segmentation).squeeze()
    categories = np.unique(array)
    image = np.empty((array.shape[0], array.shape[1], 3), dtype=out_dtype)

    for category in categories:
        mask = array == category
        try:
            image[mask] = CATEGORY_TO_RGB[category]
        except KeyError:
            warnings.warn(f"Category {category} not found")
            image[mask] = (255, 255, 255)
    return image


def earthsignature(cfg: DemoConfig, center):
    with st.form(key="earthsignature"):
        st.subheader("Query Earthsignature")
        host = st.selectbox(
            "Host",
            ("earthsignature.snapearth.eu", "10.110.3.49", "10.108.3.49"),
        )
        port = st.selectbox("Port", (443, 50051))
        use_ssl = st.checkbox("Use SSL", value=cfg.grpc.use_ssl)
        geom = st.text_input("Area (wkt format)", value="")
        start_date = st.date_input("Start date", value=datetime.now() - timedelta(1))
        end_date = st.date_input("End date", value=datetime.now())
        product_ids = st.text_input(
            "Product IDs (comma separated)",
            value="",
        )  # TODO List of all product_id in the database ?
        categories = st.text_input(
            "Categories (comma separated)",
            value="",
        )  # TODO Multiselect box with all the categories
        n_results = st.number_input("Max results", value=cfg.grpc.max_results)
        submitted = st.form_submit_button("Query")

    if submitted:
        map_ = folium.Map(
            location=center["coordinates"][::-1],
            zoom_start=3,
            crs="EPSG3857",
        )
        product_ids = product_ids.split(",") if not product_ids == "" else None
        categories = categories.split(",") if not categories == "" else None
        start = perf_counter()
        responses = asyncio.run(
            call_service(
                host,
                port,
                use_ssl,
                geom,
                start_date,
                end_date,
                product_ids,
                categories,
                n_results,
            ),
        )
        data = []
        stop = perf_counter() - start
        print(f"{len(responses)} responses in {stop}s")
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
            image = segmentation_to_image(response.segmentation)
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
        df = pd.DataFrame(data)
        st.dataframe(df)
        folium_static(map_)


def earthsearch(cfg: DemoConfig, center):
    with st.form(key="earthsearch"):
        st.subheader("Query Earthsearch")
        host = st.text_input("Host", value=cfg.vespa.host)
        port = st.number_input("Port", value=cfg.vespa.port)
        rank_profile = st.text_input("Rank profile", value="default")
        query = st.text_input("Query", value="")
        hits = st.number_input("Max hits", value=cfg.vespa.max_results)
        submitted = st.form_submit_button("Query")

    if submitted:
        vespa_app = Vespa(url=f"{host}:{port}")
        query_model = QueryModel(
            match_phase=WeakAnd(hits=hits, field="default"),
            rank_profile=RankProfile(name=rank_profile),
        )
        properties = (
            qp.get_query_properties(query=query) for qp in query_model.query_properties
        )
        query_properties = dict(
            ChainMap(query_model.match_phase.get_query_properties(), *properties),
        )
        match_filter = query_model.match_phase.create_match_filter(query=query)
        body = {
            "yql": f"select * from earthsearch where {match_filter};",
            "ranking": {
                "profile": query_model.rank_profile.name,
                # "list_features": query_model.rank_profile.list_features,
            },
        }
        body.update(query_properties)

        results = vespa_app.query(body=body)
        data = [
            dict(relevance=d["relevance"], **d["fields"])
            for d in results.json["root"].get("children", {})
            if d
        ]
        st.dataframe(pd.DataFrame(data))


cfg = DemoConfig.from_environ()
st.title("Snapearth")
center = mapping(EUROPE_COORDINATES.centroid)
app = st.sidebar.selectbox(
    "Service",
    [Application.EARTHSIGNATURE.value, Application.EARTHSEARCH.value],
)

if app == Application.EARTHSIGNATURE.value:
    st.subheader("Earthsignature")
    earthsignature(cfg, center)
elif app == Application.EARTHSEARCH.value:
    st.subheader("Earthsearch")
    earthsearch(cfg, center)
