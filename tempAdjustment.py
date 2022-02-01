def adjusted(amb, temp):
    if temp >= 43:
        return amb + temp + 10
    if temp >= 40:
        return amb + temp + 7
    if temp >= 35:
        return amb + temp + 5
    if temp >= 30:
        return amb + temp + 2
    if temp >= 25:
        return amb + temp -10
    else:
        return temp
