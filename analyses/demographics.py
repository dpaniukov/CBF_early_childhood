import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import scipy.stats as stats

main_dir = "/media/veracrypt1/Analysis/ASL/cbf2mni/"
id_age_file = "/media/veracrypt1/repos/CBF_early_childhood/analyses/predictors_inc_find_removed.csv"

df_main = pd.read_csv(os.path.join(id_age_file),sep='\t')

def get_age(scan_id):

    df = df_main
    subj_age = df.Age[df.Scan_id==scan_id]

    if subj_age is None:
        raise Exception("Age is NA for", scan_id)
    else:
        return float(subj_age)

def get_sex(scan_id):

    df = df_main
    subj_sex = str(list(df.Male[df.Scan_id == scan_id])[0])

    if subj_sex != "1" and subj_sex != "0":
        raise Exception("Age is NA for", scan_id)
    else:
        if subj_sex == "1": #Male
            return 1
        elif subj_sex == "0":
            return 0

def get_hand(scan_id):

    df = df_main
    r_hand = df.R_Hand[df.Scan_id == scan_id]

    if r_hand.isna().values.any():
        return "NA"
    else:
        return int(r_hand)


counter = 0
id_vect = []
age_vect = []
sex_vect = []
r_hand_vect = []
comm = ""

for r in range(len(df_main)):

    subj_id = df_main.loc[r, 'Subj_id']
    scan_id = df_main.loc[r, 'Scan_id']

    counter+=1
    id_vect.append(subj_id)
    age_vect.append(get_age(scan_id))
    sex_vect.append(get_sex(scan_id))
    r_hand_vect.append(get_hand(scan_id))

cols = ["age"]
dt = np.array([age_vect]).transpose()
df = pd.DataFrame(dt, columns=cols, dtype=float)

uid_vect = pd.unique(id_vect)
usex_vect = []

for j, uid in enumerate(uid_vect):
    for i, id in enumerate(id_vect):
        if id==uid:
            usex_vect.append(sex_vect[i])
            break

uhand_vect = []

for j, uid in enumerate(uid_vect):
    for i, id in enumerate(id_vect):
        if id==uid:
            uhand_vect.append(r_hand_vect[i])
            break


print("Females",usex_vect.count(0))
print("Males",usex_vect.count(1))
print("Unique IDs", len(pd.unique(id_vect)))
print("Age M", np.mean(age_vect))
print("Age SD", np.std(age_vect))
print("Age min", np.min(age_vect))
print("Age max", np.max(age_vect))
print("R hand", uhand_vect.count(1))
print("L hand", uhand_vect.count(0))
print("NA hand", uhand_vect.count("NA"))

subj_counts = df_main['Subj_id'].value_counts()
usubj_counts = subj_counts.value_counts()
print("counts:")
print(usubj_counts)
print()

# # comapre brain volume with age
print("Running correlation betwen the age and the brain volume")
df = pd.read_csv(id_age_file, sep='\t')
r, p = stats.pearsonr(df['Age'].dropna(), df['Brain_vol'].dropna())
print("r",r)
print("p",p)
print("VIF",1/(1-r**2))
