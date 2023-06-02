#!/bin/bash

inpFile="tableList.txt"
loc="/var/lib/mysql/workloadmgr"
fileSizes="fileSizes-`hostname | cut -d"-" -f1`.txt"
tableCount=`wc -l $inpFile | awk '{print $1}'`
iCnt=1

date >> $fileSizes
echo "Capture File sizes : $1" >> $fileSizes

while read line
do
	du -sh $loc/$line.ibd >> $fileSizes
	iCnt=`expr $iCnt + 1`
done < tableList.txt

echo "Done taking sizes at `date`" >> $fileSizes
