import os
import re
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles file discovery, image-metadata matching, and JSON metadata updates
    for the Smart Shelf Life Prediction dataset.

    Attributes:
        data_dir (Path): Root directory containing the dataset.
    """

    def __init__(self, data_dir: str = 'data') -> None:
        """
        Args:
            data_dir: Root directory containing the dataset.
        """
        self.data_dir = Path(data_dir)

        # Image pattern: env(1 char), sample(char+digits), view(1 char), day(d+digits)
        self._img_pattern = re.compile(
            r'^([aAcC])([aAbB]\d{1,2})([sStTbBrRLl]{1,2})([dD]\d{1,2})\.(?:png|jpg|jpeg)$'
        )
        # JSON pattern: env(1 char), any string, day(d+digits)
        self._json_pattern = re.compile(r'^([aAcC])(.*)([dD]\d{1,2})\.json$')

        logger.info("DataLoader initialised with data_dir='%s'.", self.data_dir)

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    def get_files(self) -> tuple[list[dict], list[dict]]:
        """
        Single O(N) pass through the data directory to collect image and
        metadata file records.

        Returns:
            Tuple of (images, metadata), where each entry is a dict containing
            the file path and parsed naming-convention keys.
        """
        images: list[dict] = []
        metadata: list[dict] = []

        for dir_path, _, file_names in os.walk(self.data_dir):
            for file_name in file_names:
                img_match = self._img_pattern.match(file_name)
                if img_match:
                    env, sample, view, day = img_match.groups()
                    images.append({
                        'path':   os.path.join(dir_path, file_name),
                        'env':    env.lower(),
                        'sample': sample.lower(),
                        'view':   view.lower(),
                        'day':    day.lower(),
                    })
                    continue

                json_match = self._json_pattern.match(file_name)
                if json_match:
                    env, _, day = json_match.groups()
                    metadata.append({
                        'path': os.path.join(dir_path, file_name),
                        'env':  env.lower(),
                        'day':  day.lower(),
                    })

        logger.info(
            "Discovery complete: %d image(s), %d metadata file(s).",
            len(images), len(metadata),
        )
        return images, metadata

    def get_json_files(self) -> list[str]:
        """
        Returns a sorted list of all JSON file paths found under data_dir.
        """
        pattern = re.compile(r'^.*\.json$')
        json_files = [
            os.path.join(dir_path, file_name)
            for dir_path, _, file_names in os.walk(self.data_dir)
            for file_name in file_names
            if pattern.match(file_name)
        ]
        logger.debug("Located %d JSON file(s).", len(json_files))
        return sorted(json_files)

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def get_intersection(self) -> tuple[list[dict], list[str]]:
        """
        Matches images to their corresponding metadata by (env, day) key.

        Returns:
            Tuple of (matched_pairs, unmatched_images).
            Each matched pair is a dict with 'image_path', 'metadata_path', 'view'.
        """
        images, metadata = self.get_files()

        metadata_lookup: dict[tuple, str] = {
            (m['env'], m['day']): m['path'] for m in metadata
        }

        matched_pairs: list[dict] = []
        unmatched_images: list[str] = []

        for img in images:
            key = (img['env'], img['day'])
            if key in metadata_lookup:
                matched_pairs.append({
                    'image_path':    img['path'],
                    'metadata_path': metadata_lookup[key],
                    'view':          img['view'],
                })
            else:
                unmatched_images.append(img['path'])
                logger.warning("No metadata found for image: %s", img['path'])

        logger.info(
            "Intersection: %d matched pair(s), %d unmatched image(s).",
            len(matched_pairs), len(unmatched_images),
        )
        return matched_pairs, unmatched_images

    # ------------------------------------------------------------------
    # Metadata update
    # ------------------------------------------------------------------

    def update_metadata_images(self) -> int:
        """
        Appends matched image paths into the 'images' field of each JSON
        metadata file. Skips duplicates and writes back only when changed.

        Returns:
            Number of JSON files updated.
        """
        matches, _ = self.get_intersection()

        # Group image paths by metadata file using setdefault (cleaner than if/else)
        metadata_to_images: dict[str, list[str]] = {}
        for match in matches:
            metadata_to_images.setdefault(match['metadata_path'], []).append(
                match['image_path']
            )

        updated_count = 0
        for json_path, img_paths in metadata_to_images.items():
            with open(json_path, 'r') as f:
                data = json.load(f)

            images: list[str] = data.get('images', [])
            modified = False

            for img_path in img_paths:
                if img_path not in images:
                    images.append(img_path)
                    modified = True

            if modified:
                data['images'] = images
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=2)
                updated_count += 1
                logger.info("Updated metadata file: %s", json_path)

        logger.info(
            "Metadata update complete — %d file(s) modified.", updated_count
        )
        return updated_count


# ----------------------------------------------------------------------
# Script entry point (for quick diagnostics)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)s — %(message)s',
    )
    loader = DataLoader()
    matches, unmatched = loader.get_intersection()
    print(f"\nFound {len(matches)} matched image-metadata pair(s).")
    for m in matches:
        print(f"  {m['image_path']} -> {m['metadata_path']}")
    if unmatched:
        print(f"\n{len(unmatched)} unmatched image(s):")
        for u in unmatched:
            print(f"  {u}")
    updated = loader.update_metadata_images()
    print(f"\nUpdated {updated} JSON file(s).")
