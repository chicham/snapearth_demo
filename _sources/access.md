# How to use the API

## Accessing the API

The API is a gRPC service that can be queried using multiple way.
- Using a bash script with the `grpcurl` command
- By implementing a gRPC client in your language of choice

### Using grpcurl

You can directly use the API with grpcurl by using the following command:

```bash
grpcurl url -d '{"n_results": 5, "start_date": "2021-01-01T00:00:00Z", "end_date": "2022-01-01T00:00:00Z", "wkt": "MULTIPOLYGON (((1.6415459999999999 48.6570210000000003, 2.5066069999999998 48.6616240000000033, 2.5143049999999998 48.6782680000000028, 2.5817120000000000 48.8229529999999983, 2.6498390000000001 48.9676520000000011, 2.7181340000000001 49.1124610000000033, 2.7869250000000001 49.2572189999999992, 2.8559869999999998 49.4018480000000011, 2.9250820000000002 49.5464559999999992, 2.9757820000000001 49.6517830000000018, 1.6142719999999999 49.6444299999999998, 1.6415459999999999 48.6570210000000003)))" }' earthsignature.snapearth.eu:443 snapearth.api.v1.database.DatabaseProductService.ListSegmentation > res.pbtxt
```

It is important to note that all the fields are note required and by default you will get the latest products in the database.
The fields are used to restrict the results:

- `n_results`: the number of results to return
- `start_date`: the start date of the results
- `end_date`: the end date of the results
- `wkt`: the WKT of the area of interest


### Implementing a gRPC client

The other way to use the API is to implement a gRPC client. An example client in python can be found in the [snapearth_demo](https://github.com/chicham/snapearth_demo#alternative-implementing-a-client) repository.
