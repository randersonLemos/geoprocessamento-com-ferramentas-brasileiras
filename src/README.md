# Função de segmentação de imagens e máscaras

## Interface
**patch_img_msk(img_src='img.tif', img_dst='patches', img_dim=100, msk_src=None)**


## Descrição
A função `patch_img_msk` segmenta uma imagem GeoTIFF de satélite (img_src) do programa CBERS04-A em segmentos (patches) de tamanho `img_dim` x `img_dim`. Os segmentos são salvos em formato GeoTIFF com metadados atualizados no diretório `img_dst`. Se fornecida uma máscara (`msk_src`), assume-se que é do programa TerraClass. Gera imagens com sufixo `_img.tif` e máscaras com sufixo `_msk.tif`.

## Parâmetros
- **img_src** (`str`): Caminho para a imagem de entrada no formato GeoTIFF. Padrão é `'img.tif'`.
- **img_dst** (`str`): Diretório onde os patches serão salvos. Padrão é `'patches'`.
- **img_dim** (`int`): Dimensão dos patches (em pixels). Padrão é `100`.
- **msk_src** (`str`, opcional): Caminho para a máscara de segmentação no formato GeoTIFF. Padrão é `None`.

## Funcionalidade
1. **Criação do Diretório de Saída**: Cria o diretório especificado em `img_dst` caso ele não exista.
2. **Leitura da Imagem de Entrada**: Usa a biblioteca `rasterio` para ler a imagem especificada em `img_src`.
   - Extrai metadados da imagem, incluindo sistema de coordenadas (CRS), resolução (metros por pixel) e origem (coordenadas UTM).
3. **Cálculo de Dimensões e Iterações**:
   - Calcula a maior dimensão da imagem e o número máximo de iterações necessárias para cobrir toda a imagem com patches de dimensão `img_dim`.
4. **Segmentação da Imagem**:
   - Para cada patch, calcula o offset em metros e pixels, e usa a classe `Window` do `rasterio` para extrair o segmento da imagem.
   - Atualiza os metadados GeoTIFF para refletir a nova origem e resolução do patch.
   - Salva o patch no diretório de saída com o sufixo `_img.tif`.
5. **Segmentação da Máscara (opcional)**:
   - Se uma máscara (`msk_src`) for fornecida, carrega a máscara e calcula os offsets necessários.
   - Segmenta a máscara utilizando o mesmo processo descrito para a imagem, ajustando para a resolução da máscara.
   - Redimensiona a máscara para combinar com a dimensão do patch e salva no diretório de saída com o sufixo `_msk.tif`.


# Função de rasterização de shapefile

## Interface
rasterize_shapefile_patch(msk_src, patch_x_UTM, patch_y_UTM, img_dim_pixels=100, img_res=8)

## Descrição
A função `rasterize_shapefile_patch` segmenta um shapefile a partir de coordenadas UTM, que podem ter sido obtidas na segmentação de uma imagem. Carrega apenas os polígonos que interseccionam um bounding box do patch. É necessário fornecer a dimensão da imagem em pixels e sua resolução em metros por pixel.

## Parâmetros
- **msk_src** (`str`): Caminho para o shapefile a ser segmentado.
- **patch_x_UTM** (`float`): Coordenada UTM x da origem do patch.
- **patch_y_UTM** (`float`): Coordenada UTM y da origem do patch.
- **img_dim_pixels** (`int`): Dimensão do patch em pixels. Padrão é `100`.
- **img_res** (`float`): Resolução da imagem em metros por pixel. Padrão é `8`.

## Funcionalidade
1. **Cálculo do Bounding Box**:
   - Calcula o bounding box do patch em coordenadas UTM.
   - Determina as coordenadas dos cantos superior esquerdo (UL) e inferior direito (LR) do bounding box.
