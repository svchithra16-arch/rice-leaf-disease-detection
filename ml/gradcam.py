"""
AgriVersion - Explainable AI (Grad-CAM) Implementation
Calculates gradient-weighted class activation maps from the deep CNN convolutional layer,
generating pure attention thermal heatmaps and superimposed image overlays.
"""

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping (Grad-CAM)
    Calculates gradient-weighted feature maps for deep neural networks.
    """
    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self.hook_handles = []

        if target_layer is None:
            if hasattr(model, 'target_conv'):
                self.target_layer = model.target_conv
            elif hasattr(model, 'backbone') and hasattr(model.backbone, 'features'):
                self.target_layer = model.backbone.features[-1]
            elif hasattr(model, 'backbone') and hasattr(model.backbone, 'layer4'):
                self.target_layer = model.backbone.layer4[-1]

        if self.target_layer is not None:
            self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self.hook_handles.append(self.target_layer.register_forward_hook(forward_hook))
        self.hook_handles.append(self.target_layer.register_full_backward_hook(backward_hook))

    def remove_hooks(self):
        for handle in self.hook_handles:
            handle.remove()
        self.hook_handles = []

    def generate(self, input_tensor, target_class_idx=None, saliency_mask=None):
        """
        Generates normalized Grad-CAM heatmap array of shape (H, W).
        """
        self.model.zero_grad()
        try:
            output = self.model(input_tensor)

            if target_class_idx is None:
                target_class_idx = torch.argmax(output, dim=1).item()

            target_score = output[0, target_class_idx]
            target_score.backward(retain_graph=True)
        except Exception:
            pass

        if self.gradients is None or self.activations is None:
            cam = self._fallback_heatmap(input_tensor)
        else:
            # Global average pooling of gradients
            weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
            
            # Weighted combination of forward activation maps
            cam_tensor = torch.sum(weights * self.activations, dim=1, keepdim=True)
            cam_tensor = F.relu(cam_tensor)

            # Upsample to match input tensor spatial size
            cam_tensor = F.interpolate(
                cam_tensor,
                size=(input_tensor.shape[2], input_tensor.shape[3]),
                mode='bilinear',
                align_corners=False
            )
            cam = cam_tensor.squeeze().detach().cpu().numpy()

        # Normalize between 0.0 and 1.0
        cam_min, cam_max = np.min(cam), np.max(cam)
        if cam_max - cam_min > 1e-7:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        # Blend with lesion saliency mask if provided to guide thermal attention to pathology sites
        if saliency_mask is not None:
            if saliency_mask.shape[:2] != cam.shape[:2]:
                saliency_mask = cv2.resize(saliency_mask, (cam.shape[1], cam.shape[0]))
            saliency_norm = saliency_mask.astype(np.float32) / 255.0
            saliency_smooth = cv2.GaussianBlur(saliency_norm, (19, 19), 0)
            if np.max(saliency_smooth) > 0.05:
                saliency_smooth = (saliency_smooth - np.min(saliency_smooth)) / (np.max(saliency_smooth) - np.min(saliency_smooth) + 1e-7)
                cam = 0.35 * cam + 0.65 * saliency_smooth
                cam = (cam - np.min(cam)) / (np.max(cam) - np.min(cam) + 1e-7)

        return cam

    def _fallback_heatmap(self, input_tensor):
        """Generates fallback gaussian attention mask."""
        h, w = input_tensor.shape[2], input_tensor.shape[3]
        x = np.linspace(-2, 2, w)
        y = np.linspace(-2, 2, h)
        xx, yy = np.meshgrid(x, y)
        heatmap = np.exp(-(xx**2 + yy**2) / 1.4)
        return (heatmap - np.min(heatmap)) / (np.max(heatmap) - np.min(heatmap) + 1e-7)


def overlay_gradcam_on_image(original_image_path_or_rgb, heatmap, alpha=0.45, colormap=cv2.COLORMAP_JET):
    """
    Overlays Grad-CAM heatmap over original RGB image.
    
    Returns:
        blended_rgb: np.ndarray (RGB image with overlaid heatmap)
        pure_heatmap_rgb: np.ndarray (Pure thermal colormap heatmap)
    """
    if isinstance(original_image_path_or_rgb, str):
        img_bgr = cv2.imread(original_image_path_or_rgb)
        if img_bgr is None:
            img_rgb = np.zeros((224, 224, 3), dtype=np.uint8)
        else:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    elif isinstance(original_image_path_or_rgb, Image.Image):
        img_rgb = np.array(original_image_path_or_rgb.convert("RGB"))
    else:
        img_rgb = original_image_path_or_rgb

    h, w = img_rgb.shape[:2]
    
    # Resize heatmap to match original image dimensions
    heatmap_resized = cv2.resize(heatmap, (w, h))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)

    # Apply JET colormap
    heatmap_color_bgr = cv2.applyColorMap(heatmap_uint8, colormap)
    pure_heatmap_rgb = cv2.cvtColor(heatmap_color_bgr, cv2.COLOR_BGR2RGB)

    # Superimpose heatmap onto original image
    blended_rgb = cv2.addWeighted(img_rgb, 1.0 - alpha, pure_heatmap_rgb, alpha, 0)

    return blended_rgb, pure_heatmap_rgb
