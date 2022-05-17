# -*- coding: utf-8 -*-
"""Copy of Copy of BDM_Final_Sample.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SatckCw3Ew9LDW93l9hFSXcQU0cmadoa
"""

import json
import numpy as np
from pyproj import Transformer
import csv
import pandas as pd
from shapely.geometry import Point
import pyspark
from pyspark import SparkContext
import sys
from pyspark.sql import SparkSession

if __name__=='__main__':
  sc = pyspark.SparkContext.getOrCreate()
  spark = SparkSession(sc)
  l1 = sc.textFile('nyc_supermarkets.csv') \
      .map(lambda x: next(csv.reader([x]))) \
      .map(lambda x: (x[9])) \
      .collect()

  l2 = sc.textFile('nyc_cbg_centroids.csv')\
      .map(lambda x: next(csv.reader([x])))\
        .map(lambda x: x[0]) \
        .collect()
  t = Transformer.from_crs(4326, 2263)
  loc = sc.textFile('nyc_cbg_centroids.csv')\
      .map(lambda x: next(csv.reader([x])))\
          .map(lambda x: (x[1],x[2])) \
          .cache().collect()
  ll = []
  for i in loc[1:]:
    ll.append(t.transform(i[0],i[1]))
  loc = pd.Series(ll,index = l2[1:])
  def mapper1(id, part):
    if id==0:
      next(part)
    for line in csv.reader(part):
      poi = str(line[18])
      vistors = json.loads(line[19])
      if line[0] in l1:
        
        if (str(line[12][0:7]) in ['2019-03','2019-10','2020-03','2020-10']) | (str(line[13][0:7]) in ['2019-03','2019-10','2020-03','2020-10']):
         
          if str(line[12][0:7]) in ['2019-03','2019-10','2020-03','2020-10']:
            date = str(line[12][0:7])
          else:
            date = str(line[13][0:7])
          for k in vistors.keys():
            if k in l2:
              distance = Point(loc[k]).distance(Point(loc[poi]))/5280
              trips = [distance] * vistors[k]
              yield ((k, date), trips)
  def mapper2(x):
    m = str(round(sum(x[1])/len(x[1]),2))
    if x[0][1] == '2019-03':
      return (x[0][0],m,'','','')
    elif x[0][1] == '2019-10':
      return (x[0][0],'',m,'','')
    elif x[0][1] == '2020-03':
      return (x[0][0],'','',m,'')
    elif x[0][1] == '2020-10':
      return (x[0][0],'','','',m)
  print("after mpper1", sc.textFile('/tmp/bdm/weekly-patterns-nyc-2019-2020/*', use_unicode=True).mapPartitionsWithIndex(mapper1).count())
  print("after reduceByKey", sc.textFile('/tmp/bdm/weekly-patterns-nyc-2019-2020/*', use_unicode=True).mapPartitionsWithIndex(mapper1).reduceByKey(lambda x,y: x+y).count())
  print("after mapper2", sc.textFile('/tmp/bdm/weekly-patterns-nyc-2019-2020/*', use_unicode=True).mapPartitionsWithIndex(mapper1).reduceByKey(lambda x,y: x+y).map(lambda x: mapper2(x)).count())

  
  
  # output1 = sc.textFile('/tmp/bdm/weekly-patterns-nyc-2019-2020/*', use_unicode=True).mapPartitionsWithIndex(mapper1) \
  #   .reduceByKey(lambda x,y: x+y) \
  #   .map(lambda x: mapper2(x))\
  #   .toDF(['cbg_fips', '2019-03' , '2019-10' , '2020-03' , '2020-10']) \
  #   .sort('cbg_fips', ascending = True)\
  #   .write.options(header = True).csv(sys.argv[1])

