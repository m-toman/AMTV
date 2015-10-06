#!/bin/bash
# Unsupervised HSMM interpolation
# prompt: <speaker> <variety> <labels-dir> <output-dir> [-e]
# Flags: -e - Expand HSMM states before interpolation
# Example Call: bash interpolate.h csc at ivg /data/xyz/labs /data/xyz/output -e


#---------------------------- paths -------------------------------------------
svnroot="/home/mtoman/svn_avds"
basemodeldir="/data/all/models/ac_sd/"
ipoldir="/data/all/models/interpolation/"

# keep synthesis temp files?
keep="1"

#---------------------------- argument handling -------------------------------

# interpolate speaker from variety1 to variety2
# using labs in labdir and output to ipoldir
speaker=$1
variety1=$2
variety2=$3

# lexica names
lex1="alllex"
lex2="alllex"

# AMTV specifica
if [ $variety1 = "at" ]
then
   lex1="avlex" 
fi
if [ $variety1 = "vd" ]
then
   lex1="avlex" 
fi

if [ $variety2 = "at" ]
then
   lex2="avlex" 
fi
if [ $variety2 = "vd" ]
then
   lex2="avlex" 
fi

# label dirs
labdir=$4
labels1="$labdir/${variety1}/"
labels2="$labdir/${variety2}/"

# output dir
if [ -n "$5" ]
  then
    ipoldir=$5
fi


# expanded/condensed flag
method="condensed"
if [ -n "$6" ]
then
 ipolflag=$6
	if [ $ipolflag = "-e" ]
	then
	method="expanded" 
	fi
fi

# build model directories
modeldir1="$basemodeldir/${speaker}-${variety1}.${lex1}.44100/models/1/"
modeldir2="$basemodeldir/${speaker}-${variety2}.${lex2}.44100/models/1/"


#------------------------------ interpolation ---------------------------------

export PATH="$svnroot"/src/hts/tool/bin:"$PATH"
cd "$svnroot/src/interpolation"


# do interpolation
for label1 in $labels1/*.lab
do	
	label2=$labels2/$(basename $label1)
	
	if [ -e $label2 ]
	then
		
		echo "Checking labels"
		python $svnroot/src/misc/check_phoneset_presyn.py $modeldir1 $label1
		if [ $? -ne 0 ]; then
			echo "ERROR: $modeldir1 $label1 failed the presyn check"
    		exit 1    
		fi

		python $svnroot/src/misc/check_phoneset_presyn.py $modeldir2 $label2
		if [ $? -ne 0 ]; then
			echo "ERROR: $modeldir2 $label2 failed the presyn check"			
    		exit 1    
		fi
	
		nfo=$labels1/$(basename $label1 .lab).nfo
		nfoflag=""
		
		if [ -e $nfo ]
		then
			nfoflag="-r $nfo"
		fi
	
		echo "Interpolating $label1 with $label2, ipolmethod: $ipolflag, nfoflag: $nfoflag"
		set +x
		
		#for alpha in "0.0" "0.1" "0.2" "0.3" "0.4" "0.5" "0.6" "0.7" "0.75" "0.8" "0.85" "0.9" "0.95" "1.0"
		for alpha in "0.0" "0.2" "0.4" "0.6" "0.8" "1.0" 
		do
			echo "Alpha: $alpha"
			
			mkdir -p $ipoldir/logs/	
			
			# build interpolated mmfs   
			python interpolate.py $ipolflag $nfoflag $alpha \
				$modeldir1 \
				$label1 \
				$modeldir2 \
				$label2 \
				$ipoldir/clustered.cmp.mmf \
				$ipoldir/clustered.dur.mmf \
				$ipoldir/mapping.txt # &> $ipoldir/logs/log_${speaker}_$(basename $label1 .lab)-${method}-${alpha}.txt
	
	
		    rm -rf $ipoldir/synthesis
	
			# synthesize
			tcsh -f "$svnroot"/src/interpolation/synthesis-HMGenS.sh \
			    -hmmdir "$ipoldir" \
			    -labdir "$svnroot/src/interpolation/pseudolabels" \
			    -outdir "$ipoldir/synthesis" \
			    -regclass 0 \
			    -linear 0
			
			# copy output to output folder
			mkdir -p $ipoldir/output/
			cp  $ipoldir/synthesis/output.wav $ipoldir/output/${speaker}_$(basename $label1 .lab)-${method}-${alpha}.wav
		
			# delete synthesis folder or move it to a more meaningful name
			if [ $keep = "0" ];	then			
				rm -rf $ipoldir/synthesis
			else			
				mkdir -p $ipoldir/analysis
				rm -rf $ipoldir/analysis/synthesis_$(basename $label1 .lab)_${alpha}
				
				outdir=$ipoldir/analysis/${speaker}_$(basename $label1 .lab)-${method}-${alpha}
				mkdir -p $outdir
				mv  $ipoldir/synthesis $outdir
				mv  $ipoldir/clustered.cmp.mmf $outdir
				mv  $ipoldir/clustered.dur.mmf $outdir
				mv  $ipoldir/mapping.txt $outdir				
			fi
		done
	fi
done
