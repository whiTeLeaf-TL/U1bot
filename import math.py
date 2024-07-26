import math

base_increase = 0.05
# 使用对数函数计算增加值，并设定最大增加值
print(min(base_increase * math.log1p(7), 0.25))