2. **Transformação de Coordenadas**:
   - Transforma as coordenadas do bounding box de UTM para graus de longitude/latitude (WGS 84) usando a biblioteca `pyproj`.
3. **Leitura do Shapefile**:
   - Carrega do shapefile (`msk_src`) apenas os polígonos que interseccionam o bounding box em graus.
4. **Rasterização**:
   - Se não houver polígonos no bounding box, gera uma máscara vazia de zeros.
   - Caso contrário, rasteriza os polígonos do shapefile em uma máscara de dimensão `img_dim_pixels` x `img_dim_pixels`.
   - A máscara rasterizada é criada com base nos polígonos e seus valores de classe (`COD_CLASSE`).
5. **Formatação da Máscara**:
   - A máscara rasterizada é formatada para ter uma forma adequada para processamento posterior.


# Função de remoção de dados vazios

## Interface
remove_empty_data(img_src, msk_src, channel_order='channels_first')

## Descrição
A função `remove_empty_data` elimina da máscara (`msk_src`) todo pixel de classificação cujo pixel multi-canal associado na imagem (`img_src`) é nulo.

## Parâmetros
- **img_src** (`str`): Caminho para a imagem multi-canal no formato GeoTIFF.
- **msk_src** (`str`): Caminho para a máscara no formato GeoTIFF.
- **channel_order** (`str`): Ordem dos canais na imagem. Pode ser `'channels_first'` (canais primeiro) ou `'channels_last'` (canais por último). Padrão é `'channels_first'`.

## Funcionalidade
1. **Leitura da Imagem**:
   - Usa a biblioteca `rasterio` para ler a imagem multi-canal especificada em `img_src`.
2. **Leitura da Máscara**:
   - Usa a biblioteca `rasterio` para ler a máscara especificada em `msk_src`.
3. **Eliminação de Pixels Nulos**:
   - Verifica a ordem dos canais especificada por `channel_order`.
   - Se `channel_order` for `'channels_first'`, elimina pixels da máscara onde qualquer canal da imagem multi-canal associada é nulo.
   - Se `channel_order` for `'channels_last'`, realiza a mesma operação considerando a ordem dos canais apropriada.
4. **Escrita dos Dados**:
   - Atualiza a imagem e a máscara com os dados processados e escreve de volta nos arquivos originais.


# Função criação de dataset

## Interface
create_dataset(img_dst='patches', train_size=0.5, random_state=0)

## Descrição
A função `create_dataset` organiza imagens e máscaras em diretórios específicos para treinamento, validação e teste. Assume que as imagens e máscaras estão em um único diretório (`img_dst`), com imagens tendo sufixo `_img` e máscaras tendo sufixo `_msk`. Garante que os pares imagem-máscara estão no mesmo conjunto (treino, validação ou teste).

## Parâmetros
- **img_dst** (`str`): Diretório contendo as imagens e máscaras. Padrão é `'patches'`.
- **train_size** (`float`): Proporção do conjunto de dados a ser usada para treinamento. Padrão é `0.5`.
- **random_state** (`int`): Semente para geração de números aleatórios usada para replicabilidade. Padrão é `0`.

## Funcionalidade
1. **Listagem dos Arquivos**:
   - Lista os nomes dos arquivos no diretório `img_dst`, removendo os sufixos `_img` e `_msk` e as extensões.
2. **Divisão do Conjunto de Dados**:
   - Divide os nomes dos arquivos em conjuntos de treinamento, validação e teste usando `train_test_split` do `sklearn`.
   - Proporções padrão: Treinamento 70%, Validação 15%, Teste 15%.
3. **Criação dos Diretórios**:
   - Cria os diretórios `train/img`, `train/msk`, `validate/img`, `validate/msk`, `test/img`, `test/msk` dentro de `img_dst`.
4. **Movimentação dos Arquivos**:
   - Move os arquivos de imagens e máscaras para os diretórios apropriados de treinamento, validação e teste, mantendo os pares juntos.
