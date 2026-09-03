import sys
from pathlib import Path
import torch
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DSEG_DIR = PROJECT_ROOT / "dseg_models-main" / "dseg_models-main"
DSEG_MODELS_DIR = DSEG_DIR / "models"

BACKBONE_WEIGHT_PATH = DSEG_DIR / "pretrained_weights" / "cpt" / "rest_small.pth"
UPERHEAD_WEIGHT_PATH = DSEG_DIR / "pretrained_weights" / "cpt" / "NEU_ResT_S_UperHead_light.pth"
sys.path.insert(0, str(DSEG_MODELS_DIR))
sys.path.insert(0, str(DSEG_DIR))

NEU_CLASS_NAMES = {
    0: "inclusion",
    1: "patch",
    2: "scratch",
}

from proposed_models.Transformer_based import Transformer_based
from NEU_dataloaders import get_transforms

#net = Transformer_based('ResT-S')
#net.init_pretrained(str(BACKBONE_WEIGHT_PATH))
#model = net
#model.eval()
device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)
checkpoint = torch.load(UPERHEAD_WEIGHT_PATH, map_location=device)
model = Transformer_based('ResT-S')
model.load_state_dict(checkpoint["state_dict"], strict=True)
model.to(device)
model.eval()

def preprocess_image(image_path: str):
    image_path = Path(image_path)
    image = cv2.imread(str(image_path))
    original_height, original_width = image.shape[:2]

    transforms = get_transforms(phase="test", mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
    transformed = transforms(image=image)
    image_tensor = transformed["image"]

    image_tensor = image_tensor.unsqueeze(0)

    device = next(model.parameters()).device
    image_tensor = image_tensor.to(device)

    return image_tensor, original_width, original_height

def predict_masks(image_path: str):
    image_tensor, original_width, original_height = preprocess_image(image_path)
    model.eval()

    with torch.no_grad():
        output = model(image_tensor)
        prob = torch.sigmoid(output)
        prob = (prob > 0.5).float()

    masks = (
        prob
        .squeeze(0)
        .cpu()
        .numpy()
        .astype("uint8")
    )

    return {
        "masks": masks,
        "original_width": original_width,
        "original_height": original_height,
    }

def postprocess_masks(
    image_path: str,
    masks: np.ndarray,
    original_width: int,
    original_height: int
):
    defects = []

    # 用于计算所有缺陷的并集，防止不同类别重叠时重复计算。
    overall_mask = np.zeros(
        (original_height, original_width),
        dtype=np.uint8,
    )

    for channel_index, defect_name in NEU_CLASS_NAMES.items():
        model_mask = masks[channel_index]

        # 将 256×256 mask 恢复到原始图片尺寸。
        original_size_mask = cv2.resize(
            model_mask,
            (original_width, original_height),
            interpolation=cv2.INTER_NEAREST,
        )

        original_size_mask = (
            original_size_mask > 0
        ).astype(np.uint8)

        defect_pixel_count = int(
            original_size_mask.sum()
        )

        total_pixel_count = (
            original_width * original_height
        )

        area_ratio = (
            defect_pixel_count / total_pixel_count
        )

        # 找出 mask 中所有缺陷像素的位置。
        y_coordinates, x_coordinates = np.where(original_size_mask > 0)

        if len(x_coordinates) == 0:
            continue

        x_min = int(x_coordinates.min())
        y_min = int(y_coordinates.min())
        x_max = int(x_coordinates.max())
        y_max = int(y_coordinates.max())

        defects.append(
            {
                "defect_type": defect_name,
                "class_id": channel_index + 1,
                "area_ratio": round(area_ratio, 6),
                "location": {
                    "bbox_pixels": {
                        "x_min": x_min,
                        "y_min": y_min,
                        "x_max": x_max,
                        "y_max": y_max,
                    }
                },
            }
        )

        # 加入所有缺陷 mask 的并集。
        overall_mask = np.maximum(
            overall_mask,
            original_size_mask,
        )

    overall_area_ratio = (
        float(overall_mask.sum())
        / (original_width * original_height)
    )

    return {
        "image_path": str(Path(image_path).resolve()),
        "image_width": original_width,
        "image_height": original_height,
        "has_defect": len(defects) > 0,
        "overall_area_ratio": round(
            overall_area_ratio,
            6,
        ),
        "defects": defects,
        "model_name": "dseg-NEU-ResT-S-UPerHead",
    }

def inspect_steel_image(image_path: str):
    prediction = predict_masks(image_path)

    result = postprocess_masks(
        image_path=image_path,
        masks=prediction["masks"],
        original_width=prediction["original_width"],
        original_height=prediction["original_height"],
    )

    return result


results = inspect_steel_image("test_1.jpg")
print(results)

