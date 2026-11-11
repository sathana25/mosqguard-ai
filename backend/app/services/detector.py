"""Breeding-site detection.

Three engines, picked automatically (override with the DETECTOR env variable):

1. Custom YOLOv8 model  - weights trained with ml/train.py (classes such as
   stagnant_water, container, tyre, drain, larvae). Best accuracy.
2. Pretrained YOLOv8n   - COCO model; flags water-holding objects it knows
   (bottle, cup, bowl, vase, potted plant, sink, toilet).
3. Basic heuristic      - no ML install needed; looks for smooth, dark or
   reflective regions that look like standing water. Keeps the app running
   on any machine, but is much less accurate.

Every engine returns the same dict, so the rest of the app does not change.
The result is always a *suspected* site that a field worker must confirm.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from ..config import DETECTOR, MODEL_PATH

log = logging.getLogger(__name__)

# COCO classes that commonly hold water outdoors
COCO_CONTAINERS = {
    "bottle": "bottle",
    "cup": "cup / small container",
    "bowl": "bowl / open container",
    "vase": "pot / vase",
    "potted plant": "flower pot",
    "sink": "sink / basin",
    "toilet": "toilet / tank",
}
# People and vehicles: if they fill the photo, it is not a close-up of a breeding site
SCENE_CLASSES = {"person", "car", "bus", "truck", "motorcycle", "bicycle", "train"}
# Custom model classes that mean "breeding site"
CUSTOM_RISK_CLASSES = {"stagnant_water", "container", "tyre", "tire", "drain", "larvae", "tank", "pot"}


def _result(objects, water, larvae, engine, base_conf=None):
    conf = base_conf if base_conf is not None else max([o["confidence"] for o in objects], default=0.0)
    suspected = bool(objects) or water
    if suspected:
        labels = ", ".join(sorted({o["label"] for o in objects})) or "standing water"
        summary = f"Possible breeding site: {labels}."
        if larvae:
            summary = summary[:-1] + "; possible larvae seen."
    else:
        summary = "No water-holding objects or standing water detected."
    return {
        "suspected": suspected,
        "confidence": round(float(conf), 3),
        "objects": objects,
        "water_visible": bool(water),
        "larvae_visible": bool(larvae),
        "summary": summary,
        "engine": engine,
    }


def _largest_blob(mask: np.ndarray) -> int:
    """Size of the largest 4-connected region in a small boolean mask."""
    seen = np.zeros_like(mask, dtype=bool)
    rows, cols = mask.shape
    best = 0
    for r0 in range(rows):
        for c0 in range(cols):
            if not mask[r0, c0] or seen[r0, c0]:
                continue
            stack, size = [(r0, c0)], 0
            seen[r0, c0] = True
            while stack:
                r, c = stack.pop()
                size += 1
                for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= rr < rows and 0 <= cc < cols and mask[rr, cc] and not seen[rr, cc]:
                        seen[rr, cc] = True
                        stack.append((rr, cc))
            best = max(best, size)
    return best


class HeuristicDetector:
    """Rule-based fallback using colour and texture. No ML packages needed.

    Looks for ONE large, very smooth patch with water-like colour. Scattered
    dark pixels (clothes, shadows, hair) do not count. Confidence is capped
    low because a heuristic cannot tell a puddle from wet asphalt reliably.
    """

    name = "Basic image heuristic"
    MIN_BLOB = 0.12     # largest water-like patch must cover 12% of the photo
    MAX_BLOB = 0.85     # ...but not the whole photo: a puddle has ground around it
    MAX_CONF = 0.6

    def detect(self, path: str | Path) -> dict:
        img = Image.open(path).convert("RGB").resize((256, 192))
        rgb = np.asarray(img, dtype=np.float32) / 255.0
        hsv = np.asarray(img.convert("HSV"), dtype=np.float32) / 255.0
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

        # Standing water is very smooth compared with soil, grass, walls or people
        gray = rgb.mean(axis=2)
        gy, gx = np.gradient(gray)
        smooth = np.hypot(gx, gy) < 0.02

        # Murky (dark, dull) or reflective blue/green water
        murky = (v > 0.12) & (v < 0.42) & (s < 0.4)
        bluish = (h > 0.45) & (h < 0.7) & (s > 0.15) & (v > 0.25)
        greenish = (h > 0.18) & (h < 0.45) & (s > 0.2) & (v < 0.5)
        fine = smooth & (murky | bluish | greenish)
        # 4x4 blocks: a block counts as water when most of its pixels do
        mask = fine.reshape(48, 4, 64, 4).mean(axis=(1, 3)) > 0.6

        ratio = _largest_blob(mask) / mask.size
        water = self.MIN_BLOB < ratio < self.MAX_BLOB
        conf = min(self.MAX_CONF, 0.3 + ratio * 0.6) if water else 0.0
        objects = [{"label": "possible standing water", "confidence": round(conf, 3), "box": None}] if water else []
        return _result(objects, water, False, self.name, conf)


class YoloDetector:
    def __init__(self, weights: str, custom: bool):
        from ultralytics import YOLO  # imported lazily: optional dependency

        self.model = YOLO(weights)
        self.custom = custom
        self.name = "YOLOv8 (custom MOSQGUARD model)" if custom else "YOLOv8n (pretrained COCO)"

    def detect(self, path: str | Path) -> dict:
        res = self.model.predict(str(path), conf=0.25, verbose=False)[0]
        names = res.names
        objects, water, larvae = [], False, False
        img_area = float(res.orig_shape[0] * res.orig_shape[1])
        scene_area = 0.0  # area covered by people and vehicles
        for box in res.boxes:
            cls = names[int(box.cls)]
            conf = float(box.conf)
            xyxy = [round(float(x), 1) for x in box.xyxy[0].tolist()]
            if cls in SCENE_CLASSES:
                scene_area += (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])
            if self.custom:
                key = cls.lower().replace(" ", "_")
                if key not in CUSTOM_RISK_CLASSES:
                    continue
                water |= key == "stagnant_water"
                larvae |= key == "larvae"
                label = cls.replace("_", " ")
            else:
                if cls not in COCO_CONTAINERS:
                    continue
                label = COCO_CONTAINERS[cls]
            objects.append({"label": label, "confidence": round(conf, 3), "box": xyxy})

        if not self.custom and scene_area / img_area < 0.15:
            # COCO cannot see water itself, so add the heuristic's water check,
            # but not on photos of people or traffic (dark clothes and roads fool it)
            h = HeuristicDetector().detect(path)
            water = h["water_visible"]
            if water and not objects:
                objects = h["objects"]
        objects.sort(key=lambda o: o["confidence"], reverse=True)
        return _result(objects[:6], water, larvae, self.name)


@lru_cache(maxsize=1)
def get_detector():
    choice = DETECTOR.lower()
    if choice in ("auto", "yolo"):
        try:
            custom = Path(MODEL_PATH).exists()
            det = YoloDetector(MODEL_PATH if custom else "yolov8n.pt", custom)
            log.info("Detector: %s", det.name)
            return det
        except Exception as exc:  # ultralytics missing or weights not downloadable
            if choice == "yolo":
                raise
            log.warning("YOLOv8 unavailable (%s); using basic heuristic detector", exc)
    return HeuristicDetector()


def detect(path: str | Path) -> dict:
    try:
        return get_detector().detect(path)
    except Exception as exc:
        log.exception("Detector failed, falling back to heuristic: %s", exc)
        return HeuristicDetector().detect(path)
