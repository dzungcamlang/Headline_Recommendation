# -*- coding: UTF-8 -*-

data = [('ddSub', 2.3513752571634776), ('H5', 2.3513752571634776), ('beforeCreate', 2.3513752571634776)]
print(data)
print()

def func(data):
    for index in range(len(data)):
        print(data[index], list(data[index]))
        data[index] = list(data[index]) # 元组转换为列表，为后续.append做准备
        print(data[index])
        data[index].append(index)
        data[index][1] = float(data[index][1])

func(data)
print(data)


print("-" * 30)


import json

data = {
    'name' : 'Connor',
    'sex' : 'boy',
    'age' : 26
}
print(data)
data1=json.dumps(data)
print(data1)
data2=json.loads(data1)
print(data2)
print(type(data))#输出原始数据格式
print(type(data1))#输出经过json.dumps的数据格式
print(type(data2))#输出经过json.loads的数据格式