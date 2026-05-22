"""
11 class, chia train / val / test = 70 / 15 / 15

"""

import os
import shutil
import random
import json
from pathlib import Path


BASE_DIR   = r"C:\Skin Disease Detection\Base_Data"
OUTPUT_DIR = r"C:\Skin Disease Detection\skin_data"

TRAIN_RATIO = 0.70
VAL_RATIO   = 0.15


RANDOM_SEED = 42
MIN_IMAGES  = 100   # bỏ qua class có ít hơn số này

IMAGE_EXTS  = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


CLASS_MAP = {
    # có ở cả 2 dataset
    "Acne and Rosacea Photos":                                  "acne_rosacea",
    "Eczema Photos":                                            "eczema",
    "Atopic Dermatitis Photos":                                 "atopic_dermatitis",
    "Tinea Ringworm Candidiasis and other Fungal Infections":   "tinea",
    "Urticaria Hives":                                          "urticaria",
    "Warts Molluscum and other Viral Infections":               "warts",
    "Exanthems and Drug Eruptions":                             "drug_eruptions",
    "Bullous Disease Photos":                                   "bullous_disease",
    # chỉ có ở Dermnet 
    "Hair Loss Photos Alopecia and other Hair Diseases":        "alopecia",
    "Nail Fungus and other Nail Disease":                       "nail_fungus",
    "Scabies Lyme Disease and other Infestations and Bites":    "scabies",
}


SOURCES = [
    Path(BASE_DIR) / "Dermnet"                  / "train",
    Path(BASE_DIR) / "Dermnet"                  / "test",
    Path(BASE_DIR) / "20 Skin Diseases Dataset" / "Dataset" / "train",
    Path(BASE_DIR) / "20 Skin Diseases Dataset" / "Dataset" / "test",
]


def collect_images(folder_name):
    images = []
    for src in SOURCES:
        folder = src / folder_name
        if folder.exists():
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    images.append(f)
    return images


def deduplicate(images):
    """Loại bỏ ảnh trùng tên file từ 2 nguồn khác nhau."""
    seen, unique = set(), []
    for img in images:
        if img.name not in seen:
            seen.add(img.name)
            unique.append(img)
    return unique


def copy_split(images, class_name):
    random.shuffle(images)
    n       = len(images)
    n_train = int(n * TRAIN_RATIO)
    n_val   = int(n * VAL_RATIO)

    splits = {
        "train": images[:n_train],
        "val":   images[n_train : n_train + n_val],
        "test":  images[n_train + n_val :],
    }

    for split, files in splits.items():
        dest = Path(OUTPUT_DIR) / split / class_name
        dest.mkdir(parents=True, exist_ok=True)
        for i, src in enumerate(files):
            shutil.copy2(src, dest / f"{class_name}_{i:05d}{src.suffix.lower()}")

    return {k: len(v) for k, v in splits.items()}


def main():
    random.seed(RANDOM_SEED)

    print("=" * 65)
    print("  Skin Disease - Data Preparation (14 classes)")
    print(f"  Source : {BASE_DIR}")
    print(f"  Output : {OUTPUT_DIR}")
    print("=" * 65)

    stats   = {}
    skipped = []

    for folder_name, class_name in CLASS_MAP.items():
        images = collect_images(folder_name)
        images = deduplicate(images)

        if len(images) < MIN_IMAGES:
            skipped.append((class_name, len(images)))
            print(f"  [SKIP]  {class_name:<32s}  {len(images):>4d} anh  (< {MIN_IMAGES})")
            continue

        split_counts = copy_split(images, class_name)
        stats[class_name] = split_counts
        print(
            f"  [OK]    {class_name:<32s}  "
            f"total={len(images):>4d}  "
            f"train={split_counts['train']:>4d}  "
            f"val={split_counts['val']:>3d}  "
            f"test={split_counts['test']:>3d}"
        )


    print("\n" + "=" * 65)
    total_imgs = sum(sum(v.values()) for v in stats.values())
    print(f"  Classes thanh cong : {len(stats)}")
    if skipped:
        print(f"  Classes bi skip    : {len(skipped)}")
        for cls, cnt in skipped:
            print(f"                       - {cls} ({cnt} anh)")
    print(f"  Tong anh da copy   : {total_imgs:,}")
    print("=" * 65)

    # class_names.json
    class_names = sorted(stats.keys())
    out_json = Path(OUTPUT_DIR) / "class_names.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2, ensure_ascii=False)

    print(f"\n  class_names.json da luu -> {out_json}")


if __name__ == "__main__":
    main()
