# -*- coding: utf-8 -*-

import numpy as np
import statsmodels.api as sm
import pandas as pd
import time
import nibabel as nib
import os, errno
import parmap


model = "1"

main_dir = "/media/veracrypt1/Analysis/ASL/cbf2mni/"
res_dir = "/media/veracrypt1/Analysis/ASL/results/"+model
preproc_dir = "/home/dmitrii/repos/ASL_longitudinal/data_selection/"

try:
    os.makedirs(res_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

brain_file = main_dir + "2mm/cbf_all_2mm_inc_find_removed.nii.gz"
cbf_all = nib.load(brain_file).get_data()

cbf_mask = "/media/veracrypt1/Analysis/ASL/MNI/gm_mask_2mm.nii.gz"
cbf_mask_array = nib.load(cbf_mask).get_data()

df = pd.read_csv("../predictors_inc_find_removed.csv", sep='\t')

print("Starting analysis...")

"""
Create an array to store coordinates
"""
print("Extracting coordinates from the mask")
def coord_extract(mask_array):

    d0,d1,d2 = np.where(mask_array>0)
    coord_array = np.zeros((len(d0), 3), dtype=int)
    coord_array[:,0] = d0
    coord_array[:,1] = d1
    coord_array[:,2] = d2

    return coord_array

coord_array = coord_extract(cbf_mask_array)
print("Total voxels", len(coord_array))


"""
Main analysis function
"""

def analyze(crow):

    d0, d1, d2 = coord_array[crow,:]

    df['cbf'] = cbf_all[d0,d1,d2,:]

    # drop zero voxel from the analysis
    # these are the voxels that are masked out or improperly aligned
    # save as a new df
    df_clean = df[df.cbf > 0]

    if len(df_clean) > 0:

        # run linear regression, the intercept and the random intercept are done by default
        res1 = sm.MixedLM.from_formula("cbf ~ Age_cent * C(Male) + Brain_vol + R_Hand", data=df_clean, missing='drop', groups=df_clean["Subj_id"]).fit(reml=True)

        res1_1_beta = res1.params[1] # sex
        res1_1_tval = res1.tvalues[1]
        res1_1_pval = res1.pvalues[1]
        res1_2_beta = res1.params[2] # age
        res1_2_tval = res1.tvalues[2]
        res1_2_pval = res1.pvalues[2]
        res1_3_beta = res1.params[3]  # interaction
        res1_3_tval = res1.tvalues[3]
        res1_3_pval = res1.pvalues[3]
        res1_llf = res1.llf

    else:
        res1_1_beta = 0
        res1_1_tval = 0
        res1_1_pval = 1
        res1_2_beta = 0
        res1_2_tval = 0
        res1_2_pval = 1
        res1_3_beta = 0
        res1_3_tval = 0
        res1_3_pval = 1
        res1_llf = None

    return [d0, d1, d2, res1_1_beta, res1_1_tval, res1_1_pval, res1_2_beta, res1_2_tval, res1_2_pval, res1_3_beta, res1_3_tval, res1_3_pval]


def save_res(results):

    """
    Create arrays to store beta-,t-,p-values
    Iterate through each voxel and do regressions
    """
    beta1_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    t1_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    p1_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    beta2_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    t2_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    p2_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    beta3_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    t3_values_array = np.zeros((cbf_mask_array.shape), dtype=float)
    p3_values_array = np.zeros((cbf_mask_array.shape), dtype=float)

    print("Saving the results")

    for i in range(len(results)):
        d0, d1, d2, res1_1_beta, res1_1_tval, res1_1_pval, res1_2_beta, res1_2_tval, res1_2_pval, res1_3_beta, res1_3_tval, res1_3_pval  = results[i]

        beta1_values_array[d0, d1, d2] = res1_1_beta
        t1_values_array[d0, d1, d2] = res1_1_tval
        p1_values_array[d0, d1, d2] = res1_1_pval
        beta2_values_array[d0, d1, d2] = res1_2_beta
        t2_values_array[d0, d1, d2] = res1_2_tval
        p2_values_array[d0, d1, d2] = res1_2_pval
        beta3_values_array[d0, d1, d2] = res1_3_beta
        t3_values_array[d0, d1, d2] = res1_3_tval
        p3_values_array[d0, d1, d2] = res1_3_pval

    values_img = nib.Nifti1Image(beta1_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "betas1.nii.gz"))
    values_img = nib.Nifti1Image(t1_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "tstats1.nii.gz"))
    values_img = nib.Nifti1Image(p1_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "pstats1.nii.gz"))

    values_img = nib.Nifti1Image(beta2_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "betas2.nii.gz"))
    values_img = nib.Nifti1Image(t2_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "tstats2.nii.gz"))
    values_img = nib.Nifti1Image(p2_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "pstats2.nii.gz"))

    values_img = nib.Nifti1Image(beta3_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "betas3.nii.gz"))
    values_img = nib.Nifti1Image(t3_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "tstats3.nii.gz"))
    values_img = nib.Nifti1Image(p3_values_array, np.eye(4))
    nib.save(values_img, os.path.join(res_dir, "pstats3.nii.gz"))

def pm_err():
    print("Something went wrong with the parmap")

print("Starting regression analyses...")
start_time = time.time()
from multiprocessing import Pool

with Pool(12) as pool:
    results = pool.map(analyze, list(range(len(coord_array))))

print("--- Regression is done in %s seconds ---" % (time.time() - start_time))

save_res(results)
