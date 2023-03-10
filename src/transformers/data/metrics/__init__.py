# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors and The HuggingFace Inc. team.
# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    from scipy.stats import pearsonr, spearmanr
    import numpy as np
    from sklearn.metrics import matthews_corrcoef, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score

    _has_sklearn = True
except (AttributeError, ImportError):
    _has_sklearn = False


def is_sklearn_available():
    return _has_sklearn


if _has_sklearn:

    def simple_accuracy(preds, labels):
        return (preds == labels).mean()

    def acc_and_f1(preds, labels):
        acc = simple_accuracy(preds, labels)
        f1 = f1_score(y_true=labels, y_pred=preds)
        return {
            "acc": acc,
            "f1": f1,
            "acc_and_f1": (acc + f1) / 2,
        }
    
    def acc_f1_mcc(preds, labels):
        acc = simple_accuracy(preds, labels)
        f1 = f1_score(y_true=labels, y_pred=preds)
        mcc = matthews_corrcoef(labels, preds)
        return {
            "acc": acc,
            "f1": f1,
            "mcc": mcc
        }

    def acc_f1_mcc_auc_aupr_pre_rec(preds, labels, probs):
        acc = simple_accuracy(preds, labels)
        precision = precision_score(y_true=labels, y_pred=preds)
        recall = recall_score(y_true=labels, y_pred=preds)
        f1 = f1_score(y_true=labels, y_pred=preds)
        mcc = matthews_corrcoef(labels, preds)
        auc = roc_auc_score(labels, probs)
        aupr = average_precision_score(labels, probs)
        return {
            "acc": acc,
            "f1": f1,
            "mcc": mcc,
            "auc": auc,
            "aupr": aupr,
            "precision": precision,
            "recall": recall,
        }

    def acc_f1_mcc_auc_pre_rec(preds, labels, probs):
        acc = simple_accuracy(preds, labels)
        precision = precision_score(y_true=labels, y_pred=preds, average="macro")
        recall = recall_score(y_true=labels, y_pred=preds, average="macro")
        f1 = f1_score(y_true=labels, y_pred=preds, average="binary")
        mcc = matthews_corrcoef(labels, preds)
        auc = roc_auc_score(labels, probs, average="macro", multi_class="ovo")
        return {
            "acc": acc,
            "f1": f1,
            "mcc": mcc,
            "auc": auc,
            "precision": precision,
            "recall": recall,
        }

    def pearson_and_spearman(preds, labels):
        pearson_corr = pearsonr(preds, labels)[0]
        spearman_corr = spearmanr(preds, labels)[0]
        return {
            "pearson": pearson_corr,
            "spearmanr": spearman_corr,
            "corr": (pearson_corr + spearman_corr) / 2,
        }

    def custom_metrics_deepsea(preds, labels, probs):
        NUM_LABELS = 919
        aucs = np.zeros(NUM_LABELS, dtype = np.float32)
        metrics = {}
        print(labels.shape, probs.shape, sep = '\t')
        for i in range(NUM_LABELS):
            try:
                aucs[i] = roc_auc_score(labels[:, i], probs[:, i])
            except ValueError:
                aucs[i] = 0.5
        metrics['TF_median_auc'] = np.median(aucs[125:125 + 690])
        metrics['DHS_median_auc'] = np.median(aucs[:125])
        metrics['HM_median_auc'] = np.median(aucs[125 + 690:125 + 690 + 104])
        metrics['mean_auc'] = (metrics['TF_median_auc'] + metrics['DHS_median_auc'] + metrics['HM_median_auc']) / 3.0
        return metrics
    
    def custom_metrics_spliceai(preds, labels, probs):
        metrics = {}
        
#         print('#' * 20, labels.shape, probs.shape, f"LABELS = {labels}", probs, '#' * 20, sep = '\n\n\n')
        
        # labels.shape = (bs, seq_len) [bs, 5k]
        # probs.shape = (bs, seq_len, 3) 
        
        # a - ?????????? ????????????, y - ????????????
        for lbl in [0, 1, 2]:
            y_ = labels[:, lbl]
            a_ = probs[:, lbl]
            
            if not np.isnan(a_).any():
                pr_auc = average_precision_score(y_, a_, pos_label=1)
            else:
                pr_auc = np.nan
                
            metrics[f'pr_auc_{lbl}'] = pr_auc if not np.isnan(pr_auc) else 0.0
            
        metrics['pr_auc_mean'] = (metrics['pr_auc_1'] + metrics['pr_auc_2']) / 2
        return metrics

    def glue_compute_metrics(task_name, preds, labels, probs=None):
        assert len(preds) == len(labels)
        if task_name == "cola":
            return {"mcc": matthews_corrcoef(labels, preds)}
        elif task_name == "sst-2":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name in ["dna690", "dnapair"]:
            return acc_f1_mcc_auc_aupr_pre_rec(preds, labels, probs)
        elif task_name == "dnaprom":
            return acc_f1_mcc_auc_pre_rec(preds, labels, probs)
            # return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "dnasplice":
            return acc_f1_mcc_auc_pre_rec(preds, labels, probs)
        elif task_name == "mrpc":
            return acc_and_f1(preds, labels)
        elif task_name == "sts-b":
            return pearson_and_spearman(preds, labels)
        elif task_name == "qqp":
            return acc_and_f1(preds, labels)
        elif task_name == "mnli":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "mnli-mm":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "qnli":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "rte":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "wnli":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == "hans":
            return {"acc": simple_accuracy(preds, labels)}
        elif task_name == 'deepsea':
            return custom_metrics_deepsea(preds, labels, probs)
        elif task_name == 'spliceai':
            return custom_metrics_spliceai(preds, labels, probs)
        else:
            raise KeyError(task_name)

    def xnli_compute_metrics(task_name, preds, labels):
        assert len(preds) == len(labels)
        if task_name == "xnli":
            return {"acc": simple_accuracy(preds, labels)}
        else:
            raise KeyError(task_name)