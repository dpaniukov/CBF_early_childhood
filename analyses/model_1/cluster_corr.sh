#!/usr/bin/env bash

cbf_2mm="/media/veracrypt1/Analysis/ASL/cbf2mni/2mm/cbf_all_2mm.nii.gz"
cbf_2mm_mask="/media/veracrypt1/Analysis/ASL/MNI/gm_mask_2mm.nii.gz"
model="1"
res_dir="/media/veracrypt1/Analysis/ASL/results/"${model}/

3dFWHMx -acf -input ${cbf_2mm} -mask ${cbf_2mm_mask} >> fhwm_acf.txt

3dClustSim -mask ${cbf_2mm_mask} -acf 0.201667 4.41251 23.0045 -pthr 0.01 -nodec -iter 10000 -prefix acf_0p01 -quiet

3dcalc -a ${res_dir}tstats1.nii.gz -expr 'a*astep(a,1.97)' -prefix ${res_dir}tstats1_thresholed.nii.gz
3dcalc -a ${res_dir}tstats2.nii.gz -expr 'a*astep(a,1.97)' -prefix ${res_dir}tstats2_thresholed.nii.gz
3dcalc -a ${res_dir}tstats3.nii.gz -expr 'a*astep(a,1.97)' -prefix ${res_dir}tstats3_thresholed.nii.gz

fslmaths ${res_dir}tstats1_thresholed.nii.gz -thr 0 ${res_dir}tstats1_thresholed_1.nii.gz
fslmaths ${res_dir}tstats1_thresholed.nii.gz -mul -1 -thr 0 ${res_dir}tstats1_thresholed_2.nii.gz
fslmaths ${res_dir}tstats2_thresholed.nii.gz -thr 0 ${res_dir}tstats2_thresholed_1.nii.gz
fslmaths ${res_dir}tstats2_thresholed.nii.gz -mul -1 -thr 0 ${res_dir}tstats2_thresholed_2.nii.gz
fslmaths ${res_dir}tstats3_thresholed.nii.gz -thr 0 ${res_dir}tstats3_thresholed_1.nii.gz
fslmaths ${res_dir}tstats3_thresholed.nii.gz -mul -1 -thr 0 ${res_dir}tstats3_thresholed_2.nii.gz

3dmerge -prefix ${res_dir}tstats1_corrected_1.nii.gz -1clust 4 11648 ${res_dir}tstats1_thresholed_1.nii.gz
3dmerge -prefix ${res_dir}tstats1_corrected_2.nii.gz -1clust 4 11648 ${res_dir}tstats1_thresholed_2.nii.gz
3dmerge -prefix ${res_dir}tstats2_corrected_1.nii.gz -1clust 4 11648 ${res_dir}tstats2_thresholed_1.nii.gz
3dmerge -prefix ${res_dir}tstats2_corrected_2.nii.gz -1clust 4 11648 ${res_dir}tstats2_thresholed_2.nii.gz
3dmerge -prefix ${res_dir}tstats3_corrected_1.nii.gz -1clust 4 11648 ${res_dir}tstats3_thresholed_1.nii.gz
3dmerge -prefix ${res_dir}tstats3_corrected_2.nii.gz -1clust 4 11648 ${res_dir}tstats3_thresholed_2.nii.gz
