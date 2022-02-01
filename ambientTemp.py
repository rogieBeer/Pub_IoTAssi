avg_temp = [20, 25, 22, 23, 20]



def average(tmp):
    
    if len(avg_temp) >= 100:
        avg_temp.pop(0)
    avg_temp.append(tmp)
    avg = sum(avg_temp)/len(avg_temp)
    print(avg_temp)
    return avg
   
  

