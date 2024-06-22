import rasterio
import numpy as np

'''
Elimina da máscara todo pixel de classificação cujo pixel multi-canal associado da imagem é nulo.
'''

def remove_empty_data(img_src, msk_src, channel_order='channels_first'):
    with rasterio.open(img_src) as src1:
        img = src.read(src1)
        with rasterio.open(msk_src) as src2:
            msk = src.read(src2)
            if channel_order == 'channels_first':
                msk *= ~np.logical_and(np.logical_and(img[0], img[1]), img[2])
            elif channel_order == 'channels_last':
                msk *= ~np.logical_and(np.logical_and(img[:,:,0], img[:,:,1]), img[:,:,2])
            else:
                pass
            src1.write(img)
            src2.write(msk)