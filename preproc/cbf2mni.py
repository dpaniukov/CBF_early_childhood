# -*- coding: utf-8 -*-

import os, sys  # system functions
import nipype.interfaces.io as nio  # Data i/o
import nipype.interfaces.fsl as fsl  # fsl
import nipype.pipeline.engine as pe  # pypeline engine
import nipype.interfaces.utility as util  # utility
import nipype.interfaces.ants as ants
from nipype.interfaces.c3 import C3dAffineTool
from nipype.interfaces.ants.segmentation import BrainExtraction

import multiprocessing, time
from multiprocessing import Pool

nprocs = multiprocessing.cpu_count()

start_time = time.time()

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

"""
Project info
"""

main_dir = "/media/veracrypt1/"
project_dir = main_dir+"/Analysis/ASL/"
work_dir = main_dir+"/scratch/ASL/"

if not os.path.exists(work_dir):
    os.makedirs(work_dir)

template_brain = os.path.join(project_dir, 'MNI', 'nihpd_asym_04.5-08.5_brain.nii.gz')
brain_mask_MNI = os.path.join(project_dir, 'MNI', 'nihpd_asym_04.5-08.5_brain_mask.nii.gz')

# which subjects to run
subject_id = str(sys.argv[1])
scan_id = str(sys.argv[2])

subj_reg = os.path.join(project_dir, "reg_n4")
subj_preproc = os.path.join(project_dir, "preproc")
brain_mask = os.path.join(subj_reg, subject_id + "_" + scan_id + "/anat/mask2t1/_warp_mask0/sub-08_T1w_brainmask_trans.nii.gz")
composite_transform = os.path.join(subj_reg, subject_id + "_" + scan_id + "/anat/anat2mni_mat/anat2mni_Composite.h5")
subj_wm =  os.path.join(subj_preproc, subject_id + "_" + scan_id + "/anat/anat_WM_OASIS/highres001_BrainExtractionWM.nii.gz")

"""
Create workflow
"""

wf = pe.Workflow(name='wf')
wf.base_dir = os.path.join(work_dir, "cbf2mni_wdir", subject_id, scan_id)
wf.config = {"execution": {"crashdump_dir": os.path.join(work_dir, 'cbf2mni_crashdumps', subject_id, scan_id)}}

datasource = pe.Node(nio.DataGrabber(infields=['subject_id', 'scan_id'], outfields=['asl', 'anat']), name='datasource')
datasource.inputs.base_directory = project_dir
datasource.inputs.template = '*'
datasource.inputs.field_template = dict(asl='%s/%s/asl/cbf.nii.gz',
                                        anat='%s/%s/anat/anat.nii.gz')
datasource.inputs.template_args = dict(asl=[['subject_id', 'scan_id']],
                                       anat=[['subject_id', 'scan_id']])
datasource.inputs.sort_filelist = True
datasource.inputs.subject_id = subject_id
datasource.inputs.scan_id = scan_id

inputnode = pe.Node(interface=util.IdentityInterface(fields=['asl',
                                                             'anat', ]),
                    name='inputspec')

wf.connect([(datasource, inputnode, [('anat', 'anat'), ('asl', 'asl'), ]), ])


"""
T1 skull stripping
"""
biniraze_mask = pe.Node(interface=fsl.ImageMaths(out_data_type='float',
                                                            op_string='-bin',
                                                            suffix='_dtype'),
                                   iterfield=['in_file'],
                                   name='biniraze_mask')

biniraze_mask.inputs.in_file = brain_mask

brainextraction = pe.Node(interface=fsl.ImageMaths(out_data_type='float',
                                                      op_string='-mul',
                                                      suffix='_dtype'),
                             iterfield=['in_file', 'in_file2'],
                             name='brainextraction')

wf.connect(inputnode, 'anat', brainextraction, 'in_file')
wf.connect(biniraze_mask, 'out_file', brainextraction, 'in_file2')

