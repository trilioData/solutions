#!/bin/bash

finalQuery=""
inpFile="fileList.txt"
tableCount=`wc -l $inpFile | awk '{print $1}'`
iCnt=1

while read line
do
	query="select '$line' as Tables, count(*) from $line"
	if [ $iCnt -lt $tableCount ]
	then
		query=$query" UNION ALL "
	fi
	iCnt=`expr $iCnt + 1`
	finalQuery=$finalQuery$query
done < fileList.txt
echo "Run $finalQuery"
date >> recCounts.txt
mysql -e "$finalQuery" workloadmgr | tee -a recCounts.txt
date >> recCounts.txt
echo "" >> recCounts.txt
