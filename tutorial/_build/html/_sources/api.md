# API Overview

## What is EarthSignature

The project EarthSignature is a gRPC API that allows to query a database of semantically interpreted Sentinel2 product. The service uses an innovative semantic segmentation model to classify each pixels from a Sentinel2 product into one of the CORINE Land Cover classes.
The products are downloaded and processed by the service everyday. The product published at a day D are available in the service at day D+2.
The service is currently open for anyone to use and a live demonstrator is available on [mybinder](https://mybinder.org/v2/gh/chicham/snapearth_demo/HEAD?urlpath=%2Fvoila%2Frender%2Fdemo.ipynb)
