import os, shutil
from sklearn.model_selection import train_test_split

'''
Pressupõe que imagens e máscaras estão em um único diretório /img_dst.
Pressupõe que imagens têm sufixo _img e máscaras têm sufixo _msk.
Separa os segmentos em pastas train/validate/test e sub-pastas img/msk.
Garante que os pares img-msk estão no mesmo conjunto (train, validate, ou test).
'''

def create_dataset(img_dst='patches', train_size=0.5, random_state=0):
    # Lista de imagens
    filenames = [filename.split('.')[0][:-4] for filename in os.listdir(img_dst)]

    # Treino: 70%. Validação: 15%. Teste: 15%.
    train, val_test = train_test_split(filenames, train_size=train_size, random_state=random_state)
    val, test       = train_test_split(val_test,  test_size=0.5, random_state=random_state)

    # Cria diretórios train/img, train/msk, validate/img, validate/msk, test/img, test/msk
    for folder in ['train', 'validate', 'test']:
        for subfolder in ['img', 'msk']:
            os.makedirs(os.path.join(img_dst, folder, subfolder), exist_ok=True)

    # Move arquivos
    for folder, filenames in [('train', train), ('validate', val), ('test', test)]:
        for filename in filenames:
            for subfolder in ['img', 'msk']:
                src_path = os.path.join(img_dst, f"{filename}_{subfolder}.png")
                dst_path = os.path.join(img_dst, folder, subfolder, f"{filename}.png")
                shutil.move(src_path, dst_path)
                shutil.move(src_path, dst_path)