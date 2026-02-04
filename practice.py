import pandas as pd
import polars as pl
import numpy as np
import os


base_dir = "/content/drive/MyDrive"
train_path = os.path.join(base_dir, "train.parquet")
test_path = os.path.join(base_dir, "test.parquet")

train_df = pl.scan_parquet(train_path)
seq_df = train_df.select(pl.col("seq")).collect()



