"""
AgriVersion - Deep CNN Model Architectures for Rice Leaf Disease Classification
Includes RiceNet (Custom Deep Residual SE-CNN), MobileNetV2, and ResNet50 backbones.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class SqueezeExcitation(nn.Module):
    """Squeeze-and-Excitation channel attention block."""
    def __init__(self, channels, reduction=16):
        super(SqueezeExcitation, self).__init__()
        self.fc1 = nn.Linear(channels, max(channels // reduction, 8))
        self.fc2 = nn.Linear(max(channels // reduction, 8), channels)

    def forward(self, x):
        b, c, _, _ = x.size()
        squeeze = x.view(b, c, -1).mean(dim=2)
        excitation = F.relu(self.fc1(squeeze), inplace=True)
        excitation = torch.sigmoid(self.fc2(excitation)).view(b, c, 1, 1)
        return x * excitation


class ResidualConvBlock(nn.Module):
    """Residual Convolutional Block with BatchNorm and SE-Attention."""
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualConvBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.se = SqueezeExcitation(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        residual = self.shortcut(x)
        out = F.relu(self.bn1(self.conv1(x)), inplace=True)
        out = self.bn2(self.conv2(out))
        out = self.se(out)
        out = F.relu(out + residual, inplace=True)
        return out


class RiceNet(nn.Module):
    """
    RiceNet - High-Accuracy Deep Residual Squeeze-and-Excitation CNN
    Optimized for fine-grained leaf pathology, spot texture extraction, and Grad-CAM interpretability.
    """
    def __init__(self, num_classes=20):
        super(RiceNet, self).__init__()
        
        # Initial stem
        self.stem = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Residual Feature Stages
        self.stage1 = self._make_stage(64, 128, num_blocks=2, stride=2)
        self.stage2 = self._make_stage(128, 256, num_blocks=3, stride=2)
        self.stage3 = self._make_stage(256, 512, num_blocks=3, stride=2)
        
        # Target layer for Grad-CAM
        self.target_conv = nn.Sequential(
            nn.Conv2d(512, 512, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True)
        )

        # Global Pooling and Classifier
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

    def _make_stage(self, in_channels, out_channels, num_blocks, stride):
        layers = [ResidualConvBlock(in_channels, out_channels, stride=stride)]
        for _ in range(1, num_blocks):
            layers.append(ResidualConvBlock(out_channels, out_channels, stride=1))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.stem(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.target_conv(x)
        x = self.global_pool(x)
        x = torch.flatten(x, 1)
        logits = self.classifier(x)
        return logits


class RiceMobileNetV2(nn.Module):
    """MobileNetV2 transfer backbone for ultra-fast edge inference."""
    def __init__(self, num_classes=20, pretrained=True):
        super(RiceMobileNetV2, self).__init__()
        weights = models.MobileNet_V2_Weights.DEFAULT if pretrained else None
        self.backbone = models.mobilenet_v2(weights=weights)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)


class RiceResNet50(nn.Module):
    """ResNet50 transfer backbone for high-capacity benchmark comparisons."""
    def __init__(self, num_classes=20, pretrained=True):
        super(RiceResNet50, self).__init__()
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet50(weights=weights)
        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)


def get_model(model_name="ricenet", num_classes=20):
    """Model factory returning specified architecture."""
    name = model_name.lower()
    if name in ["cnn_pca_vqc", "vqc", "quantum"]:
        from ml.quantum_vqc import HybridCNNPCAVQC
        return HybridCNNPCAVQC(num_classes=num_classes)
    elif name == "mobilenetv2":
        return RiceMobileNetV2(num_classes=num_classes, pretrained=False)
    elif name == "resnet50":
        return RiceResNet50(num_classes=num_classes, pretrained=False)
    else:
        return RiceNet(num_classes=num_classes)

