packages <- available.packages()
write.csv(packages[,c(1,9)],"r-licenses.csv")