"""
CBF to T1
"""
# Rigid
rigid = pe.Node(fsl.FLIRT(), iterfield=['in_file'], name='rigid')
rigid.inputs.dof = 6

wf.connect(inputnode, 'asl', rigid, 'in_file')
wf.connect(brainextraction, 'out_file', rigid, 'reference')

# BBR
flt = pe.Node(interface=fsl.FLIRT(cost_func='bbr', dof=6, output_type="NIFTI_GZ"),
              iterfield=['in_file', 'in_matrix_file'], name="flt")
flt.inputs.schedule = os.path.join(os.getenv('FSLDIR'), 'etc/flirtsch/bbr.sch')
wf.connect(inputnode, 'asl', flt, 'in_file')
wf.connect(brainextraction, 'out_file', flt, 'reference')
# flt.inputs.wm_seg = subj_wm
wf.connect(rigid, 'out_matrix_file', flt, 'in_matrix_file')


"""
Convert and merge transform matrices.
This is not needed in the pipeline, but the joint matrix may be useful in the future.
"""

convert2itk = pe.Node(C3dAffineTool(), iterfield=['source_file', 'transform_file'], name='convert2itk')
convert2itk.inputs.fsl2ras = True
convert2itk.inputs.itk_transform = True

wf.connect(flt, 'out_matrix_file', convert2itk, 'transform_file')
wf.connect(inputnode, 'asl', convert2itk, 'source_file')
wf.connect(brainextraction, 'out_file', convert2itk, 'reference_file')

merge = pe.Node(util.Merge(2), iterfield=['in2'], name='mergexfm')

wf.connect(convert2itk, 'itk_transform', merge, 'in2')
merge.inputs.in1 = composite_transform

"""
Transform CBF, which is aligned to T1, to MNI
"""

warp_cbf = pe.Node(ants.ApplyTransforms(), iterfield=['input_image', 'transforms'], name='warp_cbf')
warp_cbf.inputs.input_image_type = 0
warp_cbf.inputs.interpolation = 'Linear'
warp_cbf.inputs.invert_transform_flags = [False]
warp_cbf.inputs.terminal_output = 'file'

wf.connect(flt, 'out_file', warp_cbf, 'input_image')  # image is in t1 space
warp_cbf.inputs.transforms = composite_transform  # using transform matrix from t1 to mni
warp_cbf.inputs.reference_image = template_brain

"""
Extract brain for CBF
"""

cbf_be = pe.Node(interface=fsl.ImageMaths(op_string='-mul'), iterfield=['in_file', 'in_file2'], name='cbf_be')

wf.connect(warp_cbf, 'output_image', cbf_be, 'in_file')
cbf_be.inputs.in_file2 = brain_mask_MNI


"""
Convert to float, so ANTs can read it later
"""

warped_float = pe.Node(interface=fsl.ImageMaths(out_data_type='float',
                                                            op_string='',
                                                            suffix='_dtype'),
                                   iterfield=['in_file'],
                                   name='warped_float')

wf.connect(cbf_be, 'out_file', warped_float, 'in_file')


"""
Save data
"""

datasink = pe.Node(nio.DataSink(), name='sinker')
datasink.inputs.base_directory = os.path.join(project_dir, "cbf2mni")

datasink.inputs.container = subject_id + '_' + scan_id

wf.connect(brainextraction, 'out_file', datasink, 'anat.brain')

wf.connect(flt, 'out_file', datasink, 'asl.cbf2anat')
wf.connect(flt, 'out_matrix_file', datasink, 'asl.cbf2anat_mat')

wf.connect(warp_cbf, 'output_image', datasink, 'asl.cbf2mni')

wf.connect(cbf_be, 'out_file', datasink, 'asl.cbf_be2mni')

wf.connect(merge, 'out', datasink, 'asl.cbf2mni_mat')

wf.connect(warped_float, 'out_file', datasink, 'asl.cbf_be_float2mni')

"""
Run
"""
outgraph = wf.run(plugin='MultiProc')

print("--- %s seconds ---" % (time.time() - start_time))
