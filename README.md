# AMTV
Some results from research project "Acoustic modeling and transformation of varieties for speech synthesis".
Experiments have been performed for Hidden Semi-Markov Models (HSMMs) using the HTS toolkit: http://hts.sp.nitech.ac.jp/.
Voice models have been trained using the EMIME scripts: http://emime.org/

## interpolation
Unsupervised interpolation of HSMM states for HTS model files.

Given 2 HTS model files (.mmf), 2 label files (.lab) and an interpolation parameter alpha, aligns HSMM state models by Dynamic Time Warping (DTW) and using Kullback-Leibler Divergence (KLD) on state model distributions, then performs linear interpolation to produce an output utterance.

See also (open access) publication on unsupervised interpolation for language varieties at http://www.sciencedirect.com/science/article/pii/S0167639315000692
