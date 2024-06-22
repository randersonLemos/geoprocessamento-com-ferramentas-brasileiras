import numpy as np
import geopandas as gpd
from pyproj import Transformer
from rasterio.features import rasterize

'''
A partir de coordenadas UTM, que podem ter sido obtidas na segmentação de uma imagem, segmenta um shapefile.
Para isso, carrega do shapefile apenas os polígonos que interseccionam um bounding box do patch.
Necessita receber dimensão da imagem em pixels e sua resolução de metros / pixel. 
'''

def rasterize_shapefile_patch(msk_src, patch_x_UTM, patch_y_UTM, img_dim_pixels=100, img_res=8):
	# Reads from a shapefile the polygons which intersect our image patch bounding box in UTM
	img_dim_meters = img_dim_pixels * img_res
	bbox_UL_x_UTM, bbox_UL_y_UTM = patch_x_UTM, patch_y_UTM
	bbox_LR_x_UTM, bbox_LR_y_UTM = bbox_UL_x_UTM + img_dim_meters, bbox_UL_y_UTM - img_dim_meters

	# Transforms from meters (UTM) to lon/lat degrees (WGS 84)
	transformer_UTM_WGS84    = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
	bbox_UL_lon, bbox_UL_lat = transformer_UTM_WGS84.transform(bbox_UL_x_UTM, bbox_UL_y_UTM)
	bbox_LR_lon, bbox_LR_lat = transformer_UTM_WGS84.transform(bbox_LR_x_UTM, bbox_LR_y_UTM)

	# Reading shapefile patch
	gdf = gpd.read_file(msk_src, bbox=box(minx=bbox_UL_lon, maxx=bbox_LR_lon, miny=bbox_LR_lat, maxy=bbox_UL_lat))

	# If there are no polygons in the bounding box, produce an empty mask of zeros, otherwise rasterize the shapefile
	if len(gdf.index) == 0:
	    rasterized_image = np.zeros((img_dim_pixels, img_dim_pixels))
	else:
	    transform = rasterio.transform.from_bounds(west=bbox_UL_lon, south=bbox_LR_lat, east=bbox_LR_lon, north=bbox_UL_lat, width=img_dim_pixels, height=img_dim_pixels)
	    rasterized_image = rasterize(
	        [(geometry, value) for geometry, value in zip(gdf['geometry'], gdf['COD_CLASSE'])],
	        out_shape=(img_dim_pixels, img_dim_pixels), transform=transform, fill=0, all_touched=True, dtype='float32'
	        )
	msk = rasterized_image[None, : , : ]