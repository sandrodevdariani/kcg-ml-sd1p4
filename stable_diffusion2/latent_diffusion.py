"""
---
title: Latent Diffusion Models
summary: >
 Annotated PyTorch implementation/tutorial of latent diffusion models from paper
 High-Resolution Image Synthesis with Latent Diffusion Models
---

# Latent Diffusion Models

Latent diffusion models use an auto-encoder to map between image space and
latent space. The diffusion model works on the latent space, which makes it
a lot easier to train.
It is based on paper
[High-Resolution Image Synthesis with Latent Diffusion Models](https://papers.labml.ai/paper/2112.10752).

They use a pre-trained auto-encoder and train the diffusion U-Net on the latent
space of the pre-trained auto-encoder.

For a simpler diffusion implementation refer to our [DDPM implementation](../ddpm/index.html).
We use same notations for $\alpha_t$, $\beta_t$ schedules, etc.
"""

from typing import List

import torch
import torch.nn as nn

from .model.vae.autoencoder import Autoencoder
from .model.clip.clip_embedder import CLIPTextEmbedder
from .model.unet.unet import UNetModel
from .constants import AUTOENCODER_PATH, UNET_PATH, LATENT_DIFFUSION_PATH, EMBEDDER_PATH

class DiffusionWrapper(nn.Module):
    """
    *This is an empty wrapper class around the [U-Net](model/unet.html).
    We keep this to have the same model structure as
    [CompVis/stable-diffusion](https://github.com/CompVis/stable-diffusion)
    so that we do not have to map the checkpoint weights explicitly*.
    """

    def __init__(self, diffusion_model: UNetModel):
        super().__init__()
        self.diffusion_model = diffusion_model

    def forward(self, x: torch.Tensor, time_steps: torch.Tensor, context: torch.Tensor):
        return self.diffusion_model(x, time_steps, context)


class LatentDiffusion(nn.Module):
    """
    ## Latent diffusion model

    This contains following components:

    * [AutoEncoder](model/autoencoder.html)
    * [U-Net](model/unet.html) with [attention](model/unet_attention.html)
    * [CLIP embeddings generator](model/clip_embedder.html)
    """
    model: DiffusionWrapper
    first_stage_model: Autoencoder
    cond_stage_model: CLIPTextEmbedder

    def __init__(self,
                 latent_scaling_factor: float,
                 n_steps: int,
                 linear_start: float,
                 linear_end: float,
                 unet_model: UNetModel = None,
                 autoencoder: Autoencoder = None,
                 clip_embedder: CLIPTextEmbedder = None
                 ):
        """
        :param unet_model: is the [U-Net](model/unet.html) that predicts noise
         $\epsilon_\text{cond}(x_t, c)$, in latent space
        :param autoencoder: is the [AutoEncoder](model/autoencoder.html)
        :param clip_embedder: is the [CLIP embeddings generator](model/clip_embedder.html)
        :param latent_scaling_factor: is the scaling factor for the latent space. The encodings of
         the autoencoder are scaled by this before feeding into the U-Net.
        :param n_steps: is the number of diffusion steps $T$.
        :param linear_start: is the start of the $\beta$ schedule.
        :param linear_end: is the end of the $\beta$ schedule.
        """
        super().__init__()
        # Wrap the [U-Net](model/unet.html) to keep the same model structure as
        # [CompVis/stable-diffusion](https://github.com/CompVis/stable-diffusion).
        self.model = DiffusionWrapper(unet_model)
        # Auto-encoder and scaling factor
        self.first_stage_model = autoencoder
        self.latent_scaling_factor = latent_scaling_factor
        # [CLIP embeddings generator](model/clip_embedder.html)
        self.cond_stage_model = clip_embedder

        # Number of steps $T$
        self.n_steps = n_steps

        # $\beta$ schedule
        beta = torch.linspace(linear_start ** 0.5, linear_end ** 0.5, n_steps, dtype=torch.float64) ** 2
        self.beta = nn.Parameter(beta.to(torch.float32), requires_grad=False)
        # $\alpha_t = 1 - \beta_t$
        alpha = 1. - beta
        # $\bar\alpha_t = \prod_{s=1}^t \alpha_s$
        alpha_bar = torch.cumprod(alpha, dim=0)
        self.alpha_bar = nn.Parameter(alpha_bar.to(torch.float32), requires_grad=False)

    @property
    def device(self):
        """
        ### Get model device
        """
        return next(iter(self.model.parameters())).device

    def save_submodels(self, autoencoder_path = AUTOENCODER_PATH, embedder_path = EMBEDDER_PATH, unet_path = UNET_PATH):
        """
        ### Save the model to a checkpoint
        """
        self.first_stage_model.save(autoencoder_path=autoencoder_path)
        self.cond_stage_model.save(embedder_path=embedder_path)
        self.model.diffusion_model.save(unet_path=unet_path)
        # torch.save(self.encoder, encoder_path)
        # torch.save(self.decoder, decoder_path)

    def save(self, latent_diffusion_path = LATENT_DIFFUSION_PATH):
        """
        ### Save the model to a checkpoint
        """
        torch.save(self, latent_diffusion_path)

    def load_submodels(self,  autoencoder_path = AUTOENCODER_PATH, embedder_path = EMBEDDER_PATH, unet_path = UNET_PATH, device = "cuda:0"):
        
        """
        ### Load the model from a checkpoint
        """
        self.first_stage_model = torch.load(autoencoder_path, map_location=device)
        self.first_stage_model.eval()
        self.cond_stage_model = torch.load(embedder_path, map_location=device)
        self.cond_stage_model.eval()
        self.model = DiffusionWrapper(torch.load(unet_path, map_location=device).eval())

    def unload_submodels(self):
        del self.first_stage_model
        del self.cond_stage_model
        del self.model
        torch.cuda.empty_cache()
        self.first_stage_model = None
        self.cond_stage_model = None    
        self.model = None

    def get_text_conditioning(self, prompts: List[str]):
        """
        ### Get [CLIP embeddings](model/clip_embedder.html) for a list of text prompts
        """
        return self.cond_stage_model(prompts)

    def autoencoder_encode(self, image: torch.Tensor):
        """
        ### Get scaled latent space representation of the image

        The encoder output is a distribution.
        We sample from that and multiply by the scaling factor.
        """
        return self.latent_scaling_factor * self.first_stage_model.encode(image).sample()

    def autoencoder_decode(self, z: torch.Tensor):
        """
        ### Get image from the latent representation

        We scale down by the scaling factor and then decode.
        """
        return self.first_stage_model.decode(z / self.latent_scaling_factor)

    def forward(self, x: torch.Tensor, t: torch.Tensor, context: torch.Tensor):
        """
        ### Predict noise

        Predict noise given the latent representation $x_t$, time step $t$, and the
        conditioning context $c$.

        $$\epsilon_\text{cond}(x_t, c)$$
        """
        return self.model(x, t, context)
