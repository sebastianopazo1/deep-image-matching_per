import cv2
import numpy as np

from pathlib import Path
from lib.pairs_generator import PairsGenerator
from lib.image_list import ImageList
from lib.deep_image_matcher import (SuperGlueMatcher, LOFTRMatcher, LightGlueMatcher, Quality, TileSelection, GeometricVerification, DetectAndDescribe)
from lib.local_features import LocalFeatureExtractor

class ImageMatching:
    def __init__(
            self, 
            imgs_dir : Path, 
            matching_strategy : str, 
            pair_file : Path, 
            retrieval_option : str,
            overlap : int,
            local_features : str,
            custom_config : str,
            max_feat_numb : int,
            ):
        
        self.matching_strategy = matching_strategy
        self.pair_file = pair_file
        self.retrieval_option = retrieval_option
        self.overlap = overlap
        self.local_features = local_features
        self.custom_config = custom_config
        self.max_feat_numb = max_feat_numb
        self.keypoints = {}
        self.correspondences = {}

        # Initialize ImageList class
        self.image_list = ImageList(imgs_dir)
        images = self.image_list.img_names
 
        if len(images) == 0:
            raise ValueError("Image folder empty. Supported formats: '.jpg', '.JPG', '.png'")
        elif len(images) == 1:
            raise ValueError("Image folder must contain at least two images")
        
    def img_names(self):
        return self.image_list.img_names

    def generate_pairs(self):
        self.pairs = []
        if self.pair_file is not None and self.matching_strategy == 'custom_pairs':
            with open(self.pair_file, 'r') as txt_file:
                lines = txt_file.readlines()
                for line in lines:
                    im1, im2 = line.strip().split(' ', 1)
                    self.pairs.append((im1, im2))
        else:
            pairs_generator = PairsGenerator(self.image_list.img_paths, self.matching_strategy, self.retrieval_option, self.overlap)
            self.pairs = pairs_generator.run()
        
        return self.pairs

    def match_pairs(self):
        # Add function to import matching_cfg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        if self.local_features == 'lightglue':
            matcher = LightGlueMatcher()
            cfg = self.custom_config["general"]

        if self.local_features == 'superglue':
            matcher = SuperGlueMatcher()
            cfg = self.custom_config["general"]

        if self.local_features == 'loftr':
            matcher = LOFTRMatcher()
            cfg = self.custom_config["general"]

        if self.local_features == 'detect_and_describe':
            detector_and_descriptor = self.custom_config["general"]["detector_and_descriptor"]
            local_feat_conf = self.custom_config[detector_and_descriptor]
            local_feat_extractor = LocalFeatureExtractor(
                                                detector_and_descriptor,
                                                local_feat_conf,
                                                self.max_feat_numb,
                                                )
            matcher = DetectAndDescribe()
            self.custom_config["ALIKE"]["n_limit"] = self.max_feat_numb
            cfg = self.custom_config
            cfg["local_feat_extractor"] = local_feat_extractor

        for pair in self.pairs:
            im0 = pair[0]
            im1 = pair[1]
            image0 = cv2.imread(str(im0), cv2.COLOR_RGB2BGR)
            image1 = cv2.imread(str(im1), cv2.COLOR_RGB2BGR)

            if len(image0.shape) == 2:
                image0 = cv2.cvtColor(image0, cv2.COLOR_GRAY2RGB)
            if len(image1.shape) == 2:
                image1 = cv2.cvtColor(image1, cv2.COLOR_GRAY2RGB)

            matcher.match(
                image0,
                image1,
                **cfg,
            )

            ktps0 = matcher.mkpts0
            ktps1 = matcher.mkpts1
            #descs0 = matcher.descriptors0
            #descs1 = matcher.descriptors1

            self.keypoints[im0.name] = ktps0
            self.keypoints[im1.name] = ktps1

            n_tie_points = np.arange(ktps0.shape[0]).reshape((-1, 1))

            self.correspondences[(im0, im1)] = np.hstack((n_tie_points, n_tie_points))




        return self.keypoints, self.correspondences