# Response of the API

Once the API is called, the response is returned in the form of a protobuf message.

The message is formatted as follows:
```
message SegmentationResponse {
	string wkt = 1;
	bytes segmentation = 2;
	bytes cloud_mask = 3;
	string product_id = 4;
	string quicklook = 5;
	string product_type = 6;
	google.protobuf.Timestamp publication_date = 7;
	google.protobuf.Timestamp creation_date = 8;
	float cloud_cover = 9;
	string browse_url = 10;
	string download_url = 11;
```

Where:
- `wkt` is the polygon of the segmentation
- `segmentation` is the segmentation image encoded in base64
- `cloud_mask` is the cloud mask image encoded in base64
- `product_id` is the ID of the product
- `quicklook` is an URL to quickly visualize the product
- `product_type` is the type of the product
- `publication_date` is the date of publication of the product
- `creation_date` is the date of creation of the product
- `cloud_cover` is the cloud cover percentage of the product
- `browse_url` is an URL to visualize the API in a viewer (e.g. peps)
- `download_url` is the URL the service used to download the product.


If multiple images matches the criterion you specified, the API will return a list of the images.
The segmentation fields contains a geotiff encoded in base64 where each pixel is a category. The categories are defined according to the [CLC level 3](https://land.copernicus.eu/user-corner/technical-library/corine-land-cover-nomenclature-guidelines/html).
The cloud mask is a binary image where 0 is clear and 1 is cloudy. It can be used to remove areas with high uncertainty in the segmentation image.
Once you have decoded the segmentation and the cloud mask, you can start using the data for your use-case.
