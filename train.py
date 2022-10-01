"""
Usage:
    train.py --input_dir FOLDER --output_dir FOLDER [--epochs EPOCHS --batch_size BATCH_SIZE --split SPLIT --checkpoint PATH]

Options:
    --input_dir FOLDER          Folder with the dataset in format of Deepforest.
    --output_dir FOLDER         Folder to save ouput data (model and evaluation results).
    --epochs EPOCHS             Number of epochs to train [default: 10]
    --batch_size BATCH_SIZE     Size of batch_size [default: 8]
    --split SPLIT               Percentage of split [default: 0.2]
    --checkpoint PATH           Path to checkpoint to continue training
"""
import os
from typing import Tuple

import numpy as np
import pandas as pd
import torch
from deepforest import main
from docopt import docopt
from pytorch_lightning import Trainer

class Training:
    def __init__(self, input_dir_dataset: str, 
                        ouput_dir: str,
                        checkpoint: str = None) -> None:
        self.input_dir_dataset = input_dir_dataset
        self.ouput_dir = ouput_dir
        self.model = main.deepforest()

        if checkpoint:
            self.model.model.load_state_dict(torch.load(checkpoint))
        else:
            self.model.use_release()
        self.train_file, self.validation_file = None, None
        os.makedirs(self.ouput_dir, exist_ok = True)

    def __split_dataset(self, split: float) -> Tuple[str, str]:
        path_csv = os.path.join(self.input_dir_dataset, 'annotations.csv')
        if split:
            train_annotations = pd.read_csv(path_csv)
            image_paths = train_annotations.image_path.unique()
            np.random.seed(42)
            valid_paths = np.random.choice(image_paths, int(len(image_paths)*split))
            valid_annotations = train_annotations.loc[train_annotations.image_path.isin(valid_paths)]
            train_annotations = train_annotations.loc[~train_annotations.image_path.isin(valid_paths)]
            
            train_file= os.path.join(self.input_dir_dataset, "train.csv")
            validation_file= os.path.join(self.input_dir_dataset, "valid.csv")
            
            train_annotations.to_csv(train_file, index=False)
            valid_annotations.to_csv(validation_file, index=False)

            return train_file,validation_file
        else:
            return path_csv, path_csv
        
    def train(self, epochs: int=10, batch_size: int=8, split: float=0.2): 
        self.train_file, self.validation_file = self.__split_dataset(split) 
        self.evaluate("results_pre_training.csv")
        self.model.config["train"]["epochs"] = epochs
        self.model.config["train"]["csv_file"] = self.train_file
        self.model.config['batch_size'] = batch_size
        self.model.config["train"]["root_dir"] = self.input_dir_dataset

        self.model.config["save-snapshot"] = False
        self.model.config["train"]["preload_images"] = True
        
        self.model.trainer =  Trainer(
                                      accelerator="auto",
                                      strategy="ddp",
                                      enable_checkpointing=False,
                                      max_epochs=self.model.config["train"]["epochs"],
                                      default_root_dir=self.ouput_dir
                                    )
        self.model.trainer.fit(self.model)

    def save(self,):
        ouput_model_name = "{}/checkpoint.pl".format(self.ouput_dir)
        torch.save(self.model.model.state_dict(), ouput_model_name)

    def evaluate(self, _file='results.csv'):
        print('Evaluating...')
        results = self.model.evaluate(self.validation_file, self.input_dir_dataset, iou_threshold = 0.4)
        results["results"].to_csv(os.path.join(self.ouput_dir, _file))
        print(f"Box precision {results['box_precision']}")
        print(f"Box Recall {results['box_recall']}")
        print(f"Class Recall {results['class_recall']}")
        print("Results")
        print(results["results"])
        

if __name__ == "__main__":
    args = docopt(__doc__)
    input_dirname = args['--input_dir']
    out_dirname = args['--output_dir']
    epochs = int(args['--epochs'])
    bath_size = int(args['--batch_size'])
    split = float(args['--split'])
    checkpoint = args['--checkpoint']
   
    training = Training(input_dirname, out_dirname, checkpoint)
    training.train(epochs=epochs, batch_size=bath_size, split=split)
    training.save()
    training.evaluate()