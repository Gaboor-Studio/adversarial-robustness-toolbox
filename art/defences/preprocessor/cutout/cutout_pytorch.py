# MIT License
#
# Copyright (C) The Adversarial Robustness Toolbox (ART) Authors 2022
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
This module implements the cutout data augmentation defence in PyTorch.
| Paper link: https://arxiv.org/abs/1708.04552
| Please keep in mind the limitations of defences. For more information on the limitations of this defence,
    see https://arxiv.org/abs/1803.09868 . For details on how to evaluate classifier security in general, see
    https://arxiv.org/abs/1902.06705
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from typing import Optional, Tuple, TYPE_CHECKING

from art.defences.preprocessor.preprocessor import PreprocessorPyTorch

import numpy as np

if TYPE_CHECKING:
    import torch


class CutoutPyTorch(PreprocessorPyTorch):
    """
    Implement the Cutout data augmentation defense
    """

    params = ['length', "channels_first"]

    def __init__(
        self,
        length: int = 16,
        channels_first: bool = False,
        apply_fit: bool = False,
        apply_predict: bool = True,
        device_type: str = "gpu",
        verbose: bool = False,
    ):
        """
        Create an instance of Cutout data augmentation.
        :param length: length of the cutout bounding box.
        :param channels_first: Set channels first or last.
        :param apply_fit: True if applied during fitting/training.
        :param apply_predict: True if applied during predicting.
        :param device_type: Type of device on which the classifier is run, either `gpu` or `cpu`.
        :param verbose: Show progress bars.
        """
        super().__init__(
            device_type=device_type,
            is_fitted=True,
            apply_fit=apply_fit,
            apply_predict=apply_predict,
        )
        self.length = length
        self.channels_first = channels_first
        self.verbose = verbose
        self._check_params()

    def forward(
        self, x: "torch.Tensor", y: Optional["torch.Tensor"] = None
    ) -> Tuple["torch.Tensor", Optional["torch.Tensor"]]:
        """
        Apply Cutout data augmentation to sample `x`.
        :param x: Sample to augment with shape `(length, channel)` or an array of sample arrays with shape
                  (length,) or (length, channel).
        :param y: Labels of the sample `x`. This function does not affect them in any way.
        :return: Data augmented sample.
        """
        import torch  # lgtm [py/repeated-import]

        x_ndim = x.ndim

        if x_ndim == 4:
            if self.channels_first:
                # NCHW
                n, c, h, w = x.shape
            else:
                # NHWC
                n, h, w, c = x.shape
        else:
            raise ValueError("Unrecognized input dimension. Cutout can only be applied to image data.")

        # generate a random bounding box per image
        masks = torch.ones(*x.shape)
        for i in range(n):
            # uniform sampling
            cy = torch.randint(h)
            cx = torch.randint(w)
            bby1 = torch.clamp(cy - self.length // 2, 0, h)
            bbx1 = torch.clamp(cx - self.length // 2, 0, w)
            bby2 = torch.clamp(cy + self.length // 2, 0, h)
            bbx2 = torch.clamp(cx + self.length // 2, 0, w)

            if self.channels_first:
                masks[i, :, bbx1:bbx2, bby1:bby2] = 0
            else:
                masks[i, bbx1:bbx2, bby1:bby2, :] = 0
        
        x_aug = x * masks

        return x_aug, y

    def _check_params(self) -> None:
        if self.length <= 0:
            raise ValueError('Bounding box length must be positive.')
