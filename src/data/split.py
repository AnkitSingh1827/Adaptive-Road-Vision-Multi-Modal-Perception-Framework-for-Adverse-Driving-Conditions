"""
Dataset Splitting, Leakage Audit, and Condition Stratification Utilities.
Ensures zero data leakage between train/val/test splits and builds balanced subsets.
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def audit_split_leakage(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    id_col: str = "image_name"
) -> Dict[str, Any]:
    """
    Verifies that no image or sequence identifiers leak between train, validation, and test splits.
    """
    train_ids = set(train_df[id_col].astype(str).str.strip())
    val_ids = set(val_df[id_col].astype(str).str.strip())
    test_ids = set(test_df[id_col].astype(str).str.strip())

    leakage_train_val = train_ids.intersection(val_ids)
    leakage_train_test = train_ids.intersection(test_ids)
    leakage_val_test = val_ids.intersection(test_ids)

    total_leakage = len(leakage_train_val) + len(leakage_train_test) + len(leakage_val_test)

    audit_report = {
        "passed": total_leakage == 0,
        "train_count": len(train_ids),
        "val_count": len(val_ids),
        "test_count": len(test_ids),
        "leakage_train_val_count": len(leakage_train_val),
        "leakage_train_test_count": len(leakage_train_test),
        "leakage_val_test_count": len(leakage_val_test),
        "total_violations": total_leakage,
    }

    if total_leakage > 0:
        logger.error("DATA LEAKAGE DETECTED! Audit report: %s", audit_report)
    else:
        logger.info("Split integrity verified: 0 leakage violations.")

    return audit_report


def build_stratified_balanced_split(
    df: pd.DataFrame,
    condition_col: str = "condition",
    samples_per_condition: int = 1500,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Samples a balanced dataset subset across specified condition classes.
    """
    balanced_chunks = []
    for cond_name, group in df.groupby(condition_col):
        n = min(len(group), samples_per_condition)
        sampled = group.sample(n=n, random_state=random_state)
        balanced_chunks.append(sampled)

    balanced_df = pd.concat(balanced_chunks).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return balanced_df


def partition_train_val_test(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    stratify_col: Optional[str] = "condition",
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits a dataframe into train, val, test with optional stratification.
    """
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"
    rng = np.random.RandomState(random_state)

    if stratify_col and stratify_col in df.columns:
        train_dfs, val_dfs, test_dfs = [], [], []
        for _, group in df.groupby(stratify_col):
            shuffled = group.sample(frac=1.0, random_state=random_state)
            n_total = len(shuffled)
            n_train = int(n_total * train_ratio)
            n_val = int(n_total * val_ratio)

            train_dfs.append(shuffled.iloc[:n_train])
            val_dfs.append(shuffled.iloc[n_train:n_train + n_val])
            test_dfs.append(shuffled.iloc[n_train + n_val:])

        train_out = pd.concat(train_dfs).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
        val_out = pd.concat(val_dfs).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
        test_out = pd.concat(test_dfs).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    else:
        shuffled = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
        n_total = len(shuffled)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)

        train_out = shuffled.iloc[:n_train].reset_index(drop=True)
        val_out = shuffled.iloc[n_train:n_train + n_val].reset_index(drop=True)
        test_out = shuffled.iloc[n_train + n_val:].reset_index(drop=True)

    train_out["split"] = "train"
    val_out["split"] = "val"
    test_out["split"] = "test"

    return train_out, val_out, test_out
