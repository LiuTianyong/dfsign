# -*- coding: utf-8 -*-
"""submit
"""

import os
import sys
import json
import glob
import argparse
import pandas as pd
import numpy as np
import utils

import pdb

home = os.path.expanduser('~')
root_datadir = os.path.join(home, 'data/dfsign')
src_traindir = root_datadir + '/train'
src_testdir = root_datadir + '/test'
src_annotation = root_datadir + '/train_label_fix.csv'

dest_datadir = root_datadir + '/dfsign_detect_voc'
image_dir = dest_datadir + '/JPEGImages'
list_dir = dest_datadir + '/ImageSets/Main'
anno_dir = dest_datadir + '/Annotations'

# chip loc
loc_json = os.path.join(anno_dir, 'test_chip.json')
# detections
detect_json = os.path.join(home,
                        'working/dfsign/mmdetection/dfsign/results_detect.json')
                        # 'working/dfsign/faster-rcnn.pytorch/output/results.json')

def main():
    parser = argparse.ArgumentParser(description="dfsign submit")
    parser.add_argument('outname', type=str, default='predict',
                        help='outname (default: predict)')
    args = parser.parse_args()
    
    # read chip loc
    with open(loc_json, 'r') as f:
        chip_loc = json.load(f)
    # read chip detections
    with open(detect_json, 'r') as f:
        chip_detect = json.load(f)

    dfsign_results = []
    for chip_id, chip_result in chip_detect.items():
        chip_id = os.path.basename(chip_id)
        img_id = chip_id.split('_')[0] + '.jpg'

        loc = chip_loc[chip_id]['loc']
        for i, pred_box in enumerate(chip_result['pred_box']):
            # transform to orginal image
            # ratio = (loc[2] - loc[0]) / 416.
            pred_box = [pred_box[0] + loc[0],
                        pred_box[1] + loc[1],
                        pred_box[2] + loc[0],
                        pred_box[3] + loc[1]]
            sign_type = int(chip_result['pred_label'][i])
            score = chip_result['pred_score'][i]
            pred_box = [pred_box[0], pred_box[1], pred_box[2], pred_box[1],
                        pred_box[2], pred_box[3], pred_box[0], pred_box[3]]
            # pred_box = [int(x) for x in pred_box]
            dfsign_results.append([img_id] + pred_box + [sign_type, score])
    
    chip = False
    filter_results = []
    temp = np.array(dfsign_results)
    detected_img = np.unique(temp[:, 0])
    for img_id in detected_img:
        preds = temp[temp[:, 0] == img_id]

        # mean or max
        pred_cls = preds[:, -2]
        pred_cls = np.unique(pred_cls)
        if chip:
            preds = preds[preds[:, -1].argsort()]
            filter_results.append(list(preds[-1])[:-1])
        else:
            box = np.mean(preds[:, 1:-2].astype(np.float64), axis=0)
            preds = preds[preds[:, -1].argsort()]
            cls_score = preds[-1][-2:]
            if len(pred_cls) > 1:
                print(img_id, preds[:, -1])  

            filter_results.append(np.hstack((np.array(img_id), box, cls_score)))

    
    columns = ['filename','X1','Y1','X2','Y2','X3','Y3','X4','Y4','type', 'score']
    df = pd.DataFrame(filter_results, columns=columns)
    df.to_csv(args.outname + '.csv', index=False)

    

if __name__ == '__main__':
    main()
