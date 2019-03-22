import os


main_dir = "/media/veracrypt1/Analysis/ASL/"
preproc_dir = main_dir+"reg_n4_/"
QA_t1_dir = main_dir+"QA_t1/"

parents = next(os.walk(preproc_dir))[1]

for p in parents:

    if p[0] == "1":

        subj_id = p[:5]
        scan_id = p[6:]

        # QA for T1 registration
        anat = preproc_dir+p+"/anat/mask2t1/_warp_mask0/anat.nii.gz"
        mask_prob = preproc_dir+p+"/anat/mask2t1/_warp_mask0/sub-08_T1w_brainmask_trans.nii.gz"
        mask = preproc_dir + p + "/anat/mask2t1/_warp_mask0/mni_mask.nii.gz"
        slices_out_file = QA_t1_dir+p+".png"
        print("fslmaths "+mask_prob+" -bin "+mask)
        print("slicer "+anat+" "+mask+" -s 2 -x 0.35 sla.png -x 0.45 slb.png -x 0.55 slc.png -x 0.65 sld.png -y 0.35 sle.png -y 0.45 slf.png -y 0.55 slg.png -y 0.65 slh.png -z 0.35 sli.png -z 0.45 slj.png -z 0.55 slk.png -z 0.65 sll.png ; pngappend sla.png + slb.png + slc.png + sld.png + sle.png + slf.png + slg.png + slh.png + sli.png + slj.png + slk.png + sll.png "+slices_out_file+"; /bin/rm -f sl?.png")


main_dir = "/Users/dmitriipaniukov/Analysis/ASL/"
preproc_dir = main_dir+"cbf2mni/"
QA_cbf_dir = main_dir+"QA_cbf2mni/"
mask = main_dir+"MNI/nihpd_asym_04.5-08.5_brain.nii.gz"

parents = next(os.walk(preproc_dir))[1]

for p in parents:

    if p[0] == "1":

        # QA for initial CBF files
        cbf = os.path.join(preproc_dir, p, "asl", "cbf_be2mni", "cbf_flirt_trans_maths.nii.gz")
        cbf_qa = os.path.join(QA_cbf_dir,p+"_"+p+"_cbf_qa.gif")
        print("slices "+str(cbf)+" "+mask+" -o "+str(cbf_qa))
