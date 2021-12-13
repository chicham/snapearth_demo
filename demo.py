# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.1
# ---

# %%
import nest_asyncio
import ipywidgets as widgets
from datetime import datetime, timedelta
from utils import DemoConfig, EUROPE_COORDINATES, plot_responses

nest_asyncio.apply()

cfg: DemoConfig = DemoConfig.from_environ(
    {
        "SNAPEARTH_GRPC_HOST": "earthsignature.snapearth.eu",
        "SNAPEARTH_GRPC_PORT": 443,
        "SNAPEARTH_GRPC_USE_SSL": True,
        "SNAPEARTH_GRPC_KEEPALIVE_TIMEOUT_MS": 60000,
        "SNAPEARTH_GRPC_MAX_RECEIVE_MESSAGE_LENGTH": 10 ** 20,
        "SNAPEARTH_GRPC_MAX_SEND_MESSAGE_LENGTH": 10 ** 20,
    }
)

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

# %%
widgets.VBox([geom, start_date, end_date, product_ids, categories, n_results])

# %%
df, map_ = plot_responses(
    cfg.grpc.host,
    cfg.grpc.port,
    cfg.grpc.use_ssl,
    geom,
    start_date,
    end_date,
    product_ids,
    categories,
    n_results,
)
map_
