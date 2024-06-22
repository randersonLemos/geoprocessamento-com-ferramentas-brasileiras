import os, PIL, copy, rasterio
import numpy as np
from rasterio.windows   import Window
from rasterio.transform import Affine

'''
Código para segmentar uma imagem GeoTIFF de satélite (img_src) do programa CBERS04-A em segmentos (patches) img_dim × img_dim.
Salva os segmentos em formato GeoTIFF com metadados atualizados no diretório /img_dst.
Caso seja fornecido uma máscara (msk_src), pressupõe que seja do programa TerraClass.
Gera imagens com sufixo _img.tif e máscaras com sufixo _msk.tif.
'''

def patch_img_msk(img_src='img.tif', img_dst='patches', img_dim=100, msk_src=None):
    os.makedirs(img_dst, exist_ok=True)

    # Carrega imagem usando RasterIO
    with rasterio.open(img_src) as src:
        # Carrega meta dados da imagem. Código especializado para imagens CBERS-04A
        meta = src.meta
        crs  = src.crs
        img_x_UTM      = meta['transform'].xoff    # Origem da imagem em UTM
        img_y_UTM      = meta['transform'].yoff
        img_res        = meta['transform'][0]      # Metros / pixel
        img_dim_pixels = img_dim
        img_dim_meters = img_dim_pixels * img_res  # Uma imagem N×N pixels com resolução K cobriria um território KN×KN

        # Calcula maior dimensão da imagem, para segmentar a imagem toda
        max_src_dim = max(meta['width'], meta['height'])     
        max_iter    = int(max_src_dim / img_dim_pixels) + 1  # Serão geradas (max_iter)² imagens (e.g. 32² = 1024)

        for it_x in range(max_iter):
            img_x_offset_meters = it_x * img_dim_meters               # Offset do segmento em metros no eixo X
            img_x_offset_pixels = int(img_x_offset_meters / img_res)  # Offset do segmento em pixels no eixo X
            patch_x_UTM         = img_x_UTM + img_x_offset_meters     # Origem do segmento em UTM
            if img_x_offset_pixels + img_dim_pixels > meta['width']:  # Verifica se o segmento estoura o limite
                break

            for it_y in range(max_iter):
                img_y_offset_meters = init_offset_meters + (it_y * img_dim_meters)  # Idem para Y como para X acima
                img_y_offset_pixels = int(img_y_offset_meters / img_res)
                patch_y_UTM         = img_y_UTM - img_y_offset_meters
                if img_y_offset_pixels + img_dim_pixels > meta['height']:
                    break

                # Uso da classe Window do RasterIO para carregar a imagem em segmentos
                window = Window(col_off=img_x_offset_pixels, row_off=img_y_offset_pixels, width=img_dim_pixels, height=img_dim_pixels)
                patch  = src.read(window=window).astype(np.uint8)

                # Atualiza metadados GeoTIFF
                # A transformada afim informa a resolução de metros / pixel
                # Ela também informa as coordenadas de origem (upper-left) da imagem em UTM (atributos .xoff e .yoff)
                affine_old = meta['transform']
                affine_new = Affine(affine_old.a, affine_old.b, patch_x_UTM, affine_old.d, affine_old.e, patch_y_UTM)
                meta_new   = copy.deepcopy(meta)
                meta_new.update({'width': img_dim_pixels, 'height': img_dim_pixels, 'transform': affine_new})

                # Salva a imagem em formato GeoTIFF
                with rasterio.open(f"{img_dst}{os.sep}{img_dst}_{int(affine_new.xoff)}_{int(affine_new.yoff)}_EPSG{crs.to_epsg()}_img.tif", "w", **meta_new) as dst:
                    dst.write(patch)

                # Aproveita as variáveis de coordenada da segmentação da imagem para segmentar a máscara
                # Pressupõe que o arquivo possui os metadados da máscara de segmentação do projeto TerraClass
                if msk_src is not None:
                    with rasterio.open(msk_src) as src2:
                        msk_res_degree             = src2.meta['transform'][0]                                      # Resolução (px): 0.00027777779999999994° / pixel (graus por pixel)
                        msk_res_meters             = msk_res_degree * np.pi * 6371000 / 180                         # Resolução (m):  30.8874820944869 metros / pixel (metros por pixel)
                        transformer_UTM_SIRGAS2000 = Transformer.from_crs(src_b.crs, src2.crs, always_xy=True)
                        patch_lon, patch_lat       = transformer_UTM_SIRGAS2000.transform(patch_x_UTM, patch_y_UTM) # Origem do segmento em coordenadas SIRGAS 2000
                        msk_lon, msk_lat           = src2.meta['transform'].xoff, src2.meta['transform'].yoff       # Origem da máscara em coordenadas SIRGAS 2000
                        Δ_lon, Δ_lat               = abs(msk_lon - patch_lon), abs(msk_lat - patch_lat)             # Offset do segmento em graus SIRGAS 2000
                        Δ_x_pixel, Δ_y_pixel       = int(Δ_lon / msk_res_degree), int(Δ_lat / msk_res_degree)       # Offset do segmento em pixels
                        msk_dim_pixels             = int(img_dim_pixels * (img_res / msk_res_meters)) 
                        window                     = Window(col_off=Δ_x_pixel, row_off=Δ_y_pixel, width=msk_dim_pixels, height=msk_dim_pixels)
                        msk                        = src2.read(window=window)[0]                                    # Shape: (msk_dim_pixels × msk_dim_pixels)
                        msk                        = np.array(PIL.Image.fromarray(msk).resize((img_dim_pixels, img_dim_pixels), resample=PIL.Image.NEAREST)) # Resampling to obtain new shape: (img_dim × img_dim)
                        msk                        = msk.reshape((1, 224, 224))  
                    with rasterio.open(f"{img_dst}{os.sep}{img_dst}_{int(affine_new.xoff)}_{int(affine_new.yoff)}_EPSG{crs.to_epsg()}_msk.tif", "w", **meta_new) as dst:
                        dst.write(msk)