# kcg-ml-sd1p4

[![Build Status](http://103.68.223.207:8111/app/rest/builds/buildType:(id:KcgMlSd1p4_Build)/statusIcon)](http://teamcity/viewType.html?buildTypeId=KcgMlSd1p4_Build&guest=1)

## Summary

- [kcg-ml-sd1p4](#kcg-ml-sd1p4)
  - [Installing requirements](#installing-requirements)
  - [Downloading models](#downloading-models)
  - [Saving submodels](#saving-submodels)
  - [Running `stable_diffusion` scripts](#running-stable_diffusion-scripts)
      - [Embed prompts](#embed-prompts)
      - [Images from embeddings](#images-from-embeddings)
      - [Images from distributions](#images-from-distributions)
      - [Images from temperature range](#images-from-temperature-range)
      - [Images and encodings](#images-and-encodings)
      - [Perturbations on prompts embeddings](#perturbations-on-prompts-embeddings)
  - [Notebooks](#notebooks)

## Installing requirements
```bash
pip3 install -r requirements.txt
```

## Downloading models

Download the currently supported checkpoint, `v1-5-pruned-emaonly.safetensors`, to `./input/model/`.

```bash
./download-model.sh
```

Alternatively, if you prefer to download directly, use [this link.](https://mega.nz/file/AVZnGbzL#EfXN4YINe0Wb7ukiqpCPa7THssugyCQU8pvpMpvxPAw)
## Saving submodels

Start by running this.

This script initializes a `LatentDiffusion` module, load its weights from a checkpoint file at `./input/model/v1-5-pruned-emaonly.safetensors` and then save all submodules.
**Note**: saving these models will take an extra ~5GB of storage.

```bash
python scripts/process_base_model.py input/model/v1-5-pruned-emaonly.safetensors
```

**Command line arguments**

- `-g, --granularity`: Determines the height in the model tree on which to save the submodels. Defaults to `0`, saving all submodels of the `LatentDiffusion` class and all submodels thereof. If `1` is given, it saves only up to the first level, i.e., autoencoder, UNet and CLIP text embedder. *Note*: that the other scripts and notebooks expect this to be ran with `0`.
- `--root_models_path`: Base directory for the models' folder structure. Defaults to the constant `ROOT_MODELS_DIR`, which is expected to be `./input/model/`.
- `--checkpoint_path`: Relative path of the checkpoint file (*.safetensors). Defaults to the constant `CHECKPOINT_PATH`, which is expected to be `'./input/model/v1-5-pruned-emaonly.safetensors' = os.path.join(ROOT_MODELS_DIR, 'v1-5-pruned-emaonly.safetensors')`.

### Text To Image

Takes in a prompt and generates images
These are the available CLI arguments:

```
options:
  --prompt        PROMPT
                        An array of strings to help guide the generation process
  --batch_size   BATCH_SIZE
                        How many images to generate at once
  --output        OUTPUT
                        Number of folders to
  --sampler       SAMPLER
                        Name of the sampler to use
  --checkpoint_path     CHECKPOINT_PATH
                        Path to the checkpoint file
  --flash         FLASH
                        Whether to use flash attention
  --steps         STEPS
                        Number of steps to use
  --cgf_scale         SCALE
                        Unconditional guidance scale: eps = eps(x, empty) + scale * (eps(x, cond) - eps(x, empty))
  --seed      SEED
                        Array of seed for the image generation: example '0, 1, 0, 7', Its better if the size of the array is the same as the number of generated images
  --low-vram      LOW_VRAM
                        Limit vram usage
  --force_cpu     FORCE_CPU
                        Force cpu usage
  --cuda_device   CUDA_DEVICE
                        Cuda device to use for generation process
  --num_images    NUM_IMAGES
                        Number of images to output
```

#### Example Usage:

``` shell
python3 ./scripts/text_to_image.py --prompt "character, chibi, waifu, side scrolling, white background, centered" --checkpoint_path "./input/model/v1-5-pruned-emaonly.safetensors" --batch_size 1 --num_images 6
```

## Running `stable_diffusion` scripts

There are five other new scripts besides `scripts/process_base_model.py`.

#### Embed prompts

Saves a tensor of a batch of prompts embeddings, and the tensor for the null prompt `""`.

Command:

```bash
python3 ./scripts/embed_prompts.py --prompts 'A painting of a computer virus', 'An old photo of a computer scientist', 'A computer drawing a computer'
```

**Command line arguments**

- `-p, --prompts`: The prompts to embed. Defaults to `['A painting of a computer virus', 'An old photo of a computer scientist']`.
- `--embedded_prompts_dir`: The path to the directory containing the embedded prompts tensors. Defaults to a constant `EMBEDDED_PROMPTS_DIR`, which is expected to be `'./input/embedded_prompts/'`.
-
#### Images from embeddings

Only run this _after_ generating the embedded prompts with the [above script](#embed-prompts).

Try running:

```bash
python3 ./scripts/generate_images_from_embeddings.py --num_seeds 4 --temperature 1.2 --ddim_eta 0.2
```

**Command line arguments**

- `-p, --embedded_prompts_dir`: The path to the directory containing the embedded prompts tensors. Defaults to the `EMBEDDED_PROMPTS_DIR` constant, which is expected to be `'./input/embedded_prompts/'`.
- `-od, --output_dir`: The output directory. Defaults to the `OUTPUT_DIR` constant, which is expected to be `'./output/noise-tests/from_embeddings'`.
- `--num_seeds`: Number of random seeds to use. Defaults to `3`. Ranges from `1` to `7`.
- `-bs, --batch_size`: Batch size to use. Defaults to `1`.
- `-t, --temperature`: Sampling temperature. Defaults to `1.0`.
- `--ddim_eta`: Amount of noise to readd during the sampling process. Defaults to `0.0`.
- `--clear_output_dir`: Either to clear or not the output directory before running. Defaults to `False`.
- `--cuda_device`: CUDA device to use. Defaults to `get_device()`.

#### Images from distributions

Try running:
```bash
python3 ./scripts/generate_images_from_distributions.py -d 4 --params_steps 4 --params_range 0.49 0.54 --num_seeds 4 --temperature 1.2 --ddim_eta 1.2
```

**Command line arguments**

- `-p, --prompt`: The prompt to generate images from. Defaults to `"A woman with flowers in her hair in a courtyard, in the style of Frank Frazetta"`.
- `-od, --output_dir`: The output directory. Defaults to the `OUTPUT_DIR` constant, which should be `"./output/noise-tests/from_distributions"`.
- `-cp, --checkpoint_path`: The path to the checkpoint file to load from. Defaults to the `CHECKPOINT_PATH` constant, which should be `"./input/model/v1-5-pruned-emaonly.safetensors"`.
- `-F, --fully_initialize`: Whether to fully initialize or not. Defaults to `False`.
- `-d, --distribution_index`: The distribution index to use. Defaults to `4`. Options: 0: "Normal", 1: "Cauchy", 2: "Gumbel", 3: "Laplace", 4: "Logistic".
- `-bs, --batch_size`: The batch size to use. Defaults to `1`.
- `--params_steps`: The number of steps for the parameters. Defaults to `3`.
- `--params_range`: The range of parameters. Defaults to `[0.49, 0.54]`.
- `--num_seeds`: Number of random seeds to use. Defaults to `3`.
- `-t, --temperature`: Sampling temperature. Defaults to `1.0`.
- `--ddim_eta`: Amount of noise to readd during the sampling process. Defaults to `0.0`.
- `--clear_output_dir`: Either to clear or not the output directory before running. Defaults to `False`.
- `--cuda_device`: CUDA device to use. Defaults to `"get_device()"`.

#### Images from temperature range

Try running:

```bash
python3 ./scripts/generate_images_from_temperature_range.py -d 4 --params_range 0.49 0.54 --params_steps 3 --temperature_steps 3 --temperature_range 0.8 2.0
```

**Command line arguments**

- `-p, --prompt`: The prompt to generate images from. Defaults to `"A woman with flowers in her hair in a courtyard, in the style of Frank Frazetta"`.
- `-od, --output_dir`: The output directory. Defaults to the `OUTPUT_DIR` constant, which is expected to be `"./output/noise-tests/temperature_range"`.
- `-cp, --checkpoint_path`: The path to the checkpoint file to load from. Defaults to the `CHECKPOINT_PATH` constant, which is expected to be `"./input/model/v1-5-pruned-emaonly.safetensors"`.
- `-F, --fully_initialize`: Whether to fully initialize or not. Defaults to `False`.
- `-d, --distribution_index`: The distribution index to use. Defaults to 4. Options: 0: "Normal", 1: "Cauchy", 2: "Gumbel", 3: "Laplace", 4: "Logistic".
- `-s, --seed`: The seed value. Defaults to `2982`.
- `-bs, --batch_size`: The batch size to use. Defaults to `1`.
- `--params_steps`: The number of steps for the parameters. Defaults to `3`.
- `--params_range`: The range of parameters. Defaults to `[0.49, 0.54]`.
- `--temperature_steps`: The number of steps for the temperature. Defaults to `3`.
- `--temperature_range`: The range of temperature. Defaults to `[1.0, 4.0]`.
- `--ddim_eta`: The value of ddim_eta. Defaults to `0.1`.
- `--clear_output_dir`: Whether to clear the output directory or not. Defaults to `False`.
- `--cuda_device`: The CUDA device to use. Defaults to `"get_device()"`.


#### Images and encodings

Try running:
```bash
python3 ./scripts/generate_images_and_encodings.py --prompt "An oil painting of a computer generated image of a geometric pattern" --num_iterations 10
```

**Command line arguments**

- `--batch_size`: How many images to generate at once. Defaults to `1`.
- `--num_iterations`: How many times to iterate the generation of a batch of images. Defaults to `10`.
- `--prompt`: The prompt to render. It is an optional argument. Defaults to `"a painting of a cute monkey playing guitar"`.
- `--cuda_device`: CUDA device to use for generation. Defaults to `"get_device()"`.

#### Perturbations on prompts embeddings

Try running:
```bash
python3 ./scripts/embed_prompts_and_generate_images.py
```
Outputs in: `./output/disturbing_embeddings`

- `--prompt`: The prompt to embed. Defaults to `"A woman with flowers in her hair in a courtyard, in the style of Frank Frazetta"`.
- `--num_iterations`: The number of iterations to batch-generate images. Defaults to `8`.
- `--seed`: The noise seed used to generate the images. Defaults to `2982`.
- `--noise_multiplier`: The multiplier for the amount of noise used to disturb the prompt embedding. Defaults to `0.01`.
- `--cuda_device`: The CUDA device to use. Defaults to `"get_device()"`.


#### Random Pormpts Generation and Disturbing Embeddings Image Generation

Try running:

```bash
python3 ./scripts/data_bounding_box_and_score_and_embedding_dataset.py
```

- `--save_embeddings`: If True, the disturbed embeddings will be saved to disk. Defaults to `False`.
- `cfg_strength`: Configuration strength. Defaults to `12`.
- `embedded_prompts_dir`: The path to the directory containing the embedded prompts tensors. Defaults to a constant EMBEDDED_PROMPTS_DIR, which is expected to be `'./input/embedded_prompts/'`
- `num_iterations`: The number of iterations to batch-generate images. Defaults to `8`.
- `batch_size`: The number of images to generate per batch. Defaults to `1`.
- `seed`: The noise seed used to generate the images. Defaults to `2982`.
- `noise_multiplier`: The multiplier for the amount of noise used to disturb the prompt embedding. Defaults to `0.008`.
- `cuda_device`: The CUDA device to use. Defaults to `'get_device()'`.
- `clear_output_dir`: If True, the output directory will be cleared before generating images. Defaults to `False`.
- `random_walk`: Random walk on the embedding space, with the prompt embedding as origin. Defaults to False.


#### Image Grid Creator

The Image Grid Creator is a script that generates a grid of images from a directory or a zip file containing images. 

##### Usage

Run the script with the following command:

    python script_name.py --input_path <input_path> --n <number of images width> --m <number of images height> --img_size <size of grid image>
