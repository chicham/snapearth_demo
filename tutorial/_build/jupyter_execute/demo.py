#!/usr/bin/env python

# # Demonstator

# In[1]:


from datetime import datetime, timedelta

import ipywidgets as widgets
from ipywidgets.widgets.widget_layout import Layout
import nest_asyncio
from IPython.display import clear_output, display
from ipywidgets.widgets.widget_box import GridBox, HBox

from utils import EUROPE_COORDINATES, DemoConfig, plot_responses

nest_asyncio.apply()

cfg: DemoConfig = DemoConfig.from_environ(
    {
        "SNAPEARTH_GRPC_HOST": "earthsignature.snapearth.eu",
        "SNAPEARTH_GRPC_PORT": 443,
        "SNAPEARTH_GRPC_USE_SSL": True,
        "SNAPEARTH_GRPC_KEEPALIVE_TIMEOUT_MS": 60000,
        "SNAPEARTH_GRPC_MAX_RECEIVE_MESSAGE_LENGTH": 10**20,
        "SNAPEARTH_GRPC_MAX_SEND_MESSAGE_LENGTH": 10**20,
    },
)

style = {"description_width": "initial"}
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
    style=style,
)

categories = widgets.Text(
    value="",
    description="Categories (comma separated)",
    disabled=False,
    style=style,
)

n_results = widgets.IntSlider(
    value=cfg.grpc.max_results,
    min=1,
    max=20,
    step=1,
    description="Max results",
    disabled=False,
)

submit = widgets.Button(description="Submit")
output = widgets.Output()


def on_click(_):
    output.clear_output()
    with output:
        map_ = plot_responses(
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
        display(map_)


submit.on_click(on_click)


# In[ ]:


form = widgets.VBox(
    children=[geom, start_date, end_date, product_ids, categories, n_results, submit],
)
display(
    GridBox(
        children=[form, output],
        layout=Layout(
            grid_template_rows="auto",
            grid_template_columns="30% auto",
            grid_gap="5px 10px",
        ),
    ),
)
