import albumentations as A
from albumentations.pytorch import ToTensorV2


def get_transform(augment):
        """This is the new transform"""
        if augment:
            trans = A.Compose([
                A.RandomCrop(width=200, height=200, p=0.5),
                A.HorizontalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                A.RandomBrightnessContrast(p=0.6),
                ToTensorV2()
            ], bbox_params=A.BboxParams(format='pascal_voc',label_fields=["category_ids"]))
            
            n = 5
            transforms = [trans for _ in range(n)]
            transform = A.Compose(transforms)
            transform = ToTensorV2()
            
        else:
            transform = ToTensorV2()
            
        return transform